// Gestion des techniciens

// Cache pour les techniciens
let techniciansCache = null;
let techniciansCacheTime = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Charge les techniciens depuis l'API
 */
async function loadTechniciansFromAPI() {
    try {
        const response = await api.request('/api/technicians');
        return response || [];
    } catch (error) {
        console.error('Error loading technicians:', error);
        return [];
    }
}

/**
 * Obtient tous les techniciens actifs (avec cache)
 */
async function getTechnicians() {
    const now = Date.now();

    // Utiliser le cache si valide
    if (techniciansCache && techniciansCacheTime && (now - techniciansCacheTime) < CACHE_DURATION) {
        return techniciansCache;
    }

    // Recharger depuis l'API
    const technicians = await loadTechniciansFromAPI();
    techniciansCache = technicians;
    techniciansCacheTime = now;

    return technicians;
}

/**
 * Rafraîchit le cache des techniciens
 */
async function refreshTechniciansCache() {
    techniciansCache = null;
    techniciansCacheTime = null;
    return await getTechnicians();
}

/**
 * Obtient un technicien par son nom
 */
async function getTechnicianByName(name) {
    const technicians = await getTechnicians();
    return technicians.find(t => t.name === name);
}

/**
 * Crée un nouveau technicien
 */
async function createTechnician(name, email = null) {
    try {
        const response = await api.request('/api/technicians', {
            method: 'POST',
            body: JSON.stringify({ name, email })
        });

        // Rafraîchir le cache
        await refreshTechniciansCache();

        return response;
    } catch (error) {
        console.error('Error creating technician:', error);
        throw error;
    }
}

/**
 * Met à jour un technicien
 */
async function updateTechnician(technicianId, data) {
    try {
        const response = await api.request(`/api/technicians/${technicianId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        // Rafraîchir le cache
        await refreshTechniciansCache();

        return response;
    } catch (error) {
        console.error('Error updating technician:', error);
        throw error;
    }
}

/**
 * Désactive un technicien
 */
async function deleteTechnician(technicianId) {
    try {
        const response = await api.request(`/api/technicians/${technicianId}`, {
            method: 'DELETE'
        });

        // Rafraîchir le cache
        await refreshTechniciansCache();

        return response;
    } catch (error) {
        console.error('Error deleting technician:', error);
        throw error;
    }
}
