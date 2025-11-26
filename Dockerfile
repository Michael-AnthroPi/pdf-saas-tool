FROM python:3.9-slim

# On installe UNIQUEMENT les outils légers
# poppler-utils = pour les images
# ghostscript = pour la compression
RUN apt-get update && apt-get install -y \
    poppler-utils \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/uploads /tmp/outputs

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
