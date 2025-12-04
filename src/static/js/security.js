/**
 * Utilitaires de sécurité pour le frontend
 */

/**
 * Échappe les caractères HTML pour prévenir XSS
 * @param {string} text - Texte à échapper
 * @returns {string} Texte échappé
 */
function escapeHtml(text) {
    if (!text) return '';

    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * Crée un élément HTML de manière sécurisée avec contenu échappé
 * @param {string} tag - Nom de la balise
 * @param {string} content - Contenu textuel (sera échappé)
 * @param {Object} attributes - Attributs de l'élément
 * @returns {HTMLElement} Élément créé
 */
function createSafeElement(tag, content, attributes = {}) {
    const element = document.createElement(tag);

    // Ajouter le contenu textuel (automatiquement échappé)
    if (content) {
        element.textContent = content;
    }

    // Ajouter les attributs
    for (const [key, value] of Object.entries(attributes)) {
        if (key === 'style' && typeof value === 'object') {
            // Gérer les styles comme objet
            for (const [styleProp, styleValue] of Object.entries(value)) {
                element.style[styleProp] = styleValue;
            }
        } else {
            element.setAttribute(key, value);
        }
    }

    return element;
}

/**
 * Nettoie un nom de fichier pour éviter path traversal
 * @param {string} filename - Nom de fichier
 * @returns {string} Nom de fichier nettoyé
 */
function sanitizeFilename(filename) {
    if (!filename) return '';

    // Supprimer les caractères dangereux
    let clean = filename.replace(/[^a-zA-Z0-9_\-\.]/g, '_');

    // Supprimer les chemins
    clean = clean.replace(/\.\./g, '').replace(/[\/\\]/g, '');

    // Limiter la longueur
    if (clean.length > 255) {
        const parts = clean.split('.');
        const ext = parts.length > 1 ? parts.pop() : '';
        const name = parts.join('.');
        clean = name.substring(0, 250) + (ext ? '.' + ext : '');
    }

    return clean;
}

/**
 * Valide une URL de redirection (autoriser seulement chemins relatifs)
 * @param {string} url - URL à valider
 * @returns {boolean} True si sûre
 */
function isSafeRedirectUrl(url) {
    if (!url) return false;

    // Autoriser seulement les chemins relatifs commençant par /
    if (url.startsWith('/') && !url.startsWith('//')) {
        return true;
    }

    // Bloquer tous les protocoles externes
    const dangerousProtocols = ['http:', 'https:', 'javascript:', 'data:', 'file:', 'ftp:'];
    return !dangerousProtocols.some(proto => url.toLowerCase().startsWith(proto));
}

/**
 * Extrait le texte brut d'un contenu HTML (strip tags)
 * @param {string} html - Contenu HTML
 * @returns {string} Texte brut
 */
function stripHtmlTags(html) {
    if (!html) return '';

    const div = document.createElement('div');
    div.innerHTML = html;
    return (div.textContent || div.innerText || '').trim();
}

/**
 * Tronque un texte à une longueur maximale
 * @param {string} text - Texte à tronquer
 * @param {number} maxLength - Longueur maximale
 * @param {string} suffix - Suffixe (défaut: '...')
 * @returns {string} Texte tronqué
 */
function truncateText(text, maxLength = 100, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Valide un email (format basique)
 * @param {string} email - Email à valider
 * @returns {boolean} True si valide
 */
function isValidEmail(email) {
    if (!email) return false;
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email.trim());
}

/**
 * Affiche du HTML sécurisé (pour contenu riche comme procédures)
 * Utiliser SEULEMENT pour contenu de confiance stocké en BD
 * @param {string} html - HTML à afficher
 * @returns {string} HTML (non échappé - ATTENTION)
 */
function renderTrustedHtml(html) {
    // ATTENTION: N'utiliser que pour contenu créé par l'application
    // (procédures Quill, etc.), jamais pour input utilisateur direct
    return html || '';
}
