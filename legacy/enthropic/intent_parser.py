"""
Parseur d'intentions pour l'analyse de texte naturel.

Ce module analyse le texte utilisateur pour en extraire
les intentions et les entités pertinentes.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .ai_service import Intent, IntentType


class IntentParser:
    """Parseur d'intentions."""
    
    def __init__(self):
        """Initialise le parseur."""
        self.logger = logging.getLogger(__name__)
        
        # Patterns pour la détection d'intentions
        self.patterns = {
            IntentType.CONTROL: [
                r"(allume|éteins|active|désactive|mets|change|règle|ajuste)\s+(.+?)(\s|$)",
                r"(lumière|lampe|éclairage|interrupteur)\s+(.+?)(\s|$)",
                r"(augmente|diminue|monte|descends)\s+(.+?)(\s|$)"
            ],
            IntentType.QUERY: [
                r"(combien|quelle|quel|quelles|quels|état|statut|valeur)\s+(.+?)(\s|$)",
                r"(température|humidité|luminosité|pression)\s+(.+?)(\s|$)",
                r"(est-ce que|est ce que|est-ce|est ce)\s+(.+?)(\s|\?)"
            ],
            IntentType.SCENE: [
                r"(scène|mode|ambiance|atmosphère)\s+(.+?)(\s|$)",
                r"(cinéma|lecture|dîner|romantique|travail|relax)\s+(.+?)(\s|$)",
                r"(mets|active|lance)\s+(.+?)(\s|$)"
            ],
            IntentType.AUTOMATION: [
                r"(quand|si|lorsque|dès que)\s+(.+?)(\s|$)",
                r"(automatise|programme|planifie)\s+(.+?)(\s|$)",
                r"(routine|automatisation|scénario)\s+(.+?)(\s|$)"
            ]
        }
        
        # Entités communes
        self.entity_patterns = {
            "device": [
                r"(lumière|lampe|éclairage|interrupteur|prise|capteur|thermostat)",
                r"(salon|cuisine|chambre|salle de bain|bureau|couloir|jardin)"
            ],
            "action": [
                r"(allume|éteins|active|désactive|mets|change)",
                r"(augmente|diminue|monte|descends|règle|ajuste)"
            ],
            "value": [
                r"(\d+)\s*(pourcent|%|degrés|°C|°F|lux|hPa)",
                r"(chaud|froid|clair|sombre|fort|faible|haut|bas)"
            ],
            "time": [
                r"(maintenant|tout de suite|immédiatement|plus tard)",
                r"(dans\s+\d+\s+(minutes|heures|jours))",
                r"(à\s+\d+\s*h\s*\d*)"
            ]
        }
        
        self.logger.info("IntentParser initialisé")
    
    def parse(self, text: str, user_id: Optional[str] = None) -> Intent:
        """
        Parse un texte pour en extraire l'intention.
        
        Args:
            text: Texte à parser
            user_id: ID de l'utilisateur (optionnel)
            
        Returns:
            Intention détectée
        """
        text_lower = text.lower().strip()
        
        # Détection du type d'intention
        intent_type, confidence = self._detect_intent_type(text_lower)
        
        # Extraction des entités
        entities = self._extract_entities(text_lower)
        
        # Création de l'intention
        intent = Intent(
            type=intent_type,
            text=text,
            confidence=confidence,
            entities=entities,
            timestamp=datetime.now()
        )
        
        self.logger.info(f"Intention parsée: {intent_type.value} (confiance: {confidence})")
        return intent
    
    def _detect_intent_type(self, text: str) -> tuple[IntentType, float]:
        """
        Détecte le type d'intention.
        
        Args:
            text: Texte en minuscules
            
        Returns:
            Tuple (type, confiance)
        """
        scores = {intent_type: 0.0 for intent_type in IntentType}
        
        # Calcul des scores pour chaque type
        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[intent_type] += 0.3
        
        # Détection basée sur les mots-clés
        keyword_mapping = {
            IntentType.CONTROL: ["allume", "éteins", "active", "désactive", "mets", "change"],
            IntentType.QUERY: ["combien", "quelle", "quel", "état", "statut", "valeur"],
            IntentType.SCENE: ["scène", "mode", "ambiance", "atmosphère", "cinéma"],
            IntentType.AUTOMATION: ["quand", "si", "automatise", "programme", "routine"],
            IntentType.ROUTINE: ["routine", "habitude", "quotidien", "matin", "soir"],
            IntentType.DIAGNOSTIC: ["problème", "erreur", "ne marche pas", "dysfonctionne"]
        }
        
        for intent_type, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in text:
                    scores[intent_type] += 0.2
        
        # Normalisation des scores
        total_score = sum(scores.values())
        if total_score > 0:
            for intent_type in scores:
                scores[intent_type] /= total_score
        
        # Sélection du type avec le score le plus élevé
        best_type = max(scores.items(), key=lambda x: x[1])
        
        # Si aucun score significatif, retourner CONTROL par défaut
        if best_type[1] < 0.1:
            return IntentType.CONTROL, 0.1
        
        return best_type
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrait les entités du texte.
        
        Args:
            text: Texte en minuscules
            
        Returns:
            Dictionnaire d'entités
        """
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            entity_values = []
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Nettoyage des matches
                    for match in matches:
                        if isinstance(match, tuple):
                            # Prendre le premier groupe non vide
                            value = next((m for m in match if m), "")
                        else:
                            value = match
                        
                        if value and value not in entity_values:
                            entity_values.append(value)
            
            if entity_values:
                entities[entity_type] = entity_values
        
        # Extraction des valeurs numériques
        numeric_values = re.findall(r'\b\d+\b', text)
        if numeric_values:
            entities["numeric"] = [int(v) for v in numeric_values]
        
        # Extraction des unités
        units = re.findall(r'(pourcent|%|degrés|°C|°F|lux|hPa)', text, re.IGNORECASE)
        if units:
            entities["units"] = units
        
        return entities
    
    def validate_intent(self, intent: Intent) -> bool:
        """
        Valide une intention.
        
        Args:
            intent: Intention à valider
            
        Returns:
            True si valide, False sinon
        """
        # Vérification de base
        if not intent.text or len(intent.text.strip()) == 0:
            return False
        
        if intent.confidence < 0.1:
            return False
        
        # Vérification spécifique au type
        if intent.type == IntentType.CONTROL:
            # Pour les intentions de contrôle, vérifier qu'il y a une action
            if "action" not in intent.entities:
                return False
        
        return True
    
    def enrich_intent(self, intent: Intent, context: Dict[str, Any]) -> Intent:
        """
        Enrichit une intention avec le contexte.
        
        Args:
            intent: Intention à enrichir
            context: Contexte supplémentaire
            
        Returns:
            Intention enrichie
        """
        # Ajout d'informations de contexte aux entités
        enriched_entities = intent.entities.copy()
        
        # Ajout du contexte utilisateur
        if "user_id" in context:
            enriched_entities["user"] = context["user_id"]
        
        # Ajout de la localisation si disponible
        if "location" in context:
            enriched_entities["location"] = context["location"]
        
        # Ajout des préférences utilisateur
        if "preferences" in context:
            enriched_entities["preferences"] = context["preferences"]
        
        # Création d'une nouvelle intention enrichie
        enriched_intent = Intent(
            type=intent.type,
            text=intent.text,
            confidence=intent.confidence,
            entities=enriched_entities,
            timestamp=intent.timestamp
        )
        
        return enriched_intent
    
    def get_suggested_actions(self, intent: Intent) -> List[Dict[str, Any]]:
        """
        Retourne les actions suggérées pour une intention.
        
        Args:
            intent: Intention analysée
            
        Returns:
            Liste d'actions suggérées
        """
        suggestions = []
        
        if intent.type == IntentType.CONTROL:
            if "action" in intent.entities:
                actions = intent.entities["action"]
                for action in actions:
                    if action in ["allume", "active"]:
                        suggestions.append({
                            "action": "turn_on",
                            "description": f"Allumer {intent.entities.get('device', ['l\'appareil'])[0]}",
                            "confidence": intent.confidence
                        })
                    elif action in ["éteins", "désactive"]:
                        suggestions.append({
                            "action": "turn_off",
                            "description": f"Éteindre {intent.entities.get('device', ['l\'appareil'])[0]}",
                            "confidence": intent.confidence
                        })
        
        elif intent.type == IntentType.QUERY:
            suggestions.append({
                "action": "query_status",
                "description": "Récupérer le statut des appareils",
                "confidence": intent.confidence
            })
        
        elif intent.type == IntentType.SCENE:
            if "scene" in intent.entities:
                for scene in intent.entities["scene"]:
                    suggestions.append({
                        "action": "activate_scene",
                        "description": f"Activer la scène {scene}",
                        "parameters": {"scene_name": scene},
                        "confidence": intent.confidence
                    })
        
        return suggestions
