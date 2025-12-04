/**
 * Gestion centralisée des catégories
 */

let categoriesCache = null;
let categoriesLoadPromise = null;

/**
 * Charge les catégories depuis l'API (avec cache)
 */
async function loadCategoriesFromAPI() {
    // Si déjà en cours de chargement, retourner la même promesse
    if (categoriesLoadPromise) {
        return categoriesLoadPromise;
    }

    // Si déjà chargées, retourner du cache
    if (categoriesCache) {
        return Promise.resolve(categoriesCache);
    }

    // Charger depuis l'API
    categoriesLoadPromise = fetch('/api/categories')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load categories');
            }
            return response.json();
        })
        .then(categories => {
            categoriesCache = categories;
            categoriesLoadPromise = null;
            return categories;
        })
        .catch(error => {
            console.error('Error loading categories:', error);
            categoriesLoadPromise = null;
            // Retourner des catégories par défaut en cas d'erreur
            return [
                { name: 'logiciel', icon: '💿', color: '#0079BF' },
                { name: 'materiel', icon: '🔧', color: '#70B500' },
                { name: 'reseau', icon: '🌐', color: '#C377E0' },
                { name: 'securite', icon: '🔒', color: '#FF5733' },
                { name: 'autre', icon: '📋', color: '#838C91' }
            ];
        });

    return categoriesLoadPromise;
}

/**
 * Remplit un select avec les catégories
 */
async function populateCategorySelect(selectElement, selectedValue = null) {
    const categories = await loadCategoriesFromAPI();

    selectElement.innerHTML = categories.map(cat => {
        const selected = selectedValue === cat.name ? 'selected' : '';
        return `<option value="${cat.name}" ${selected}>${cat.icon} ${formatCategoryLabel(cat.name)}</option>`;
    }).join('');
}

/**
 * Formate le label d'une catégorie
 */
function formatCategoryLabel(name) {
    const labels = {
        'logiciel': 'Logiciel',
        'materiel': 'Matériel',
        'reseau': 'Réseau',
        'securite': 'Sécurité',
        'autre': 'Autre',
        'installation_logiciel': 'Installation logiciel',
        'depannage_materiel': 'Dépannage matériel',
        'demande_licence': 'Demande de licence',
        'support_applicatif': 'Support applicatif'
    };

    return labels[name] || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Obtient l'icône d'une catégorie
 */
async function getCategoryIcon(categoryName) {
    const categories = await loadCategoriesFromAPI();
    const category = categories.find(c => c.name === categoryName);
    return category ? category.icon : '📋';
}

/**
 * Obtient la couleur d'une catégorie
 */
async function getCategoryColor(categoryName) {
    const categories = await loadCategoriesFromAPI();
    const category = categories.find(c => c.name === categoryName);
    return category ? category.color : '#838C91';
}

/**
 * Obtient toutes les catégories sous forme d'objets {name, icon, color, label}
 */
async function getCategories() {
    const categories = await loadCategoriesFromAPI();
    return categories.map(cat => ({
        ...cat,
        label: formatCategoryLabel(cat.name)
    }));
}

/**
 * Force le rechargement des catégories (invalide le cache)
 */
function refreshCategories() {
    categoriesCache = null;
    return loadCategoriesFromAPI();
}

// Charger les catégories au démarrage de l'application
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => loadCategoriesFromAPI());
} else {
    loadCategoriesFromAPI();
}
