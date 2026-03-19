#!/bin/bash

echo "=========================================="
echo "  Belgium Bank - Démarrage du serveur"
echo "=========================================="
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null
then
    echo "Python 3 n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Aller dans le dossier backend
cd "$(dirname "$0")/backend"

# Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
echo "Installation des dépendances..."
pip install -q -r requirements.txt

# Initialiser la base de données
echo "Initialisation de la base de données..."
python database.py

echo ""
echo "=========================================="
echo "  Démarrage du serveur..."
echo "=========================================="
echo ""
echo "Le serveur démarre sur http://localhost:5000"
echo ""
echo "Identifiants Admin:"
echo "  Email: admin@belgiumbank.be"
echo "  Mot de passe: AdminSecure2024!"
echo "  Clé de sécurité: BELGIUM-BANK-ADMIN-2024"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

# Lancer le serveur
python app.py