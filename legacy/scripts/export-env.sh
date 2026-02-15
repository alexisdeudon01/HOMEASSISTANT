#!/bin/bash

# Script pour exporter les variables d'environnement depuis .env
# Utilisé dans les conteneurs Docker pour charger les variables

set -e

ENV_FILE="${ENV_FILE:-/app/.env}"

if [ -f "$ENV_FILE" ]; then
    echo "Chargement des variables d'environnement depuis $ENV_FILE"
    
    # Charger toutes les variables
    set -a
    source "$ENV_FILE"
    set +a
    
    # Exporter les variables pour les sous-processus
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | cut -d= -f1)
    
    # Afficher les variables chargées (sans les valeurs sensibles)
    echo "Variables chargées:"
    grep -v '^#' "$ENV_FILE" | grep -v '^$' | cut -d= -f1 | while read var; do
        if [[ "$var" =~ (API_KEY|TOKEN|SECRET|PASSWORD|AUTH) ]]; then
            echo "  $var=*** (masqué)"
        else
            value="${!var}"
            if [ ${#value} -gt 50 ]; then
                echo "  $var=${value:0:50}... (tronqué)"
            else
                echo "  $var=$value"
            fi
        fi
    done
    
    echo "Nombre total de variables: $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | wc -l)"
else
    echo "Avertissement: Fichier .env non trouvé à $ENV_FILE"
    echo "Utilisation des variables d'environnement existantes"
fi

# Exécuter la commande passée en paramètre
if [ $# -gt 0 ]; then
    exec "$@"
fi
