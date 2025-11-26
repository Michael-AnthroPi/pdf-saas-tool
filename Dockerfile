# On part d'une version légère de Python
FROM python:3.9-slim

# --- INSTALLATION DES OUTILS SYSTÈME ---
# On ajoute :
# 1. ghostscript (pour compresser)
# 2. libreoffice-writer et java (pour convertir Word <-> PDF)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    ghostscript \
    libreoffice-writer \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dossiers temporaires
RUN mkdir -p /tmp/uploads /tmp/outputs

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
