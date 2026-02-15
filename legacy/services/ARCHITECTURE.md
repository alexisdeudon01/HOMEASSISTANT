# Architecture des Services Sinik OS

## Vue d'ensemble

Sinik OS est une plateforme domotique modulaire composée de plusieurs services microservices qui communiquent entre eux via Redis et MQTT. Chaque service a une responsabilité spécifique et expose une API REST pour l'intégration.

## Services Principaux

### 1. Gateway Service (`services/gateway-service/`)

**Responsabilité** : Gestion centralisée des devices, entités et protocoles de communication.

**Description** :
- Service principal de passerelle qui expose une API REST complète
- Gère les devices (création, mise à jour, suppression)
- Gère les entités (sensors, lights, switches, etc.)
- Supporte plusieurs protocoles (MQTT, HTTP, WebSocket)
- Fournit des endpoints de découverte automatique

**Routes API principales** :
- `GET /` - Statut du service
- `GET /health` - Santé du service
- `GET /devices` - Liste des devices
- `POST /devices` - Création d'un device
- `GET /entities` - Liste des entités
- `POST /entities` - Création d'une entité
- `POST /command` - Envoi de commandes aux devices
- `GET /discover` - Découverte automatique

**Dépendances** :
- Redis pour le stockage en mémoire
- MQTT Broker pour la communication
- Protocoles HTTP/WebSocket pour l'intégration

### 2. HA Manager Service (`services/ha-manager-service/`)

**Responsabilité** : Intégration avec Home Assistant.

**Description** :
- Service d'intégration avec Home Assistant via API REST
- Gère la synchronisation des devices et entités
- Expose des webhooks pour les événements Home Assistant
- Fournit un endpoint de santé détaillé

**Routes API principales** :
- `GET /` - Statut du service
- `GET /health` - Santé détaillée avec vérification des composants
- `GET /ha/status` - Statut de Home Assistant
- `GET /ha/devices` - Liste des devices Home Assistant
- `POST /ha/devices/register` - Enregistrement de device
- `POST /ha/entities/register` - Enregistrement d'entité
- `POST /ha/webhook/{webhook_id}` - Gestion des webhooks

**Dépendances** :
- Home Assistant (API REST)
- Redis pour le cache
- MQTT pour la communication

### 3. Brain Service (`services/brain-service/`)

**Responsabilité** : Intelligence artificielle et prise de décision automatisée.

**Description** :
- Service d'IA qui analyse les événements réseau
- Prend des décisions automatisées pour les lumières
- Utilise Claude (Anthropic) pour l'analyse contextuelle
- Implémente des règles automatiques basées sur l'activité

**Fonctionnalités principales** :
- Analyse des services de streaming (Netflix, YouTube, etc.)
- Décisions automatisées pour les lumières Philips Hue
- Cooldown pour éviter les actions répétitives
- Logging des décisions dans Redis

**Règles automatiques** :
- Netflix/YouTube/Disney+ → Tamiser lumières (brightness 30-50)
- Spotify/Apple Music → Ambiance colorée
- Twitch → Lumière gaming (violet/bleu)
- Aucune activité → Ne rien faire

**Dépendances** :
- Redis pour les événements et le contexte
- API Anthropic (Claude) pour l'IA
- Philips Hue Bridge pour le contrôle des lumières

### 4. Entity Service (`services/entity-service/`)

**Responsabilité** : Gestion des modèles d'entités et de leur persistance.

**Description** :
- Service de gestion des modèles de données
- Définit les classes d'entités (Device, Entity, etc.)
- Gère la persistance des données
- Fournit des factories pour la création d'entités

**Classes principales** :
- `Device` - Représente un device physique
- `BaseEntity` - Classe de base pour toutes les entités
- `SensorEntity`, `LightEntity`, `SwitchEntity` - Entités spécifiques
- `MQTTEntity` - Entité MQTT spécialisée

### 5. Protocol Service (`services/protocol-service/`)

**Responsabilité** : Gestion des protocoles de communication.

**Description** :
- Service de gestion des protocoles (MQTT, HTTP, WebSocket)
- Fournit des clients pour chaque protocole
- Gère les connexions et la reconnexion
- Standardise l'interface de communication

**Protocoles supportés** :
- **MQTT** : Communication publish/subscribe
- **HTTP** : API REST standard
- **WebSocket** : Communication temps réel

### 6. Infrastructure Manager (`infrastructure-manager/`)

**Responsabilité** : Gestion de l'infrastructure et monitoring.

**Description** :
- Service de monitoring et de gestion d'infrastructure
- Dashboard web pour la visualisation
- Découverte automatique des devices
- Tests d'intégration

**Fonctionnalités** :
- Dashboard HTML pour la visualisation
- Découverte des devices HACS
- Tests d'intégration automatisés
- Rapports de statut

## Services de Support

### 7. Sensor Service (`sensor/`)

**Responsabilité** : Collecte de données des capteurs.

### 8. Reconciler Service (`reconciler/`)

**Responsabilité** : Réconciliation des données entre services.

### 9. Mosquitto (`mosquitto/`)

**Responsabilité** : Broker MQTT pour la communication entre services.

## Architecture Technique

### Communication entre Services

```
┌─────────────────┐    Redis Pub/Sub    ┌─────────────────┐
│   Brain Service │◄───────────────────►│ Gateway Service │
└─────────────────┘                     └─────────────────┘
         │                                       │
         │ MQTT                                  │ HTTP/REST
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│ Philips Hue     │                     │ Home Assistant  │
│ Bridge          │                     │                 │
└─────────────────┘                     └─────────────────┘
```

### Stack Technologique

- **Langage** : Python 3.13
- **Framework Web** : FastAPI
- **Communication** : Redis Pub/Sub, MQTT
- **Validation** : Pydantic
- **Configuration** : Pydantic Settings
- **IA** : Anthropic Claude
- **Conteneurisation** : Docker
- **Orchestration** : Docker Compose

### Structure des Données

```python
# Device
{
    "id": "device_001",
    "protocol": "mqtt",
    "name": "Living Room Light",
    "type": "light",
    "model": "Hue Color",
    "manufacturer": "Philips",
    "capabilities": {"on_off": True, "dimming": True, "color": True},
    "metadata": {"room": "living_room", "ip": "192.168.1.100"}
}

# Entity
{
    "entity_id": "light.living_room",
    "name": "Living Room Light",
    "domain": "light",
    "device_id": "device_001",
    "attributes": {"brightness": 255, "color": "warm"}
}
```

## Déploiement

### Configuration Docker Compose

```yaml
version: '3.8'
services:
  # Services principaux
  gateway-service:
    build: ./services/gateway-service
    ports: ["8000:8000"]
    environment:
      - REDIS_HOST=redis
      - MQTT_BROKER=mosquitto
    
  ha-manager-service:
    build: ./services/ha-manager-service
    ports: ["8001:8001"]
    environment:
      - HA_URL=http://homeassistant:8123
      - REDIS_URL=redis://redis:6379
    
  brain-service:
    build: ./services/brain-service
    environment:
      - REDIS_HOST=redis
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - HUE_BRIDGE_IP=${HUE_BRIDGE_IP}
    
  # Services de support
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
    
  mosquitto:
    image: eclipse-mosquitto:latest
    ports: ["1883:1883", "9001:9001"]
    
  # Infrastructure
  homeassistant:
    image: homeassistant/home-assistant:latest
    ports: ["8123:8123"]
```

### Variables d'Environnement

```bash
# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883

# Home Assistant
HA_URL=http://homeassistant:8123
HA_TOKEN=your_token_here

# Philips Hue
HUE_BRIDGE_IP=192.168.1.100
HUE_API_KEY=your_hue_api_key

# Anthropic AI
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Flux de Données

### 1. Découverte de Device
```
Device → Gateway Service → Redis → HA Manager Service → Home Assistant
```

### 2. Commande de Device
```
Utilisateur → Gateway Service → Protocol Service → Device
```

### 3. Événement IA
```
Network Event → Redis Pub/Sub → Brain Service → Hue Bridge → Lights
```

### 4. Synchronisation HA
```
Home Assistant Webhook → HA Manager Service → Redis → Gateway Service
```

## Sécurité

### Mesures de Sécurité Implémentées

1. **Configuration externalisée** : Utilisation de Pydantic Settings avec validation
2. **Tokens sécurisés** : Utilisation de `SecretStr` pour masquer les tokens sensibles
3. **Validation des données** : Validation stricte avec Pydantic
4. **Gestion des erreurs** : Hiérarchie d'exceptions personnalisées
5. **Logging sécurisé** : Masquage des informations sensibles dans les logs

### Bonnes Pratiques

- Utilisation de variables d'environnement pour les secrets
- Validation de toutes les entrées utilisateur
- Gestion appropriée des erreurs avec messages non techniques
- Logging structuré avec niveaux appropriés
- Documentation complète des APIs

## Monitoring et Maintenance

### Endpoints de Santé

Chaque service expose un endpoint `/health` qui fournit :
- Statut global du service
- Statut des dépendances (Redis, MQTT, etc.)
- Métriques de performance
- Version du service

### Logging

- Logging structuré avec format standard
- Niveaux de log configurables (DEBUG, INFO, WARNING, ERROR)
- Rotation des logs pour éviter la saturation
- Contextualisation des logs avec informations de requête

### Métriques

- Nombre de devices actifs
- Nombre d'entités gérées
- Latence des requêtes
- Taux d'erreur
- Utilisation mémoire/CPU

## Évolution Future

### Améliorations Planifiées

1. **Authentification JWT** : Ajout d'authentification sécurisée
2. **Rate Limiting** : Protection contre les abus
3. **Monitoring avancé** : Intégration avec Prometheus/Grafana
4. **Tests unitaires complets** : Couverture de test améliorée
5. **Documentation OpenAPI** : Documentation interactive des APIs
6. **Support de nouveaux protocoles** : Zigbee, Z-Wave, Matter
7. **Interface utilisateur** : Dashboard web complet

### Scalabilité

- Architecture microservices permettant le scaling horizontal
- Utilisation de Redis pour le cache et la communication
- Design stateless pour faciliter le déploiement
- Configuration externalisée pour différents environnements

## Conclusion

Sinik OS est une plateforme domotique modulaire et extensible conçue pour être robuste, maintenable et évolutive. L'architecture microservices permet une grande flexibilité et facilite l'ajout de nouvelles fonctionnalités. Chaque service a une responsabilité clairement définie et communique via des interfaces standardisées.

La plateforme est prête pour la production avec une gestion d'erreurs robuste, une configuration flexible et une documentation complète.
