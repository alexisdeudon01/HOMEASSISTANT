# Plan d'Implémentation de l'Architecture de Microservices

## État Actuel du Projet

### Fichiers à conserver:
- `.env` (fichier de variables d'environnement)
- `.gitignore` (déjà créé pour exclure les fichiers .env)
- `PLAN_IMPLEMENTATION.md` (documentation existante)

### Structure actuelle à migrer:
- `docker-compose.yml` (configuration Docker existante)
- Répertoire `services/` (services existants)
- Répertoire `gateway/` (gateway existant)
- Répertoire `enthropic/` (service AI existant)
- Répertoire `entities/` (modèles d'entités existants)
- Répertoire `protocols/` (protocoles existants)

## Nouvelle Architecture Proposée

### Microservices à créer:

1. **gateway-service** - Point d'entrée principal de l'API
2. **ha-integration-service** - Intégration avec Home Assistant
3. **ai-service** - Service d'intelligence artificielle
4. **discovery-service** - Découverte automatique des devices
5. **entity-service** - Gestion des entités
6. **protocol-service** - Gestion des protocoles de communication
7. **mqtt-service** - Service MQTT
8. **redis-service** - Service Redis
9. **monitoring-service** - Surveillance des conteneurs

## Plan d'Implémentation Détaillé

### Phase 1: Préparation et Migration (Jour 1-2)

#### Étape 1.1: Sauvegarde et analyse
- [ ] Sauvegarder la structure actuelle dans un dossier `legacy/`
- [ ] Analyser le code existant pour identifier les fonctionnalités à migrer
- [ ] Documenter les dépendances entre services existants

#### Étape 1.2: Configuration Git
- [ ] Vérifier que le dépôt GitHub est correctement configuré (déjà fait)
- [ ] S'assurer que l'authentification SSH fonctionne
- [ ] Mettre à jour le fichier `.gitignore` pour la nouvelle structure

### Phase 2: Création de la Structure (Jour 2-3)

#### Étape 2.1: Nettoyage de la racine
- [ ] Déplacer les fichiers non essentiels vers `legacy/`
- [ ] Conserver uniquement `.env`, `.gitignore`, et documentation

#### Étape 2.2: Création des répertoires de microservices
Pour chaque microservice dans la liste:
- [ ] Créer le répertoire principal (ex: `gateway-service/`)
- [ ] Créer la structure interne (`app/`, `Dockerfile`, `requirements.txt`, `main.py`)
- [ ] Configurer les permissions et propriétaires

### Phase 3: Implémentation des Modèles de Données (Jour 3-4)

#### Étape 3.1: Modèles communs
- [ ] Créer un module `shared/models.py` avec les dataclasses:
  - `Entity`, `Sensor`, `Domain`, `Integration`, `Notification`, `Device`
- [ ] Implémenter `EntityFactory` pour la création d'entités
- [ ] Ajouter la validation avec Pydantic

#### Étape 3.2: Configuration des dépendances
- [ ] Créer `requirements.txt` pour chaque microservice
- [ ] Définir les versions compatibles des bibliothèques
- [ ] Configurer `pip` pour l'installation optimisée

### Phase 4: Implémentation des Services (Jour 4-7)

#### Étape 4.1: Gateway Service
- [ ] Implémenter les routes CRUD pour devices et entités
- [ ] Ajouter l'authentification et l'autorisation
- [ ] Configurer le logging et la gestion d'erreurs

#### Étape 4.2: HA Integration Service
- [ ] Implémenter l'intégration avec l'API Home Assistant
- [ ] Gérer les webhooks et les callbacks
- [ ] Synchroniser les états entre services

#### Étape 4.3: AI Service
- [ ] Migrer le code existant d'`enthropic/`
- [ ] Implémenter l'analyse des logs Docker
- [ ] Intégrer avec l'API Anthropic

#### Étape 4.4: Discovery Service
- [ ] Implémenter la découverte MQTT
- [ ] Ajouter la détection automatique des devices
- [ ] Configurer les règles de découverte

#### Étape 4.5: Entity Service
- [ ] Implémenter la gestion des intégrations
- [ ] Créer le registre des entités
- [ ] Gérer le cycle de vie des entités

#### Étape 4.6: Protocol Service
- [ ] Migrer le code existant de `protocols/`
- [ ] Implémenter les adaptateurs de protocole
- [ ] Gérer les connexions et les timeouts

#### Étape 4.7: MQTT Service
- [ ] Configurer le broker MQTT
- [ ] Implémenter les handlers de messages
- [ ] Gérer les abonnements et publications

#### Étape 4.8: Redis Service
- [ ] Configurer Redis comme cache distribué
- [ ] Implémenter les opérations de cache
- [ ] Gérer l'expiration des données

#### Étape 4.9: Monitoring Service
- [ ] Implémenter la surveillance Docker
- [ ] Analyser les logs des conteneurs
- [ ] Envoyer des notifications à Home Assistant

### Phase 5: Configuration Docker (Jour 7-8)

#### Étape 5.1: Dockerfiles
- [ ] Créer un Dockerfile optimisé pour chaque microservice
- [ ] Configurer les multi-stage builds
- [ ] Optimiser les layers pour le cache

#### Étape 5.2: Docker Compose
- [ ] Créer un nouveau `docker-compose.yml` unifié
- [ ] Configurer les réseaux et volumes
- [ ] Définir les dépendances entre services
- [ ] Ajouter le montage du fichier `.env` dans chaque conteneur

#### Étape 5.3: Scripts d'initialisation
- [ ] Créer `scripts/export-env.sh` pour exporter les variables
- [ ] Configurer l'entrée point pour chaque conteneur
- [ ] Implémenter les health checks

### Phase 6: Injection de Dépendances (Jour 8-9)

#### Étape 6.1: Configuration DI
- [ ] Implémenter un conteneur d'injection de dépendances
- [ ] Configurer les dépendances entre microservices
- [ ] Gérer le cycle de vie des services

#### Étape 6.2: Communication inter-services
- [ ] Configurer Redis pour la communication
- [ ] Implémenter les messages asynchrones
- [ ] Gérer les retries et la résilience

### Phase 7: Tests et Validation (Jour 9-10)

#### Étape 7.1: Tests unitaires
- [ ] Écrire des tests pour chaque microservice
- [ ] Configurer la couverture de code
- [ ] Automatiser l'exécution des tests

#### Étape 7.2: Tests d'intégration
- [ ] Tester la communication entre microservices
- [ ] Valider les flux de données
- [ ] Tester les scénarios d'erreur

#### Étape 7.3: Tests de performance
- [ ] Tester la charge et la scalabilité
- [ ] Mesurer les temps de réponse
- [ ] Optimiser les performances

### Phase 8: Déploiement et Documentation (Jour 10-11)

#### Étape 8.1: Documentation
- [ ] Documenter l'API de chaque microservice
- [ ] Créer des guides d'installation
- [ ] Documenter les variables d'environnement

#### Étape 8.2: Déploiement
- [ ] Configurer les variables d'environnement de production
- [ ] Préparer les scripts de déploiement
- [ ] Tester le déploiement en environnement isolé

#### Étape 8.3: Monitoring et logging
- [ ] Configurer la collecte de logs centralisée
- [ ] Implémenter les métriques de monitoring
- [ ] Configurer les alertes

## Structure de Fichiers Recommandée

```
sinik-os-full/
├── .env
├── .gitignore
├── docker-compose.yml
├── README.md
├── gateway-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       ├── models.py
│       └── dependencies.py
├── ha-integration-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── ai-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── discovery-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── entity-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── protocol-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── mqtt-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── mqtt.py
│       └── config.py
├── redis-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── redis.py
│       └── config.py
├── monitoring-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── routes.py
│       ├── services.py
│       └── models.py
├── shared/
│   ├── __init__.py
│   ├── models.py
│   ├── config.py
│   └── utils.py
├── scripts/
│   ├── export-env.sh
│   ├── deploy.sh
│   └── test.sh
└── tests/
    ├── unit/
    ├── integration/
    └── performance/
```

## Variables d'Environnement à Ajouter

Basé sur l'analyse du fichier `.env` existant, voici les variables supplémentaires nécessaires:

```bash
# Microservices ports
GATEWAY_SERVICE_PORT=8000
HA_INTEGRATION_SERVICE_PORT=8001
AI_SERVICE_PORT=8002
DISCOVERY_SERVICE_PORT=8003
ENTITY_SERVICE_PORT=8004
PROTOCOL_SERVICE_PORT=8005
MQTT_SERVICE_PORT=8006
REDIS_SERVICE_PORT=6379
MONITORING_SERVICE_PORT=8007

# Service URLs
GATEWAY_SERVICE_URL=http://gateway-service:8000
HA_INTEGRATION_SERVICE_URL=http://ha-integration-service:8001
AI_SERVICE_URL=http://ai-service:8002
DISCOVERY_SERVICE_URL=http://discovery-service:8003
ENTITY_SERVICE_URL=http://entity-service:8004
PROTOCOL_SERVICE_URL=http://protocol-service:8005
MQTT_SERVICE_URL=http://mqtt-service:8006
REDIS_SERVICE_URL=redis://redis-service:6379
MONITORING_SERVICE_URL=http://monitoring-service:8007

# Database and cache
REDIS_HOST=redis-service
REDIS_PORT=6379
REDIS_DB=0

# MQTT configuration
MQTT_BROKER_HOST=mqtt-service
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Home Assistant
HA_URL=http://homeassistant:8123
HA_TOKEN=${HA_TOKEN}

# AI Configuration
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
MONITORING_INTERVAL=60
ALERT_THRESHOLD=5
```

## Prochaines Étapes Immédiates

1. **Approbation du plan** - Attendre la validation de l'utilisateur
2. **Sauvegarde** - Créer une sauvegarde complète du projet actuel
3. **Migration incrémentale** - Commencer par un microservice à la fois
4. **Tests continus** - Valider chaque étape avant de passer à la suivante

## Risques et Atténuation

- **Risque**: Perte de données pendant la migration
  - **Atténuation**: Sauvegardes complètes avant chaque étape

- **Risque**: Incompatibilité entre ancien et nouveau code
  - **Atténuation**: Migration progressive avec tests d'intégration

- **Risque**: Temps d'arrêt prolongé
  - **Atténuation**: Déploiement en blue-green avec basculement progressif

## Estimation de Temps

- **Total**: 11 jours (88 heures)
- **Phase 1-2**: 3 jours (préparation et structure)
- **Phase 3-4**: 4 jours (implémentation)
- **Phase 5-6**: 2 jours (configuration)
- **Phase 7-8**: 2 jours (tests et déploiement)

Ce plan fournit une feuille de route détaillée pour la migration vers l'architecture de microservices tout en préservant les fonctionnalités existantes.
