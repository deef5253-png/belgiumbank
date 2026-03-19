# Belgium Bank - Application Bancaire en Ligne

Une application bancaire complète avec espace utilisateur et espace administrateur.

## Structure du projet

```
belgiumbank/
├── backend/           # API Flask
│   ├── app.py        # Serveur principal
│   ├── database.py   # Gestion de la base de données
│   ├── notifications.py # Service de notifications
│   └── requirements.txt # Dépendances Python
├── frontend/         # Interface utilisateur
│   ├── index.html    # Page d'accueil
│   ├── login.html    # Connexion utilisateur
│   ├── register.html # Inscription
│   ├── dashboard.html # Espace client
│   ├── admin-login.html # Connexion admin
│   └── admin-dashboard.html # Espace admin
├── database/         # Base de données SQLite
├── uploads/          # Documents téléversés
└── README.md
```

## Fonctionnalités

### Espace Utilisateur
- Inscription complète avec informations personnelles
- Téléversement de documents (pièce d'identité, justificatif de domicile)
- Connexion sécurisée avec JWT
- Tableau de bord avec solde en temps réel
- Effectuer des virements (avec saisie RIB)
- Historique des transactions
- Notifications par email

### Espace Administrateur
- Accès hautement sécurisé (clé de sécurité additionnelle)
- Consultation de tous les utilisateurs
- Visualisation des documents téléversés
- Validation des comptes utilisateurs
- Gestion et validation des virements
- Créditer les comptes utilisateurs
- Données sensibles masquées par défaut

### Statuts de virement
- En attente
- En cours de traitement
- Validé
- Refusé

## Installation

### Prérequis
- Python 3.8+
- pip

### Installation des dépendances

```bash
cd backend
pip install -r requirements.txt
```

### Démarrage

```bash
# Initialiser la base de données et démarrer le serveur
cd backend
python app.py
```

Le serveur démarre sur `http://localhost:5000`

## Accès

### Espace Utilisateur
- Page d'accueil: `http://localhost:5000/frontend/index.html`
- Inscription: `http://localhost:5000/frontend/register.html`
- Connexion: `http://localhost:5000/frontend/login.html`

### Espace Administrateur
- Connexion: `http://localhost:5000/frontend/admin-login.html`

**Identifiants admin par défaut:**
- Email: `admin@belgiumbank.be`
- Mot de passe: `AdminSecure2024!`
- Clé de sécurité: `BELGIUM-BANK-ADMIN-2024`

## Configuration Email

Pour activer l'envoi d'emails, modifiez le fichier `backend/notifications.py`:

```python
SMTP_USERNAME = 'servicclientt@gmail.com'
SMTP_PASSWORD = 'votre-mot-de-passe-app'
```

Pour Gmail, utilisez un "mot de passe d'application".

## Sécurité

- Authentification JWT pour toutes les routes protégées
- Mots de passe hashés avec bcrypt
- Données sensibles masquées dans l'interface admin
- Validation des documents obligatoire
- Clé de sécurité additionnelle pour l'admin

## Contact

- Email: servicclientt@gmail.com
- Téléphone: +32 460 22 65 71

## Licence

© 2024 Belgium Bank - Tous droits réservés