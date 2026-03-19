import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configuration SMTP
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'servicclientt@gmail.com'
SMTP_PASSWORD = 'your-app-password'  # To be configured with actual app password

ADMIN_EMAIL = 'servicclientt@gmail.com'

def send_email(to_email, subject, body, html_body=None):
    """
    Send an email notification
    In production, configure with actual SMTP credentials
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f'Belgium Bank <{SMTP_USERNAME}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Plain text version
        msg.attach(MIMEText(body, 'plain'))
        
        # HTML version if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # For demo purposes, we log the email instead of sending
        # In production, uncomment the SMTP code below
        
        # server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # server.starttls()
        # server.login(SMTP_USERNAME, SMTP_PASSWORD)
        # server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        # server.quit()
        
        print(f"[EMAIL SENT] To: {to_email}, Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")
        return False

def notify_admin(message):
    """Send notification to admin email"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = f'[Belgium Bank] Notification Admin - {timestamp}'
    body = f"""
Cher Administrateur,

Une nouvelle notification requiert votre attention:

{message}

Date: {timestamp}

---
Belgium Bank - Système de Notification
"""
    
    # Log for demo
    print(f"[ADMIN NOTIFICATION] {message}")
    # send_email(ADMIN_EMAIL, subject, body)
    return True

def send_transfer_notification(user_email, user_name, transfer_amount, transfer_status, reference, reason=None):
    """Send transfer status notification to user"""
    status_messages = {
        'en_attente': 'est en attente de validation',
        'en_cours': 'est en cours de traitement',
        'valide': 'a été validé et exécuté',
        'refuse': 'a été refusé'
    }
    
    subject = f'Belgium Bank - Votre virement {transfer_status}'
    
    body = f"""
Bonjour {user_name},

Votre virement de {transfer_amount} EUR {status_messages.get(transfer_status, 'a été mis à jour')}.

Référence: {reference}
Statut: {transfer_status.upper()}
"""
    
    if reason and transfer_status == 'refuse':
        body += f"\nMotif du refus: {reason}\n"
    
    body += """
Pour toute question, contactez notre service client:
- Email: servicclientt@gmail.com
- Téléphone: +32460226571

Cordialement,
L'équipe Belgium Bank
"""
    
    return send_email(user_email, subject, body)

def send_welcome_email(user_email, user_name):
    """Send welcome email to new user"""
    subject = 'Bienvenue chez Belgium Bank'
    
    body = f"""
Bonjour {user_name},

Bienvenue chez Belgium Bank ! Nous sommes ravis de vous compter parmi nos clients.

Votre inscription a bien été reçue et est en cours de traitement par notre équipe.
Vous recevrez un email de confirmation dès que votre compte sera validé.

En attendant, vous pouvez:
- Téléverser vos documents d'identité
- Consulter nos conditions générales
- Contacter notre service client pour toute question

Vos informations de contact:
- Email: servicclientt@gmail.com
- Téléphone: +32460226571

Cordialement,
L'équipe Belgium Bank
"""
    
    return send_email(user_email, subject, body)

def send_account_verified_email(user_email, user_name, account_number):
    """Send account verification confirmation"""
    subject = 'Votre compte Belgium Bank est validé'
    
    body = f"""
Bonjour {user_name},

Nous avons le plaisir de vous informer que votre compte Belgium Bank a été validé avec succès.

Votre numéro de compte: {account_number}

Vous pouvez désormais:
- Consulter votre solde en temps réel
- Effectuer des virements
- Consulter l'historique de vos transactions
- Gérer vos paramètres de sécurité

Connectez-vous dès maintenant sur notre plateforme sécurisée.

Pour toute assistance:
- Email: servicclientt@gmail.com
- Téléphone: +32460226571

Cordialement,
L'équipe Belgium Bank
"""
    
    return send_email(user_email, subject, body)