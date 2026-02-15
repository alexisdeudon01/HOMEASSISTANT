"""
Implémentation WebSocket.

Ce module fournit une implémentation du protocole WebSocket
avec support du pattern Observer.
"""

from typing import Dict, Any, Optional
from .base import Protocol, ProtocolState, ProtocolMessage


class WebSocketClient:
    """Client WebSocket."""
    
    def __init__(self, url: str):
        self.url = url
        self._connection = None
    
    async def connect(self) -> bool:
        """Établit la connexion WebSocket."""
        try:
            import websockets
            self._connection = await websockets.connect(self.url)
            return True
        except Exception as e:
            print(f"Erreur de connexion WebSocket: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion WebSocket."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def send(self, message: str) -> bool:
        """Envoie un message WebSocket."""
        if not self._connection:
            return False
        
        try:
            await self._connection.send(message)
            return True
        except Exception as e:
            print(f"Erreur d'envoi WebSocket: {e}")
            return False
    
    async def receive(self) -> Optional[str]:
        """Reçoit un message WebSocket."""
        if not self._connection:
            return None
        
        try:
            data = await self._connection.recv()
            if isinstance(data, bytes):
                return data.decode('utf-8')
            return str(data)
        except Exception as e:
            print(f"Erreur de réception WebSocket: {e}")
            return None


class WebSocketProtocol(Protocol):
    """Implémentation du protocole WebSocket."""
    
    def __init__(self, url: str):
        super().__init__("websocket")
        self.url = url
        self._client: Optional[WebSocketClient] = None
        self._listen_task = None
    
    async def connect(self) -> bool:
        """Établit la connexion WebSocket."""
        await self._notify_state_change(ProtocolState.CONNECTING)
        
        try:
            self._client = WebSocketClient(self.url)
            connected = await self._client.connect()
            if connected:
                await self._notify_state_change(ProtocolState.CONNECTED)
                return True
            else:
                await self._notify_state_change(ProtocolState.ERROR)
                return False
        except Exception as e:
            await self._notify_state_change(ProtocolState.ERROR, e)
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion WebSocket."""
        if self._client:
            await self._client.disconnect()
            self._client = None
        
        await self._notify_state_change(ProtocolState.DISCONNECTED)
    
    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publie un message WebSocket."""
        if not self._client:
            return False
        
        try:
            message = {
                'topic': topic,
                'payload': payload,
                'qos': qos,
                'retain': retain
            }
            import json
            return await self._client.send(json.dumps(message))
        except Exception:
            return False
    
    async def subscribe(self, topic: str, qos: int = 0) -> bool:
        """S'abonne à un topic WebSocket."""
        # Pour WebSocket, on écoute tous les messages
        return True
    
    async def unsubscribe(self, topic: str) -> bool:
        """Se désabonne d'un topic WebSocket."""
        return True
    
    async def send_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> Any:
        """
        Envoie une commande WebSocket.
        
        Args:
            device_id: ID du device
            command: Commande à exécuter
            parameters: Paramètres de la commande
            
        Returns:
            Réponse WebSocket
        """
        if not self._client:
            raise RuntimeError("Client WebSocket non connecté")
        
        # Pour WebSocket, on envoie un message JSON
        message = {
            "device_id": device_id,
            "command": command,
            "parameters": parameters
        }
        
        import json
        success = await self._client.send(json.dumps(message))
        
        if success:
            # On peut attendre une réponse si spécifié
            wait_for_response = parameters.get("wait_for_response", False)
            if wait_for_response:
                response = await self._client.receive()
                return {
                    "success": True,
                    "device_id": device_id,
                    "command": command,
                    "response": response
                }
            else:
                return {
                    "success": True,
                    "device_id": device_id,
                    "command": command
                }
        else:
            return {
                "success": False,
                "device_id": device_id,
                "command": command,
                "error": "Échec de l'envoi du message WebSocket"
            }
