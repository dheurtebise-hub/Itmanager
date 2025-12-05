// Client API pour communiquer avec le backend

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Tickets
    async getTickets(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/tickets${params ? '?' + params : ''}`);
    }

    async getTicket(id) {
        return this.request(`/api/tickets/${id}`);
    }

    async updateTicket(id, data) {
        return this.request(`/api/tickets/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async markAsNotUserRequest(id) {
        return this.request(`/api/tickets/${id}/mark-not-user-request`, {
            method: 'POST',
        });
    }

    async getSuggestion(id) {
        return this.request(`/api/tickets/${id}/suggest`);
    }

    // Stats
    async getStats() {
        return this.request('/api/tickets/stats');
    }

    // Sync
    async syncNow(initialImport = false, importLimit = 50) {
        return this.request('/api/sync', {
            method: 'POST',
            body: JSON.stringify({
                initial_import: initialImport,
                import_limit: importLimit
            }),
        });
    }

    async getSyncStatus() {
        return this.request('/api/sync/status');
    }

    // Export
    getExportURL(format, filters = {}) {
        const params = new URLSearchParams({ format, ...filters }).toString();
        return `/api/export/tickets?${params}`;
    }

    // Config
    async getConfig() {
        return this.request('/api/config');
    }

    async updateConfig(data) {
        return this.request('/api/config', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // Categories
    async getCategories() {
        return this.request('/api/categories');
    }

    // Procedures
    async getProcedureSuggestions(ticketId, page = 1, perPage = 10) {
        const response = await this.request(`/api/procedures/suggestions/${ticketId}?page=${page}&per_page=${perPage}`);
        // La réponse contient maintenant { suggestions: [...], pagination: {...} }
        // On retourne l'objet complet pour que le code appelant puisse accéder aux métadonnées de pagination
        return response;
    }

    async createProcedureFromTicket(ticketId) {
        return this.request('/api/procedures/create', {
            method: 'POST',
            body: JSON.stringify({ ticket_id: ticketId }),
        });
    }

    async createProcedureManually(procedureData) {
        return this.request('/api/procedures', {
            method: 'POST',
            body: JSON.stringify(procedureData),
        });
    }

    async submitProcedureFeedback(procedureId, ticketId, feedbackType) {
        return this.request('/api/procedures/feedback', {
            method: 'POST',
            body: JSON.stringify({
                procedure_id: procedureId,
                ticket_id: ticketId,
                feedback_type: feedbackType,
            }),
        });
    }

    async getProcedures(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        const response = await this.request(`/api/procedures${params ? '?' + params : ''}`);

        // L'API retourne maintenant { procedures: [...], pagination: {...} }
        // Pour la rétrocompatibilité, on retourne juste le tableau de procédures
        // Si l'appelant a besoin de la pagination, il peut utiliser getProceduresPaginated()
        if (response && response.procedures) {
            return response.procedures;
        }

        // Fallback pour l'ancien format (si jamais)
        return response;
    }

    async getProceduresPaginated(filters = {}) {
        // Cette méthode retourne l'objet complet avec pagination
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/procedures${params ? '?' + params : ''}`);
    }

    async getProcedure(procedureId) {
        return this.request(`/api/procedures/${procedureId}`);
    }

    async updateProcedure(procedureId, data) {
        return this.request(`/api/procedures/${procedureId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteProcedure(procedureId) {
        return this.request(`/api/procedures/${procedureId}`, {
            method: 'DELETE',
        });
    }
}

// Instance globale
const api = new APIClient();
