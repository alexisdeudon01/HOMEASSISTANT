# Services Sinik OS

Ce répertoire contient tous les services microservices de la plateforme Sinik OS.

## Vue d'ensemble

Sinik OS est une plateforme domotique modulaire composée de plusieurs services qui communiquent entre eux via Redis et MQTT. Chaque service a une responsabilité spécifique et expose une API REST pour l'intégration.

## Services Disponibles

### Services Principaux

1. **Gateway Service** (`gateway-service/`)
   - Gestion centralisée des devices et entités
   - Support de multiples protocoles (MQTT, HTTP, WebSocket)
   - API REST complète pour la gestion des devices

2. **HA Manager Service** (`ha-manager-service/`)
   - Intégration avec Home Assistant
   - Synchronisation des devices et entités
   - Webhooks pour les événements Home Assistant

3. **Brain Service** (`brain-service/`)
   - Intelligence artificielle pour l'automatisation
   - Analyse des événements réseau
   - Contrôle automatisé des lumières Philips Hue

4. **Entity Service** (`entity-service/`)
   - Gestion des modèles de données
   - Persistance des entités
   - Factories pour la création d'entités

5. **Protocol Service** (`protocol-service/`)
   - Gestion des protocoles de communication
   - Clients MQTT, HTTP, WebSocket
   - Standardisation des interfaces

### Services de Support

6. **Infrastructure Manager** (`../infrastructure-manager/`)
   - Monitoring et gestion d'infrastructure
   - Dashboard web de visualisation
   - Tests d'intégration

7. **Sensor Service** (`../sensor/`)
   - Collecte de données des capteurs

8. **Reconciler Service** (`../reconciler/`)
   - Réconciliation des données entre services

## Démarrage Rapide

### Prérequis

- Docker et Docker Compose
- Python 3.13+
- Redis
- MQTT Broker (Mosquitto)

### Installation

1. **Cloner le projet** :
   ```bash
   git clone <repository-url>
   cd sinik-os-full
   ```

2. **Configurer les variables d'environnement** :
   ```bash
   cp .env.example .env
   # Éditer .env avec vos configurations
   ```

3. **Démarrer les services** :
   ```bash
   docker-compose up -d
   ```

4. **Vérifier le statut** :
   ```bash
   docker-compose ps
   ```

### Configuration des Services

#### Gateway Service
```bash
# Port : 8000
# URL : http://localhost:8000
# Documentation : http://localhost:8000/docs
```

#### HA Manager Service
```bash
# Port : 8001
# URL : http://localhost:8001
# Documentation : http://localhost:8001/docs
```

#### Brain Service
```bash
# Service d'arrière-plan
# Écoute les événements Redis
# Nécessite une clé API Anthropic
```

## Utilisation

### 1. Découvrir des devices
```bash
curl -X GET "http://localhost:8000/discover?protocol=mqtt"
```

### 2. Créer un device
```bash
curl -X POST "http://localhost:8000/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "light_001",
    "protocol": "mqtt",
    "name": "Living Room Light",
    "type": "light",
    "model": "Hue Color",
    "manufacturer": "Philips",
    "capabilities": {
      "on_off": true,
      "dimming": true,
      "color": true
    }
  }'
```

### 3. Envoyer une commande
```bash
curl -X POST "http://localhost:8000/command" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "light_001",
    "command": "turn_on",
    "parameters": {
      "brightness": 255,
      "color": "warm"
    }
  }'
```

### 4. Vérifier la santé des services
```bash
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8001/health"
```

## Développement

### Structure d'un Service

Chaque service suit la structure standard :

```
service-name/
├── Dockerfile              # Configuration Docker
├── requirements.txt        # Dépendances Python
├── main.py                # Point d'entrée principal
├── config.py              # Configuration (optionnel)
├── models.py              # Modèles de données (optionnel)
└── data/                  # Données persistantes (optionnel)
```

### Ajouter un Nouveau Service

1. **Créer le répertoire du service** :
   ```bash
   mkdir services/my-new-service
   cd services/my-new-service
   ```

2. **Créer les fichiers de base** :
   ```bash
   touch Dockerfile requirements.txt main.py
   ```

3. **Ajouter au docker-compose.yml** :
   ```yaml
   my-new-service:
     build: ./services/my-new-service
     ports: ["8002:8002"]
     environment:
       - REDIS_HOST=redis
       - MQTT_BROKER=mosquitto
     depends_on:
       - redis
       - mosquitto
   ```

4. **Développer le service** :
   - Utiliser FastAPI pour les APIs REST
   - Utiliser Pydantic pour la validation
   - Utiliser Redis pour la communication inter-services

### Tests

Chaque service devrait inclure des tests :

```bash
# Exécuter les tests
cd services/gateway-service
python -m pytest tests/

# Tests avec couverture
python -m pytest --cov=main tests/
```

## Architecture Détailée

Pour une documentation complète de l'architecture, consultez [ARCHITECTURE.md](ARCHITECTURE.md).

### Communication entre Services

- **Redis Pub/Sub** : Pour les événements asynchrones
- **MQTT** : Pour la communication avec les devices
- **HTTP/REST** : Pour les APIs entre services
- **WebSocket** : Pour la communication temps réel

### Flux de Données

1. **Découverte** : Device → Gateway → Redis → HA Manager → Home Assistant
2. **Commande** : Utilisateur → Gateway → Protocol → Device
3. **IA** : Événement → Redis → Brain → Hue Bridge → Lights
4. **Synchronisation** : Home Assistant → HA Manager → Redis → Gateway

## Dépannage

### Problèmes Courants

1. **Service non démarré** :
   ```bash
   docker-compose logs <service-name>
   ```

2. **Redis non accessible** :
   ```bash
   docker-compose restart redis
   ```

3. **MQTT non accessible** :
   ```bash
   docker-compose restart mosquitto
   ```

4. **Problèmes de dépendances** :
   ```bash
   cd services/<service-name>
   pip install -r requirements.txt
   ```

### Logs

Consulter les logs des services :

```bash
# Tous les services
docker-compose logs

# Service spécifique
docker-compose logs gateway-service

# Logs en temps réel
docker-compose logs -f gateway-service
```

## Contribution

### Guidelines de Développement

1. **Code Style** :
   - Suivre PEP 8
   - Utiliser Black pour le formatage
   - Utiliser isort pour l'organisation des imports

2. **Documentation** :
   - Documenter toutes les fonctions et classes
   - Mettre à jour le README.md
   - Ajouter des exemples d'utilisation

3. **Tests** :
   - Écrire des tests unitaires
   - Maintenir une couverture de code > 80%
   - Tester les cas d'erreur

4. **Validation** :
   - Valider toutes les entrées avec Pydantic
   - Gérer les erreurs de manière appropriée
   - Loguer les erreurs avec contexte

### Processus de Contribution

1. Fork du repository
2. Créer une branche de fonctionnalité
3. Développer la fonctionnalité avec tests
4. Soumettre une Pull Request
5. Revue de code et intégration

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](../LICENSE) pour plus de détails.

## Support

Pour le support et les questions :

- **Documentation** : [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues** : [GitHub Issues](<repository-url>/issues)
- **Discussions** : [GitHub Discussions](<repository-url>/discussions)

---

**Note** : Cette documentation est en constante évolution. Consultez régulièrement les mises à jour.
