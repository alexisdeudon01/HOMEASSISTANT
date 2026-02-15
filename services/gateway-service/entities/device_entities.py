"""
Entités de device spécifiques.

Ce module définit les entités concrètes pour différents types de devices:
- SensorEntity: capteurs
- BinarySensorEntity: capteurs binaires
- LightEntity: lumières
- SwitchEntity: interrupteurs
- CoverEntity: volets/rideaux
- ClimateEntity: climatisation
- MediaPlayerEntity: média
"""

from typing import Optional, Dict, Any, List
from .base import BaseEntity, Device


class SensorEntity(BaseEntity):
    """Entité de type capteur."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        device_class: Optional[str] = None,
        unit_of_measurement: Optional[str] = None,
        state_class: Optional[str] = None
    ):
        super().__init__(entity_id, name, device, domain="sensor")
        self.device_class = device_class
        self.unit_of_measurement = unit_of_measurement
        self.state_class = state_class
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du capteur."""
        caps = ["measure"]
        if self.device_class:
            caps.append(f"measure_{self.device_class}")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'device_class': self.device_class,
            'unit_of_measurement': self.unit_of_measurement,
            'state_class': self.state_class
        })
        return base


class BinarySensorEntity(BaseEntity):
    """Entité de type capteur binaire."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        device_class: Optional[str] = None
    ):
        super().__init__(entity_id, name, device, domain="binary_sensor")
        self.device_class = device_class
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du capteur binaire."""
        caps = ["binary_measure"]
        if self.device_class:
            caps.append(f"binary_{self.device_class}")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'device_class': self.device_class
        })
        return base


class LightEntity(BaseEntity):
    """Entité de type lumière."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        brightness: bool = True,
        color_temp: bool = False,
        rgb_color: bool = False
    ):
        super().__init__(entity_id, name, device, domain="light")
        self.brightness = brightness
        self.color_temp = color_temp
        self.rgb_color = rgb_color
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités de la lumière."""
        caps = ["turn_on", "turn_off"]
        if self.brightness:
            caps.append("brightness")
        if self.color_temp:
            caps.append("color_temp")
        if self.rgb_color:
            caps.append("rgb_color")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'brightness': self.brightness,
            'color_temp': self.color_temp,
            'rgb_color': self.rgb_color
        })
        return base


class SwitchEntity(BaseEntity):
    """Entité de type interrupteur."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None
    ):
        super().__init__(entity_id, name, device, domain="switch")
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités de l'interrupteur."""
        return ["turn_on", "turn_off"]


class CoverEntity(BaseEntity):
    """Entité de type volet/rideau."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        position: bool = True,
        tilt: bool = False
    ):
        super().__init__(entity_id, name, device, domain="cover")
        self.position = position
        self.tilt = tilt
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du volet."""
        caps = ["open", "close", "stop"]
        if self.position:
            caps.append("set_position")
        if self.tilt:
            caps.append("tilt")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'position': self.position,
            'tilt': self.tilt
        })
        return base


class ClimateEntity(BaseEntity):
    """Entité de type climatisation."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        temperature: bool = True,
        humidity: bool = False,
        fan_mode: bool = False,
        swing_mode: bool = False
    ):
        super().__init__(entity_id, name, device, domain="climate")
        self.temperature = temperature
        self.humidity = humidity
        self.fan_mode = fan_mode
        self.swing_mode = swing_mode
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du climatiseur."""
        caps = ["set_temperature"] if self.temperature else []
        if self.humidity:
            caps.append("set_humidity")
        if self.fan_mode:
            caps.append("set_fan_mode")
        if self.swing_mode:
            caps.append("set_swing_mode")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'temperature': self.temperature,
            'humidity': self.humidity,
            'fan_mode': self.fan_mode,
            'swing_mode': self.swing_mode
        })
        return base


class MediaPlayerEntity(BaseEntity):
    """Entité de type lecteur média."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        volume: bool = True,
        source: bool = False,
        media_content: bool = False
    ):
        super().__init__(entity_id, name, device, domain="media_player")
        self.volume = volume
        self.source = source
        self.media_content = media_content
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du lecteur média."""
        caps = ["play", "pause", "stop", "next", "previous"]
        if self.volume:
            caps.append("volume_set")
        if self.source:
            caps.append("select_source")
        if self.media_content:
            caps.append("play_media")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'volume': self.volume,
            'source': self.source,
            'media_content': self.media_content
        })
        return base
