#!/usr/bin/env python3
"""
Script pour remplacer les variables hardcodées par des appels à os.getenv()
avec des valeurs par défaut appropriées.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

def load_env_vars(env_file: str = ".env") -> Dict[str, str]:
    """Charge les variables d'environnement depuis le fichier .env"""
    env_vars = {}
    if not os.path.exists(env_file):
        print(f"⚠️  Fichier {env_file} non trouvé")
        return env_vars
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                parts = line.split('=', 1)
                var_name = parts[0].strip()
                var_value = parts[1].strip() if len(parts) > 1 else ''
                env_vars[var_name] = var_value
    
    return env_vars

def find_hardcoded_lines(file_path: str) -> List[Tuple[int, str, str, str]]:
    """Trouve les lignes avec des variables hardcodées dans un fichier"""
    hardcoded_lines = []
    
    patterns = [
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]+)"', 'string'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\'([^\']+)\'', 'string'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+)', 'number'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', 'ip'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]{1,5})', 'port'),
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Ignorer les lignes avec os.getenv ou os.environ.get
            if 'os.getenv' in line or 'os.environ.get' in line:
                continue
            
            # Ignorer les commentaires
            if line.strip().startswith('#'):
                continue
            
            for pattern, var_type in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    var_name = match[0]
                    var_value = match[1]
                    
                    # Exclure certaines valeurs communes
                    if var_value in ['True', 'False', 'None', 'self', '', '0', '1', '127.0.0.1', 'localhost']:
                        continue
                    
                    # Exclure les noms de variables courts
                    if len(var_name) < 3:
                        continue
                    
                    # Vérifier si c'est une variable d'environnement potentielle
                    if var_name.isupper() or '_' in var_name:
                        hardcoded_lines.append((i, var_name, var_value, line.rstrip()))
    
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture de {file_path}: {e}")
    
    return hardcoded_lines

def determine_default_value(var_name: str, current_value: str, var_type: str) -> str:
    """Détermine la valeur par défaut appropriée pour une variable"""
    # Variables de statut/état
    status_vars = {'CONNECTED', 'CONNECTING', 'DISCONNECTED', 'ERROR', 'RECONNECTING'}
    if var_name in status_vars:
        return f'"{current_value}"'
    
    # Variables de type d'intention
    intent_vars = {'AUTOMATION', 'CONTROL', 'DIAGNOSTIC', 'QUERY', 'ROUTINE', 'SCENE'}
    if var_name in intent_vars:
        return f'"{current_value}"'
    
    # Variables de configuration
    config_vars = {'MQTT_BROKER', 'HA_TOKEN', 'HA_URL', 'REDIS_HOST', 'REDIS_PORT'}
    if var_name in config_vars:
        return f'"{current_value}"'
    
    # Variables numériques
    if var_type in ['number', 'port']:
        return current_value
    
    # Variables de chaîne
    if var_type == 'string':
        return f'"{current_value}"'
    
    # Par défaut, utiliser la valeur actuelle comme chaîne
    return f'"{current_value}"'

def replace_hardcoded_in_file(file_path: str, env_vars: Dict[str, str]) -> int:
    """Remplace les variables hardcodées dans un fichier"""
    hardcoded_lines = find_hardcoded_lines(file_path)
    
    if not hardcoded_lines:
        return 0
    
    print(f"\n📝 Traitement de {file_path}:")
    print(f"   • {len(hardcoded_lines)} variables hardcodées trouvées")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        replacements = 0
        new_content = content
        
        for line_num, var_name, current_value, original_line in hardcoded_lines:
            # Vérifier si la variable est déjà dans .env
            if var_name in env_vars:
                # Remplacer par os.getenv avec valeur par défaut du .env
                default_value = env_vars[var_name]
                if default_value.isdigit():
                    replacement = f'{var_name} = os.getenv("{var_name}", {default_value})'
                else:
                    replacement = f'{var_name} = os.getenv("{var_name}", "{default_value}")'
            else:
                # Utiliser la valeur hardcodée comme valeur par défaut
                default_value = determine_default_value(var_name, current_value, 'string')
                replacement = f'{var_name} = os.getenv("{var_name}", {default_value})'
            
            # Remplacer la ligne
            pattern = re.escape(original_line)
            new_content = re.sub(pattern, replacement, new_content, count=1)
            replacements += 1
            
            print(f"   • Ligne {line_num}: {var_name} = {current_value} → {replacement}")
        
        # Ajouter l'import os si nécessaire
        if replacements > 0 and 'import os' not in new_content:
            # Trouver la première ligne d'import
            lines = new_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'import os')
                    break
            else:
                # Ajouter au début du fichier
                lines.insert(0, 'import os')
new_content = os.getenv("new_content", "
")
        
        # Écrire le fichier modifié
        if replacements > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"   ✅ {replacements} remplacements effectués")
        
        return replacements
    
    except Exception as e:
        print(f"   ❌ Erreur lors du traitement: {e}")
        return 0

def process_directory(root_dir: str = ".", env_vars: Dict[str, str] = None) -> Dict[str, int]:
    """Traite tous les fichiers Python dans un répertoire"""
    if env_vars is None:
        env_vars = load_env_vars()
        if env_vars is None:
            env_vars = {}
    
    results = {}
    excluded_dirs = {'__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules'}
    
    for py_file in Path(root_dir).rglob('*.py'):
        # Exclure les répertoires spécifiques
        if any(excluded in str(py_file) for excluded in excluded_dirs):
            continue
        
        replacements = replace_hardcoded_in_file(str(py_file), env_vars)
        if replacements > 0:
            results[str(py_file)] = replacements
    
    return results

def main():
    """Fonction principale"""
    print("🔄 Remplacement des variables hardcodées...")
    
    # Charger les variables d'environnement
    env_vars = load_env_vars()
    
    if not env_vars:
        print("❌ Aucune variable d'environnement trouvée dans .env")
        print("   Veuillez d'abord configurer le fichier .env")
        return
    
    print(f"✅ {len(env_vars)} variables chargées depuis .env")
    
    # Traiter tous les fichiers Python
    results = process_directory(".", env_vars)
    
    # Générer un rapport
    print("\n" + "="*80)
    print("📊 RAPPORT DE REMPLACEMENT")
    print("="*80)
    
    total_replacements = sum(results.values())
    
    if total_replacements == 0:
        print("✅ Aucune variable hardcodée à remplacer!")
    else:
        print(f"\n📈 Statistiques:")
        print(f"   • Fichiers modifiés: {len(results)}")
        print(f"   • Remplacements totaux: {total_replacements}")
        
        print(f"\n📋 Fichiers modifiés:")
        for file_path, count in sorted(results.items()):
            print(f"   • {file_path}: {count} remplacements")
        
        print(f"\n✅ Toutes les variables hardcodées ont été remplacées!")
        print(f"   Les valeurs par défaut proviennent du fichier .env")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
