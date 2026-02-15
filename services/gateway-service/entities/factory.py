"""
Factory pattern pour la création d'entités.

Ce module implémente un pattern Factory pour créer des entités
basées sur leur type ou domaine.
"""

from typing import Dict, Any, Optional, Type
import logging
from entities.models import Device, BaseEntity
from entities.device_entities import SensorEntity, BinarySensorEntity, LightEntity, SwitchEntity, CoverEntity, ClimateEntity, MediaPlayerEntity


class EntityFactory:
    """Factory pour créer des entités basées sur leur type."""
    
    # Registre des types d'entités supportés
    _entity_registry: Dict[str, Type[BaseEntity]] = {
        'sensor': SensorEntity,
        'binary_sensor': BinarySensorEntity,
        'light': LightEntity,
        'switch': SwitchEntity,
        'climate': ClimateEntity,
        'cover': CoverEntity,
        'media_player': MediaPlayerEntity,
    }
    
    @classmethod
    def register_entity_type(cls, entity_type: str, entity_class: Type[BaseEntity]) -> None:
        """
        Enregistre un nouveau type d'entité dans la factory.
        
        Args:
            entity_type: Type d'entité (ex: 'light', 'switch')
            entity_class: Classe d'entité correspondante
        """
        cls._entity_registry[entity_type] = entity_class
        logging.info(f"Type d'entité enregistré: {entity_type} -> {entity_class.__name__}")
    
    @classmethod
    def create_entity(
        cls,
        entity_type: str,
        entity_id: str,
        name: str,
        device: Optional[Device] = None,
        **kwargs
    ) -> BaseEntity:
        """
        Crée une entité basée sur son type.
        
        Args:
            entity_type: Type d'entité (ex: 'sensor', 'light')
            entity_id: ID unique de l'entité
            name: Nom de l'entité
            device: Device associé (optionnel)
            **kwargs: Arguments supplémentaires pour l'initialisation
            
        Returns:
            Instance de l'entité créée
            
        Raises:
            ValueError: Si le type d'entité n'est pas supporté
        """
        if entity_type not in cls._entity_registry:
            # Essayer de détecter le type basé sur l'ID ou le nom
            entity_type = cls._detect_entity_type(entity_id, name, kwargs)
            
            if entity_type not in cls._entity_registry:
                raise ValueError(f"Type d'entité non supporté: {entity_type}")
        
        entity_class = cls._entity_registry[entity_type]
        
        # Création de l'entité
        entity = entity_class(entity_id=entity_id, name=name, device=device)
        
        # Configuration des propriétés spécifiques
        cls._configure_entity(entity, entity_type, kwargs)
        
        logging.debug(f"Entité créée: {entity_id} ({entity_type})")
        return entity
    
    @classmethod
    def _detect_entity_type(
        cls,
        entity_id: str,
        name: str,
        kwargs: Dict[str, Any]
    ) -> str:
        """
        Détecte le type d'entité basé sur des indices.
        
        Args:
            entity_id: ID de l'entité
            name: Nom de l'entité
            kwargs: Arguments supplémentaires
            
        Returns:
            Type d'entité détecté
        """
        # Détection basée sur l'ID
        entity_id_lower = entity_id.lower()
        
        if 'sensor' in entity_id_lower:
            return 'sensor'
        elif 'binary' in entity_id_lower or 'switch' in entity_id_lower:
            return 'binary_sensor'
        elif 'light' in entity_id_lower or 'lamp' in entity_id_lower:
            return 'light'
        elif 'temperature' in entity_id_lower or 'humidity' in entity_id_lower:
            return 'sensor'
        
        # Détection basée sur les capacités du device
        if 'device' in kwargs and kwargs['device']:
            device = kwargs['device']
            capabilities = device.capabilities
            
            if capabilities.get('has_measurements', False):
                return 'sensor'
            elif capabilities.get('has_on_off', False):
                return 'binary_sensor'
            elif capabilities.get('has_brightness', False) or capabilities.get('has_color', False):
                return 'light'
        
        # Par défaut
        return 'sensor'
    
    @classmethod
    def _configure_entity(
        cls,
        entity: BaseEntity,
        entity_type: str,
        kwargs: Dict[str, Any]
    ) -> None:
        """
        Configure les propriétés spécifiques d'une entité.
        
        Args:
            entity: Entité à configurer
            entity_type: Type d'entité
            kwargs: Arguments de configuration
        """
        if entity_type == 'sensor' and isinstance(entity, SensorEntity):
            cls._configure_sensor(entity, kwargs)
        elif entity_type == 'binary_sensor' and isinstance(entity, BinarySensorEntity):
            cls._configure_binary_sensor(entity, kwargs)
        elif entity_type == 'light' and isinstance(entity, LightEntity):
            cls._configure_light(entity, kwargs)
        elif entity_type == 'switch' and isinstance(entity, SwitchEntity):
            cls._configure_switch(entity, kwargs)
        elif entity_type == 'climate' and isinstance(entity, ClimateEntity):
            cls._configure_climate(entity, kwargs)
        elif entity_type == 'cover' and isinstance(entity, CoverEntity):
            cls._configure_cover(entity, kwargs)
        elif entity_type == 'media_player' and isinstance(entity, MediaPlayerEntity):
            cls._configure_media_player(entity, kwargs)
    
    @classmethod
    def _configure_sensor(cls, entity: SensorEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un capteur."""
        if 'device_class' in kwargs:
            entity.device_class = kwargs['device_class']
        if 'unit_of_measurement' in kwargs:
            entity.unit_of_measurement = kwargs['unit_of_measurement']
        if 'state_class' in kwargs:
            entity.state_class = kwargs['state_class']
    
    @classmethod
    def _configure_binary_sensor(cls, entity: BinarySensorEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un capteur binaire."""
        if 'device_class' in kwargs:
            entity.device_class = kwargs['device_class']
    
    @classmethod
    def _configure_light(cls, entity: LightEntity, kwargs: Dict[str, Any]) -> None:
        """Configure une lumière."""
        if 'brightness' in kwargs:
            entity.brightness = kwargs['brightness']
        if 'color_temp' in kwargs:
            entity.color_temp = kwargs['color_temp']
        if 'rgb_color' in kwargs:
            entity.rgb_color = kwargs['rgb_color']
    
    @classmethod
    def _configure_switch(cls, entity: SwitchEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un interrupteur."""
        # Pas de configuration spécifique pour l'instant
        pass
    
    @classmethod
    def _configure_climate(cls, entity: ClimateEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un climatiseur."""
        if 'temperature' in kwargs:
            entity.temperature = kwargs['temperature']
        if 'humidity' in kwargs:
            entity.humidity = kwargs['humidity']
        if 'fan_mode' in kwargs:
            entity.fan_mode = kwargs['fan_mode']
        if 'swing_mode' in kwargs:
            entity.swing_mode = kwargs['swing_mode']
    
    @classmethod
    def _configure_cover(cls, entity: CoverEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un volet/rideau."""
        if 'position' in kwargs:
            entity.position = kwargs['position']
        if 'tilt' in kwargs:
            entity.tilt = kwargs['tilt']
    
    @classmethod
    def _configure_media_player(cls, entity: MediaPlayerEntity, kwargs: Dict[str, Any]) -> None:
        """Configure un lecteur média."""
        if 'volume' in kwargs:
            entity.volume = kwargs['volume']
        if 'source' in kwargs:
            entity.source = kwargs['source']
        if 'media_content' in kwargs:
            entity.media_content = kwargs['media_content']
    
    @classmethod
    def create_from_device(
        cls,
        device: Device,
        entity_id_template: str = "{protocol}_{id}_{index}"
    ) -> list[BaseEntity]:
        """
        Crée des entités à partir d'un device.
        
        Args:
            device: Device source
            entity_id_template: Template pour les IDs d'entités
            
        Returns:
            Liste d'entités créées
        """
        entities = []
        capabilities = device.capabilities
        
        # Détection du type principal
        main_entity_type = cls._detect_device_type(device)
        
        # Création de l'entité principale
        main_entity_id = entity_id_template.format(
            protocol=device.protocol,
            id=device.id,
            index="main"
        )
        
        main_entity = cls.create_entity(
            entity_type=main_entity_type,
            entity_id=main_entity_id,
            name=device.name,
            device=device
        )
        entities.append(main_entity)
        
        # Création d'entités supplémentaires basées sur les capacités
        if capabilities.get('has_temperature', False):
            temp_entity_id = entity_id_template.format(
                protocol=device.protocol,
                id=device.id,
                index="temperature"
            )
            temp_entity = cls.create_entity(
                entity_type='sensor',
                entity_id=temp_entity_id,
                name=f"{device.name} Temperature",
                device=device,
                device_class='temperature',
                unit_of_measurement='°C',
                state_class='measurement'
            )
            entities.append(temp_entity)
        
        if capabilities.get('has_humidity', False):
            humidity_entity_id = entity_id_template.format(
                protocol=device.protocol,
                id=device.id,
                index="humidity"
            )
            humidity_entity = cls.create_entity(
                entity_type='sensor',
                entity_id=humidity_entity_id,
                name=f"{device.name} Humidity",
                device=device,
                device_class='humidity',
                unit_of_measurement='%',
                state_class='measurement'
            )
            entities.append(humidity_entity)
        
        return entities
    
    @classmethod
    def _detect_device_type(cls, device: Device) -> str:
        """
        Détecte le type d'entité principal pour un device.
        
        Args:
            device: Device à analyser
            
        Returns:
            Type d'entité principal
        """
        capabilities = device.capabilities
        
        if capabilities.get('has_measurements', False):
            return 'sensor'
        elif capabilities.get('has_on_off', False):
            return 'binary_sensor'
        elif capabilities.get('has_brightness', False) or capabilities.get('has_color', False):
            return 'light'
        else:
            return device.type if device.type else 'sensor'
