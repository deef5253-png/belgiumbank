/**
 * Configuration de l'API
 * Modifier l'URL selon votre environnement
 */

const CONFIG = {
    // En développement (local)
    // API_URL: 'http://localhost:5000/api',
    
    // En production - remplacez par votre domaine
    API_URL: '/api',
    
    // Version de l'application
    VERSION: '1.0.0',
    
    // Nom de la banque
    BANK_NAME: 'Belgium Bank',
    
    // Contact
    CONTACT_EMAIL: 'servicclientt@gmail.com',
    CONTACT_PHONE: '+32 460 22 65 71'
};

// Exporter pour utilisation dans les autres fichiers
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
