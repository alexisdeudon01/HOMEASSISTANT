"""
Entités spécifiques MQTT.

Ce module définit les entités liées au protocole MQTT:
- MQTTEntity: entité générique MQTT
- MQTTDeviceEntity: entité MQTT avec device associé
- MQTTTopicEntity: entité basée sur un topic MQTT
"""

from typing import Optional, Dict, Any, List
from .base import BaseEntity, Device


class MQTTEntity(BaseEntity):
    """Entité générique MQTT."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        topic: str,
        device: Optional[Device] = None,
        qos: int = 0,
        retain: bool = False
    ):
        super().__init__(entity_id, name, device, domain="mqtt")
        self.topic = topic
        self.qos = qos
        self.retain = retain
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités MQTT."""
        return ["publish", "subscribe"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'topic': self.topic,
            'qos': self.qos,
            'retain': self.retain
        })
        return base


class MQTTDeviceEntity(MQTTEntity):
    """Entité MQTT avec device associé."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        topic: str,
        device: Device,
        qos: int = 0,
        retain: bool = False
    ):
        super().__init__(entity_id, name, topic, device, qos, retain)
        self.domain = f"mqtt_{device.type}"
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du device MQTT."""
        caps = super().get_capabilities()
        if self.device:
            caps.extend(self.device.capabilities.keys())
        return caps


class MQTTTopicEntity(BaseEntity):
    """Entité basée sur un topic MQTT."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        topic_pattern: str,
        device: Optional[Device] = None,
        value_template: Optional[str] = None
    ):
        super().__init__(entity_id, name, device, domain="mqtt_topic")
        self.topic_pattern = topic_pattern
        self.value_template = value_template
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du topic MQTT."""
        return ["pattern_match", "template_processing"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'topic_pattern': self.topic_pattern,
            'value_template': self.value_template
        })
        return base
