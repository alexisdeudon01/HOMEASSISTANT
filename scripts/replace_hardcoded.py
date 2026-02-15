#!/usr/bin/env python3
"""
Script pour remplacer automatiquement les valeurs hardcodées par des variables d'environnement.
"""

import os
import re
import sys
from pathlib import Path

# Mapping des valeurs hardcodées vers les variables d'environnement
REPLACEMENT_MAP = {
    # IPs
    os.getenv('HUE_BRIDGE_IP', '192.168.178.69'): "HUE_BRIDGE_IP",
    os.getenv('REDIS_HOST', '127.0.0.1'): "REDIS_HOST",
    os.getenv('SERVICE_HOST', '0.0.0.0'): "SERVICE_HOST",
    
    # Ports
    os.getenv('REDIS_PORT', 'int(os.getenv('REDIS_PORT', '6379'))'): "REDIS_PORT",
    os.getenv('MQTT_PORT', 'int(os.getenv('MQTT_PORT', '1883'))'): "MQTT_PORT",
    os.getenv('HA_PORT', '8123'): "HA_PORT",
    os.getenv('GATEWAY_PORT', 'int(os.getenv('GATEWAY_PORT', '8080'))'): "GATEWAY_PORT",
    os.getenv('MANAGER_PORT', 'int(os.getenv('MANAGER_PORT', '8082'))'): "MANAGER_PORT",
    
    # URLs
    os.getenv('HA_URL', 'http://127.0.0.1:int(os.getenv('HA_PORT', '8123'))'): "HA_URL",
    os.getenv('ENTHROPIC_BASE_URL', 'http://localhost:8000'): "ENTHROPIC_BASE_URL",
    
    # Clés API
    os.getenv('HUE_API_KEY', 'tNZIBriUkfuBz7jvE1v9CtzrtmsdumDOgsVQI554'): "HUE_API_KEY",
    os.getenv('HA_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2ZGI5YWI4NmRiNmY0N2VhYjlhOTY2ZDEwMzBhNjRiNSIsImlhdCI6MTc3MTExNTcyMCwiZXhwIjoyMDg2NDc1NzIwfQ.pr3Yn6kBqTiamGH03I10R9EzK7x-uk4rpP1JXanRsVE'): "HA_TOKEN",
    
    # Modèles
    os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'): "CLAUDE_MODEL",
    
    # Métriques
    os.getenv('METRICS_TOTAL_CONNECTIONS_RECEIVED', 'total_connections_received'): "METRICS_TOTAL_CONNECTIONS_RECEIVED",
    os.getenv('METRICS_TOTAL_COMMANDS_PROCESSED', 'total_commands_processed'): "METRICS_TOTAL_COMMANDS_PROCESSED",
    os.getenv('TOPIC_MULTI_LEVEL_MATCHING', 'multi_level_matching'): "TOPIC_MULTI_LEVEL_MATCHING",
}

def replace_in_file(file_path):
    """Remplace les valeurs hardcodées dans un fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Remplacer les valeurs entre guillemets simples ou doubles
    for hardcoded, env_var in REPLACEMENT_MAP.items():
        # Pattern pour trouver la valeur entre guillemets
        pattern_single = f"'{hardcoded}'"
        pattern_double = f'"{hardcoded}"'
        
        # Remplacer avec os.getenv()
        replacement = f"os.getenv('{env_var}', '{hardcoded}')"
        
        # Compter les remplacements
        count_single = content.count(pattern_single)
        count_double = content.count(pattern_double)
        
        if count_single > 0:
            content = content.replace(pattern_single, replacement)
            changes_made.append(f"  - '{hardcoded}' → os.getenv('{env_var}') ({count_single} fois)")
        
        if count_double > 0:
            content = content.replace(pattern_double, replacement)
            changes_made.append(f'  - "{hardcoded}" → os.getenv("{env_var}") ({count_double} fois)')
    
    # Remplacer les valeurs sans guillemets (pour les nombres)
    for hardcoded, env_var in REPLACEMENT_MAP.items():
        if hardcoded.isdigit():
            # Pattern pour trouver le nombre seul (entouré de caractères non-alphanumériques)
            pattern = r'\b' + re.escape(hardcoded) + r'\b'
            matches = list(re.finditer(pattern, content))
            
            for match in reversed(matches):
                # Vérifier que ce n'est pas déjà dans un os.getenv()
                start, end = match.span()
                if not (content[start-20:start].find('os.getenv') != -1 or 
                        content[start-20:start].find('getenv') != -1):
                    # Remplacer
                    content = content[:start] + f"int(os.getenv('{env_var}', '{hardcoded}'))" + content[end:]
                    changes_made.append(f"  - {hardcoded} → int(os.getenv('{env_var}'))")
    
    # Ajouter l'import os si nécessaire
    if 'import os' not in content and changes_made:
        lines = content.split('\n')
        import_found = False
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                # Insérer après les imports
                lines.insert(i + 1, 'import os')
                import_found = True
                break
        
        if not import_found:
            # Ajouter au début du fichier
            lines.insert(0, 'import os')
        
        content = '\n'.join(lines)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return []

def process_directory(directory):
    """Traite récursivement un répertoire."""
    py_files = list(Path(directory).rglob('*.py'))
    total_changes = 0
    total_files = 0
    
    print(f"Traitement du répertoire: {directory}")
    print(f"Fichiers Python trouvés: {len(py_files)}")
    print("-" * 80)
    
    for py_file in py_files:
        # Ignorer les fichiers dans venv/ et autres répertoires à ignorer
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
            
        changes = replace_in_file(py_file)
        if changes:
            total_files += 1
            total_changes += len(changes)
            print(f"\nFichier: {py_file}")
            for change in changes:
                print(change)
    
    print(f"\n{'='*80}")
    print(f"RÉSUMÉ:")
    print(f"  Fichiers modifiés: {total_files}")
    print(f"  Changements effectués: {total_changes}")
    print(f"{'='*80}")
    
    return total_files, total_changes

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Traiter le répertoire racine
    files_changed, changes_made = process_directory(project_root)
    
    # Sauvegarder un rapport
    report_path = os.path.join(current_dir, 'replacement_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Rapport de remplacement des valeurs hardcodées\n")
        f.write(f"Date: {os.popen('date').read().strip()}\n")
        f.write(f"Fichiers modifiés: {files_changed}\n")
        f.write(f"Changements effectués: {changes_made}\n")
    
    print(f"\nRapport sauvegardé dans: {report_path}")
