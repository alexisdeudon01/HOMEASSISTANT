"""
Implémentation MQTT avec pattern Observer.

Ce module fournit une implémentation complète du protocole MQTT
utilisant aiomqtt avec support du pattern Observer.
"""

import asyncio
import os
import json
from typing import Dict, Any, List, Optional, Callable, Union, Awaitable
import aiomqtt
from .base import Protocol, ProtocolObserver, ProtocolState, ProtocolMessage


class MQTTMessage(ProtocolMessage):
    """Message MQTT spécialisé."""
    
    def __init__(
        self,
        topic: str,
        payload: Any,
        qos: int = 0,
        retain: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(topic, payload, qos=qos, retain=retain, metadata=metadata or {})
    
    @classmethod
    def from_aiomqtt(cls, message: aiomqtt.Message) -> 'MQTTMessage':
        """Crée un MQTTMessage à partir d'un message aiomqtt."""
        try:
            payload = json.loads(message.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = message.payload.decode()
        
        return cls(
            topic=str(message.topic),
            payload=payload,
            qos=message.qos,
            retain=message.retain,
            metadata={
                'mid': message.mid,
                'properties': message.properties
            }
        )


class MQTTClient:
    """Client MQTT wrapper autour de aiomqtt."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = int(os.getenv('MQTT_PORT', '1883')),
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        keepalive: int = 60,
        tls: bool = False
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.keepalive = keepalive
        self.tls = tls
        
        self._client: Optional[aiomqtt.Client] = None
        self._connected = False
        self._subscriptions: Dict[str, int] = {}
    
    async def connect(self) -> bool:
        """Établit la connexion MQTT."""
        try:
            self._client = aiomqtt.Client(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                identifier=self.client_id,
                keepalive=self.keepalive
            )
            
            await self._client.__aenter__()
            self._connected = True
            return True
        except Exception as e:
            print(f"Erreur de connexion MQTT: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion MQTT."""
        if self._client and self._connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                print(f"Erreur de déconnexion MQTT: {e}")
            finally:
                self._connected = False
                self._client = None
    
    async def publish(
        self,
        topic: str,
        payload: Any,
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """Publie un message MQTT."""
        if not self._connected or not self._client:
            return False
        
        try:
            if isinstance(payload, (dict, list)):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)
            
            await self._client.publish(topic, payload_str, qos=qos, retain=retain)
            return True
        except Exception as e:
            print(f"Erreur de publication MQTT: {e}")
            return False
    
    async def subscribe(self, topic: str, qos: int = 0) -> bool:
        """S'abonne à un topic MQTT."""
        if not self._connected or not self._client:
            return False
        
        try:
            await self._client.subscribe(topic, qos=qos)
            self._subscriptions[topic] = qos
            return True
        except Exception as e:
            print(f"Erreur d'abonnement MQTT: {e}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """Se désabonne d'un topic MQTT."""
        if not self._connected or not self._client:
            return False
        
        try:
            await self._client.unsubscribe(topic)
            self._subscriptions.pop(topic, None)
            return True
        except Exception as e:
            print(f"Erreur de désabonnement MQTT: {e}")
            return False
    
    async def listen(self, callback: Union[Callable[[MQTTMessage], None], Callable[[MQTTMessage], Awaitable[None]]]) -> None:
        """Écoute les messages MQTT (à exécuter dans une tâche séparée)."""
        if not self._connected or not self._client:
            return
        
        async for message in self._client.messages:
            mqtt_message = MQTTMessage.from_aiomqtt(message)
            # Si le callback est async, on l'attend
            result = callback(mqtt_message)
            if asyncio.iscoroutine(result):
                await result


class MQTTProtocol(Protocol):
    """Implémentation du protocole MQTT."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = int(os.getenv('MQTT_PORT', '1883')),
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        keepalive: int = 60,
        tls: bool = False
    ):
        super().__init__("mqtt")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.keepalive = keepalive
        self.tls = tls
        
        self._client: Optional[MQTTClient] = None
        self._listen_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Établit la connexion MQTT."""
        await self._notify_state_change(ProtocolState.CONNECTING)
        
        try:
            self._client = MQTTClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                client_id=self.client_id,
                keepalive=self.keepalive,
                tls=self.tls
            )
            
            connected = await self._client.connect()
            if connected:
                await self._notify_state_change(ProtocolState.CONNECTED)
                self._start_listening()
                return True
            else:
                await self._notify_state_change(ProtocolState.ERROR)
                return False
        except Exception as e:
            await self._notify_state_change(ProtocolState.ERROR, e)
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion MQTT."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        
        if self._client:
            await self._client.disconnect()
            self._client = None
        
        await self._notify_state_change(ProtocolState.DISCONNECTED)
    
    async def publish(
        self,
        topic: str,
        payload: Any,
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """Publie un message MQTT."""
        if not self._client:
            return False
        
        return await self._client.publish(topic, payload, qos, retain)
    
    async def subscribe(self, topic: str, qos: int = 0) -> bool:
        """S'abonne à un topic MQTT."""
        if not self._client:
            return False
        
        return await self._client.subscribe(topic, qos)
    
    async def unsubscribe(self, topic: str) -> bool:
        """Se désabonne d'un topic MQTT."""
        if not self._client:
            return False
        
        return await self._client.unsubscribe(topic)
    
    def _start_listening(self) -> None:
        """Démarre l'écoute des messages."""
        if self._client:
            self._listen_task = asyncio.create_task(self._listen_loop())
    
    async def _listen_loop(self) -> None:
        """Boucle d'écoute des messages MQTT."""
        if not self._client:
            return
        
        async def message_callback(message: MQTTMessage) -> None:
            await self._notify_message(message)
        
        try:
            await self._client.listen(message_callback)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._notify_state_change(ProtocolState.ERROR, e)
    
    async def send_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> Any:
        """
        Envoie une commande MQTT.
        
        Args:
            device_id: ID du device
            command: Commande à exécuter (topic)
            parameters: Paramètres de la commande
            
        Returns:
            Résultat de la publication
        """
        if not self._client:
            raise RuntimeError("Client MQTT non connecté")
        
        # Pour MQTT, la commande est le topic
        topic = command
        payload = parameters.get("payload", {})
        qos = parameters.get("qos", 0)
        retain = parameters.get("retain", False)
        
        success = await self._client.publish(topic, payload, qos, retain)
        
        return {
            "success": success,
            "device_id": device_id,
            "topic": topic,
            "payload": payload,
            "qos": qos,
            "retain": retain
        }
