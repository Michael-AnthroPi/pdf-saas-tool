# On part d'une version légère de Python sur Linux
FROM python:3.9-slim

# On installe les outils système nécessaires (Poppler pour les PDF)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# On définit le dossier de travail
WORKDIR /app

# On copie les fichiers de dépendances et on installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le reste du code
COPY . .

# On crée les dossiers pour les fichiers temporaires
RUN mkdir -p /tmp/uploads /tmp/outputs

# On lance le serveur Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
