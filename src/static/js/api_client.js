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

    async getSuggestion(id) {
        return this.request(`/api/tickets/${id}/suggest`);
    }

    // Stats
    async getStats() {
        return this.request('/api/tickets/stats');
    }

    // Sync
    async syncNow() {
        return this.request('/api/sync', { method: 'POST' });
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
}

// Instance globale
const api = new APIClient();
