"""
Classes de base pour toutes les entités.

Ce module réexporte les classes de base depuis entities/models.py
pour maintenir la compatibilité.
"""

from entities.models import (
    Device,
    State,
    BaseEntity,
    Service,
    Action,
    Prompt,
    EntityPrompt,
    DeviceInfo,
    DeviceTopics,
    DiscoveredDevice
)

# Réexport pour la compatibilité
__all__ = [
    'Device',
    'State',
    'BaseEntity',
    'Service',
    'Action',
    'Prompt',
    'EntityPrompt',
    'DeviceInfo',
    'DeviceTopics',
    'DiscoveredDevice'
]
