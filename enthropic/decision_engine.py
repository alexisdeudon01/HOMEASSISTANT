"""
Moteur de décision pour l'IA.

Ce module prend des décisions intelligentes basées sur
les intentions utilisateur, le contexte et les actions disponibles.
"""

import logging
import os
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

import httpx

from .ai_service import Intent, Context, Decision, IntentType


@dataclass
class DecisionRule:
    """Règle de décision."""
    condition: Dict[str, Any]
    action: str
    target: str
    parameters: Dict[str, Any]
    priority: int
    confidence: float = 1.0


@dataclass
class DecisionFactor:
    """Facteur influençant la décision."""
    name: str
    weight: float
    value: float


class DecisionEngine:
    """Moteur de décision."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = os.getenv('ENTHROPIC_BASE_URL', 'http://localhost:8000')):
        """
        Initialise le moteur de décision.
        
        Args:
            api_key: Clé API pour les services externes
            base_url: URL de base pour les API IA
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Règles de décision
        self.rules = self._initialize_rules()
        
        # Facteurs de décision
        self.factors = self._initialize_factors()
        
        # Cache des décisions
        self._decision_cache: Dict[str, Decision] = {}
        
        self.logger.info("DecisionEngine initialisé")
    
    def _initialize_rules(self) -> List[DecisionRule]:
        """
        Initialise les règles de décision.
        
        Returns:
            Liste des règles
        """
        return [
            DecisionRule(
                condition={"intent_type": IntentType.CONTROL, "entities.action": ["allume", "active"]},
                action="turn_on",
                target="living_room_light",
                parameters={},
                priority=1,
                confidence=0.9
            ),
            DecisionRule(
                condition={"intent_type": IntentType.CONTROL, "entities.action": ["éteins", "désactive"]},
                action="turn_off",
                target="living_room_light",
                parameters={},
                priority=1,
                confidence=0.9
            ),
            DecisionRule(
                condition={"intent_type": IntentType.QUERY},
                action="query_status",
                target="all_devices",
                parameters={},
                priority=2,
                confidence=0.8
            ),
            DecisionRule(
                condition={"intent_type": IntentType.SCENE, "entities.scene": ["cinéma", "cinema"]},
                action="activate_scene",
                target="living_room",
                parameters={"scene_name": "cinema"},
                priority=1,
                confidence=0.85
            ),
            DecisionRule(
                condition={"intent_type": IntentType.SCENE, "entities.scene": ["lecture", "reading"]},
                action="activate_scene",
                target="living_room",
                parameters={"scene_name": "reading"},
                priority=1,
                confidence=0.85
            ),
            DecisionRule(
                condition={"intent_type": IntentType.AUTOMATION},
                action="create_automation",
                target="system",
                parameters={},
                priority=3,
                confidence=0.7
            ),
            DecisionRule(
                condition={"intent_type": IntentType.DIAGNOSTIC},
                action="diagnose",
                target="system",
                parameters={},
                priority=4,
                confidence=0.6
            )
        ]
    
    def _initialize_factors(self) -> List[DecisionFactor]:
        """
        Initialise les facteurs de décision.
        
        Returns:
            Liste des facteurs
        """
        return [
            DecisionFactor(name="intent_confidence", weight=0.3, value=0.0),
            DecisionFactor(name="context_relevance", weight=0.2, value=0.0),
            DecisionFactor(name="time_of_day", weight=0.15, value=0.0),
            DecisionFactor(name="user_preferences", weight=0.2, value=0.0),
            DecisionFactor(name="energy_efficiency", weight=0.1, value=0.0),
            DecisionFactor(name="privacy_concerns", weight=0.05, value=0.0)
        ]
    
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
        # Vérification du cache
        cache_key = self._get_decision_cache_key(intent, context)
        if cache_key in self._decision_cache:
            return self._decision_cache[cache_key]
        
        try:
            # Tentative d'appel à l'API IA
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
            
        except Exception as e:
            self.logger.warning(f"API IA non disponible, utilisation des règles locales: {e}")
            # Utilisation des règles locales
            decision = self._make_local_decision(intent, context, available_actions)
        
        # Mise en cache
        self._decision_cache[cache_key] = decision
        
        self.logger.info(f"Décision prise: {decision.action} sur {decision.target} (confiance: {decision.confidence})")
        return decision
    
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
            self.logger.warning(f"API de décision non disponible: {e}")
            raise
    
    def _make_local_decision(
        self,
        intent: Intent,
        context: Context,
        available_actions: List[Dict[str, Any]]
    ) -> Decision:
        """
        Prend une décision locale basée sur les règles.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            available_actions: Actions disponibles
            
        Returns:
            Décision locale
        """
        # Évaluation des règles
        matching_rules = self._evaluate_rules(intent, context)
        
        if matching_rules:
            # Sélection de la règle avec la priorité la plus élevée
            best_rule = max(matching_rules, key=lambda r: (r.priority, r.confidence))
            
            # Calcul de la confiance
            confidence = self._calculate_confidence(intent, context, best_rule)
            
            # Génération du raisonnement
            reasoning = self._generate_reasoning(intent, context, best_rule)
            
            # Génération des alternatives
            alternatives = self._generate_alternatives(matching_rules, best_rule)
            
            return Decision(
                action=best_rule.action,
                target=best_rule.target,
                parameters=best_rule.parameters,
                confidence=confidence,
                reasoning=reasoning,
                alternatives=alternatives,
                timestamp=datetime.now()
            )
        
        # Aucune règle correspondante
        return Decision(
            action="noop",
            target="",
            parameters={},
            confidence=0.1,
            reasoning="Aucune règle correspondante trouvée",
            alternatives=[],
            timestamp=datetime.now()
        )
    
    def _evaluate_rules(self, intent: Intent, context: Context) -> List[DecisionRule]:
        """
        Évalue les règles par rapport à l'intention et au contexte.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            
        Returns:
            Règles correspondantes
        """
        matching_rules = []
        
        for rule in self.rules:
            if self._rule_matches(rule, intent, context):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches(self, rule: DecisionRule, intent: Intent, context: Context) -> bool:
        """
        Vérifie si une règle correspond à l'intention et au contexte.
        
        Args:
            rule: Règle à vérifier
            intent: Intention utilisateur
            context: Contexte actuel
            
        Returns:
            True si la règle correspond
        """
        # Vérification du type d'intention
        if "intent_type" in rule.condition:
            if intent.type != rule.condition["intent_type"]:
                return False
        
        # Vérification des entités
        if "entities" in rule.condition:
            for entity_type, expected_values in rule.condition["entities"].items():
                if entity_type not in intent.entities:
                    return False
                
                entity_values = intent.entities[entity_type]
                if not any(value in entity_values for value in expected_values):
                    return False
        
        # Vérification du contexte
        if "context" in rule.condition:
            for context_key, expected_value in rule.condition["context"].items():
                context_value = getattr(context, context_key, None)
                if context_value != expected_value:
                    return False
        
        return True
    
    def _calculate_confidence(
        self,
        intent: Intent,
        context: Context,
        rule: DecisionRule
    ) -> float:
        """
        Calcule la confiance de la décision.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            rule: Règle sélectionnée
            
        Returns:
            Niveau de confiance
        """
        base_confidence = rule.confidence
        
        # Ajustement basé sur la confiance de l'intention
        intent_factor = intent.confidence * 0.3
        
        # Ajustement basé sur le contexte
        context_factor = self._calculate_context_factor(context) * 0.2
        
        # Ajustement basé sur l'heure
        time_factor = self._calculate_time_factor(context) * 0.15
        
        # Ajustement basé sur les préférences utilisateur
        preference_factor = self._calculate_preference_factor(context) * 0.2
        
        # Ajustement basé sur l'efficacité énergétique
        energy_factor = self._calculate_energy_factor(intent, context) * 0.1
        
        # Ajustement basé sur la confidentialité
        privacy_factor = self._calculate_privacy_factor(intent, context) * 0.05
        
        # Calcul final
        confidence = base_confidence * (
            intent_factor + context_factor + time_factor +
            preference_factor + energy_factor + privacy_factor
        )
        
        # Normalisation
        return max(0.1, min(1.0, confidence))
    
    def _calculate_context_factor(self, context: Context) -> float:
        """
        Calcule le facteur de contexte.
        
        Args:
            context: Contexte actuel
            
        Returns:
            Facteur de contexte
        """
        # Plus le contexte est riche, plus le facteur est élevé
        factor = 0.5
        
        if context.location:
            factor += 0.1
        
        if context.weather:
            factor += 0.1
        
        if context.device_states:
            factor += 0.2
        
        if context.user_preferences:
            factor += 0.1
        
        return min(1.0, factor)
    
    def _calculate_time_factor(self, context: Context) -> float:
        """
        Calcule le facteur temporel.
        
        Args:
            context: Contexte actuel
            
        Returns:
            Facteur temporel
        """
        if not context.time_of_day:
            return 0.5
        
        # Certaines décisions sont plus appropriées à certains moments
        time_factors = {
            "morning": 0.8,
            "afternoon": 0.9,
            "evening": 0.7,
            "night": 0.5
        }
        
        return time_factors.get(context.time_of_day, 0.5)
    
    def _calculate_preference_factor(self, context: Context) -> float:
        """
        Calcule le facteur de préférences utilisateur.
        
        Args:
            context: Contexte actuel
            
        Returns:
            Facteur de préférences
        """
        if not context.user_preferences:
            return 0.5
        
        # Vérification des préférences d'automatisation
        auto_optimization = context.user_preferences.get("auto_optimization", False)
        if auto_optimization:
            return 0.9
        
        return 0.5
    
    def _calculate_energy_factor(self, intent: Intent, context: Context) -> float:
        """
        Calcule le facteur d'efficacité énergétique.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            
        Returns:
            Facteur d'énergie
        """
        # Les actions d'extinction sont plus efficaces énergétiquement
        if intent.type == IntentType.CONTROL:
            if "action" in intent.entities:
                actions = intent.entities["action"]
                if any(action in ["éteins", "désactive"] for action in actions):
                    return 0.9
        
        return 0.5
    
    def _calculate_privacy_factor(self, intent: Intent, context: Context) -> float:
        """
        Calcule le facteur de confidentialité.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            
        Returns:
            Facteur de confidentialité
        """
        # Les requêtes sont moins sensibles que les contrôles
        if intent.type == IntentType.QUERY:
            return 0.8
        
        return 0.5
    
    def _generate_reasoning(
        self,
        intent: Intent,
        context: Context,
        rule: DecisionRule
    ) -> str:
        """
        Génère un raisonnement pour la décision.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            rule: Règle sélectionnée
            
        Returns:
            Raisonnement
        """
        reasoning_parts = []
        
        # Partie intention
        reasoning_parts.append(f"Intention détectée: {intent.type.value}")
        
        # Partie contexte
        if context.time_of_day:
            reasoning_parts.append(f"Moment de la journée: {context.time_of_day}")
        
        if context.location:
            reasoning_parts.append(f"Localisation: {context.location}")
        
        # Partie règle
        reasoning_parts.append(f"Règle appliquée: {rule.action} sur {rule.target}")
        
        # Partie confiance
        confidence = self._calculate_confidence(intent, context, rule)
        reasoning_parts.append(f"Confiance: {confidence:.2f}")
        
        return ". ".join(reasoning_parts)
    
    def _generate_alternatives(
        self,
        matching_rules: List[DecisionRule],
        selected_rule: DecisionRule
    ) -> List[Dict[str, Any]]:
        """
        Génère des alternatives à la décision.
        
        Args:
            matching_rules: Règles correspondantes
            selected_rule: Règle sélectionnée
            
        Returns:
            Alternatives
        """
        alternatives = []
        
        for rule in matching_rules:
            if rule == selected_rule:
                continue
            
            alternatives.append({
                "action": rule.action,
                "target": rule.target,
                "parameters": rule.parameters,
                "confidence": rule.confidence * 0.8,  # Alternatives moins confiantes
                "reasoning": f"Alternative: {rule.action} sur {rule.target}"
            })
        
        return alternatives
    
    def _get_decision_cache_key(self, intent: Intent, context: Context) -> str:
        """
        Génère une clé de cache pour une décision.
        
        Args:
            intent: Intention utilisateur
            context: Contexte actuel
            
        Returns:
            Clé de cache
        """
        intent_part = f"{intent.type.value}:{intent.text[:20]}"
        context_part = f"{context.user_id}:{context.time_of_day}"
        return f"decision:{intent_part}:{context_part}"
    
    async def evaluate_decision_quality(self, decision: Decision, outcome: Dict[str, Any]) -> float:
        """
        Évalue la qualité d'une décision basée sur son résultat.
        
        Args:
            decision: Décision prise
            outcome: Résultat de l'exécution
            
        Returns:
            Score de qualité (0.0 à 1.0)
        """
        try:
            # Facteurs de qualité
            success_factor = 1.0 if outcome.get("success", False) else 0.0
            user_satisfaction = outcome.get("user_satisfaction", 0.5)
            efficiency = outcome.get("efficiency", 0.5)
            energy_saved = outcome.get("energy_saved", 0.0)
            
            # Calcul du score
            score = (
                success_factor * 0.4 +
                user_satisfaction * 0.3 +
                efficiency * 0.2 +
                min(energy_saved, 1.0) * 0.1
            )
            
            # Ajustement basé sur la confiance initiale
            adjusted_score = score * decision.confidence
            
            self.logger.info(f"Qualité de décision évaluée: {adjusted_score:.2f}")
            return adjusted_score
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'évaluation de la qualité: {e}")
            return 0.5
