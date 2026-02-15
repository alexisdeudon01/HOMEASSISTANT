"""
Classes de base pour les protocoles.

Ce module définit les interfaces et classes abstraites pour tous les protocoles.
Pattern Observer pour la notification des messages.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum


class ProtocolState(Enum):
    """États possibles d'un protocole."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ProtocolMessage:
    """Message générique pour les protocoles."""
    
    topic: str
    payload: Any
    timestamp: datetime = field(default_factory=datetime.now)
    qos: int = 0
    retain: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le message en dictionnaire."""
        return {
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'qos': self.qos,
            'retain': self.retain,
            'metadata': self.metadata
        }


class ProtocolObserver(ABC):
    """Observateur pour les messages des protocoles."""
    
    @abstractmethod
    async def on_message(self, message: ProtocolMessage) -> None:
        """Appelé lorsqu'un message est reçu."""
        pass
    
    @abstractmethod
    async def on_state_change(self, state: ProtocolState, error: Optional[Exception] = None) -> None:
        """Appelé lorsque l'état du protocole change."""
        pass


class Protocol(ABC):
    """Interface de base pour tous les protocoles."""
    
    def __init__(self, name: str):
        self.name = name
        self.state = ProtocolState.DISCONNECTED
        self.observers: List[ProtocolObserver] = []
        self._lock = asyncio.Lock()
    
    def add_observer(self, observer: ProtocolObserver) -> None:
        """Ajoute un observateur."""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: ProtocolObserver) -> None:
        """Retire un observateur."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    async def _notify_message(self, message: ProtocolMessage) -> None:
        """Notifie tous les observateurs d'un nouveau message."""
        tasks = [observer.on_message(message) for observer in self.observers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _notify_state_change(self, state: ProtocolState, error: Optional[Exception] = None) -> None:
        """Notifie tous les observateurs d'un changement d'état."""
        self.state = state
        tasks = [observer.on_state_change(state, error) for observer in self.observers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @abstractmethod
    async def connect(self) -> bool:
        """Établit la connexion."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Ferme la connexion."""
        pass
    
    @abstractmethod
    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publie un message."""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, qos: int = 0) -> bool:
        """S'abonne à un topic."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str) -> bool:
        """Se désabonne d'un topic."""
        pass
    
    @abstractmethod
    async def send_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> Any:
        """
        Envoie une commande à un device.
        
        Args:
            device_id: ID du device
            command: Commande à exécuter
            parameters: Paramètres de la commande
            
        Returns:
            Résultat de la commande
        """
        pass


class ProtocolFactory(ABC):
    """Factory pour créer des instances de protocoles."""
    
    @abstractmethod
    def create_protocol(self, config: Dict[str, Any]) -> Protocol:
        """Crée une instance de protocole."""
        pass
    
    @abstractmethod
    def get_supported_protocols(self) -> List[str]:
        """Retourne la liste des protocoles supportés."""
        pass
