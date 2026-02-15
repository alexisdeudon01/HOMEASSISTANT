FROM python:3.11-slim
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script d'export des variables d'environnement
COPY ../../scripts/export-env.sh /scripts/export-env.sh
RUN chmod +x /scripts/export-env.sh

# Copier le code de l'application
COPY . .

# Exécuter le script d'export avant de lancer l'application
CMD ["/bin/bash", "-c", "source /scripts/export-env.sh && python -u brain.py"]
