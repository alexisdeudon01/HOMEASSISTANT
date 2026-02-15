from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the system."""
    DEVICE = "device"
    SENSOR = "sensor"
    SWITCH = "switch"
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    CAMERA = "camera"
    MEDIA_PLAYER = "media_player"
    SCENE = "scene"
    AUTOMATION = "automation"
    USER = "user"
    GROUP = "group"


class EntityState(str, Enum):
    """Possible states of an entity."""
    UNKNOWN = "unknown"
    ON = "on"
    OFF = "off"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class ProtocolType(str, Enum):
    """Supported communication protocols."""
    MQTT = "mqtt"
    HTTP = "http"
    WEBSOCKET = "websocket"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    BLUETOOTH = "bluetooth"
    MODBUS = "modbus"


class BaseEntity(BaseModel):
    """Base entity model shared across all microservices."""
    id: str = Field(..., description="Unique identifier for the entity")
    name: str = Field(..., description="Human-readable name")
    entity_type: EntityType = Field(..., description="Type of entity")
    state: EntityState = Field(default=EntityState.UNKNOWN, description="Current state")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for the entity")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeviceEntity(BaseEntity):
    """Device-specific entity model."""
    protocol: ProtocolType = Field(..., description="Communication protocol")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")
    model: Optional[str] = Field(None, description="Device model")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    ip_address: Optional[str] = Field(None, description="IP address if applicable")
    mac_address: Optional[str] = Field(None, description="MAC address if applicable")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")
    is_online: bool = Field(default=False, description="Whether the device is currently online")


class SensorEntity(BaseEntity):
    """Sensor-specific entity model."""
    unit_of_measurement: Optional[str] = Field(None, description="Unit of measurement")
    device_class: Optional[str] = Field(None, description="Device class (temperature, humidity, etc.)")
    value: Optional[float] = Field(None, description="Current sensor value")
    last_value: Optional[float] = Field(None, description="Previous sensor value")
    min_value: Optional[float] = Field(None, description="Minimum expected value")
    max_value: Optional[float] = Field(None, description="Maximum expected value")
    accuracy: Optional[float] = Field(None, description="Sensor accuracy")


class Command(BaseModel):
    """Command model for controlling entities."""
    entity_id: str = Field(..., description="Target entity ID")
    command: str = Field(..., description="Command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Command timestamp")
    source: Optional[str] = Field(None, description="Source of the command")
    priority: int = Field(default=0, description="Command priority (higher = more important)")


class Event(BaseModel):
    """Event model for system events."""
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source: Optional[str] = Field(None, description="Source of the event")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class ServiceResponse(BaseModel):
    """Standard response model for all microservices."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
