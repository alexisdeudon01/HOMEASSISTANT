"""
HA Manager Service - Service d'intégration avec Home Assistant.

Ce service expose une API REST pour gérer l'intégration avec Home Assistant,
incluant la découverte de devices, la synchronisation des entités, et la gestion
des webhooks.
"""

import asyncio
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import httpx
import aiomqtt
import redis.asyncio as redis

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="HA Manager Service",
    description="Service d'intégration avec Home Assistant",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour l'API
class HADevice(BaseModel):
    id: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    sw_version: Optional[str] = None
    via_device: Optional[str] = None
    area_id: Optional[str] = None

class HAEntity(BaseModel):
    entity_id: str
    name: Optional[str] = None
    state: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    last_changed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    device_id: Optional[str] = None
    domain: Optional[str] = None

class DeviceRegistration(BaseModel):
    device_id: str
    name: str
    domain: str = "sensor"
    manufacturer: str = "unknown"
    model: str = "unknown"
    sw_version: str = "1.0"
    identifiers: List[str] = Field(default_factory=list)
    connections: List[List[str]] = Field(default_factory=list)
    configuration_url: Optional[str] = None

class EntityRegistration(BaseModel):
    entity_id: str
    name: str
    device_id: str
    domain: str
    state_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None
    icon: Optional[str] = None
    options: Optional[List[str]] = None

class WebhookPayload(BaseModel):
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    time_fired: Optional[datetime] = None

# Configuration (à externaliser)
HA_URL = "http://homeassistant:int(os.getenv('HA_PORT', '8123'))"
HA_TOKEN = "your_long_lived_access_token"
REDIS_URL = "redis://redis:int(os.getenv('REDIS_PORT', '6379'))"
MQTT_BROKER = "mosquitto"
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))

# Clients globaux
redis_client: Optional[redis.Redis] = None
mqtt_client: Optional[aiomqtt.Client] = None
http_client: Optional[httpx.AsyncClient] = None

# Initialisation des clients
async def init_clients():
    """Initialise les clients Redis, MQTT et HTTP."""
    global redis_client, mqtt_client, http_client
    
    try:
        # Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Client Redis initialisé")
        
        # HTTP
        http_client = httpx.AsyncClient(
            base_url=HA_URL,
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        logger.info("Client HTTP initialisé")
        
        # MQTT - utilisation du contexte async with
        mqtt_client = aiomqtt.Client(
            hostname=MQTT_BROKER,
            port=MQTT_PORT
        )
        # Note: aiomqtt.Client est utilisé avec async with, pas avec connect()
        # Nous allons le connecter dans une tâche séparée
        logger.info("Client MQTT configuré (connexion différée)")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des clients: {e}")
        raise

# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    logger.info("Démarrage du HA Manager Service...")
    await init_clients()
    logger.info("HA Manager Service démarré avec succès")

@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application."""
    logger.info("Arrêt du HA Manager Service...")
    
    if http_client:
        await http_client.aclose()
    
    # Note: aiomqtt.Client n'a pas de méthode disconnect()
    # La connexion est gérée via le contexte async with
    if mqtt_client:
        # Fermeture propre de la connexion MQTT
        try:
            await mqtt_client.__aexit__(None, None, None)
        except:
            pass
    
    if redis_client:
        await redis_client.aclose()
    
    logger.info("HA Manager Service arrêté")

# Routes API
@app.get("/")
async def root():
    """Route racine."""
    return {
        "service": "HA Manager Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Endpoint de santé."""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "clients": {
            "redis": redis_client is not None,
            "mqtt": mqtt_client is not None,
            "http": http_client is not None
        }
    }
    return status

@app.get("/ha/status")
async def get_ha_status():
    """Récupère le statut de Home Assistant."""
    if not http_client:
        raise HTTPException(status_code=500, detail="Client HTTP non initialisé")
    
    try:
        response = await http_client.get("/api/")
        return response.json()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut HA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ha/devices")
async def get_ha_devices():
    """Récupère tous les devices de Home Assistant."""
    if not http_client:
        raise HTTPException(status_code=500, detail="Client HTTP non initialisé")
    
    try:
        response = await http_client.get("/api/devices")
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
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des devices HA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ha/entities")
async def get_ha_entities():
    """Récupère toutes les entités de Home Assistant."""
    if not http_client:
        raise HTTPException(status_code=500, detail="Client HTTP non initialisé")
    
    try:
        response = await http_client.get("/api/states")
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
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des entités HA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/devices/register")
async def register_device(device: DeviceRegistration):
    """Enregistre un nouveau device dans Home Assistant."""
    try:
        # Publication MQTT pour la découverte
        if mqtt_client:
            discovery_topic = f"homeassistant/{device.domain}/{device.device_id}/config"
            discovery_payload = {
                "name": device.name,
                "device": {
                    "identifiers": device.identifiers or [device.device_id],
                    "name": device.name,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "sw_version": device.sw_version
                },
                "state_topic": f"homeassistant/{device.domain}/{device.device_id}/state",
                "availability_topic": f"homeassistant/{device.domain}/{device.device_id}/availability",
                "unique_id": device.device_id
            }
            
            if device.configuration_url:
                discovery_payload["device"]["configuration_url"] = device.configuration_url
            
            if device.connections:
                discovery_payload["device"]["connections"] = device.connections
            
            # Utilisation de async with pour la publication MQTT
            async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
                await client.publish(
                    discovery_topic,
                    json.dumps(discovery_payload),
                    retain=True
                )
            
            logger.info(f"Device enregistré via MQTT: {device.device_id}")
        
        # Stockage dans Redis
        if redis_client:
            await redis_client.hset(
                f"ha:devices:{device.device_id}",
                mapping=device.dict()
            )
            await redis_client.sadd("ha:devices:registered", device.device_id)
        
        return {
            "success": True,
            "device_id": device.device_id,
            "method": "mqtt_discovery",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/entities/register")
async def register_entity(entity: EntityRegistration):
    """Enregistre une nouvelle entité dans Home Assistant."""
    try:
        # Publication MQTT pour la découverte
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
        
        # Utilisation de async with pour la publication MQTT
        async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
            await client.publish(
                discovery_topic,
                json.dumps(discovery_payload),
                retain=True
            )
        
        logger.info(f"Entité enregistrée via MQTT: {entity.entity_id}")
    
        # Stockage dans Redis
        if redis_client:
            await redis_client.hset(
                f"ha:entities:{entity.entity_id}",
                mapping=entity.dict()
            )
            await redis_client.sadd("ha:entities:registered", entity.entity_id)
        
        return {
            "success": True,
            "entity_id": entity.entity_id,
            "method": "mqtt_discovery",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'entité: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/webhook/{webhook_id}")
async def handle_webhook(webhook_id: str, request: Request):
    """Gère les webhooks de Home Assistant."""
    try:
        payload = await request.json()
        
        # Log du webhook
        logger.info(f"Webhook reçu: {webhook_id}")
        logger.debug(f"Payload: {payload}")
        
        # Stockage dans Redis
        if redis_client:
            webhook_key = f"ha:webhooks:{webhook_id}:{datetime.now().isoformat()}"
            await redis_client.hset(webhook_key, mapping={
                "webhook_id": webhook_id,
                "payload": json.dumps(payload),
                "timestamp": datetime.now().isoformat()
            })
            await redis_client.expire(webhook_key, 86400)  # 24h
        
        # Traitement selon le type d'événement
        event_type = payload.get("event_type")
        
        if event_type == "state_changed":
            # Mise à jour de l'état dans Redis
            entity_id = payload.get("data", {}).get("entity_id")
            new_state = payload.get("data", {}).get("new_state", {})
            
            if entity_id and redis_client:
                await redis_client.hset(
                    f"ha:entities:state:{entity_id}",
                    mapping={
                        "state": new_state.get("state"),
                        "attributes": json.dumps(new_state.get("attributes", {})),
                        "last_changed": new_state.get("last_changed"),
                        "last_updated": new_state.get("last_updated"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        return {"success": True, "webhook_id": webhook_id}
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/entities/{entity_id}/state")
async def update_entity_state(entity_id: str, state: Dict[str, Any]):
    """Met à jour l'état d'une entité dans Home Assistant."""
    try:
        # Détermination du domaine à partir de l'entity_id
        domain = entity_id.split(".")[0] if "." in entity_id else "sensor"
        
        # Publication MQTT avec async with
        state_topic = f"homeassistant/{domain}/{entity_id}/state"
        async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
            await client.publish(
                state_topic,
                json.dumps(state),
                retain=True
            )
        
        logger.info(f"État mis à jour: {entity_id} = {state}")
        
        return {
            "success": True,
            "entity_id": entity_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'état: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/redis/stats")
async def get_redis_stats():
    """Récupère les statistiques Redis."""
    if not redis_client:
        raise HTTPException(status_code=500, detail="Client Redis non initialisé")
    
    try:
        info = await redis_client.info()
        
        # Comptage des clés
        device_count = await redis_client.scard("ha:devices:registered")
        entity_count = await redis_client.scard("ha:entities:registered")
        
        return {
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            os.getenv('METRICS_TOTAL_CONNECTIONS_RECEIVED', 'total_connections_received'): info.get(os.getenv('METRICS_TOTAL_CONNECTIONS_RECEIVED', 'total_connections_received')),
            os.getenv('METRICS_TOTAL_COMMANDS_PROCESSED', 'total_commands_processed'): info.get(os.getenv('METRICS_TOTAL_COMMANDS_PROCESSED', 'total_commands_processed')),
            "stats": {
                "devices_registered": device_count,
                "entities_registered": entity_count
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats Redis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv('SERVICE_HOST', '0.0.0.0'), port=8001)
