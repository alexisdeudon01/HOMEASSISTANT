"""
Client HTTP pour communiquer avec les autres services.

Ce module fournit un client HTTP asynchrone pour appeler les APIs
des autres services de l'architecture Sinik OS.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

from ..models.ha_models import HADevice, HAEntity, DeviceRegistration, EntityRegistration


logger = logging.getLogger(__name__)


class ServiceHTTPClient:
    """Client HTTP pour communiquer avec les autres services."""
    
    def __init__(self, base_url: str = "http://localhost", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        
    async def connect(self) -> None:
        """Connecter le client HTTP."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            logger.info(f"Client HTTP connecté à {self.base_url}")
            
    async def disconnect(self) -> None:
        """Déconnecter le client HTTP."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("Client HTTP déconnecté")
            
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Effectuer une requête HTTP."""
        if self.client is None:
            await self.connect()
            
        try:
            if self.client is None:
                raise RuntimeError("Client HTTP non initialisé")
                
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la requête HTTP: {e}")
            raise


class GatewayServiceClient(ServiceHTTPClient):
    """Client pour le Gateway Service (port 8000)."""
    
    def __init__(self):
base_url = os.getenv("base_url", "http://gateway-service:8000")
        
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Récupérer la liste des devices depuis le Gateway Service."""
        result = await self._request("GET", "/api/devices")
        return result.get("devices", []) if isinstance(result, dict) else result
        
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Récupérer un device spécifique."""
        return await self._request("GET", f"/api/devices/{device_id}")
        
    async def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer un nouveau device."""
        return await self._request("POST", "/api/devices", json=device_data)
        
    async def send_command(self, device_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Envoyer une commande à un device."""
        return await self._request("POST", f"/api/devices/{device_id}/command", 
                                  json={"command": command, "params": params})


class EntityServiceClient(ServiceHTTPClient):
    """Client pour l'Entity Service (port 8002)."""
    
    def __init__(self):
base_url = os.getenv("base_url", "http://entity-service:8002")
        
    async def get_entities(self) -> List[Dict[str, Any]]:
        """Récupérer la liste des entités."""
        result = await self._request("GET", "/api/entities")
        return result.get("entities", []) if isinstance(result, dict) else result
        
    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Récupérer une entité spécifique."""
        return await self._request("GET", f"/api/entities/{entity_id}")
        
    async def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Créer une nouvelle entité."""
        return await self._request("POST", "/api/entities", json=entity_data)
        
    async def update_entity_state(self, entity_id: str, state: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Mettre à jour l'état d'une entité."""
        return await self._request("PUT", f"/api/entities/{entity_id}/state",
                                  json={"state": state, "attributes": attributes})


class ProtocolServiceClient(ServiceHTTPClient):
    """Client pour le Protocol Service (port 8003)."""
    
    def __init__(self):
base_url = os.getenv("base_url", "http://protocol-service:8003")
        
    async def get_protocols(self) -> List[Dict[str, Any]]:
        """Récupérer la liste des protocoles supportés."""
        result = await self._request("GET", "/api/protocols")
        return result.get("protocols", []) if isinstance(result, dict) else result
        
    async def execute_protocol_command(self, protocol: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécuter une commande via un protocole spécifique."""
        return await self._request("POST", f"/api/protocols/{protocol}/execute",
                                  json={"command": command, "params": params})


class BrainServiceClient(ServiceHTTPClient):
    """Client pour le Brain Service."""
    
    def __init__(self):
base_url = os.getenv("base_url", "http://brain-service:8004")
        
    async def process_intent(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter une intention avec le service d'IA."""
        return await self._request("POST", "/api/intent/process",
                                  json={"intent": intent, "context": context})
        
    async def get_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Obtenir une décision pour une situation donnée."""
        return await self._request("POST", "/api/decision",
                                  json={"situation": situation})


class ServiceClientManager:
    """Gestionnaire central pour tous les clients de service."""
    
    def __init__(self):
        self.gateway_client = GatewayServiceClient()
        self.entity_client = EntityServiceClient()
        self.protocol_client = ProtocolServiceClient()
        self.brain_client = BrainServiceClient()
        
    async def connect_all(self) -> None:
        """Connecter tous les clients."""
        await self.gateway_client.connect()
        await self.entity_client.connect()
        await self.protocol_client.connect()
        await self.brain_client.connect()
        logger.info("Tous les clients de service sont connectés")
        
    async def disconnect_all(self) -> None:
        """Déconnecter tous les clients."""
        await self.gateway_client.disconnect()
        await self.entity_client.disconnect()
        await self.protocol_client.disconnect()
        await self.brain_client.disconnect()
        logger.info("Tous les clients de service sont déconnectés")
        
    async def __aenter__(self):
        await self.connect_all()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect_all()
