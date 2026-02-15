#!/usr/bin/env python3
"""
Script pour identifier les variables hardcodées dans les fichiers Python
et les comparer avec les variables définies dans le fichier .env
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
    
    print(f"✅ {len(env_vars)} variables chargées depuis {env_file}")
    return env_vars

def find_hardcoded_values(root_dir: str = ".") -> List[Dict]:
    """Recherche les valeurs hardcodées dans les fichiers Python"""
    hardcoded_findings = []
    excluded_dirs = {'__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules'}
    
    patterns = [
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]+)"', 'string'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\'([^\']+)\'', 'string'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+)', 'number'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', 'ip'),
        (r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]{1,5})', 'port'),
    ]
    
    for py_file in Path(root_dir).rglob('*.py'):
        # Exclure les répertoires spécifiques
        if any(excluded in str(py_file) for excluded in excluded_dirs):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
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
                            hardcoded_findings.append({
                                'file': str(py_file),
                                'line': i,
                                'variable': var_name,
                                'value': var_value,
                                'type': var_type,
                                'full_line': line.strip()
                            })
        
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture de {py_file}: {e}")
    
    return hardcoded_findings

def analyze_findings(hardcoded_findings: List[Dict], env_vars: Dict[str, str]) -> Tuple[Dict, Set[str], Set[str]]:
    """Analyse les résultats et génère des recommandations"""
    variables_summary = {}
    
    for finding in hardcoded_findings:
        var_name = finding['variable']
        if var_name not in variables_summary:
            variables_summary[var_name] = []
        variables_summary[var_name].append(finding)
    
    # Variables manquantes dans .env
    missing_in_env = set(variables_summary.keys()) - set(env_vars.keys())
    
    # Variables déjà dans .env mais hardcodées
    hardcoded_but_in_env = set(variables_summary.keys()) & set(env_vars.keys())
    
    return variables_summary, missing_in_env, hardcoded_but_in_env

def generate_report(variables_summary: Dict, missing_in_env: Set[str], 
                    hardcoded_but_in_env: Set[str], env_vars: Dict[str, str]):
    """Génère un rapport détaillé"""
    print("\n" + "="*80)
    print("📊 RAPPORT D'ANALYSE DES VARIABLES HARCODÉES")
    print("="*80)
    
    print(f"\n📈 Statistiques:")
    print(f"   • Variables hardcodées trouvées: {len(variables_summary)}")
    print(f"   • Variables manquantes dans .env: {len(missing_in_env)}")
    print(f"   • Variables déjà dans .env mais hardcodées: {len(hardcoded_but_in_env)}")
    
    if missing_in_env:
        print(f"\n🔴 VARIABLES À AJOUTER AU .env:")
        for var_name in sorted(missing_in_env):
            findings = variables_summary[var_name]
            print(f"\n   {var_name}:")
            for finding in findings[:2]:  # Limiter à 2 occurrences
                print(f"     • {finding['file']}:{finding['line']}")
                print(f"       Valeur: {finding['value']} ({finding['type']})")
                print(f"       Ligne: {finding['full_line'][:60]}...")
    
    if hardcoded_but_in_env:
        print(f"\n🟡 VARIABLES DÉJÀ DANS .env MAIS HARCODÉES:")
        for var_name in sorted(hardcoded_but_in_env):
            findings = variables_summary[var_name]
            env_value = env_vars[var_name]
            print(f"\n   {var_name}:")
            print(f"     • Valeur dans .env: {env_value}")
            for finding in findings[:2]:
                print(f"     • {finding['file']}:{finding['line']}")
                print(f"       Valeur hardcodée: {finding['value']}")
    
    print(f"\n📋 RECOMMANDATIONS:")
    print(f"   1. Ajouter les variables manquantes au fichier .env")
    print(f"   2. Remplacer les valeurs hardcodées par os.getenv()")
    print(f"   3. Utiliser des valeurs par défaut appropriées")
    print(f"   4. Tester après chaque modification")
    
    print("\n" + "="*80)

def main():
    """Fonction principale"""
    print("🔍 Analyse des variables hardcodées...")
    
    # Charger les variables d'environnement
    env_vars = load_env_vars()
    
    # Rechercher les valeurs hardcodées
    hardcoded_findings = find_hardcoded_values()
    
    if not hardcoded_findings:
        print("✅ Aucune variable hardcodée trouvée!")
        return
    
    # Analyser les résultats
    variables_summary, missing_in_env, hardcoded_but_in_env = analyze_findings(
        hardcoded_findings, env_vars
    )
    
    # Générer le rapport
    generate_report(variables_summary, missing_in_env, hardcoded_but_in_env, env_vars)
    
    # Sauvegarder les résultats dans un fichier
    with open("hardcoded_analysis.txt", "w") as f:
        f.write("Variables à ajouter au .env:\n")
        for var_name in sorted(missing_in_env):
            f.write(f"- {var_name}\n")
        
        f.write("\nVariables déjà dans .env mais hardcodées:\n")
        for var_name in sorted(hardcoded_but_in_env):
            f.write(f"- {var_name}\n")
    
    print("📄 Résultats sauvegardés dans hardcoded_analysis.txt")

if __name__ == "__main__":
    main()
