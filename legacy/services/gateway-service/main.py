"""
Gateway Service - Service principal pour la passerelle.

Ce service expose une API REST pour gérer les devices, entités et protocoles.
"""

import asyncio
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from protocols.mqtt import MQTTProtocol
from protocols.http import HTTPProtocol
from protocols.websocket import WebSocketProtocol
from entities.models import Device, DeviceInfo, DeviceTopics, DiscoveredDevice, BaseEntity
from entities.device_entities import SensorEntity, BinarySensorEntity, LightEntity, SwitchEntity, CoverEntity, ClimateEntity, MediaPlayerEntity
from entities.mqtt_entities import MQTTEntity, MQTTDeviceEntity, MQTTTopicEntity

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="Gateway Service",
    description="Service de passerelle pour la gestion des devices et protocoles",
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
class DeviceCreate(BaseModel):
    id: str
    protocol: str
    name: str
    type: str
    model: str = "unknown"
    manufacturer: str = "unknown"
    capabilities: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    metadata: Optional[Dict[str, Any]] = None

class EntityCreate(BaseModel):
    entity_id: str
    name: str
    domain: str
    device_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class CommandRequest(BaseModel):
    device_id: str
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

# Stockage en mémoire (à remplacer par une base de données)
devices: Dict[str, Device] = {}
entities: Dict[str, BaseEntity] = {}
protocols: Dict[str, Any] = {}

# Initialisation des protocoles
async def init_protocols():
    """Initialise les protocoles de communication."""
    try:
        # MQTT
        mqtt_protocol = MQTTProtocol()
        await mqtt_protocol.connect()
        protocols["mqtt"] = mqtt_protocol
        logger.info("Protocole MQTT initialisé")
        
        # HTTP
        http_protocol = HTTPProtocol()
        protocols["http"] = http_protocol
        logger.info("Protocole HTTP initialisé")
        
        # WebSocket
        ws_protocol = WebSocketProtocol("ws://localhost:int(os.getenv('GATEWAY_PORT', '8080'))/ws")
        protocols["websocket"] = ws_protocol
        logger.info("Protocole WebSocket initialisé")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des protocoles: {e}")

# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    logger.info("Démarrage du Gateway Service...")
    await init_protocols()
    logger.info("Gateway Service démarré avec succès")

@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application."""
    logger.info("Arrêt du Gateway Service...")
    for protocol_name, protocol in protocols.items():
        if hasattr(protocol, 'disconnect'):
            await protocol.disconnect()
    logger.info("Gateway Service arrêté")

# Routes API
@app.get("/")
async def root():
    """Route racine."""
    return {
        "service": "Gateway Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Endpoint de santé."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "protocols": list(protocols.keys())
    }

@app.get("/devices", response_model=List[Dict[str, Any]])
async def get_devices():
    """Récupère tous les devices."""
    return [device.to_dict() for device in devices.values()]

@app.get("/devices/{device_id}", response_model=Dict[str, Any])
async def get_device(device_id: str):
    """Récupère un device spécifique."""
    if device_id not in devices:
status_code = os.getenv("status_code", "404")
    return devices[device_id].to_dict()

@app.post("/devices", response_model=Dict[str, Any])
async def create_device(device_data: DeviceCreate):
    """Crée un nouveau device."""
    if device_data.id in devices:
status_code = os.getenv("status_code", "400")
    
    device = Device(
        id=device_data.id,
        protocol=device_data.protocol,
        name=device_data.name,
        type=device_data.type,
        model=device_data.model,
        manufacturer=device_data.manufacturer,
        capabilities=device_data.capabilities,
        metadata=device_data.metadata
    )
    
    devices[device.id] = device
    logger.info(f"Device créé: {device.id}")
    
    return device.to_dict()

@app.put("/devices/{device_id}", response_model=Dict[str, Any])
async def update_device(device_id: str, device_update: DeviceUpdate):
    """Met à jour un device existant."""
    if device_id not in devices:
status_code = os.getenv("status_code", "404")
    
    device = devices[device_id]
    
    if device_update.name is not None:
        device.name = device_update.name
    
    if device_update.capabilities is not None:
        device.capabilities = device_update.capabilities
    
    if device_update.metadata is not None:
        device.metadata.update(device_update.metadata)
    
    device.last_seen = datetime.now()
    logger.info(f"Device mis à jour: {device_id}")
    
    return device.to_dict()

@app.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Supprime un device."""
    if device_id not in devices:
status_code = os.getenv("status_code", "404")
    
    del devices[device_id]
    logger.info(f"Device supprimé: {device_id}")
    
    return {"message": "Device supprimé avec succès"}

@app.get("/entities", response_model=List[Dict[str, Any]])
async def get_entities():
    """Récupère toutes les entités."""
    return [entity.to_dict() for entity in entities.values()]

@app.post("/entities", response_model=Dict[str, Any])
async def create_entity(entity_data: EntityCreate):
    """Crée une nouvelle entité."""
    if entity_data.entity_id in entities:
status_code = os.getenv("status_code", "400")
    
    device = None
    if entity_data.device_id and entity_data.device_id in devices:
        device = devices[entity_data.device_id]
    
    # Création de l'entité selon le domaine
    if entity_data.domain == "sensor":
        entity = SensorEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "binary_sensor":
        entity = BinarySensorEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "light":
        entity = LightEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "switch":
        entity = SwitchEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "cover":
        entity = CoverEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "climate":
        entity = ClimateEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "media_player":
        entity = MediaPlayerEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device
        )
    elif entity_data.domain == "mqtt":
        entity = MQTTEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            topic=entity_data.attributes.get("topic", ""),
            device=device
        )
    else:
        # Entité générique
        entity = BaseEntity(
            entity_id=entity_data.entity_id,
            name=entity_data.name,
            device=device,
            domain=entity_data.domain
        )
    
    entities[entity.entity_id] = entity
    logger.info(f"Entité créée: {entity.entity_id}")
    
    return entity.to_dict()

@app.post("/command")
async def send_command(command: CommandRequest):
    """Envoie une commande à un device."""
    if command.device_id not in devices:
status_code = os.getenv("status_code", "404")
    
    device = devices[command.device_id]
    protocol = protocols.get(device.protocol)
    
    if not protocol:
status_code = os.getenv("status_code", "400")
    
    try:
        # Exécution de la commande via le protocole
        result = await protocol.send_command(
            device_id=device.id,
            command=command.command,
            parameters=command.parameters
        )
        
        logger.info(f"Commande exécutée: {command.command} sur {device.id}")
        
        return {
            "success": True,
            "device_id": device.id,
            "command": command.command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande: {e}")
status_code = os.getenv("status_code", "500")

@app.get("/protocols")
async def get_protocols():
    """Récupère la liste des protocoles disponibles."""
    return {
        "protocols": list(protocols.keys()),
        "status": {name: "connected" if hasattr(p, 'is_connected') and p.is_connected else "disconnected" 
                  for name, p in protocols.items()}
    }

@app.get("/discover")
async def discover_devices(protocol: str = "mqtt"):
    """Découvre les devices via un protocole."""
    if protocol not in protocols:
status_code = os.getenv("status_code", "400")
    
    try:
        discovered = await protocols[protocol].discover()
        
        # Conversion en DiscoveredDevice
        discovered_devices = []
        for device_data in discovered:
            discovered_device = DiscoveredDevice(
                device_id=device_data.get("id", ""),
                name=device_data.get("name", ""),
                manufacturer=device_data.get("manufacturer"),
                model=device_data.get("model"),
                protocol=protocol,
                capabilities=device_data.get("capabilities", []),
                raw_config=device_data
            )
            discovered_devices.append(discovered_device.to_dict())
        
        return {
            "protocol": protocol,
            "count": len(discovered_devices),
            "devices": discovered_devices
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la découverte: {e}")
status_code = os.getenv("status_code", "500")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv('SERVICE_HOST', '0.0.0.0'), port=8000)
