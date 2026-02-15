"""
Modèles Pydantic pour le HA Manager Service.

Ce module contient tous les modèles de données utilisés par le service
pour la validation et la sérialisation des données.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


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


class WebhookPayload(BaseModel):
    """Modèle pour le payload d'un webhook."""
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    time_fired: Optional[datetime] = None


class ServiceHealth(BaseModel):
    """Modèle pour la santé du service."""
    status: str
    timestamp: str
    clients: Dict[str, bool]


class RedisStats(BaseModel):
    """Modèle pour les statistiques Redis."""
    redis_version: str
    connected_clients: int
    used_memory_human: str
    total_connections_received: int
    total_commands_processed: int
    stats: Dict[str, int]
