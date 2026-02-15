"""
Gestionnaire de contexte pour l'IA.

Ce module gère le contexte des interactions utilisateur,
incluant les informations environnementales, les préférences,
et l'historique des actions.
"""

import json
import logging
from typing import Dict, Any, Optional, List, cast
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import httpx
import redis

from .ai_service import Context


@dataclass
class ContextSource:
    """Source de données de contexte."""
    name: str
    priority: int
    cache_ttl: int  # en secondes
    enabled: bool = True


class ContextManager:
    """Gestionnaire de contexte."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialise le gestionnaire de contexte.
        
        Args:
            redis_client: Client Redis pour le cache (optionnel)
        """
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis_client
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Sources de contexte
        self.sources = [
            ContextSource(name="user_profile", priority=1, cache_ttl=3600),
            ContextSource(name="device_states", priority=2, cache_ttl=30),
            ContextSource(name="environment", priority=3, cache_ttl=300),
            ContextSource(name="weather", priority=4, cache_ttl=1800),
            ContextSource(name="time", priority=5, cache_ttl=60),
            ContextSource(name="history", priority=6, cache_ttl=900),
        ]
        
        # Cache local
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("ContextManager initialisé")
    
    async def get_context(self, user_id: Optional[str] = None) -> Context:
        """
        Récupère le contexte complet.
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            Contexte complet
        """
        context_data = {}
        
        # Récupération des données de chaque source
        for source in sorted(self.sources, key=lambda x: x.priority):
            if not source.enabled:
                continue
            
            try:
                source_data = await self._get_source_data(source.name, user_id)
                if source_data:
                    context_data[source.name] = source_data
                    self.logger.debug(f"Données de contexte récupérées depuis {source.name}")
            except Exception as e:
                self.logger.warning(f"Erreur lors de la récupération de {source.name}: {e}")
        
        # Fusion des données
        merged_data = self._merge_context_data(context_data, user_id)
        
        # Création du contexte
        context = Context(
            user_id=user_id,
            location=merged_data.get("location"),
            time_of_day=merged_data.get("time_of_day"),
            weather=merged_data.get("weather"),
            device_states=merged_data.get("device_states", {}),
            user_preferences=merged_data.get("user_preferences", {}),
            recent_actions=merged_data.get("recent_actions", []),
            timestamp=datetime.now()
        )
        
        self.logger.info(f"Contexte récupéré pour l'utilisateur {user_id or 'anonyme'}")
        return context
    
    async def _get_source_data(self, source_name: str, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère les données d'une source spécifique.
        
        Args:
            source_name: Nom de la source
            user_id: ID de l'utilisateur
            
        Returns:
            Données de la source
        """
        # Vérification du cache
        cache_key = self._get_cache_key(source_name, user_id)
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Récupération des données
        if source_name == "user_profile":
            data = await self._get_user_profile(user_id)
        elif source_name == "device_states":
            data = await self._get_device_states(user_id)
        elif source_name == "environment":
            data = await self._get_environment_data(user_id)
        elif source_name == "weather":
            data = await self._get_weather_data(user_id)
        elif source_name == "time":
            data = self._get_time_data()
        elif source_name == "history":
            data = await self._get_history_data(user_id)
        else:
            data = {}
        
        # Mise en cache
        if data:
            await self._cache_data(cache_key, data, self._get_source_ttl(source_name))
        
        return data
    
    async def _get_user_profile(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère le profil utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Données du profil
        """
        if not user_id:
            return {}
        
        try:
            # Ici, on devrait appeler une API de profil
            # Pour l'instant, on retourne des données simulées
            return {
                "name": "Utilisateur",
                "preferences": {
                    "theme": "auto",
                    "language": "fr",
                    "notifications": True,
                    "auto_optimization": True
                },
                "favorite_devices": ["living_room_light", "kitchen_thermostat"],
                "routines": ["morning", "evening", "sleep"]
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du profil: {e}")
            return {}
    
    async def _get_device_states(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère les états des devices.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            États des devices
        """
        try:
            # Ici, on devrait appeler le device manager
            # Pour l'instant, on retourne des données simulées
            return {
                "living_room_light": {"on": False, "brightness": 50},
                "kitchen_thermostat": {"temperature": 21, "mode": "auto"},
                "bedroom_blind": {"position": 75},
                "living_room_tv": {"on": True, "source": "netflix"}
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des états: {e}")
            return {}
    
    async def _get_environment_data(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère les données environnementales.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Données environnementales
        """
        try:
            # Ici, on devrait récupérer depuis des capteurs
            return {
                "location": "home",
                "room_temperature": 22.5,
                "humidity": 45,
                "light_level": 300,
                "noise_level": 35,
                "motion_detected": True
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération environnementale: {e}")
            return {}
    
    async def _get_weather_data(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère les données météo.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Données météo
        """
        try:
            # Ici, on devrait appeler une API météo
            return {
                "temperature": 20,
                "condition": "clear",
                "humidity": 50,
                "wind_speed": 10,
                "sunrise": "07:30",
                "sunset": "18:45"
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération météo: {e}")
            return {}
    
    def _get_time_data(self) -> Dict[str, Any]:
        """
        Récupère les données temporelles.
        
        Returns:
            Données temporelles
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Détermination du moment de la journée
        if current_hour < 6:
            time_of_day = "night"
        elif current_hour < 12:
            time_of_day = "morning"
        elif current_hour < 18:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
        
        return {
            "time_of_day": time_of_day,
            "hour": current_hour,
            "day_of_week": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "season": self._get_season(now.month)
        }
    
    async def _get_history_data(self, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Récupère l'historique des actions.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Historique des actions
        """
        if not user_id:
            return {"recent_actions": []}
        
        try:
            # Ici, on devrait récupérer depuis une base de données
            return {
                "recent_actions": [
                    {"action": "turn_on", "device": "living_room_light", "timestamp": "2025-02-14T20:30:00"},
                    {"action": "set_temperature", "device": "kitchen_thermostat", "value": 21, "timestamp": "2025-02-14T19:45:00"},
                    {"action": "activate_scene", "scene": "cinema", "timestamp": "2025-02-14T21:15:00"}
                ]
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return {"recent_actions": []}
    
    def _merge_context_data(self, context_data: Dict[str, Dict[str, Any]], user_id: Optional[str]) -> Dict[str, Any]:
        """
        Fusionne les données de contexte.
        
        Args:
            context_data: Données de contexte par source
            user_id: ID de l'utilisateur
            
        Returns:
            Données fusionnées
        """
        merged = {
            "device_states": {},
            "user_preferences": {},
            "recent_actions": []
        }
        
        # Fusion des données de chaque source
        for source_name, data in context_data.items():
            if source_name == "user_profile":
                merged["user_preferences"].update(data.get("preferences", {}))
            elif source_name == "device_states":
                merged["device_states"].update(data)
            elif source_name == "environment":
                merged["location"] = data.get("location")
            elif source_name == "weather":
                merged["weather"] = data
            elif source_name == "time":
                merged["time_of_day"] = data.get("time_of_day")
            elif source_name == "history":
                merged["recent_actions"] = data.get("recent_actions", [])
        
        return merged
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données du cache.
        
        Args:
            cache_key: Clé de cache
            
        Returns:
            Données en cache ou None
        """
        # Cache local
        if cache_key in self._local_cache:
            return self._local_cache[cache_key]
        
        # Cache Redis
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    # Convertir bytes en string si nécessaire
                    if isinstance(cached, bytes):
                        cached_str = cached.decode('utf-8')
                    else:
                        cached_str = str(cached)
                    data = json.loads(cached_str)
                    self._local_cache[cache_key] = data
                    return data
            except Exception as e:
                self.logger.warning(f"Erreur lors de la lecture du cache Redis: {e}")
        
        return None
    
    async def _cache_data(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """
        Met en cache les données.
        
        Args:
            cache_key: Clé de cache
            data: Données à mettre en cache
            ttl: Durée de vie en secondes
        """
        # Cache local
        self._local_cache[cache_key] = data
        
        # Cache Redis
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl, json.dumps(data))
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'écriture dans le cache Redis: {e}")
    
    def _get_cache_key(self, source_name: str, user_id: Optional[str]) -> str:
        """
        Génère une clé de cache.
        
        Args:
            source_name: Nom de la source
            user_id: ID de l'utilisateur
            
        Returns:
            Clé de cache
        """
        user_part = user_id or "anonymous"
        timestamp = datetime.now().strftime("%Y%m%d%H")
        return f"context:{source_name}:{user_part}:{timestamp}"
    
    def _get_source_ttl(self, source_name: str) -> int:
        """
        Retourne le TTL pour une source.
        
        Args:
            source_name: Nom de la source
            
        Returns:
            TTL en secondes
        """
        for source in self.sources:
            if source.name == source_name:
                return source.cache_ttl
        return 300  # Valeur par défaut
    
    def _get_season(self, month: int) -> str:
        """
        Détermine la saison.
        
        Args:
            month: Mois (1-12)
            
        Returns:
            Saison
        """
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    async def update_context(self, context: Context, updates: Dict[str, Any]) -> Context:
        """
        Met à jour un contexte avec de nouvelles données.
        
        Args:
            context: Contexte à mettre à jour
            updates: Nouvelles données
            
        Returns:
            Contexte mis à jour
        """
        # Extraction des mises à jour
        device_states_updates = updates.get("device_states", {})
        user_preferences_updates = updates.get("user_preferences", {})
        recent_actions_updates = updates.get("recent_actions", [])
        
        # Fusion des dictionnaires
        merged_device_states = {**cast(Dict[str, Any], context.device_states), **device_states_updates}
        merged_user_preferences = {**cast(Dict[str, Any], context.user_preferences), **user_preferences_updates}
        
        # Création d'un nouveau contexte avec les mises à jour
        updated_context = Context(
            user_id=updates.get("user_id", context.user_id),
            location=updates.get("location", context.location),
            time_of_day=updates.get("time_of_day", context.time_of_day),
            weather=updates.get("weather", context.weather),
            device_states=merged_device_states,
            user_preferences=merged_user_preferences,
            recent_actions=context.recent_actions + recent_actions_updates,
            timestamp=datetime.now()
        )
        
        self.logger.info("Contexte mis à jour")
        return updated_context
    
    async def add_action_to_history(self, user_id: Optional[str], action: Dict[str, Any]):
        """
        Ajoute une action à l'historique.
        
        Args:
            user_id: ID de l'utilisateur
            action: Action à ajouter
        """
        if not user_id:
            return
        
        try:
            # Ici, on devrait persister dans une base de données
            # Pour l'instant, on met à jour le cache local
            cache_key = self._get_cache_key("history", user_id)
            cached_data = await self._get_cached_data(cache_key)
            
            if cached_data:
                actions = cached_data.get("recent_actions", [])
                actions.append(action)
                # Garder seulement les 10 dernières actions
                cached_data["recent_actions"] = actions[-10:]
                await self._cache_data(cache_key, cached_data, 900)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout à l'historique: {e}")
    
    async def clear_cache(self, source_name: Optional[str] = None):
        """
        Efface le cache.
        
        Args:
            source_name: Nom de la source à effacer (optionnel)
        """
        if source_name:
            # Effacer une source spécifique
            keys_to_remove = [k for k in self._local_cache.keys() if f":{source_name}:" in k]
            for key in keys_to_remove:
                del self._local_cache[key]
        else:
            # Effacer tout le cache
            self._local_cache.clear()
        
        self.logger.info(f"Cache effacé pour {source_name or 'toutes les sources'}")
    
    async def close(self):
        """Ferme les connexions."""
        await self.http_client.aclose()
        self.logger.info("ContextManager fermé")
