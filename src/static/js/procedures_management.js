// Gestion de la liste des procédures

let allProcedures = [];
let filteredProcedures = [];

// Ouvrir le modal de liste des procédures
async function openProceduresListModal() {
    document.getElementById('proceduresListModal').style.display = 'flex';
    await loadProceduresList();
}

// Fermer le modal
function closeProceduresListModal() {
    document.getElementById('proceduresListModal').style.display = 'none';
}

// Charger toutes les procédures
async function loadProceduresList() {
    try {
        allProcedures = await api.getProcedures();
        filteredProcedures = [...allProcedures];
        renderProceduresList();
    } catch (error) {
        console.error('Error loading procedures:', error);
        showNotification('❌ Erreur lors du chargement des procédures', 'error');
    }
}

// Filtrer les procédures
function filterProceduresList() {
    const searchTerm = document.getElementById('proceduresSearchInput').value.toLowerCase();
    const category = document.getElementById('proceduresCategoryFilter').value;

    filteredProcedures = allProcedures.filter(proc => {
        let matchesSearch = !searchTerm;

        if (searchTerm && !matchesSearch) {
            // Recherche dans le titre
            matchesSearch = proc.title && proc.title.toLowerCase().includes(searchTerm);

            // Recherche dans la description
            if (!matchesSearch && proc.description) {
                matchesSearch = proc.description.toLowerCase().includes(searchTerm);
            }

            // Recherche dans les mots-clés
            if (!matchesSearch && proc.keywords) {
                let keywords = proc.keywords;
                // Parser si c'est une string
                if (typeof keywords === 'string') {
                    try {
                        keywords = JSON.parse(keywords);
                    } catch (e) {
                        keywords = [];
                    }
                }
                if (Array.isArray(keywords)) {
                    matchesSearch = keywords.some(kw =>
                        kw && kw.toString().toLowerCase().includes(searchTerm)
                    );
                }
            }
        }

        const matchesCategory = !category || proc.category === category;

        return matchesSearch && matchesCategory;
    });

    renderProceduresList();
}

// Afficher la liste des procédures
function renderProceduresList() {
    const container = document.getElementById('proceduresList');

    if (filteredProcedures.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <div>Aucune procédure trouvée</div>
            </div>
        `;
        return;
    }

    container.innerHTML = filteredProcedures.map(proc => renderProcedureCard(proc)).join('');
}

// Afficher une carte de procédure
function renderProcedureCard(procedure) {
    try {
        const categoryIcons = {
            'installation_logiciel': '💿',
            'depannage_materiel': '🔧',
            'demande_licence': '🔑',
            'support_applicatif': '💻',
            'reseau': '🌐',
            'securite': '🔒',
            'autre': '📋'
        };

        const icon = categoryIcons[procedure.category] || '📋';
        const usageCount = procedure.usage_count || 0;
        const createdBy = procedure.created_by || 'unknown';
        const createdDate = procedure.created_at ? new Date(procedure.created_at).toLocaleDateString('fr-FR') : 'N/A';

        // Titre sécurisé
        const title = procedure.title || 'Sans titre';

        // Gérer les mots-clés (peut être string JSON ou array)
        let keywords = [];
        if (procedure.keywords) {
            if (typeof procedure.keywords === 'string') {
                try {
                    keywords = JSON.parse(procedure.keywords);
                } catch (e) {
                    keywords = [];
                }
            } else if (Array.isArray(procedure.keywords)) {
                keywords = procedure.keywords;
            }
        }

        // Afficher les mots-clés
        let keywordsHtml = '';
        if (keywords.length > 0) {
            keywordsHtml = keywords.slice(0, 5).map(kw => {
                const keyword = kw || '';
                return `<span class="procedure-keyword">${escapeHtml(keyword.toString())}</span>`;
            }).join('');
        }

        // Gérer les étapes (peut être string JSON ou array)
        let steps = [];
        if (procedure.steps) {
            if (typeof procedure.steps === 'string') {
                try {
                    steps = JSON.parse(procedure.steps);
                } catch (e) {
                    steps = [];
                }
            } else if (Array.isArray(procedure.steps)) {
                steps = procedure.steps;
            }
        }

        return `
            <div class="procedure-card">
                <div class="procedure-card-header">
                    <div class="procedure-title">
                        <span class="procedure-icon">${icon}</span>
                        <span>${escapeHtml(title)}</span>
                    </div>
                    <div class="procedure-actions">
                        <button class="btn-icon" onclick="editProcedureFromList(${procedure.id})" title="Modifier">✏️</button>
                        <button class="btn-icon" onclick="deleteProcedureFromList(${procedure.id})" title="Supprimer">🗑️</button>
                    </div>
                </div>

                ${procedure.description ? `
                    <div class="procedure-description">
                        ${escapeHtml(procedure.description)}
                    </div>
                ` : ''}

                ${keywordsHtml ? `
                    <div class="procedure-keywords">
                        ${keywordsHtml}
                    </div>
                ` : ''}

                <div class="procedure-meta">
                    <span title="Nombre d'utilisations">📊 ${usageCount} utilisations</span>
                    <span title="Créé le">📅 ${createdDate}</span>
                    <span title="Créé par">👤 ${createdBy}</span>
                </div>

                ${steps.length > 0 ? `
                    <details class="procedure-steps-details">
                        <summary>📝 ${steps.length} étape(s)</summary>
                        <ol class="procedure-steps-list">
                            ${steps.map(step => `<li>${escapeHtml(step || '')}</li>`).join('')}
                        </ol>
                    </details>
                ` : ''}
            </div>
        `;
    } catch (error) {
        console.error('Error rendering procedure card:', error, procedure);
        return `
            <div class="procedure-card">
                <div class="procedure-card-header">
                    <div class="procedure-title">
                        <span class="procedure-icon">⚠️</span>
                        <span>Erreur de chargement</span>
                    </div>
                </div>
                <div class="procedure-description">
                    Une erreur s'est produite lors de l'affichage de cette procédure.
                </div>
            </div>
        `;
    }
}

// Modifier une procédure depuis la liste
async function editProcedureFromList(procedureId) {
    try {
        // Fermer le modal de liste
        closeProceduresListModal();

        // Utiliser la fonction d'édition standard de procedure_editor.js
        if (typeof openProcedureModal === 'function') {
            openProcedureModal(null, procedureId);
        } else {
            throw new Error('Fonction d\'édition non disponible');
        }

    } catch (error) {
        console.error('Error loading procedure for edit:', error);
        showNotification('❌ Erreur lors du chargement de la procédure', 'error');
    }
}

// Supprimer une procédure
async function deleteProcedureFromList(procedureId) {
    const confirmed = confirm('Êtes-vous sûr de vouloir supprimer cette procédure ? Cette action est irréversible.');

    if (!confirmed) return;

    try {
        await api.deleteProcedure(procedureId);
        showNotification('✅ Procédure supprimée avec succès', 'success');

        // Recharger la liste
        await loadProceduresList();

        // Recharger les stats
        await loadStats();

    } catch (error) {
        console.error('Error deleting procedure:', error);
        showNotification('❌ Erreur lors de la suppression de la procédure', 'error');
    }
}

// Sauvegarder une procédure (modifiée ou nouvelle)
async function saveProcedure(event) {
    event.preventDefault();

    const procedureId = document.getElementById('procedureId').value;
    const title = document.getElementById('procedureTitle').value.trim();
    const category = document.getElementById('procedureCategory').value;
    const description = document.getElementById('procedureDescription').value.trim();
    const keywordsText = document.getElementById('procedureKeywords').value.trim();

    // Extraire les étapes
    const stepInputs = document.querySelectorAll('.step-input');
    const steps = Array.from(stepInputs).map(input => input.value.trim()).filter(s => s.length > 0);

    if (steps.length === 0) {
        alert('Veuillez ajouter au moins une étape');
        return;
    }

    // Parser les mots-clés
    const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k.length > 0) : [];

    const procedureData = {
        title,
        category,
        description,
        steps,
        keywords
    };

    try {
        if (procedureId) {
            // Mise à jour
            await api.updateProcedure(procedureId, procedureData);
            showNotification('✅ Procédure mise à jour avec succès', 'success');
        } else {
            // Création
            await api.createProcedureManually(procedureData);
            showNotification('✅ Procédure créée avec succès', 'success');
        }

        closeProcedureModal();

        // Recharger les stats
        await loadStats();

        // Si le modal de liste est ouvert, le recharger
        const listModal = document.getElementById('proceduresListModal');
        if (listModal.style.display === 'flex') {
            await loadProceduresList();
        }

    } catch (error) {
        console.error('Error saving procedure:', error);
        showNotification('❌ Erreur lors de l\'enregistrement de la procédure', 'error');
    }
}
