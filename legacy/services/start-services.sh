#!/bin/bash

# Script de démarrage pour les services Sinik OS
# Ce script permet de démarrer, arrêter et gérer les services microservices

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SERVICES_DIR/docker-compose-services.yml"
ENV_FILE="$SERVICES_DIR/../common.env"
DOCKER_COMPOSE_CMD=""

# Fonctions d'affichage
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_prerequisites() {
    print_info "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if [ -z "$DOCKER_COMPOSE_CMD" ]; then
        if command -v docker-compose &> /dev/null; then
            DOCKER_COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            DOCKER_COMPOSE_CMD="docker compose"
        else
            print_error "Docker Compose n'est pas installé"
            exit 1
        fi
    fi
    
    print_info "Utilisation de la commande: $DOCKER_COMPOSE_CMD"
    
    # Vérifier le fichier de configuration
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Fichier docker-compose-services.yml introuvable: $COMPOSE_FILE"
        exit 1
    fi
    
    # Vérifier le fichier d'environnement
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Fichier d'environnement introuvable: $ENV_FILE"
        print_warning "Création d'un fichier d'environnement par défaut..."
        cp "$SERVICES_DIR/../.env.example" "$ENV_FILE" 2>/dev/null || true
    fi
    
    print_success "Prérequis vérifiés avec succès"
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commandes disponibles:"
    echo "  start           Démarrer tous les services"
    echo "  stop            Arrêter tous les services"
    echo "  restart         Redémarrer tous les services"
    echo "  status          Afficher le statut des services"
    echo "  logs [SERVICE]  Afficher les logs des services"
    echo "  build           Reconstruire les images Docker"
    echo "  clean           Nettoyer les conteneurs et volumes"
    echo "  health          Vérifier la santé des services"
    echo "  help            Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 start        # Démarrer tous les services"
    echo "  $0 logs gateway # Afficher les logs du service gateway"
    echo "  $0 health       # Vérifier la santé des services"
}

# Démarrer les services
start_services() {
    print_info "Démarrage des services Sinik OS..."
    
    check_prerequisites
    
    # Vérifier si les services sont déjà en cours d'exécution
    if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        print_warning "Certains services sont déjà en cours d'exécution"
        read -p "Voulez-vous les redémarrer ? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_services
        else
            print_info "Utilisation des services existants"
            return 0
        fi
    fi
    
    # Démarrer les services
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    # Attendre que les services soient prêts
    print_info "Attente du démarrage des services..."
    sleep 10
    
    # Vérifier le statut
    status_services
    
    print_success "Services démarrés avec succès"
    print_info "Accès aux services:"
    print_info "  Gateway Service: http://localhost:8000"
    print_info "  HA Manager Service: http://localhost:8001"
    print_info "  Entity Service: http://localhost:8002"
    print_info "  Protocol Service: http://localhost:8003"
    print_info "  Home Assistant: http://localhost:8124"
}

# Arrêter les services
stop_services() {
    print_info "Arrêt des services Sinik OS..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" down
    print_success "Services arrêtés avec succès"
}

# Redémarrer les services
restart_services() {
    print_info "Redémarrage des services Sinik OS..."
    stop_services
    start_services
}

# Afficher le statut des services
status_services() {
    check_prerequisites
    print_info "Statut des services Sinik OS:"
    echo ""
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo ""
    
    # Vérifier les ports en écoute
    print_info "Ports en écoute:"
    for port in 8000 8001 8002 8003 8124 6380 1884; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_success "  Port $port: En écoute"
        else
            print_warning "  Port $port: Non disponible"
        fi
    done
}

# Afficher les logs
show_logs() {
    local service="$1"
    
    check_prerequisites
    
    if [ -z "$service" ]; then
        print_info "Affichage des logs de tous les services..."
        $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" logs -f
    else
        print_info "Affichage des logs du service: $service"
        $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

# Reconstruire les images
build_services() {
    check_prerequisites
    print_info "Reconstruction des images Docker..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache
    print_success "Images reconstruites avec succès"
}

# Nettoyer l'environnement
clean_environment() {
    check_prerequisites
    print_warning "Nettoyage de l'environnement..."
    print_warning "Cette opération supprimera tous les conteneurs, images et volumes!"
    
    read -p "Êtes-vous sûr de vouloir continuer ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Nettoyage annulé"
        return 0
    fi
    
    print_info "Arrêt et suppression des conteneurs..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" down -v --rmi all
    
    print_info "Nettoyage des ressources Docker..."
    docker system prune -f
    docker volume prune -f
    
    print_success "Environnement nettoyé avec succès"
}

# Vérifier la santé des services
check_health() {
    print_info "Vérification de la santé des services..."
    
    # Liste des services à vérifier
    services=(
        "http://localhost:8000/health"
        "http://localhost:8001/health"
        "http://localhost:8002/health"
        "http://localhost:8003/health"
        "http://localhost:8124/api/"
    )
    
    all_healthy=true
    
    for url in "${services[@]}"; do
        service_name=$(echo "$url" | cut -d'/' -f3-4)
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$service_name: En ligne"
        else
            print_error "$service_name: Hors ligne"
            all_healthy=false
        fi
    done
    
    # Vérifier Redis
    if redis-cli -p 6380 ping 2>/dev/null | grep -q "PONG"; then
        print_success "Redis (port 6380): En ligne"
    else
        print_error "Redis (port 6380): Hors ligne"
        all_healthy=false
    fi
    
    # Vérifier MQTT
    if mosquitto_pub -h localhost -p 1884 -t "test" -m "test" 2>/dev/null; then
        print_success "MQTT (port 1884): En ligne"
    else
        print_error "MQTT (port 1884): Hors ligne"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        print_success "Tous les services sont en ligne et fonctionnels"
    else
        print_warning "Certains services ne sont pas accessibles"
        return 1
    fi
}

# Point d'entrée principal
main() {
    local command="$1"
    local service="$2"
    
    case "$command" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            status_services
            ;;
        logs)
            show_logs "$service"
            ;;
        build)
            build_services
            ;;
        clean)
            clean_environment
            ;;
        health)
            check_health
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$command" ]; then
                show_help
            else
                print_error "Commande inconnue: $command"
                show_help
                exit 1
            fi
            ;;
    esac
}

# Exécuter le script
main "$@"
