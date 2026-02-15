"""
Implémentation HTTP.

Ce module fournit une implémentation du protocole HTTP
utilisant httpx avec support du pattern Observer.
"""

from typing import Dict, Any, Optional
from .base import Protocol, ProtocolState, ProtocolMessage


class HTTPRequest:
    """Requête HTTP."""
    
    def __init__(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None
    ):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.data = data
        self.params = params or {}


class HTTPResponse:
    """Réponse HTTP."""
    
    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        data: Any,
        request: HTTPRequest
    ):
        self.status_code = status_code
        self.headers = headers
        self.data = data
        self.request = request


class HTTPClient:
    """Client HTTP wrapper autour de httpx."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client = None
    
    async def connect(self) -> bool:
        """Initialise le client HTTP."""
        import httpx
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return True
    
    async def disconnect(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def request(self, req: HTTPRequest) -> HTTPResponse:
        """Exécute une requête HTTP."""
        if not self._client:
            raise RuntimeError("Client HTTP non connecté")
        
        response = await self._client.request(
            method=req.method,
            url=req.url,
            headers=req.headers,
            data=req.data,
            params=req.params
        )
        
        return HTTPResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            data=response.text,
            request=req
        )


class HTTPProtocol(Protocol):
    """Implémentation du protocole HTTP."""
    
    def __init__(self, timeout: int = 30):
        super().__init__("http")
        self.timeout = timeout
        self._client: Optional[HTTPClient] = None
    
    async def connect(self) -> bool:
        """Établit la connexion HTTP."""
        await self._notify_state_change(ProtocolState.CONNECTING)
        
        try:
            self._client = HTTPClient(timeout=self.timeout)
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
        """Ferme la connexion HTTP."""
        if self._client:
            await self._client.disconnect()
            self._client = None
        
        await self._notify_state_change(ProtocolState.DISCONNECTED)
    
    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publie un message HTTP (POST)."""
        if not self._client:
            return False
        
        try:
            req = HTTPRequest(
                method="POST",
                url=topic,  # L'URL est le "topic"
                data=payload
            )
            response = await self._client.request(req)
            return response.status_code < 400
        except Exception:
            return False
    
    async def subscribe(self, topic: str, qos: int = 0) -> bool:
        """S'abonne à un endpoint HTTP (GET périodique)."""
        # Pour HTTP, on simule un abonnement avec des requêtes périodiques
        return True
    
    async def unsubscribe(self, topic: str) -> bool:
        """Se désabonne d'un endpoint HTTP."""
        return True
    
    async def send_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> Any:
        """
        Envoie une commande HTTP.
        
        Args:
            device_id: ID du device
            command: Commande à exécuter (GET, POST, PUT, DELETE)
            parameters: Paramètres de la commande
            
        Returns:
            Réponse HTTP
        """
        if not self._client:
            raise RuntimeError("Client HTTP non connecté")
        
        # Extraction des paramètres
        url = parameters.get("url", "")
        method = command.upper() if command else "GET"
        headers = parameters.get("headers", {})
        data = parameters.get("data", None)
        params = parameters.get("params", {})
        
        if not url:
            raise ValueError("L'URL est requise pour les commandes HTTP")
        
        req = HTTPRequest(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params
        )
        
        try:
            response = await self._client.request(req)
            return {
                "status_code": response.status_code,
                "headers": response.headers,
                "data": response.data,
                "device_id": device_id,
                "command": command
            }
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'exécution de la commande HTTP: {e}")
