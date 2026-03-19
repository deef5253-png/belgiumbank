#!/usr/bin/env python3
"""
Script de démarrage pour Belgium Bank
"""

import os
import sys
import subprocess

def main():
    """Démarrer l'application Belgium Bank"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              🏦 BELGIUM BANK                             ║
    ║                                                          ║
    ║        Votre banque en ligne de confiance                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check if we're in the right directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_dir):
        print("❌ Erreur: Dossier backend non trouvé")
        sys.exit(1)
    
    # Install dependencies if needed
    print("📦 Vérification des dépendances...")
    requirements_file = os.path.join(backend_dir, 'requirements.txt')
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '-r', requirements_file])
        print("✅ Dépendances OK")
    except subprocess.CalledProcessError:
        print("⚠️  Impossible d'installer les dépendances automatiquement")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Import and initialize database
    print("🗄️  Initialisation de la base de données...")
    from database import init_database
    init_database()
    
    print("\n" + "="*60)
    print("🚀 Démarrage du serveur Belgium Bank...")
    print("="*60)
    print("\n📍 URLs d'accès:")
    print("   • Site web:      http://localhost:5000/frontend/index.html")
    print("   • Espace client: http://localhost:5000/frontend/login.html")
    print("   • Espace admin:  http://localhost:5000/frontend/admin-login.html")
    print("\n👤 Identifiants admin:")
    print("   • Email: admin@belgiumbank.be")
    print("   • Mot de passe: AdminSecure2024!")
    print("   • Clé de sécurité: BELGIUM-BANK-ADMIN-2024")
    print("\n⚠️  N'oubliez pas de configurer l'email SMTP dans notifications.py")
    print("="*60 + "\n")
    
    # Start Flask server
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()