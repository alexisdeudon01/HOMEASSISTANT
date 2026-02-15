# PLAN D'IMPLÉMENTATION - Environnement Docker avec Gestion des Variables d'Environnement

## 1. Analyse de l'État Actuel

### 1.1 Structure du Projet
```
/home/pi/last/sinik-os-full/
├── .env                    # Fichier de variables d'environnement
├── docker-compose.yml      # Docker-compose principal
├── services/
│   ├── docker-compose-services.yml  # Docker-compose des services
│   ├── gateway-service/    # Service de passerelle
│   ├── ha-manager-service/ # Service gestionnaire Home Assistant
│   ├── brain-service/      # Service IA
│   └── ...
├── gateway/                # Passerelle principale
├── enthropic/              # Services IA
├── entities/               # Entités du système
├── protocols/              # Protocoles supportés
└── homeassistant/          # Configuration Home Assistant
```

### 1.2 Problèmes Identifiés
1. **Variables hardcodées** dans les fichiers Python
2. **Services Docker dupliqués** (redis, mosquitto, homeassistant)
3. **Conflits de ports** entre les deux fichiers docker-compose
4. **Absence de .gitignore** pour exclure les fichiers .env
5. **Environnement virtuel inutile** pour les conteneurs Docker
6. **Manque d'injection de dépendances** entre services

## 2. Plan d'Action Détaillé

### Étape 1: Création du Dépôt GitHub
- [ ] Utiliser la variable `GIT_REPO=HOMEASSISTANT` du fichier .env
- [ ] Configurer l'authentification SSH avec la clé existante
- [ ] Initialiser le dépôt avec la structure actuelle

### Étape 2: Gestion des Variables d'Environnement
- [ ] Créer `.gitignore` à la racine pour exclure tous les fichiers `.env`
- [ ] Scanner tous les fichiers Python pour identifier les variables hardcodées
- [ ] Remplacer les valeurs hardcodées par `os.getenv()` avec valeurs par défaut
- [ ] Ajouter les variables manquantes au fichier `.env`
- [ ] Supprimer les variables inutilisées du `.env`

### Étape 3: Nettoyage de l'Environnement
- [ ] Supprimer l'environnement virtuel actuel (`venv/`)
- [ ] Mettre à jour la documentation pour indiquer l'utilisation de Docker

### Étape 4: Optimisation Docker Compose
- [ ] Fusionner `docker-compose.yml` et `services/docker-compose-services.yml`
- [ ] Éliminer les services dupliqués (garder une seule instance de redis, mosquitto, homeassistant)
- [ ] Standardiser les ports (garder les ports standards: 6379, 1883, 8123)
- [ ] Ajouter un volume global pour monter `.env` dans chaque conteneur
- [ ] Créer un script `export-env.sh` pour exporter les variables dans chaque conteneur

### Étape 5: Configuration des Dockerfiles
- [ ] Pour chaque microservice, ajouter `RUN pip install -r requirements.txt`
- [ ] S'assurer que tous les Dockerfiles utilisent des images de base appropriées
- [ ] Configurer les healthchecks appropriés

### Étape 6: Injection de Dépendances
- [ ] Analyser le graphe de dépendances entre services
- [ ] Implémenter un mécanisme d'injection de dépendances
- [ ] Créer un service de découverte ou utiliser DNS Docker interne
- [ ] Configurer les variables d'environnement pour les connexions inter-services

### Étape 7: Structure de Fichiers Recommandée
```
sinik-os/
├── .gitignore
├── .env
├── docker-compose.yml
├── scripts/
│   ├── export-env.sh
│   ├── find_hardcoded.py
│   └── replace_hardcoded.py
├── services/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py
│   ├── brain/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py
│   └── ...
├── shared/
│   ├── mqtt_client.py
│   └── requirements.txt
├── entities/
│   ├── __init__.py
│   ├── base.py
│   ├── device_entities.py
│   ├── factory.py
│   └── service_entities.py  # Nouvelles dataclasses
├── protocols/
│   ├── __init__.py
│   ├── base.py
│   ├── http.py
│   ├── mqtt.py
│   └── websocket.py
└── enthropic/
    ├── __init__.py
    ├── ai_service.py        # Modifié avec add_zip_to_prompt()
    ├── context_manager.py
    ├── decision_engine.py
    └── intent_parser.py
```

### Étape 8: Implémentation des Dataclasses et Commandes
- [ ] Créer `entities/service_entities.py` avec dataclasses pour les prompts
- [ ] Ajouter dataclasses pour ZIP, prompts et réponses JSON
- [ ] Implémenter le pattern Factory dans `entities/factory.py`
- [ ] Créer `services/command_service.py` avec classes Command
- [ ] Modifier `enthropic/ai_service.py` pour ajouter `add_zip_to_prompt()`

### Étape 9: Flux d'Intégration IA
- [ ] Créer un prompt d'architecture pour l'API Anthropic
- [ ] Implémenter la fonction `add_zip_to_prompt()` pour compresser le projet
- [ ] Configurer l'envoi du prompt à l'API Anthropic
- [ ] Traiter la réponse JSON et l'afficher

### Étape 10: Tests et Validation
- [ ] Tester le flux complet de compression et envoi à l'API
- [ ] Vérifier que toutes les variables d'environnement sont chargées
- [ ] Tester les dépendances entre services
- [ ] Valider le démarrage de tous les conteneurs

## 3. Variables d'Environnement à Ajouter/Corriger

### Variables manquantes identifiées:
- `GATEWAY_HOST` (hardcodé à "0.0.0.0")
- `SERVICE_PORT` (hardcodé à 8001, 8002, etc.)
- `LOG_LEVEL` (déjà dans .env mais hardcodé)
- `REDIS_URL` (format complet: redis://redis:6379)
- `MQTT_BROKER` (nom du service: mosquitto)

### Variables à supprimer (inutilisées):
- `METRICS_TOTAL_CONNECTIONS_RECEIVED`
- `METRICS_TOTAL_COMMANDS_PROCESSED`
- `TOPIC_MULTI_LEVEL_MATCHING`

## 4. Graphe de Dépendances Recommandé

```
redis (6379)
  ├── mosquitto (1883)
  │     ├── gateway-service
  │     ├── brain-service
  │     └── protocol-service
  └── homeassistant (8123)
        └── ha-manager-service
              └── infrastructure-manager
```

## 5. Scripts à Créer

### 5.1 `scripts/export-env.sh`
```bash
#!/bin/bash
# Exporte les variables d'environnement depuis .env
set -a
source /app/.env
set +a
exec "$@"
```

### 5.2 `scripts/find_hardcoded.py`
```python
# Script pour identifier les variables hardcodées
```

### 5.3 `scripts/replace_hardcoded.py`
```python
# Script pour remplacer les variables hardcodées
```

## 6. Timeline Estimée

1. **Jour 1**: Configuration Git et gestion des variables
2. **Jour 2**: Optimisation Docker et injection de dépendances
3. **Jour 3**: Implémentation des dataclasses et commandes
4. **Jour 4**: Intégration IA et tests
5. **Jour 5**: Validation et documentation

## 7. Risques et Mitigations

- **Risque**: Conflits de ports entre services
  - **Mitigation**: Utiliser des ports uniques ou le réseau Docker interne

- **Risque**: Variables sensibles exposées dans Git
  - **Mitigation**: `.gitignore` strict et utilisation de secrets Docker

- **Risque**: Dépendances circulaires entre services
  - **Mitigation**: Analyse du graphe de dépendances et refactoring

## 8. Validation du Plan

Avant de procéder à l'implémentation, veuillez:
1. [ ] Examiner ce plan
2. [ ] Donner votre feu vert pour l'implémentation
3. [ ] Identifier toute modification nécessaire

Une fois votre approbation reçue, je procéderai à l'implémentation étape par étape.
