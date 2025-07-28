# Dockerfile

FROM python:3.11-slim

# Installer les dépendances système utiles
RUN apt-get update && apt-get install -y gcc

# Définir le dossier de travail
WORKDIR /app

# Copier les fichiers dans le conteneur
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Commande par défaut : à override dans docker-compose
CMD ["python", "migration.py"]