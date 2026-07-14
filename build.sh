#!/usr/bin/env bash
set -o errexit

echo "Début du build sur Render"
echo "Dossier courant: $(pwd)"

# Installation des dépendances
echo "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Aller dans le dossier backend
echo "Déplacement dans le dossier backend..."
cd backend

# Créer les dossiers nécessaires
echo "Création des dossiers media et staticfiles..."
mkdir -p media
mkdir -p staticfiles

# Collecte des fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

# Exécuter les migrations
echo "Exécution des migrations..."
python manage.py migrate

echo "Build terminé avec succès !"