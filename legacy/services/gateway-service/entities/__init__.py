"""
Package entities - Hiérarchie d'entités modulaires.

Ce package contient toutes les structures de données pour les entités,
devices, états, et topics du système.
"""

from .base import (
    Device,
    State,
    BaseEntity,
    Service,
    Action,
    Prompt,
    EntityPrompt
)

from .device_entities import (
    SensorEntity,
    BinarySensorEntity,
    LightEntity,
    SwitchEntity,
    CoverEntity,
    ClimateEntity,
    MediaPlayerEntity
)

from .mqtt_entities import (
    MQTTEntity,
    MQTTDeviceEntity,
    MQTTTopicEntity
)

from .topic_entity import TopicEntity

__all__ = [
    # Base classes
    'Device',
    'State',
    'BaseEntity',
    'Service',
    'Action',
    'Prompt',
    'EntityPrompt',
    
    # Device entities
    'SensorEntity',
    'BinarySensorEntity',
    'LightEntity',
    'SwitchEntity',
    'CoverEntity',
    'ClimateEntity',
    'MediaPlayerEntity',
    
    # MQTT entities
    'MQTTEntity',
    'MQTTDeviceEntity',
    'MQTTTopicEntity',
    
    # Topic entity
    'TopicEntity'
]
