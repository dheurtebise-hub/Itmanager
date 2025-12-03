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
        const matchesSearch = !searchTerm ||
            proc.title.toLowerCase().includes(searchTerm) ||
            (proc.description && proc.description.toLowerCase().includes(searchTerm)) ||
            (proc.keywords && proc.keywords.some(kw => kw.toLowerCase().includes(searchTerm)));

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

    // Afficher les mots-clés
    let keywordsHtml = '';
    if (procedure.keywords && Array.isArray(procedure.keywords) && procedure.keywords.length > 0) {
        keywordsHtml = procedure.keywords.slice(0, 5).map(kw =>
            `<span class="procedure-keyword">${escapeHtml(kw)}</span>`
        ).join('');
    }

    return `
        <div class="procedure-card">
            <div class="procedure-card-header">
                <div class="procedure-title">
                    <span class="procedure-icon">${icon}</span>
                    <span>${escapeHtml(procedure.title)}</span>
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

            ${procedure.steps && procedure.steps.length > 0 ? `
                <details class="procedure-steps-details">
                    <summary>📝 ${procedure.steps.length} étape(s)</summary>
                    <ol class="procedure-steps-list">
                        ${procedure.steps.map(step => `<li>${escapeHtml(step)}</li>`).join('')}
                    </ol>
                </details>
            ` : ''}
        </div>
    `;
}

// Modifier une procédure depuis la liste
async function editProcedureFromList(procedureId) {
    try {
        // Fermer le modal de liste
        closeProceduresListModal();

        // Charger la procédure
        const response = await fetch(`/api/procedures/${procedureId}`);
        if (!response.ok) {
            throw new Error('Procédure non trouvée');
        }

        const procedure = await response.json();

        // Ouvrir le modal d'édition
        openEditProcedureModal(procedure);

    } catch (error) {
        console.error('Error loading procedure for edit:', error);
        showNotification('❌ Erreur lors du chargement de la procédure', 'error');
    }
}

// Ouvrir le modal d'édition de procédure
function openEditProcedureModal(procedure) {
    // Remplir le formulaire
    document.getElementById('procedureId').value = procedure.id;
    document.getElementById('procedureTitle').value = procedure.title;
    document.getElementById('procedureCategory').value = procedure.category || '';
    document.getElementById('procedureDescription').value = procedure.description || '';

    // Remplir les mots-clés
    if (procedure.keywords && Array.isArray(procedure.keywords)) {
        document.getElementById('procedureKeywords').value = procedure.keywords.join(', ');
    }

    // Remplir les étapes
    const stepsContainer = document.getElementById('procedureSteps');
    stepsContainer.innerHTML = '';

    if (procedure.steps && Array.isArray(procedure.steps)) {
        procedure.steps.forEach((step, index) => {
            addProcedureStepWithValue(step);
        });
    }

    // Changer le titre du modal
    document.getElementById('procedureModalTitle').textContent = 'Modifier la procédure';

    // Ouvrir le modal
    document.getElementById('procedureModal').style.display = 'flex';
}

// Ajouter une étape avec une valeur
function addProcedureStepWithValue(value = '') {
    const stepsContainer = document.getElementById('procedureSteps');
    const stepIndex = stepsContainer.children.length;

    const stepDiv = document.createElement('div');
    stepDiv.className = 'procedure-step-item';
    stepDiv.innerHTML = `
        <span class="step-number">${stepIndex + 1}.</span>
        <input type="text" class="form-control step-input" placeholder="Description de l'étape" value="${escapeHtml(value)}" required>
        <button type="button" class="btn-icon btn-remove-step" onclick="removeProcedureStep(this)">🗑️</button>
    `;

    stepsContainer.appendChild(stepDiv);
    updateStepNumbers();
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
