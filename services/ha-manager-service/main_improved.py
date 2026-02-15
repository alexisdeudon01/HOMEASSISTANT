"""
HA Manager Service - Service d'intégration avec Home Assistant (Version améliorée).

Ce service expose une API REST pour gérer l'intégration avec Home Assistant,
incluant la découverte de devices, la synchronisation des entités, et la gestion
des webhooks.

Améliorations apportées :
1. Configuration externalisée via Pydantic Settings
2. Meilleure gestion des erreurs avec des exceptions spécifiques
3. Utilisation correcte de aiomqtt avec un gestionnaire de connexion
4. Réduction de la duplication de code
5. Validation améliorée des données
6. Documentation plus complète
7. Sécurité améliorée pour les tokens
8. Gestion de la durée de vie avec lifespan (FastAPI)
9. Middleware de gestion des erreurs centralisée
10. Endpoint de santé détaillé
"""

import asyncio
import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr, validator
from pydantic_settings import BaseSettings

import httpx
import aiomqtt
import redis.asyncio as redis
from redis.exceptions import RedisError

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ha_manager_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration des paramètres
class Settings(BaseSettings):
    """Configuration du service HA Manager."""
    
    # Home Assistant
    ha_url: str = "http://homeassistant:int(os.getenv('HA_PORT', '8123'))"
    ha_token: SecretStr = SecretStr("dummy_token_for_testing")
    
    # Redis
    redis_url: str = "redis://redis:int(os.getenv('REDIS_PORT', '6379'))"
    
    # MQTT
    mqtt_broker: str = "mosquitto"
    mqtt_port: int = int(os.getenv('MQTT_PORT', '1883'))
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[SecretStr] = None
    
    # Service
    service_host: str = os.getenv('SERVICE_HOST', '0.0.0.0')
    service_port: int = 8001
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "ha_manager_"

# Initialisation des settings
settings = Settings()

# Modèles Pydantic pour l'API
class HADevice(BaseModel):
    """Modèle pour un device Home Assistant."""
    id: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    sw_version: Optional[str] = None
    via_device: Optional[str] = None
    area_id: Optional[str] = None

class HAEntity(BaseModel):
    """Modèle pour une entité Home Assistant."""
    entity_id: str
    name: Optional[str] = None
    state: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    last_changed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    device_id: Optional[str] = None
    domain: Optional[str] = None

class DeviceRegistration(BaseModel):
    """Modèle pour l'enregistrement d'un device."""
    device_id: str
    name: str
    domain: str = "sensor"
    manufacturer: str = "unknown"
    model: str = "unknown"
    sw_version: str = "1.0"
    identifiers: List[str] = Field(default_factory=list)
    connections: List[List[str]] = Field(default_factory=list)
    configuration_url: Optional[str] = None
    
    @validator('domain')
    def validate_domain(cls, v):
        """Valide que le domaine est valide."""
        valid_domains = ['sensor', 'binary_sensor', 'light', 'switch', 'cover', 'climate']
        if v not in valid_domains:
            raise ValueError(f"Domain must be one of {valid_domains}")
        return v

class EntityRegistration(BaseModel):
    """Modèle pour l'enregistrement d'une entité."""
    entity_id: str
    name: str
    device_id: str
    domain: str
    state_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None
    icon: Optional[str] = None
    options: Optional[List[str]] = None
    
    @validator('entity_id')
    def validate_entity_id(cls, v):
        """Valide le format de l'entity_id."""
        if '.' not in v:
            raise ValueError("entity_id must contain a dot (e.g., 'sensor.temperature')")
        return v

class WebhookPayload(BaseModel):
    """Modèle pour les webhooks Home Assistant."""
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    time_fired: Optional[datetime] = None

class StateUpdate(BaseModel):
    """Modèle pour la mise à jour d'état."""
    state: str
    attributes: Dict[str, Any] = Field(default_factory=dict)

# Exceptions personnalisées
class ServiceError(Exception):
    """Exception de base pour les erreurs du service."""
    pass

class HAConnectionError(ServiceError):
    """Erreur de connexion à Home Assistant."""
    pass

class RedisConnectionError(ServiceError):
    """Erreur de connexion à Redis."""
    pass

class MQTTConnectionError(ServiceError):
    """Erreur de connexion MQTT."""
    pass

# Gestionnaires de clients
class ClientManager:
    """Gestionnaire centralisé des clients."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.mqtt_client: Optional[aiomqtt.Client] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self._mqtt_connected = False
    
    async def init_redis(self) -> None:
        """Initialise le client Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_timeout=5.0
            )
            await self.redis_client.ping()
            logger.info("Client Redis initialisé avec succès")
        except RedisError as e:
            logger.error(f"Erreur de connexion Redis: {e}")
            raise RedisConnectionError(f"Impossible de se connecter à Redis: {e}")
    
    async def init_http(self) -> None:
        """Initialise le client HTTP pour Home Assistant."""
        try:
            self.http_client = httpx.AsyncClient(
                base_url=settings.ha_url,
                headers={
                    "Authorization": f"Bearer {settings.ha_token.get_secret_value()}",
                    "Content-Type": "application/json"
                },
                timeout=30.0,
                follow_redirects=True
            )
            # Test de connexion
            response = await self.http_client.get("/api/")
            response.raise_for_status()
            logger.info("Client HTTP pour Home Assistant initialisé avec succès")
        except httpx.RequestError as e:
            logger.error(f"Erreur de connexion à Home Assistant: {e}")
            raise HAConnectionError(f"Impossible de se connecter à Home Assistant: {e}")
    
    async def init_mqtt(self) -> None:
        """Initialise le client MQTT."""
        try:
            # Configuration MQTT
            mqtt_kwargs = {
                "hostname": settings.mqtt_broker,
                "port": settings.mqtt_port
            }
            
            if settings.mqtt_username:
                mqtt_kwargs["username"] = settings.mqtt_username
            if settings.mqtt_password:
                mqtt_kwargs["password"] = settings.mqtt_password.get_secret_value()
            
            self.mqtt_client = aiomqtt.Client(**mqtt_kwargs)
            logger.info("Client MQTT configuré")
        except Exception as e:
            logger.error(f"Erreur de configuration MQTT: {e}")
            raise MQTTConnectionError(f"Erreur de configuration MQTT: {e}")
    
    async def publish_mqtt(self, topic: str, payload: Dict[str, Any], retain: bool = True) -> None:
        """Publie un message MQTT."""
        if not self.mqtt_client:
            raise MQTTConnectionError("Client MQTT non initialisé")
        
        try:
            async with self.mqtt_client as client:
                await client.publish(
                    topic,
                    json.dumps(payload),
                    retain=retain,
                    qos=1  # Quality of Service level 1
                )
            logger.debug(f"Message MQTT publié sur {topic}")
        except Exception as e:
            logger.error(f"Erreur de publication MQTT: {e}")
            raise MQTTConnectionError(f"Erreur de publication MQTT: {e}")
    
    async def close(self) -> None:
        """Ferme proprement tous les clients."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Client HTTP fermé")
        
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Client Redis fermé")
        
        # Note: aiomqtt.Client se ferme automatiquement avec le contexte async with
        logger.info("Tous les clients fermés")

# Instance globale du gestionnaire de clients
client_manager = ClientManager()

# Gestionnaire de contexte pour l'application
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestionnaire de durée de vie de l'application."""
    logger.info("Démarrage du HA Manager Service...")
    
    try:
        # Initialisation séquentielle des clients
        await client_manager.init_redis()
        await client_manager.init_http()
        await client_manager.init_mqtt()
        logger.info("HA Manager Service démarré avec succès")
    except ServiceError as e:
        logger.error(f"Erreur lors du démarrage: {e}")
        # On continue malgré les erreurs de connexion pour permettre
        # à l'application de démarrer en mode dégradé
    
    yield
    
    logger.info("Arrêt du HA Manager Service...")
    await client_manager.close()
    logger.info("HA Manager Service arrêté")

# Création de l'application FastAPI
app = FastAPI(
    title="HA Manager Service",
    description="Service d'intégration avec Home Assistant (Version améliorée)",
    version="2.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de gestion des erreurs
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Middleware pour la gestion centralisée des erreurs."""
    try:
        response = await call_next(request)
        return response
    except ServiceError as e:
        logger.error(f"Erreur de service: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(e), "error_type": "service_error"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Une erreur interne est survenue", "error_type": "internal_error"}
        )

# Routes API
@app.get("/")
async def root():
    """Route racine."""
    return {
        "service": "HA Manager Service",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "clients": {
            "redis": client_manager.redis_client is not None,
            "http": client_manager.http_client is not None,
            "mqtt": client_manager.mqtt_client is not None
        }
    }

@app.get("/health")
async def health():
    """Endpoint de santé détaillé."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Vérification Redis
    if client_manager.redis_client:
        try:
            await client_manager.redis_client.ping()
            health_status["components"]["redis"] = "healthy"
        except RedisError:
            health_status["components"]["redis"] = "unhealthy"
    else:
        health_status["components"]["redis"] = "not_initialized"
    
    # Vérification HTTP
    if client_manager.http_client:
        try:
            response = await client_manager.http_client.get("/api/")
            response.raise_for_status()
            health_status["components"]["http"] = "healthy"
        except Exception:
            health_status["components"]["http"] = "unhealthy"
    else:
        health_status["components"]["http"] = "not_initialized"
    
    # Vérification MQTT
    health_status["components"]["mqtt"] = "configured" if client_manager.mqtt_client else "not_initialized"
    
    # Détermination du statut global
    if any(status == "unhealthy" for status in health_status["components"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/ha/status")
async def get_ha_status():
    """Récupère le statut de Home Assistant."""
    if not client_manager.http_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client HTTP non initialisé"
        )
    
    try:
        response = await client_manager.http_client.get("/api/")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Erreur de connexion à Home Assistant: {e}")
        raise HAConnectionError(f"Impossible de se connecter à Home Assistant: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP de Home Assistant: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Home Assistant a retourné une erreur: {e.response.text}"
        )

@app.get("/ha/devices")
async def get_ha_devices():
    """Récupère tous les devices de Home Assistant."""
    if not client_manager.http_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client HTTP non initialisé"
        )
    
    try:
        response = await client_manager.http_client.get("/api/devices")
        response.raise_for_status()
        devices_data = response.json()
        
        devices = []
        for device_data in devices_data:
            device = HADevice(
                id=device_data.get("id"),
                name=device_data.get("name"),
                manufacturer=device_data.get("manufacturer"),
                model=device_data.get("model"),
                sw_version=device_data.get("sw_version"),
                via_device=device_data.get("via_device"),
                area_id=device_data.get("area_id")
            )
            devices.append(device.dict())
        
        return {
            "count": len(devices),
            "devices": devices
        }
    except httpx.RequestError as e:
        logger.error(f"Erreur lors de la récupération des devices HA: {e}")
        raise HAConnectionError(f"Impossible de récupérer les devices: {e}")

@app.get("/ha/entities")
async def get_ha_entities():
    """Récupère toutes les entités de Home Assistant."""
    if not client_manager.http_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client HTTP non initialisé"
        )
    
    try:
        response = await client_manager.http_client.get("/api/states")
        response.raise_for_status()
        entities_data = response.json()
        
        entities = []
        for entity_data in entities_data:
            entity = HAEntity(
                entity_id=entity_data.get("entity_id"),
                name=entity_data.get("attributes", {}).get("friendly_name"),
                state=entity_data.get("state"),
                attributes=entity_data.get("attributes", {}),
                last_changed=datetime.fromisoformat(entity_data.get("last_changed").replace("Z", "+00:00")) if entity_data.get("last_changed") else None,
                last_updated=datetime.fromisoformat(entity_data.get("last_updated").replace("Z", "+00:00")) if entity_data.get("last_updated") else None
            )
            entities.append(entity.dict())
        
        return {
            "count": len(entities),
            "entities": entities
        }
    except httpx.RequestError as e:
        logger.error(f"Erreur lors de la récupération des entités HA: {e}")
        raise HAConnectionError(f"Impossible de récupérer les entités: {e}")

@app.post("/ha/devices/register")
async def register_device(device: DeviceRegistration):
    """Enregistre un nouveau device dans Home Assistant."""
    try:
        # Publication MQTT pour la découverte
        if client_manager.mqtt_client:
            discovery_topic = f"homeassistant/{device.domain}/{device.device_id}/config"
            discovery_payload = {
                "name": device.name,
                "device": {
                    "identifiers": [device.device_id] + device.identifiers,
                    "name": device.name,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "sw_version": device.sw_version,
                    "connections": device.connections,
                    "configuration_url": device.configuration_url
                },
                "state_topic": f"homeassistant/{device.domain}/{device.device_id}/state",
                "availability_topic": f"homeassistant/{device.domain}/{device.device_id}/availability",
                "unique_id": device.device_id
            }
            
            await client_manager.publish_mqtt(discovery_topic, discovery_payload)
            logger.info(f"Device {device.device_id} publié sur MQTT")
        
        # Enregistrement dans Redis
        if client_manager.redis_client:
            device_key = f"ha:device:{device.device_id}"
            await client_manager.redis_client.hset(device_key, mapping={
                "name": device.name,
                "domain": device.domain,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "sw_version": device.sw_version,
                "registered_at": datetime.now().isoformat()
            })
            logger.info(f"Device {device.device_id} enregistré dans Redis")
        
        return {
            "device_id": device.device_id,
            "name": device.name,
            "status": "registered",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du device {device.device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement du device: {e}"
        )

@app.post("/ha/entities/register")
async def register_entity(entity: EntityRegistration):
    """Enregistre une nouvelle entité pour un device."""
    try:
        # Vérification que le device existe
        if client_manager.redis_client:
            device_key = f"ha:device:{entity.device_id}"
            device_exists = await client_manager.redis_client.exists(device_key)
            if not device_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device {entity.device_id} non trouvé"
                )
        
        # Publication MQTT pour la découverte de l'entité
        if client_manager.mqtt_client:
            discovery_topic = f"homeassistant/{entity.domain}/{entity.entity_id}/config"
            discovery_payload = {
                "name": entity.name,
                "state_topic": f"homeassistant/{entity.domain}/{entity.entity_id}/state",
                "availability_topic": f"homeassistant/{entity.domain}/{entity.entity_id}/availability",
                "unique_id": entity.entity_id,
                "device": {
                    "identifiers": [entity.device_id]
                }
            }
            
            # Ajout des champs optionnels
            if entity.state_class:
                discovery_payload["state_class"] = entity.state_class
            if entity.unit_of_measurement:
                discovery_payload["unit_of_measurement"] = entity.unit_of_measurement
            if entity.device_class:
                discovery_payload["device_class"] = entity.device_class
            if entity.icon:
                discovery_payload["icon"] = entity.icon
            if entity.options:
                discovery_payload["options"] = entity.options
            
            await client_manager.publish_mqtt(discovery_topic, discovery_payload)
            logger.info(f"Entité {entity.entity_id} publiée sur MQTT")
        
        # Enregistrement dans Redis
        if client_manager.redis_client:
            entity_key = f"ha:entity:{entity.entity_id}"
            await client_manager.redis_client.hset(entity_key, mapping={
                "name": entity.name,
                "device_id": entity.device_id,
                "domain": entity.domain,
                "state_class": entity.state_class or "",
                "unit_of_measurement": entity.unit_of_measurement or "",
                "device_class": entity.device_class or "",
                "icon": entity.icon or "",
                "registered_at": datetime.now().isoformat()
            })
            logger.info(f"Entité {entity.entity_id} enregistrée dans Redis")
        
        return {
            "entity_id": entity.entity_id,
            "name": entity.name,
            "device_id": entity.device_id,
            "status": "registered",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'entité {entity.entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement de l'entité: {e}"
        )

@app.post("/ha/entities/{entity_id}/state")
async def update_entity_state(entity_id: str, state_update: StateUpdate):
    """Met à jour l'état d'une entité."""
    try:
        # Publication MQTT de l'état
        if client_manager.mqtt_client:
            # Extraction du domaine de l'entity_id (format: "domain.entity_id")
            if '.' in entity_id:
                domain = entity_id.split('.')[0]
                state_topic = f"homeassistant/{domain}/{entity_id}/state"
                
                payload = {
                    "state": state_update.state,
                    "attributes": state_update.attributes
                }
                
                await client_manager.publish_mqtt(state_topic, payload, retain=False)
                logger.info(f"État de l'entité {entity_id} mis à jour: {state_update.state}")
        
        # Mise à jour dans Redis
        if client_manager.redis_client:
            entity_key = f"ha:entity:{entity_id}"
            await client_manager.redis_client.hset(entity_key, mapping={
                "last_state": state_update.state,
                "last_updated": datetime.now().isoformat()
            })
            
            # Ajout à l'historique
            history_key = f"ha:entity:{entity_id}:history"
            history_entry = {
                "state": state_update.state,
                "attributes": json.dumps(state_update.attributes),
                "timestamp": datetime.now().isoformat()
            }
            await client_manager.redis_client.lpush(history_key, json.dumps(history_entry))
            # Garder seulement les 100 dernières entrées
            await client_manager.redis_client.ltrim(history_key, 0, 99)
        
        return {
            "entity_id": entity_id,
            "state": state_update.state,
            "status": "updated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'état de {entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de l'état: {e}"
        )

@app.get("/ha/devices/{device_id}")
async def get_device(device_id: str):
    """Récupère les informations d'un device spécifique."""
    if not client_manager.redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client Redis non initialisé"
        )
    
    try:
        device_key = f"ha:device:{device_id}"
        device_data = await client_manager.redis_client.hgetall(device_key)
        
        if not device_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} non trouvé"
            )
        
        return {
            "device_id": device_id,
            **device_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du device: {e}"
        )

@app.get("/ha/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Récupère les informations d'une entité spécifique."""
    if not client_manager.redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client Redis non initialisé"
        )
    
    try:
        entity_key = f"ha:entity:{entity_id}"
        entity_data = await client_manager.redis_client.hgetall(entity_key)
        
        if not entity_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entité {entity_id} non trouvé"
            )
        
        return {
            "entity_id": entity_id,
            **entity_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'entité {entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'entité: {e}"
        )

@app.post("/ha/webhook/{webhook_id}")
async def handle_webhook(webhook_id: str, payload: WebhookPayload, request: Request):
    """Gère les webhooks de Home Assistant."""
    logger.info(f"Webhook reçu: {webhook_id} - {payload.event_type}")
    
    # Log des headers pour le débogage
    headers = dict(request.headers)
    logger.debug(f"Headers du webhook: {headers}")
    
    # Traitement basé sur le type d'événement
    if payload.event_type == "state_changed":
        # Exemple: synchronisation avec Redis
        if client_manager.redis_client and payload.data:
            entity_id = payload.data.get("entity_id")
            new_state = payload.data.get("new_state", {})
            
            if entity_id and new_state:
                entity_key = f"ha:webhook:state:{entity_id}"
                await client_manager.redis_client.hset(entity_key, mapping={
                    "state": new_state.get("state", ""),
                    "last_changed": new_state.get("last_changed", ""),
                    "attributes": json.dumps(new_state.get("attributes", {})),
                    "received_at": datetime.now().isoformat()
                })
                logger.info(f"État synchronisé pour {entity_id}")
    
    return {
        "webhook_id": webhook_id,
        "event_type": payload.event_type,
        "status": "processed",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ha/sync")
async def sync_with_ha():
    """Synchronise les données avec Home Assistant."""
    if not client_manager.http_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client HTTP non initialisé"
        )
    
    try:
        # Récupération des devices et entités de HA
        devices_response = await client_manager.http_client.get("/api/devices")
        devices_response.raise_for_status()
        devices = devices_response.json()
        
        entities_response = await client_manager.http_client.get("/api/states")
        entities_response.raise_for_status()
        entities = entities_response.json()
        
        # Synchronisation avec Redis
        if client_manager.redis_client:
            # Synchronisation des devices
            for device in devices:
                device_id = device.get("id")
                if device_id:
                    device_key = f"ha:sync:device:{device_id}"
                    await client_manager.redis_client.hset(device_key, mapping={
                        "name": device.get("name", ""),
                        "manufacturer": device.get("manufacturer", ""),
                        "model": device.get("model", ""),
                        "sw_version": device.get("sw_version", ""),
                        "synced_at": datetime.now().isoformat()
                    })
            
            # Synchronisation des entités
            for entity in entities:
                entity_id = entity.get("entity_id")
                if entity_id:
                    entity_key = f"ha:sync:entity:{entity_id}"
                    await client_manager.redis_client.hset(entity_key, mapping={
                        "state": entity.get("state", ""),
                        "attributes": json.dumps(entity.get("attributes", {})),
                        "last_changed": entity.get("last_changed", ""),
                        "last_updated": entity.get("last_updated", ""),
                        "synced_at": datetime.now().isoformat()
                    })
        
        return {
            "status": "synced",
            "devices_count": len(devices),
            "entities_count": len(entities),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation avec HA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation: {e}"
        )
