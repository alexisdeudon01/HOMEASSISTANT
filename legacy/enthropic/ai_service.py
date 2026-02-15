"""
Service IA principal pour l'automatisation intelligente.

Ce service utilise des modèles d'IA pour comprendre les intentions,
analyser le contexte et prendre des décisions intelligentes.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import httpx


class IntentType(Enum):
    """Types d'intentions supportées."""
    CONTROL = "control"
    QUERY = "query"
    AUTOMATION = "automation"
    SCENE = "scene"
    ROUTINE = "routine"
    DIAGNOSTIC = "diagnostic"


@dataclass
class Intent:
    """Représente une intention utilisateur."""
    type: IntentType
    text: str
    confidence: float
    entities: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        data = asdict(self)
        data['type'] = self.type.value
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        else:
            data['timestamp'] = datetime.now().isoformat()
        return data


@dataclass
class Context:
    """Représente le contexte d'une interaction."""
    user_id: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[Dict[str, Any]] = None
    device_states: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    recent_actions: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.device_states is None:
            self.device_states = {}
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.recent_actions is None:
            self.recent_actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        else:
            data['timestamp'] = datetime.now().isoformat()
        return data


@dataclass
class Decision:
    """Représente une décision prise par l'IA."""
    action: str
    target: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    alternatives: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.alternatives is None:
            self.alternatives = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        else:
            data['timestamp'] = datetime.now().isoformat()
        return data


class AIService:
    """Service IA principal."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = os.getenv('ENTHROPIC_BASE_URL', 'http://localhost:8000')):
        """
        Initialise le service IA.
        
        Args:
            api_key: Clé API pour les services externes
            base_url: URL de base pour les API IA
        """
        self.api_key = api_key
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.logger = logging.getLogger(__name__)
        
        # Cache pour les résultats
        self._intent_cache: Dict[str, Intent] = {}
        self._context_cache: Dict[str, Context] = {}
        
        self.logger.info("AIService initialisé")
    
    async def analyze_intent(self, text: str, user_id: Optional[str] = None) -> Intent:
        """
        Analyse l'intention d'un texte utilisateur.
        
        Args:
            text: Texte à analyser
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            Intention détectée
        """
        cache_key = f"{user_id}:{text}"
        if cache_key in self._intent_cache:
            return self._intent_cache[cache_key]
        
        try:
            # Appel à l'API IA
            response = await self._call_intent_api(text, user_id)
            
            # Création de l'intention
            intent = Intent(
                type=IntentType(response.get("type", "control")),
                text=text,
                confidence=response.get("confidence", 0.5),
                entities=response.get("entities", {}),
                timestamp=datetime.fromisoformat(response.get("timestamp", datetime.now().isoformat()))
            )
            
            # Mise en cache
            self._intent_cache[cache_key] = intent
            
            self.logger.info(f"Intention analysée: {intent.type.value} (confiance: {intent.confidence})")
            return intent
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse d'intention: {e}")
            # Retour d'une intention par défaut
            return Intent(
                type=IntentType.CONTROL,
                text=text,
                confidence=0.1,
                entities={"error": str(e)}
            )
    
    async def _call_intent_api(self, text: str, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Appelle l'API d'analyse d'intention.
        
        Args:
            text: Texte à analyser
            user_id: ID de l'utilisateur
            
        Returns:
            Réponse de l'API
        """
        payload = {
            "text": text,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/intent",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            self.logger.warning(f"API IA non disponible, utilisation du fallback: {e}")
            # Fallback local
            return self._fallback_intent_analysis(text)
    
    def _fallback_intent_analysis(self, text: str) -> Dict[str, Any]:
        """
        Analyse d'intention de fallback local.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Analyse d'intention basique
        """
        text_lower = text.lower()
        
        # Détection basique d'intention
        if any(word in text_lower for word in ["allume", "éteins", "active", "désactive"]):
            intent_type = "control"
            entities = {"action": "toggle"}
        elif any(word in text_lower for word in ["combien", "quelle", "quel", "état"]):
            intent_type = "query"
            entities = {"query_type": "status"}
        elif any(word in text_lower for word in ["scène", "mode", "ambiance"]):
            intent_type = "scene"
            entities = {"scene_type": "ambiance"}
        else:
            intent_type = "control"
            entities = {}
        
        return {
            "type": intent_type,
            "confidence": 0.7,
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_context(self, user_id: Optional[str] = None) -> Context:
        """
        Récupère le contexte actuel.
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            Contexte actuel
        """
        cache_key = f"context:{user_id}:{datetime.now().hour}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        
        try:
            # Récupération des données de contexte
            context_data = await self._gather_context_data(user_id)
            
            # Création du contexte
            context = Context(
                user_id=user_id,
                location=context_data.get("location"),
                time_of_day=context_data.get("time_of_day"),
                weather=context_data.get("weather"),
                device_states=context_data.get("device_states", {}),
                user_preferences=context_data.get("user_preferences", {}),
                recent_actions=context_data.get("recent_actions", []),
                timestamp=datetime.fromisoformat(context_data.get("timestamp", datetime.now().isoformat()))
            )
            
            # Mise en cache
            self._context_cache[cache_key] = context
            
            return context
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du contexte: {e}")
            # Retour d'un contexte par défaut
            return Context(
                user_id=user_id,
                timestamp=datetime.now()
            )
    
    async def _gather_context_data(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Rassemble les données de contexte.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Données de contexte
        """
        # Ici, on devrait récupérer les données depuis diverses sources
        # Pour l'instant, on retourne des données simulées
        
        current_hour = datetime.now().hour
        time_of_day = "night"
        
        return {
            "location": "home",
            "time_of_day": time_of_day,
            "weather": {"temperature": 20, "condition": "clear"},
            "device_states": {},
            "user_preferences": {"theme": "auto", "language": "fr"},
            "recent_actions": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def make_decision(
        self,
        intent: Intent,
        context: Context,
        available_actions: List[Dict[str, Any]]
    ) -> Decision:
        """
        Prend une décision basée sur l'intention et le contexte.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            available_actions: Actions disponibles
            
        Returns:
            Décision prise
        """
        try:
            # Appel à l'API de décision
            decision_data = await self._call_decision_api(intent, context, available_actions)
            
            # Création de la décision
            decision = Decision(
                action=decision_data.get("action", "noop"),
                target=decision_data.get("target", ""),
                parameters=decision_data.get("parameters", {}),
                confidence=decision_data.get("confidence", 0.5),
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                alternatives=decision_data.get("alternatives", []),
                timestamp=datetime.fromisoformat(decision_data.get("timestamp", datetime.now().isoformat()))
            )
            
            self.logger.info(f"Décision prise: {decision.action} sur {decision.target}")
            return decision
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la prise de décision: {e}")
            # Décision de fallback
            return Decision(
                action="noop",
                target="",
                parameters={},
                confidence=0.1,
                reasoning=f"Erreur: {str(e)}",
                alternatives=[],
                timestamp=datetime.now()
            )
    
    async def _call_decision_api(
        self,
        intent: Intent,
        context: Context,
        available_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Appelle l'API de prise de décision.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            available_actions: Actions disponibles
            
        Returns:
            Réponse de l'API
        """
        payload = {
            "intent": intent.to_dict(),
            "context": context.to_dict(),
            "available_actions": available_actions,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/decision",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            self.logger.warning(f"API de décision non disponible, utilisation du fallback: {e}")
            # Fallback local
            return self._fallback_decision(intent, context, available_actions)
    
    def _fallback_decision(
        self,
        intent: Intent,
        context: Context,
        available_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prise de décision de fallback local.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            available_actions: Actions disponibles
            
        Returns:
            Décision basique
        """
        # Logique de décision basique
        if intent.type == IntentType.CONTROL and "light" in intent.text.lower():
            action = "turn_on" if "allume" in intent.text.lower() else "turn_off"
            target = "living_room_light"
            reasoning = "Contrôle basique de lumière basé sur l'intention"
        elif intent.type == IntentType.QUERY:
            action = "query_status"
            target = "all_devices"
            reasoning = "Requête de statut des devices"
        else:
            action = "noop"
            target = ""
            reasoning = "Aucune action appropriée trouvée"
        
        return {
            "action": action,
            "target": target,
            "parameters": {},
            "confidence": 0.6,
            "reasoning": reasoning,
            "alternatives": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_decision(self, decision: Decision, device_manager: Any) -> Dict[str, Any]:
        """
        Exécute une décision.
        
        Args:
            decision: Décision à exécuter
            device_manager: Gestionnaire de devices
            
        Returns:
            Résultat de l'exécution
        """
        try:
            # Conversion de la décision en commande
            command = self._decision_to_command(decision)
            
            # Exécution via le device manager
            if hasattr(device_manager, 'set_device_state'):
                result = await device_manager.set_device_state(
                    decision.target,
                    command
                )
            else:
                result = {"status": "error", "message": "Device manager non compatible"}
            
            self.logger.info(f"Décision exécutée: {decision.action} -> {result}")
            return {
                "decision": decision.to_dict(),
                "execution_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de la décision: {e}")
            return {
                "decision": decision.to_dict(),
                "execution_result": {"status": "error", "message": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    def _decision_to_command(self, decision: Decision) -> Dict[str, Any]:
        """
        Convertit une décision en commande de device.
        
        Args:
            decision: Décision à convertir
            
        Returns:
            Commande de device
        """
        command_map = {
            "turn_on": {"on": True},
            "turn_off": {"on": False},
            "set_brightness": {"bri": decision.parameters.get("brightness", 100)},
            "set_color": {"hue": decision.parameters.get("hue", 0), "sat": decision.parameters.get("saturation", 100)},
            "query_status": {"query": "status"}
        }
        
        return command_map.get(decision.action, {})
    
    async def close(self):
        """Ferme les connexions."""
        await self.http_client.aclose()
        self.logger.info("AIService fermé")
    
    def clear_cache(self):
        """Efface le cache."""
        self._intent_cache.clear()
        self._context_cache.clear()
        self.logger.info("Cache IA effacé")
