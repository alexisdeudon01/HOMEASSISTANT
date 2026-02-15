#!/usr/bin/env python3
"""
Script pour trouver et remplacer les valeurs hardcodées dans les fichiers Python.
"""

import os
import re
import sys
from pathlib import Path

# Patterns pour détecter les valeurs hardcodées
HARDCODED_PATTERNS = [
    # Adresses IP
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_ADDRESS'),
    # Ports communs
    (r'\b(int(os.getenv('REDIS_PORT', '6379'))|int(os.getenv('MQTT_PORT', '1883'))|int(os.getenv('HA_PORT', '8123'))|int(os.getenv('GATEWAY_PORT', '8080'))|int(os.getenv('MANAGER_PORT', '8082'))|9001)\b', 'PORT'),
    # URLs avec http/https
    (r'["\']https?://[^"\']+["\']', 'URL'),
    # Clés API (longues chaînes alphanumériques)
    (r'["\'][A-Za-z0-9_-]{20,}["\']', 'API_KEY'),
    # Tokens JWT
    (r'["\']eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+["\']', 'JWT_TOKEN'),
]

# Variables déjà définies dans .env
ENV_VARIABLES = {
    os.getenv('HUE_BRIDGE_IP', '192.168.178.69'): 'HUE_BRIDGE_IP',
    os.getenv('REDIS_HOST', '127.0.0.1'): 'REDIS_HOST',
    os.getenv('REDIS_PORT', 'int(os.getenv('REDIS_PORT', '6379'))'): 'REDIS_PORT',
    os.getenv('MQTT_PORT', 'int(os.getenv('MQTT_PORT', '1883'))'): 'MQTT_PORT',
    os.getenv('HA_PORT', '8123'): 'HA_PORT',
    os.getenv('GATEWAY_PORT', 'int(os.getenv('GATEWAY_PORT', '8080'))'): 'GATEWAY_PORT',
    os.getenv('MANAGER_PORT', 'int(os.getenv('MANAGER_PORT', '8082'))'): 'MANAGER_PORT',
    os.getenv('HUE_API_KEY', 'tNZIBriUkfuBz7jvE1v9CtzrtmsdumDOgsVQI554'): 'HUE_API_KEY',
    os.getenv('HA_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2ZGI5YWI4NmRiNmY0N2VhYjlhOTY2ZDEwMzBhNjRiNSIsImlhdCI6MTc3MTExNTcyMCwiZXhwIjoyMDg2NDc1NzIwfQ.pr3Yn6kBqTiamGH03I10R9EzK7x-uk4rpP1JXanRsVE'): 'HA_TOKEN',
    os.getenv('HA_URL', 'http://127.0.0.1:int(os.getenv('HA_PORT', '8123'))'): 'HA_URL',
    os.getenv('ENTHROPIC_BASE_URL', 'http://localhost:8000'): 'ENTHROPIC_BASE_URL',
}

def find_hardcoded_values(file_path):
    """Trouve les valeurs hardcodées dans un fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    findings = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        for pattern, pattern_type in HARDCODED_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                value = match.group(0).strip('"\'')
                if value in ENV_VARIABLES:
                    findings.append({
                        'line': i,
                        'value': value,
                        'env_var': ENV_VARIABLES[value],
                        'pattern_type': pattern_type,
                        'full_line': line.strip()
                    })
                elif pattern_type in ['IP_ADDRESS', 'API_KEY', 'JWT_TOKEN']:
                    # Chercher si cette valeur ressemble à quelque chose qui devrait être dans .env
                    findings.append({
                        'line': i,
                        'value': value,
                        'env_var': None,  # À demander à l'utilisateur
                        'pattern_type': pattern_type,
                        'full_line': line.strip()
                    })
    
    return findings

def scan_directory(directory):
    """Scanne récursivement un répertoire pour trouver des valeurs hardcodées."""
    all_findings = []
    py_files = list(Path(directory).rglob('*.py'))
    
    for py_file in py_files:
        # Ignorer les fichiers dans venv/ et autres répertoires à ignorer
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
            
        findings = find_hardcoded_values(py_file)
        if findings:
            all_findings.append({
                'file': str(py_file),
                'findings': findings
            })
    
    return all_findings

def generate_report(findings):
    """Génère un rapport des valeurs hardcodées trouvées."""
    report = []
    report.append("=" * 80)
    report.append("RAPPORT DES VALEURS HARDCODÉES")
    report.append("=" * 80)
    
    total_files = len(findings)
    total_values = sum(len(f['findings']) for f in findings)
    
    report.append(f"\nFichiers analysés: {total_files}")
    report.append(f"Valeurs hardcodées trouvées: {total_values}\n")
    
    for file_data in findings:
        report.append(f"\n{'='*60}")
        report.append(f"Fichier: {file_data['file']}")
        report.append(f"{'='*60}")
        
        for finding in file_data['findings']:
            if finding['env_var']:
                report.append(f"  Ligne {finding['line']}: {finding['value']}")
                report.append(f"    → Remplacer par: os.getenv('{finding['env_var']}')")
            else:
                report.append(f"  Ligne {finding['line']}: {finding['value']} ({finding['pattern_type']})")
                report.append(f"    → À ajouter au fichier .env")
            report.append(f"    Code: {finding['full_line'][:80]}...")
            report.append("")
    
    return '\n'.join(report)

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    print(f"Analyse du répertoire: {project_root}")
    findings = scan_directory(project_root)
    
    report = generate_report(findings)
    print(report)
    
    # Sauvegarder le rapport
    report_path = os.path.join(current_dir, 'hardcoded_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nRapport sauvegardé dans: {report_path}")
