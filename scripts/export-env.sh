#!/bin/bash
# Script d'export des variables d'environnement pour les conteneurs Docker
# Ce script charge les variables du fichier .env et les exporte dans l'environnement

set -a  # Export automatique de toutes les variables

# Vérifier si le fichier .env existe
if [ -f "/app/.env" ]; then
    echo "Chargement des variables depuis /app/.env"
    source "/app/.env"
elif [ -f ".env" ]; then
    echo "Chargement des variables depuis .env (répertoire courant)"
    source ".env"
elif [ -f "/.env" ]; then
    echo "Chargement des variables depuis /.env (racine)"
    source "/.env"
else
    echo "Avertissement: Aucun fichier .env trouvé"
fi

set +a  # Désactiver l'export automatique

# Exécuter la commande passée en paramètre
exec "$@"
