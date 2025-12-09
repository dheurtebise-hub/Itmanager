/**
 * Client API pour KB_IT_Support
 * Gère toutes les requêtes vers le backend Flask
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
    }

    /**
     * Effectue une requête HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, finalOptions);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || response.statusText);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ============================================
    // Procédures
    // ============================================

    /**
     * Récupère toutes les procédures
     */
    async getProcedures(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        return this.request(`/api/procedures?${queryParams}`);
    }

    /**
     * Récupère une procédure par son ID
     */
    async getProcedure(id) {
        return this.request(`/api/procedures/${id}`);
    }

    /**
     * Crée une nouvelle procédure
     */
    async createProcedure(data) {
        return this.request('/api/procedures', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Met à jour une procédure
     */
    async updateProcedure(id, data) {
        return this.request(`/api/procedures/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Archive une procédure
     */
    async deleteProcedure(id) {
        return this.request(`/api/procedures/${id}`, {
            method: 'DELETE'
        });
    }

    /**
     * Ajoute un tag à une procédure
     */
    async addTagToProcedure(procedureId, tag, isAiGenerated = false) {
        return this.request(`/api/procedures/${procedureId}/tags`, {
            method: 'POST',
            body: JSON.stringify({ tag, is_ai_generated: isAiGenerated })
        });
    }

    /**
     * Retire un tag d'une procédure
     */
    async removeTagFromProcedure(procedureId, tagId) {
        return this.request(`/api/procedures/${procedureId}/tags/${tagId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Upload un fichier joint
     */
    async uploadAttachment(procedureId, file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${this.baseURL}/api/procedures/${procedureId}/attachments`;

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || response.statusText);
        }

        return await response.json();
    }

    /**
     * Récupère les versions d'une procédure
     */
    async getProcedureVersions(procedureId) {
        return this.request(`/api/procedures/${procedureId}/versions`);
    }

    /**
     * Restaure une version spécifique
     */
    async restoreProcedureVersion(procedureId, versionNumber) {
        return this.request(`/api/procedures/${procedureId}/versions/${versionNumber}`, {
            method: 'POST'
        });
    }

    // ============================================
    // Catégories
    // ============================================

    /**
     * Récupère toutes les catégories
     */
    async getCategories(tree = false) {
        const params = tree ? '?tree=true' : '';
        return this.request(`/api/categories${params}`);
    }

    /**
     * Récupère une catégorie par son ID
     */
    async getCategory(id) {
        return this.request(`/api/categories/${id}`);
    }

    /**
     * Crée une nouvelle catégorie
     */
    async createCategory(data) {
        return this.request('/api/categories', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Met à jour une catégorie
     */
    async updateCategory(id, data) {
        return this.request(`/api/categories/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Supprime une catégorie
     */
    async deleteCategory(id) {
        return this.request(`/api/categories/${id}`, {
            method: 'DELETE'
        });
    }

    // ============================================
    // Tags
    // ============================================

    /**
     * Récupère tous les tags
     */
    async getTags(limit = null) {
        const params = limit ? `?limit=${limit}` : '';
        return this.request(`/api/tags${params}`);
    }

    /**
     * Recherche des tags (auto-complétion)
     */
    async searchTags(query, limit = 10) {
        return this.request(`/api/tags/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    }

    /**
     * Récupère les tags populaires
     */
    async getPopularTags(limit = 20) {
        return this.request(`/api/tags/popular?limit=${limit}`);
    }

    /**
     * Récupère les procédures associées à un tag
     */
    async getTagProcedures(tagId) {
        return this.request(`/api/tags/${tagId}/procedures`);
    }

    // ============================================
    // Paramètres
    // ============================================

    /**
     * Récupère tous les paramètres
     */
    async getSettings() {
        return this.request('/api/settings');
    }

    /**
     * Récupère un paramètre spécifique
     */
    async getSetting(key) {
        return this.request(`/api/settings/${key}`);
    }

    /**
     * Met à jour un paramètre
     */
    async updateSetting(key, value) {
        return this.request(`/api/settings/${key}`, {
            method: 'PUT',
            body: JSON.stringify({ value })
        });
    }

    /**
     * Teste la connexion Claude
     */
    async testClaude() {
        return this.request('/api/settings/test-claude');
    }

    // ============================================
    // IA (via routes procédures)
    // ============================================

    /**
     * Génère des mots-clés avec l'IA
     */
    async generateKeywords(title, category, content) {
        return this.request('/api/ai/generate-keywords', {
            method: 'POST',
            body: JSON.stringify({ title, category, content })
        });
    }
}

// Instance globale
const api = new APIClient();
