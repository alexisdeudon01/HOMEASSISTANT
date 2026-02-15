"""
HA Manager Service - Service d'intégration avec Home Assistant (Version Refactorée).

Ce service expose une API REST pour gérer l'intégration avec Home Assistant,
incluant la découverte de devices, la synchronisation des entités, et la gestion
des webhooks. Cette version utilise les clients HTTP pour communiquer avec les
autres services de l'architecture Sinik OS.
"""

import asyncio
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware

from data.models.ha_models import (
    HADevice, HAEntity, DeviceRegistration, EntityRegistration,
    WebhookPayload, ServiceHealth, RedisStats
)
from data.service_client.http_client import ServiceClientManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="HA Manager Service",
    description="Service d'intégration avec Home Assistant (Version Refactorée)",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration (à externaliser)
HA_URL = "http://homeassistant:int(os.getenv('HA_PORT', '8123'))"
HA_TOKEN = "your_long_lived_access_token"

# Gestionnaire de clients globaux
service_clients: Optional[ServiceClientManager] = None

# Initialisation des clients
async def init_clients():
    """Initialise les clients de service."""
    global service_clients
    
    try:
        service_clients = ServiceClientManager()
        await service_clients.connect_all()
        logger.info("Tous les clients de service sont initialisés")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des clients: {e}")
        raise

# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    logger.info("Démarrage du HA Manager Service (Version Refactorée)...")
    await init_clients()
    logger.info("HA Manager Service démarré avec succès")

@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application."""
    logger.info("Arrêt du HA Manager Service...")
    
    if service_clients:
        await service_clients.disconnect_all()
    
    logger.info("HA Manager Service arrêté")

# Routes API
@app.get("/")
async def root():
    """Route racine."""
    return {
        "service": "HA Manager Service (Version Refactorée)",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "architecture": "microservices avec clients HTTP"
    }

@app.get("/health")
async def health() -> ServiceHealth:
    """Endpoint de santé."""
    return ServiceHealth(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        clients={
            "service_clients": service_clients is not None
        }
    )

@app.get("/ha/status")
async def get_ha_status():
    """Récupère le statut de Home Assistant."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        # Utilisation du client HTTP pour Home Assistant
        async with service_clients.gateway_client as client:
            # Note: Home Assistant n'est pas un service Sinik OS, donc on utilise httpx directement
            # Pour l'instant, on retourne un statut simulé
            return {
                "message": "Home Assistant status endpoint",
                "note": "Cette route nécessite une intégration directe avec l'API Home Assistant",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut HA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/gateway/devices")
async def get_gateway_devices():
    """Récupère tous les devices depuis le Gateway Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        devices = await service_clients.gateway_client.get_devices()
        return {
            "count": len(devices),
            "devices": devices,
            "source": "gateway-service",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/entity/entities")
async def get_entity_entities():
    """Récupère toutes les entités depuis l'Entity Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        entities = await service_clients.entity_client.get_entities()
        return {
            "count": len(entities),
            "entities": entities,
            "source": "entity-service",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des entités: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/protocol/protocols")
async def get_protocol_protocols():
    """Récupère tous les protocoles depuis le Protocol Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        protocols = await service_clients.protocol_client.get_protocols()
        return {
            "count": len(protocols),
            "protocols": protocols,
            "source": "protocol-service",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des protocoles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/gateway/devices/register")
async def register_gateway_device(device: DeviceRegistration):
    """Enregistre un nouveau device via le Gateway Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        result = await service_clients.gateway_client.create_device(device.dict())
        return {
            "success": True,
            "device_id": device.device_id,
            "result": result,
            "method": "gateway-service-api",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/entity/entities/register")
async def register_entity_service_entity(entity: EntityRegistration):
    """Enregistre une nouvelle entité via l'Entity Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        result = await service_clients.entity_client.create_entity(entity.dict())
        return {
            "success": True,
            "entity_id": entity.entity_id,
            "result": result,
            "method": "entity-service-api",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'entité: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/protocol/execute")
async def execute_protocol_command(protocol: str, command: str, params: Dict[str, Any]):
    """Exécute une commande via un protocole spécifique."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        result = await service_clients.protocol_client.execute_protocol_command(
            protocol, command, params
        )
        return {
            "success": True,
            "protocol": protocol,
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/brain/intent")
async def process_brain_intent(intent: str, context: Dict[str, Any]):
    """Traite une intention avec le Brain Service."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        result = await service_clients.brain_client.process_intent(intent, context)
        return {
            "success": True,
            "intent": intent,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'intention: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/brain/decision")
async def get_brain_decision(situation: Dict[str, Any]):
    """Obtient une décision pour une situation donnée."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        result = await service_clients.brain_client.get_decision(situation)
        return {
            "success": True,
            "situation": situation,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention de la décision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/webhook/{webhook_id}")
async def handle_webhook(webhook_id: str, request: Request):
    """Gère les webhooks de Home Assistant."""
    try:
        payload = await request.json()
        
        # Log du webhook
        logger.info(f"Webhook reçu: {webhook_id}")
        logger.debug(f"Payload: {payload}")
        
        # Traitement selon le type d'événement
        event_type = payload.get("event_type")
        
        if event_type == "state_changed":
            # Mise à jour de l'état dans l'Entity Service
            entity_id = payload.get("data", {}).get("entity_id")
            new_state = payload.get("data", {}).get("new_state", {})
            
            if entity_id and service_clients:
                try:
                    await service_clients.entity_client.update_entity_state(
                        entity_id,
                        new_state.get("state", ""),
                        new_state.get("attributes", {})
                    )
                    logger.info(f"État synchronisé avec Entity Service: {entity_id}")
                except Exception as e:
                    logger.warning(f"Impossible de synchroniser l'état avec Entity Service: {e}")
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/sync")
async def sync_all_services():
    """Synchronise les données entre tous les services."""
    if not service_clients:
        raise HTTPException(status_code=500, detail="Clients de service non initialisés")
    
    try:
        # Récupération des données de tous les services
        devices = await service_clients.gateway_client.get_devices()
        entities = await service_clients.entity_client.get_entities()
        protocols = await service_clients.protocol_client.get_protocols()
        
        return {
            "success": True,
            "sync": {
                "devices": len(devices),
                "entities": len(entities),
                "protocols": len(protocols)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv('SERVICE_HOST', '0.0.0.0'), port=8001)
