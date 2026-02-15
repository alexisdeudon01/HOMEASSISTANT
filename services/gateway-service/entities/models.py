"""
Modèles fusionnés pour toutes les entités.

Ce module combine:
- Device de entities/base.py
- DeviceInfo et DeviceTopics de ha_manager/models.py
- DiscoveredDevice de ha_manager/models.py
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
from abc import ABC, abstractmethod


@dataclass
class Device:
    """Représente un device physique ou virtuel."""
    
    id: str
    protocol: str
    name: str
    type: str
    capabilities: Dict[str, bool] = field(default_factory=dict)
    model: str = "unknown"
    manufacturer: str = "unknown"
    last_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le device en dictionnaire."""
        result = asdict(self)
        result['last_seen'] = self.last_seen.isoformat()
        return result
    
    def to_json(self) -> str:
        """Convertit le device en JSON."""
        return json.dumps(self.to_dict())


@dataclass
class DeviceInfo:
    """Device information for HA discovery (compatible avec Home Assistant)."""
    
    identifiers: List[str]
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    sw_version: Optional[str] = None
    hw_version: Optional[str] = None
    via_device: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"identifiers": self.identifiers, "name": self.name}
        if self.manufacturer:
            result["manufacturer"] = self.manufacturer
        if self.model:
            result["model"] = self.model
        if self.sw_version:
            result["sw_version"] = self.sw_version
        if self.via_device:
            result["via_device"] = self.via_device
        return result
    
    @classmethod
    def from_device(cls, device: Device) -> "DeviceInfo":
        """Crée un DeviceInfo à partir d'un Device."""
        return cls(
            identifiers=[device.id],
            name=device.name,
            manufacturer=device.manufacturer,
            model=device.model,
            sw_version=device.metadata.get("sw_version"),
            hw_version=device.metadata.get("hw_version")
        )


@dataclass
class DeviceTopics:
    """MQTT topics pour un device."""
    
    device_id: str
    component: str
    discovery: str
    state: str
    command: Optional[str] = None
    availability: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "component": self.component,
            "discovery": self.discovery,
            "state": self.state,
            "command": self.command,
            "availability": self.availability,
        }


@dataclass
class DiscoveredDevice:
    """Un device découvert via MQTT."""
    
    device_id: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    protocol: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    raw_config: Dict[str, Any] = field(default_factory=dict)
    topics: Optional[DeviceTopics] = None
    
    def to_device(self) -> Device:
        """Convertit en Device standard."""
        return Device(
            id=self.device_id,
            protocol=self.protocol,
            name=self.name,
            type=self.raw_config.get("type", "generic"),
            capabilities={cap: True for cap in self.capabilities},
            model=self.model or "unknown",
            manufacturer=self.manufacturer or "unknown",
            metadata=self.raw_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le device découvert en dictionnaire."""
        return {
            'device_id': self.device_id,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'protocol': self.protocol,
            'capabilities': self.capabilities,
            'raw_config': self.raw_config,
            'topics': self.topics.to_dict() if self.topics else None
        }


@dataclass
class State:
    """Représente l'état d'une entité."""
    
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'état en dictionnaire."""
        return {
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'attributes': self.attributes
        }


class BaseEntity(ABC):
    """Classe de base abstraite pour toutes les entités."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        state: Optional[State] = None,
        domain: str = "generic"
    ):
        self.entity_id = entity_id
        self.name = name
        self.device = device
        self.state = state
        self.domain = domain
    
    def update_state(self, value: Any, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Met à jour l'état de l'entité."""
        self.state = State(
            value=value,
            attributes=attributes or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            'entity_id': self.entity_id,
            'name': self.name,
            'domain': self.domain,
            'device': self.device.to_dict() if self.device else None,
            'state': self.state.to_dict() if self.state else None
        }
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités de l'entité."""
        # Implémentation par défaut qui peut être surchargée
        if self.device:
            return list(self.device.capabilities.keys())
        return []


@dataclass
class Service:
    """Représente un service disponible."""
    
    domain: str
    service: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le service en dictionnaire."""
        return {
            'domain': self.domain,
            'service': self.service,
            'data': self.data
        }


class Action(ABC):
    """Classe de base pour les actions exécutables."""
    
    def __init__(
        self,
        name: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.name = name
        self.target = target
        self.parameters = parameters or {}
        self.timestamp = timestamp or datetime.now()
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Exécute l'action."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'action en dictionnaire."""
        return {
            'name': self.name,
            'target': self.target,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Prompt:
    """Prompt abstrait pour l'IA."""
    
    role: str = "user"
    content: str = ""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le prompt en dictionnaire."""
        return {
            'role': self.role,
            'content': self.content,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
    
    def to_message_format(self) -> Dict[str, str]:
        """Convertit en format message pour l'API."""
        return {
            'role': self.role,
            'content': self.content
        }


@dataclass
class EntityPrompt(Prompt):
    """Prompt qui inclut une entité JSON sérialisable."""
    
    entity: Optional[BaseEntity] = None
    entity_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialisation après création."""
        if self.entity and not self.entity_data:
            self.entity_data = self.entity.to_dict()
        
        if self.entity_data and not self.content:
            self.content = json.dumps(self.entity_data, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le prompt en dictionnaire."""
        base = super().to_dict()
        base.update({
            'entity_data': self.entity_data
        })
        return base
