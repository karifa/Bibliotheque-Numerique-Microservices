# Image de base : Python 3.12 légère
FROM python:3.12-slim

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copier et installer les dépendances en premier (optimise le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Port exposé par le service
EXPOSE 8001

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
