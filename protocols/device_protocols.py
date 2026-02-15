"""
Interfaces de protocoles pour les devices.

Ce module définit les interfaces spécifiques pour différents types de devices
(lampe, interrupteur, capteur, etc.) qui étendent l'interface Protocol de base.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .base import Protocol, ProtocolMessage


class DeviceProtocol(Protocol, ABC):
    """Interface de base pour les protocoles de devices."""
    
    @abstractmethod
    async def discover(self) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        Découvre les devices disponibles.
        
        Returns:
            Données brutes des devices découverts
        """
        pass
    
    @abstractmethod
    async def get_state(self, device_id: str) -> Dict[str, Any]:
        """
        Récupère l'état d'un device.
        
        Args:
            device_id: ID du device
            
        Returns:
            État du device
        """
        pass
    
    @abstractmethod
    async def set_state(self, device_id: str, state: Dict[str, Any]) -> bool:
        """
        Définit l'état d'un device.
        
        Args:
            device_id: ID du device
            state: État à appliquer
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Extrait les capacités d'un device à partir de ses données.
        
        Args:
            device_data: Données brutes du device
            
        Returns:
            Dictionnaire des capacités (ex: {"has_color": True, "has_brightness": False})
        """
        pass


class LightProtocol(DeviceProtocol, ABC):
    """Interface pour les protocoles de lumières."""
    
    @abstractmethod
    async def set_brightness(self, device_id: str, brightness: int) -> bool:
        """
        Définit la luminosité d'une lumière.
        
        Args:
            device_id: ID du device
            brightness: Luminosité (0-254)
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def set_color(self, device_id: str, color: Dict[str, Any]) -> bool:
        """
        Définit la couleur d'une lumière.
        
        Args:
            device_id: ID du device
            color: Dictionnaire de couleur (HS, XY, CT, etc.)
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def set_color_temperature(self, device_id: str, ct: int) -> bool:
        """
        Définit la température de couleur d'une lumière.
        
        Args:
            device_id: ID du device
            ct: Température de couleur (mireds)
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extrait les capacités spécifiques aux lumières."""
        capabilities = super().get_capabilities(device_data)
        
        # Détection des capacités de lumière
        state = device_data.get("state", {})
        capabilities.update({
            "has_color": "hue" in state or "xy" in state,
            "has_brightness": "bri" in state,
            "has_ct": "ct" in state,
            "has_on_off": "on" in state,
        })
        
        return capabilities


class SwitchProtocol(DeviceProtocol, ABC):
    """Interface pour les protocoles d'interrupteurs."""
    
    @abstractmethod
    async def toggle(self, device_id: str) -> bool:
        """
        Bascule l'état d'un interrupteur.
        
        Args:
            device_id: ID du device
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extrait les capacités spécifiques aux interrupteurs."""
        capabilities = super().get_capabilities(device_data)
        
        # Détection des capacités d'interrupteur
        state = device_data.get("state", {})
        capabilities.update({
            "has_on_off": "on" in state,
            "has_toggle": True,
        })
        
        return capabilities


class SensorProtocol(DeviceProtocol, ABC):
    """Interface pour les protocoles de capteurs."""
    
    @abstractmethod
    async def get_measurements(self, device_id: str) -> Dict[str, Any]:
        """
        Récupère les mesures d'un capteur.
        
        Args:
            device_id: ID du device
            
        Returns:
            Mesures du capteur
        """
        pass
    
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extrait les capacités spécifiques aux capteurs."""
        capabilities = super().get_capabilities(device_data)
        
        # Détection des capacités de capteur
        state = device_data.get("state", {})
        capabilities.update({
            "has_measurements": len(state) > 0,
            "has_temperature": "temperature" in state,
            "has_humidity": "humidity" in state,
            "has_pressure": "pressure" in state,
            "has_illuminance": "illuminance" in state,
        })
        
        return capabilities


class CoverProtocol(DeviceProtocol, ABC):
    """Interface pour les protocoles de volets/rideaux."""
    
    @abstractmethod
    async def set_position(self, device_id: str, position: int) -> bool:
        """
        Définit la position d'un volet/rideau.
        
        Args:
            device_id: ID du device
            position: Position (0-100)
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def stop(self, device_id: str) -> bool:
        """
        Arrête le mouvement d'un volet/rideau.
        
        Args:
            device_id: ID du device
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extrait les capacités spécifiques aux volets."""
        capabilities = super().get_capabilities(device_data)
        
        # Détection des capacités de volet
        state = device_data.get("state", {})
        capabilities.update({
            "has_position": "position" in state,
            "has_tilt": "tilt" in state,
            "has_stop": True,
        })
        
        return capabilities


class ClimateProtocol(DeviceProtocol, ABC):
    """Interface pour les protocoles de climatisation."""
    
    @abstractmethod
    async def set_temperature(self, device_id: str, temperature: float) -> bool:
        """
        Définit la température d'un climatiseur.
        
        Args:
            device_id: ID du device
            temperature: Température cible
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def set_mode(self, device_id: str, mode: str) -> bool:
        """
        Définit le mode d'un climatiseur.
        
        Args:
            device_id: ID du device
            mode: Mode (heat, cool, auto, etc.)
            
        Returns:
            True si succès, False sinon
        """
        pass
    
    def get_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extrait les capacités spécifiques aux climatiseurs."""
        capabilities = super().get_capabilities(device_data)
        
        # Détection des capacités de climatisation
        state = device_data.get("state", {})
        capabilities.update({
            "has_temperature": "temperature" in state,
            "has_mode": "mode" in state,
            "has_fan_speed": "fan_speed" in state,
            "has_swing": "swing" in state,
        })
        
        return capabilities
