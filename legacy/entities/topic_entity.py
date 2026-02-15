"""
Entité de topic MQTT avancée.

Ce module définit TopicEntity, une entité spécialisée pour la gestion
de topics MQTT avec support de patterns, wildcards et transformations.
"""

from typing import Optional, Dict, Any, List, Pattern
import os
import re
from .base import BaseEntity, Device


class TopicEntity(BaseEntity):
    """Entité spécialisée pour les topics MQTT avec patterns."""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        topic_pattern: str,
        device: Optional[Device] = None,
        value_template: Optional[str] = None,
        wildcard: bool = False,
        multi_level: bool = False
    ):
        super().__init__(entity_id, name, device, domain="topic")
        self.topic_pattern = topic_pattern
        self.value_template = value_template
        self.wildcard = wildcard
        self.multi_level = multi_level
        self._compiled_pattern: Optional[Pattern] = None
        
        if wildcard or multi_level:
            self._compile_pattern()
    
    def _compile_pattern(self) -> None:
        """Compile le pattern de topic en regex."""
        pattern = self.topic_pattern
        
        # Remplace les wildcards MQTT
        if self.wildcard:
            pattern = pattern.replace('+', '[^/]+')
        if self.multi_level:
            pattern = pattern.replace('#', '.+')
        
        # Échappe les autres caractères spéciaux
        pattern = re.escape(pattern)
        
        # Restaure les wildcards
        if self.wildcard:
            pattern = pattern.replace('\\[\\^/\\]\\+', '[^/]+')
        if self.multi_level:
            pattern = pattern.replace('\\.\\+', '.+')
        
        self._compiled_pattern = re.compile(f'^{pattern}$')
    
    def matches_topic(self, topic: str) -> bool:
        """Vérifie si un topic correspond au pattern."""
        if not self._compiled_pattern:
            return topic == self.topic_pattern
        return bool(self._compiled_pattern.match(topic))
    
    def extract_values(self, topic: str) -> Dict[str, str]:
        """Extrait les valeurs des wildcards du topic."""
        if not self.wildcard and not self.multi_level:
            return {}
        
        if not self._compiled_pattern:
            return {}
        
        match = self._compiled_pattern.match(topic)
        if not match:
            return {}
        
        # Pour les patterns simples avec +, on extrait les segments
        if '+' in self.topic_pattern:
            pattern_parts = self.topic_pattern.split('/')
            topic_parts = topic.split('/')
            
            if len(pattern_parts) != len(topic_parts):
                return {}
            
            values = {}
            for i, (pattern_part, topic_part) in enumerate(zip(pattern_parts, topic_parts)):
                if pattern_part == '+':
                    values[f'level_{i}'] = topic_part
            
            return values
        
        return {}
    
    def process_value(self, payload: str, topic: str) -> Any:
        """Traite la valeur avec le template."""
        if not self.value_template:
            return payload
        
        # Remplace les variables dans le template
        result = self.value_template
        
        # Variables spéciales
        result = result.replace('{{ value }}', payload)
        result = result.replace('{{ topic }}', topic)
        
        # Variables extraites
        extracted = self.extract_values(topic)
        for key, value in extracted.items():
            result = result.replace(f'{{{{ {key} }}}}', value)
        
        # Évaluation simple (pour les templates JSON)
        try:
            if result.startswith('{{') and result.endswith('}}'):
                # Template Jinja-like simple
                expr = result[2:-2].strip()
                if expr == 'value':
                    return payload
                elif expr == 'topic':
                    return topic
        except:
            pass
        
        return result
    
    def get_capabilities(self) -> List[str]:
        """Retourne les capacités du topic."""
        caps = ["topic_matching"]
        if self.wildcard:
            caps.append("wildcard_matching")
        if self.multi_level:
            caps.append(os.getenv('TOPIC_MULTI_LEVEL_MATCHING', 'multi_level_matching'))
        if self.value_template:
            caps.append("value_processing")
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        base = super().to_dict()
        base.update({
            'topic_pattern': self.topic_pattern,
            'value_template': self.value_template,
            'wildcard': self.wildcard,
            'multi_level': self.multi_level
        })
        return base
