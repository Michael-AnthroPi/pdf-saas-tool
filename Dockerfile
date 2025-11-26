FROM python:3.9-slim

# Installation des outils système (Poppler pour images, Ghostscript pour compression)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Création des dossiers temporaires
RUN mkdir -p /tmp/uploads /tmp/outputs

# COMMANDE DE DÉMARRAGE ÉCONOMIQUE (1 seul worker pour économiser la RAM)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
