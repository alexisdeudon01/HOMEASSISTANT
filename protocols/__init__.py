"""
Package protocols - Implémentations des protocoles de communication.

Ce package contient les implémentations des différents protocoles
supportés par le système (MQTT, HTTP, WebSocket, etc.).
"""

from .base import Protocol, ProtocolFactory, ProtocolObserver
from .mqtt import MQTTProtocol, MQTTClient, MQTTMessage
from .http import HTTPProtocol, HTTPClient, HTTPRequest, HTTPResponse
from .websocket import WebSocketProtocol, WebSocketClient
from .device_protocols import (
    DeviceProtocol,
    LightProtocol,
    SwitchProtocol,
    SensorProtocol,
    CoverProtocol,
    ClimateProtocol
)

__all__ = [
    # Base classes
    'Protocol',
    'ProtocolFactory',
    'ProtocolObserver',
    
    # MQTT
    'MQTTProtocol',
    'MQTTClient',
    'MQTTMessage',
    
    # HTTP
    'HTTPProtocol',
    'HTTPClient',
    'HTTPRequest',
    'HTTPResponse',
    
    # WebSocket
    'WebSocketProtocol',
    'WebSocketClient',
    
    # Device protocols
    'DeviceProtocol',
    'LightProtocol',
    'SwitchProtocol',
    'SensorProtocol',
    'CoverProtocol',
    'ClimateProtocol'
]
