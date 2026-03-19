# Guide de Déploiement - Belgium Bank

## Prérequis

- Python 3.11+
- Serveur Linux (Ubuntu/Debian recommandé)
- Nginx (recommandé)
- SSL Certificate (Let's Encrypt)

## Méthode 1 : Déploiement avec Docker (Recommandée)

### 1. Installation de Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Déploiement de l'application

```bash
# Copier le projet sur votre serveur
scp -r belgiumbank user@serveur:/chemin/destination/

# Se connecter au serveur
ssh user@serveur

# Aller dans le dossier
cd /chemin/destination/belgiumbank

# Lancer l'application
docker-compose up -d

# Vérifier les logs
docker-compose logs -f
```

### 3. Configuration Nginx (Reverse Proxy)

```bash
sudo nano /etc/nginx/sites-available/belgiumbank
```

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        alias /chemin/destination/belgiumbank/backend/uploads/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/belgiumbank /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

## Méthode 2 : Déploiement Manuel (VPS)

### 1. Préparation du serveur

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et dépendances
sudo apt install python3-pip python3-venv nginx -y

# Créer l'utilisateur de l'application
sudo useradd -m -s /bin/bash belgiumbank
```

### 2. Configuration de l'application

```bash
# Se connecter en tant que belgiumbank
sudo su - belgiumbank

# Copier le projet
git clone https://github.com/votre-repo/belgiumbank.git
cd belgiumbank

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
cd backend
pip install -r requirements.txt
pip install gunicorn

# Créer le dossier uploads
mkdir -p uploads/documents

# Initialiser la base de données
python3 database.py
```

### 3. Créer le service systemd

```bash
sudo nano /etc/systemd/system/belgiumbank.service
```

```ini
[Unit]
Description=Belgium Bank Application
After=network.target

[Service]
User=belgiumbank
Group=belgiumbank
WorkingDirectory=/home/belgiumbank/belgiumbank/backend
Environment="PATH=/home/belgiumbank/belgiumbank/venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=votre_cle_secrete_ici"
Environment="JWT_SECRET_KEY=votre_jwt_cle_secrete_ici"
ExecStart=/home/belgiumbank/belgiumbank/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start belgiumbank
sudo systemctl enable belgiumbank
```

### 4. Configuration Nginx

Même configuration que pour Docker (voir ci-dessus).

## Méthode 3 : Hébergement Cloud Gratuit

### Railway.app

1. Créez un compte sur railway.app
2. Connectez votre repository GitHub
3. Railway détectera automatiquement le Dockerfile
4. Déployez en un clic

### Render.com

1. Créez un compte sur render.com
2. Créez un "Blueprint" avec le fichier `render.yaml`
3. Déployez automatiquement

### PythonAnywhere

1. Créez un compte sur pythonanywhere.com
2. Téléchargez les fichiers via FTP
3. Configurez une application web Flask
4. Pointez vers le fichier WSGI

## Configuration pour la Production

### Variables d'environnement à modifier

Créez un fichier `.env` dans le dossier `backend/` :

```
FLASK_ENV=production
SECRET_KEY=une_cle_tres_longue_et_aleatoire_min_50_caracteres
JWT_SECRET_KEY=une_autre_cle_jwt_tres_longue
ADMIN_EMAIL=admin@belgiumbank.be
ADMIN_PASSWORD=VotreMotDePasseAdminTresFort!
ADMIN_SECURITY_KEY=VOTRE-CLE-ADMIN-UNIQUE-2024
```

### Sécurité

1. **Changez les mots de passe par défaut**
2. **Générez des clés secrètes uniques** :
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
3. **Activez le pare-feu** :
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

## URLs après déploiement

- **Site web** : https://votre-domaine.com
- **API** : https://votre-domaine.com/api
- **Panel Admin** : https://votre-domaine.com/admin-login.html

## Maintenance

### Backup de la base de données

```bash
# Créer un backup
cp backend/belgium_bank.db backups/belgium_bank_$(date +%Y%m%d_%H%M%S).db

# Automatiser avec crontab
crontab -e
# Ajoutez :
0 2 * * * cp /chemin/belgiumbank/backend/belgium_bank.db /chemin/backups/belgium_bank_$(date +\%Y\%m\%d).db
```

### Mise à jour de l'application

```bash
# Avec Docker
docker-compose down
docker-compose pull
docker-compose up -d

# Manuellement
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart belgiumbank
```

## Support

En cas de problème :
- Email : servicclientt@gmail.com
- Téléphone : +32 460 22 65 71
