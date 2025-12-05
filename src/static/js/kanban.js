// Gestion du Kanban Board

let allTickets = [];
let filteredTickets = [];
let categories = [];

async function loadTickets() {
    try {
        const data = await api.getTickets({ per_page: 200 });
        allTickets = data.tickets || [];
        filteredTickets = [...allTickets];
        renderTickets();
    } catch (error) {
        console.error('Error loading tickets:', error);
    }
}

async function loadCategories() {
    try {
        categories = await api.getCategories();
        renderCategoryFilter();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function renderCategoryFilter() {
    const select = document.getElementById('categoryFilter');
    if (!select) return;

    const options = categories.map(cat =>
        `<option value="${cat.name}">${cat.icon} ${cat.name}</option>`
    ).join('');

    select.innerHTML = '<option value="">Toutes les catégories</option>' + options;
}

function renderTickets() {
    const statuses = ['new', 'in_progress', 'resolved'];

    statuses.forEach(status => {
        const container = document.getElementById(`tickets-${status}`);
        const countEl = document.getElementById(`count-${status}`);

        if (!container) return;

        const tickets = filteredTickets.filter(t => t.status === status);

        if (tickets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div>Aucun ticket</div>
                </div>
            `;
        } else {
            container.innerHTML = tickets.map(t => createTicketCard(t)).join('');
        }

        if (countEl) {
            countEl.textContent = tickets.length;
        }
    });
}

function createTicketCard(ticket) {
    const timeAgo = formatTimeAgo(ticket.received_date);
    const notUserRequestClass = ticket.is_not_user_request ? ' not-user-request' : '';
    const personIcon = getPersonIcon(ticket.sender_name || ticket.sender_email);

    // Bouton pour marquer comme non-demande utilisateur (visible sauf si déjà marqué)
    const notUserRequestButton = !ticket.is_not_user_request ?
        `<button class="btn-not-user-request" onclick="event.stopPropagation(); markAsNotUserRequestFromCard(${ticket.id})" title="Ce ticket n'est pas une demande utilisateur">🚫</button>` : '';

    return `
        <div class="ticket-card${notUserRequestClass}"
             draggable="true"
             data-ticket-id="${ticket.id}"
             data-ticket-status="${ticket.status}"
             data-ticket-subject="${escapeHtml(ticket.subject)}"
             ondragstart="handleDragStart(event)"
             ondragend="handleDragEnd(event)"
             onclick="handleTicketSingleClick(event, ${ticket.id})"
             ondblclick="handleTicketDoubleClick(event, ${ticket.id})">
            <div class="ticket-header">
                <span class="ticket-id">#${ticket.id}</span>
                <div class="ticket-header-actions">
                    ${notUserRequestButton}
                </div>
            </div>
            <div class="ticket-subject">${escapeHtml(ticket.subject)}</div>
            <div class="ticket-info">
                <div class="ticket-sender">
                    ${personIcon} ${escapeHtml(ticket.sender_name || ticket.sender_email)}
                </div>
                <div class="ticket-date">${timeAgo}</div>
            </div>
        </div>
    `;
}

function getPersonIcon(name) {
    // Détection basique du genre par les prénoms féminins courants
    const femaleNames = ['marie', 'sophie', 'julie', 'claire', 'anne', 'isabelle', 'catherine', 'nathalie',
                         'sylvie', 'martine', 'christine', 'florence', 'sandrine', 'valérie', 'laurence',
                         'camille', 'emma', 'léa', 'chloé', 'manon', 'sarah', 'laura', 'alice'];

    const lowerName = (name || '').toLowerCase();
    const isFemale = femaleNames.some(fn => lowerName.includes(fn));

    return isFemale ? '👷‍♀️' : '👷';
}

function getSLAIndicator(slaStatus) {
    if (!slaStatus) return '';

    const classes = {
        ok: 'sla-ok',
        warning: 'sla-warning',
        breach: 'sla-breach',
    };

    const className = classes[slaStatus.status] || 'sla-ok';
    return `<span class="sla-indicator ${className}"></span>`;
}

function formatTimeAgo(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "à l'instant";
    if (diffMins < 60) return `il y a ${diffMins} min`;
    if (diffHours < 24) return `il y a ${diffHours}h`;
    if (diffDays < 7) return `il y a ${diffDays}j`;

    return date.toLocaleDateString('fr-FR');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// Filtres et recherche
function searchTickets() {
    const query = document.getElementById('searchInput')?.value.toLowerCase() || '';
    applyFilters(query);
}

function filterTickets() {
    const query = document.getElementById('searchInput')?.value.toLowerCase() || '';
    applyFilters(query);
}

function applyFilters(searchQuery = '') {
    const category = document.getElementById('categoryFilter')?.value || '';
    const priority = document.getElementById('priorityFilter')?.value || '';

    filteredTickets = allTickets.filter(ticket => {
        const matchSearch = !searchQuery ||
            ticket.subject?.toLowerCase().includes(searchQuery) ||
            ticket.summary?.toLowerCase().includes(searchQuery) ||
            ticket.sender_email?.toLowerCase().includes(searchQuery);

        const matchCategory = !category || ticket.category === category;
        const matchPriority = !priority || ticket.priority === priority;

        return matchSearch && matchCategory && matchPriority;
    });

    renderTickets();
}

// Synchronisation
async function syncNow(initialImport = false) {
    const button = document.querySelector('button[onclick="syncNow()"]');
    const icon = document.getElementById('syncIcon');

    if (button) button.disabled = true;
    if (icon) icon.innerHTML = '<span class="loading"></span>';

    try {
        console.log('Début synchronisation, initialImport=', initialImport);
        const result = await api.syncNow(initialImport);
        console.log('Résultat sync:', result);

        if (result.status === 'success') {
            console.log('Rechargement des tickets...');
            await loadTickets();
            console.log('Tickets rechargés, total affiché:', allTickets.length);

            await loadStats();

            const msg = initialImport
                ? `✅ Import initial réussi !\n${result.new_tickets} tickets créés\n${result.emails_found} emails analysés`
                : `✅ Synchronisation réussie !\n${result.new_tickets} nouveaux tickets`;

            showNotification(msg, 'success');

            // Si aucun ticket créé mais des emails trouvés, informer l'utilisateur
            if (result.emails_found > 0 && result.new_tickets === 0) {
                showNotification(`⚠️ ${result.emails_found} emails trouvés mais déjà importés`, 'warning');
            }
        } else if (result.status === 'error') {
            console.error('Erreur de synchronisation:', result.message);
            const errorMsg = result.message || 'Erreur inconnue';
            showNotification(`❌ Erreur de synchronisation:\n${errorMsg}`, 'error');
        } else if (result.status === 'already_syncing') {
            showNotification('⏳ Synchronisation déjà en cours...', 'warning');
        }
    } catch (error) {
        console.error('Erreur sync:', error);
        const errorMsg = error.message || error.toString();
        showNotification(`❌ Erreur lors de la synchronisation:\n${errorMsg}`, 'error');
    } finally {
        if (button) button.disabled = false;
        if (icon) icon.textContent = '🔄';
    }
}

async function initialImport() {
    if (!confirm('Importer tous les emails récents du dossier configuré (max 50) ?\n\nCela peut prendre quelques minutes si vous avez beaucoup d\'emails.')) {
        return;
    }

    await syncNow(true);
}

function showNotification(message, type = 'info') {
    // Créer une notification temporaire VISIBLE avec bouton de fermeture
    const notif = document.createElement('div');
    notif.className = `sync-notification sync-${type}`;

    // Créer le contenu avec message et bouton de fermeture
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close-btn';
    closeBtn.innerHTML = '✕';
    closeBtn.onclick = () => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    };

    notif.appendChild(messageSpan);
    notif.appendChild(closeBtn);

    document.body.appendChild(notif);

    // Animation d'entrée
    setTimeout(() => notif.classList.add('show'), 10);

    // Fermeture automatique
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 8000); // 8 secondes
}

// Stats
async function loadStats() {
    try {
        const stats = await api.getStats();

        document.getElementById('stat-today').textContent = stats.today || 0;
        document.getElementById('stat-week').textContent = stats.this_week || 0;

        // Charger le nombre de procédures
        const procedures = await api.getProcedures();
        document.getElementById('stat-procedures').textContent = procedures?.length || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Export
function exportTickets(format) {
    const category = document.getElementById('categoryFilter')?.value || '';

    const filters = {};
    if (category) filters.category = category;

    const url = api.getExportURL(format, filters);
    window.open(url, '_blank');
}

// ============================================
// DRAG & DROP
// ============================================

let draggedTicketId = null;
let isDragging = false;
let clickTimer = null;
let selectedTicketForProcedure = null;

// Simple clic : afficher les procédures
function handleTicketSingleClick(event, ticketId) {
    // Ne pas traiter si on vient de finir un drag
    if (isDragging) {
        event.preventDefault();
        event.stopPropagation();
        return;
    }

    // Annuler le timer précédent si double clic détecté
    if (clickTimer !== null) {
        clearTimeout(clickTimer);
        clickTimer = null;
        return;
    }

    // Délai pour distinguer simple clic du double clic
    clickTimer = setTimeout(() => {
        clickTimer = null;
        showProceduresForTicket(ticketId);
    }, 250);
}

// Double clic : ouvrir la modal du ticket
function handleTicketDoubleClick(event, ticketId) {
    event.preventDefault();
    event.stopPropagation();

    // Annuler le timer du simple clic
    if (clickTimer !== null) {
        clearTimeout(clickTimer);
        clickTimer = null;
    }

    // Ne pas ouvrir la modal si on vient de finir un drag
    if (isDragging) {
        return;
    }

    openTicketModal(ticketId);
}

function handleDragStart(event) {
    isDragging = true;
    draggedTicketId = event.target.dataset.ticketId;

    event.target.style.opacity = '0.5';
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/html', event.target.innerHTML);

    // Ajouter une classe visuelle
    event.target.classList.add('dragging');
}

function handleDragEnd(event) {
    event.target.style.opacity = '1';
    event.target.classList.remove('dragging');

    // Remettre isDragging à false après un court délai pour éviter le clic
    setTimeout(() => {
        isDragging = false;
    }, 100);

    // Retirer les classes de survol de toutes les colonnes
    document.querySelectorAll('.kanban-column').forEach(col => {
        col.classList.remove('drag-over');
    });
}

function handleDragOver(event) {
    if (event.preventDefault) {
        event.preventDefault();
    }
    event.dataTransfer.dropEffect = 'move';

    // Trouver la colonne parente
    const column = event.target.closest('.kanban-column');
    if (column) {
        column.classList.add('drag-over');
    }

    return false;
}

function handleDragEnter(event) {
    const column = event.target.closest('.kanban-column');
    if (column) {
        column.classList.add('drag-over');
    }
}

function handleDragLeave(event) {
    const column = event.target.closest('.kanban-column');
    if (column && !column.contains(event.relatedTarget)) {
        column.classList.remove('drag-over');
    }
}

async function handleDrop(event) {
    if (event.stopPropagation) {
        event.stopPropagation();
    }

    const column = event.target.closest('.kanban-column');
    if (!column || !draggedTicketId) {
        return false;
    }

    const newStatus = column.dataset.status;
    const oldStatus = event.dataTransfer.getData('text/html');

    // Mettre à jour le ticket
    try {
        await api.updateTicket(draggedTicketId, { status: newStatus });

        // Recharger les tickets
        await loadTickets();

        // Afficher une notification
        showNotification(`Ticket #${draggedTicketId} déplacé vers "${getStatusLabel(newStatus)}"`, 'success');
    } catch (error) {
        console.error('Error updating ticket:', error);
        showNotification('Erreur lors du déplacement du ticket', 'error');
    }

    column.classList.remove('drag-over');
    return false;
}

function getStatusLabel(status) {
    const labels = {
        'new': 'Nouveau',
        'in_progress': 'En cours',
        'resolved': 'Résolu'
    };
    return labels[status] || status;
}

function initializeDropZones() {
    const columns = document.querySelectorAll('.kanban-column');

    columns.forEach(column => {
        column.addEventListener('dragover', handleDragOver);
        column.addEventListener('dragenter', handleDragEnter);
        column.addEventListener('dragleave', handleDragLeave);
        column.addEventListener('drop', handleDrop);
    });
}

// Initialiser les drop zones au chargement
document.addEventListener('DOMContentLoaded', () => {
    initializeDropZones();
});

// ============================================
// GESTION DES PROCÉDURES
// ============================================

async function showProceduresForTicket(ticketId) {
    const procedureContent = document.getElementById('procedure-content');
    if (!procedureContent) return;

    // Trouver le ticket dans la liste
    const ticket = allTickets.find(t => t.id === ticketId);
    if (!ticket) return;

    selectedTicketForProcedure = ticket;

    // Afficher le loading
    procedureContent.innerHTML = `
        <div class="procedure-loading">
            <div class="procedure-loading-spinner">⏳</div>
            <div style="margin-top: 1rem;">Recherche des procédures...</div>
        </div>
    `;

    try {
        // Appeler l'API pour obtenir les suggestions de procédures
        const response = await api.getProcedureSuggestions(ticketId);

        // La réponse contient { suggestions: [...], pagination: {...} }
        const suggestions = response.suggestions || response; // Fallback si l'ancien format est retourné
        const pagination = response.pagination;

        renderProcedures(ticket, suggestions, pagination);
    } catch (error) {
        console.error('Error loading procedures:', error);

        // Si aucune procédure n'existe, afficher la boîte de dialogue pour en créer une
        renderCreateProcedureDialog(ticket);
    }
}

function renderProcedures(ticket, suggestions, pagination = null) {
    const procedureContent = document.getElementById('procedure-content');
    if (!procedureContent) return;

    let html = `
        <div class="procedure-selected-ticket">
            <div class="procedure-selected-ticket-title">Ticket sélectionné</div>
            <div class="procedure-selected-ticket-subject">${escapeHtml(ticket.subject)}</div>
            <div class="procedure-selected-ticket-id">#${ticket.id}</div>
        </div>
    `;

    if (!suggestions || suggestions.length === 0) {
        // Aucune procédure trouvée
        html += `
            <div class="procedure-create-dialog">
                <div class="procedure-create-dialog-icon">📝</div>
                <div class="procedure-create-dialog-title">Aucune procédure trouvée</div>
                <div class="procedure-create-dialog-description">
                    Il n'existe pas encore de procédure pour ce type de problème.
                    Voulez-vous en créer une ?
                </div>
                <button class="btn-create-procedure" onclick="createNewProcedure(${ticket.id})">
                    Créer une procédure
                </button>
            </div>
        `;
    } else {
        // Afficher les procédures suggérées
        html += `
            <div class="procedure-suggestions">
                <div class="procedure-suggestions-title">Procédures suggérées (${suggestions.length})</div>
        `;

        suggestions.forEach(proc => {
            html += createProcedureCard(proc, ticket.id);
        });

        html += `</div>`;
    }

    procedureContent.innerHTML = html;
}

function renderCreateProcedureDialog(ticket) {
    const procedureContent = document.getElementById('procedure-content');
    if (!procedureContent) return;

    procedureContent.innerHTML = `
        <div class="procedure-selected-ticket">
            <div class="procedure-selected-ticket-title">Ticket sélectionné</div>
            <div class="procedure-selected-ticket-subject">${escapeHtml(ticket.subject)}</div>
            <div class="procedure-selected-ticket-id">#${ticket.id}</div>
        </div>

        <div class="procedure-create-dialog">
            <div class="procedure-create-dialog-icon">📝</div>
            <div class="procedure-create-dialog-title">Aucune procédure trouvée</div>
            <div class="procedure-create-dialog-description">
                Il n'existe pas encore de procédure pour ce type de problème.
                Voulez-vous en créer une ?
            </div>
            <button class="btn-create-procedure" onclick="createNewProcedure(${ticket.id})">
                Créer une procédure
            </button>
        </div>
    `;
}

function createProcedureCard(procedure, ticketId) {
    const stepsHtml = procedure.steps && procedure.steps.length > 0
        ? `
            <div class="procedure-steps">
                <div class="procedure-steps-title">Étapes :</div>
                ${procedure.steps.map(step => `<div class="procedure-step">${step}</div>`).join('')}
            </div>
        `
        : '';

    const confidenceHtml = procedure.confidence
        ? `<span class="procedure-confidence">${Math.round(procedure.confidence * 100)}%</span>`
        : '';

    // Déterminer l'état du feedback
    const thumbsUpClass = procedure.feedback === 'positive' ? 'active thumbs-up' : '';
    const thumbsDownClass = procedure.feedback === 'negative' ? 'active thumbs-down' : '';

    return `
        <div class="procedure-item" data-procedure-id="${procedure.id}">
            <div class="procedure-header">
                <div class="procedure-title">${escapeHtml(procedure.title)}</div>
                ${confidenceHtml}
            </div>

            ${procedure.description ? `<div class="procedure-description">${escapeHtml(procedure.description)}</div>` : ''}

            ${stepsHtml}

            <div class="procedure-footer">
                <div class="procedure-feedback">
                    <span class="procedure-feedback-label">Utile ?</span>
                    <div class="procedure-feedback-buttons">
                        <button class="feedback-btn ${thumbsUpClass}"
                                onclick="submitProcedureFeedback(${procedure.id}, ${ticketId}, 'positive')">
                            👍
                        </button>
                        <button class="feedback-btn ${thumbsDownClass}"
                                onclick="submitProcedureFeedback(${procedure.id}, ${ticketId}, 'negative')">
                            👎
                        </button>
                    </div>
                </div>
                <div class="procedure-actions">
                    <button class="btn-procedure btn-procedure-primary" onclick="editProcedure(${procedure.id})">
                        ✏️ Modifier
                    </button>
                </div>
            </div>
        </div>
    `;
}

async function submitProcedureFeedback(procedureId, ticketId, feedbackType) {
    try {
        await api.submitProcedureFeedback(procedureId, ticketId, feedbackType);

        // Afficher une notification
        showNotification(
            feedbackType === 'positive'
                ? '✅ Merci pour votre retour positif !'
                : '📝 Merci, nous allons améliorer cette procédure',
            'success'
        );

        // Recharger les procédures pour mettre à jour l'affichage
        await showProceduresForTicket(ticketId);
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showNotification('❌ Erreur lors de l\'envoi du feedback', 'error');
    }
}

function createNewProcedure(ticketId) {
    // Ouvrir la modal d'édition de procédure
    openProcedureModal(ticketId);
}

function editProcedure(procedureId) {
    // Ouvrir la modal d'édition en mode modification
    openProcedureModal(null, procedureId);
}

async function markAsNotUserRequestFromCard(ticketId) {
    const confirmed = window.confirm(
        'Marquer ce ticket comme "non-demande utilisateur" ?\n\n' +
        'Le ticket sera marqué et pourra être filtré séparément.'
    );

    if (!confirmed) return;

    try {
        await api.markAsNotUserRequest(ticketId);
        showNotification('✅ Ticket marqué comme non-demande utilisateur', 'success');
        await loadTickets();
    } catch (error) {
        console.error('Error marking ticket as not user request:', error);
        showNotification('❌ Erreur lors du marquage du ticket', 'error');
    }
}

// ============================================
// RECHERCHE DE PROCÉDURES
// ============================================

let procedureSearchTimeout = null;
let proceduresSearchCache = [];

// Index de recherche en mémoire pour des recherches ultra-rapides
let procedureSearchIndex = {
    invertedIndex: {},      // Map: mot -> Set(procedureIds)
    procedureMap: {},       // Map: procedureId -> procedure
    normalizedText: {},     // Map: procedureId -> texte normalisé pré-calculé
    lastUpdate: null        // Timestamp de dernière mise à jour
};

// Charger toutes les procédures au démarrage
async function loadAllProcedures() {
    try {
        proceduresSearchCache = await api.getProcedures();
        // Construire l'index de recherche
        buildSearchIndex(proceduresSearchCache);
    } catch (error) {
        console.error('Error loading procedures for search:', error);
        proceduresSearchCache = [];
    }
}

// Construire l'index de recherche en mémoire
function buildSearchIndex(procedures) {
    console.log(`Building search index for ${procedures.length} procedures...`);
    const startTime = performance.now();

    // Réinitialiser l'index
    procedureSearchIndex.invertedIndex = {};
    procedureSearchIndex.procedureMap = {};
    procedureSearchIndex.normalizedText = {};

    // Stopwords français à ignorer
    const stopwords = new Set([
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux',
        'ce', 'cet', 'cette', 'ces', 'et', 'ou', 'mais', 'donc',
        'dans', 'sur', 'pour', 'par', 'avec', 'sans'
    ]);

    procedures.forEach(proc => {
        const id = proc.id;
        procedureSearchIndex.procedureMap[id] = proc;

        // Construire le texte searchable (pondéré par importance)
        const searchableText = [
            proc.title || '',
            proc.title || '',  // Titre compté 2x (plus important)
            proc.description || '',
            proc.category || '',
            ...(proc.keywords || [])
        ].join(' ');

        // Normaliser et stocker
        const normalized = normalizeText(searchableText);
        procedureSearchIndex.normalizedText[id] = normalized;

        // Extraire les mots et les ajouter à l'index inversé
        const words = normalized.split(/\s+/).filter(word => {
            // Filtrer les mots courts et les stopwords
            return word.length >= 3 && !stopwords.has(word);
        });

        // Ajouter chaque mot à l'index inversé
        words.forEach(word => {
            if (!procedureSearchIndex.invertedIndex[word]) {
                procedureSearchIndex.invertedIndex[word] = new Set();
            }
            procedureSearchIndex.invertedIndex[word].add(id);
        });
    });

    procedureSearchIndex.lastUpdate = Date.now();
    const duration = (performance.now() - startTime).toFixed(2);
    console.log(`Search index built in ${duration}ms`);
    console.log(`Index contains ${Object.keys(procedureSearchIndex.invertedIndex).length} unique words`);
}

// Normalise un texte en retirant les accents
function normalizeText(text) {
    if (!text) return '';
    return text
        .normalize('NFD')  // Décompose les caractères (sépare lettres et accents)
        .replace(/[\u0300-\u036f]/g, '')  // Retire les marques diacritiques
        .toLowerCase();
}

// Fonction de recherche avec debounce
function searchProcedures(query) {
    clearTimeout(procedureSearchTimeout);

    const resultsContainer = document.getElementById('procedure-search-results');

    if (!query || query.trim().length === 0) {
        resultsContainer.classList.remove('show');
        resultsContainer.innerHTML = '';
        return;
    }

    // Afficher un spinner pendant le chargement
    resultsContainer.classList.add('show');
    resultsContainer.innerHTML = `
        <div class="procedure-search-loading">
            <div class="procedure-search-loading-spinner">⏳</div>
            <div>Recherche en cours...</div>
        </div>
    `;

    procedureSearchTimeout = setTimeout(() => {
        performProcedureSearch(query.trim());
    }, 300); // Attendre 300ms après la dernière frappe
}

// Effectuer la recherche avec l'index
function performProcedureSearch(query) {
    const resultsContainer = document.getElementById('procedure-search-results');

    if (proceduresSearchCache.length === 0 || !procedureSearchIndex.lastUpdate) {
        // Si les procédures ne sont pas encore chargées, les charger
        loadAllProcedures().then(() => {
            performProcedureSearch(query);
        });
        return;
    }

    // Normaliser la requête (retirer les accents)
    const normalizedQuery = normalizeText(query);

    // Extraire les mots de la requête
    const queryWords = normalizedQuery.split(/\s+/).filter(w => w.length >= 2);

    // Utiliser l'index inversé pour trouver les procédures candidates
    const candidateScores = {};  // Map: procedureId -> score

    queryWords.forEach(queryWord => {
        // Pour chaque mot de la requête, trouver les procédures qui contiennent ce mot ou un mot similaire
        Object.keys(procedureSearchIndex.invertedIndex).forEach(indexWord => {
            if (indexWord.includes(queryWord) || queryWord.includes(indexWord)) {
                const procedureIds = procedureSearchIndex.invertedIndex[indexWord];
                procedureIds.forEach(id => {
                    if (!candidateScores[id]) {
                        candidateScores[id] = 0;
                    }
                    // Score basé sur la longueur du match (match exact = meilleur score)
                    const matchQuality = Math.min(indexWord.length, queryWord.length) /
                                       Math.max(indexWord.length, queryWord.length);
                    candidateScores[id] += matchQuality;
                });
            }
        });
    });

    // Calculer un score détaillé pour chaque candidat
    const scoredResults = Object.entries(candidateScores).map(([id, baseScore]) => {
        const proc = procedureSearchIndex.procedureMap[id];
        let detailedScore = baseScore;

        // Bonus pour match dans le titre
        const titleNorm = normalizeText(proc.title || '');
        if (titleNorm.includes(normalizedQuery)) {
            detailedScore += 10;  // Bonus important pour match exact dans titre
        }
        queryWords.forEach(word => {
            if (titleNorm.includes(word)) {
                detailedScore += 3;  // Bonus pour chaque mot dans titre
            }
        });

        // Bonus pour match dans catégorie
        const categoryNorm = normalizeText(proc.category || '');
        if (categoryNorm.includes(normalizedQuery)) {
            detailedScore += 5;
        }

        // Bonus pour match dans keywords
        const keywordsText = (proc.keywords || []).map(k => normalizeText(k)).join(' ');
        queryWords.forEach(word => {
            if (keywordsText.includes(word)) {
                detailedScore += 2;
            }
        });

        // Bonus pour popularité (usage_count et feedback positif)
        detailedScore += (proc.usage_count || 0) * 0.1;
        detailedScore += (proc.positive_feedback_count || 0) * 0.5;

        return {
            procedure: proc,
            score: detailedScore
        };
    });

    // Trier par score décroissant
    scoredResults.sort((a, b) => b.score - a.score);

    // Prendre les 10 meilleurs résultats
    const results = scoredResults.slice(0, 10).map(r => r.procedure);
    const limitedResults = results;

    if (limitedResults.length === 0) {
        resultsContainer.innerHTML = `
            <div class="procedure-search-empty">
                <div class="procedure-search-empty-icon">🔍</div>
                <div>Aucune procédure trouvée</div>
            </div>
        `;
    } else {
        resultsContainer.innerHTML = limitedResults.map(proc =>
            renderProcedureSearchItem(proc, query)
        ).join('');
    }

    resultsContainer.classList.add('show');
}

// Afficher un item de résultat
function renderProcedureSearchItem(procedure, query) {
    const categoryIcon = getCategoryIconSync(procedure.category);
    const categoryLabel = formatCategoryLabel(procedure.category);

    // Mettre en surbrillance les mots correspondants
    const highlightedTitle = highlightText(procedure.title || 'Sans titre', query);
    const description = procedure.description || '';
    const truncatedDesc = description.length > 100
        ? description.substring(0, 100) + '...'
        : description;

    return `
        <div class="procedure-search-item" onclick="openProcedureDetails(${procedure.id})">
            <div class="procedure-search-title">${highlightedTitle}</div>
            <div>
                <span class="procedure-search-category">${categoryIcon} ${categoryLabel}</span>
            </div>
            ${truncatedDesc ? `<div class="procedure-search-description">${escapeHtml(truncatedDesc)}</div>` : ''}
        </div>
    `;
}

// Mettre en surbrillance le texte
function highlightText(text, query) {
    if (!text || !query) return escapeHtml(text);

    const escapedText = escapeHtml(text);
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return escapedText.replace(regex, '<span class="highlight">$1</span>');
}

// Échapper les caractères spéciaux de regex
function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Obtenir l'icône de catégorie (version synchrone avec cache)
function getCategoryIconSync(categoryName) {
    const icons = {
        'installation_logiciel': '💿',
        'depannage_materiel': '🔧',
        'demande_licence': '🔑',
        'support_applicatif': '💻',
        'reseau': '🌐',
        'securite': '🔒',
        'autre': '📋'
    };
    return icons[categoryName] || '📋';
}

// Formater le label de catégorie
function formatCategoryLabel(name) {
    const labels = {
        'installation_logiciel': 'Installation logiciel',
        'depannage_materiel': 'Dépannage matériel',
        'demande_licence': 'Demande de licence',
        'support_applicatif': 'Support applicatif',
        'reseau': 'Réseau',
        'securite': 'Sécurité',
        'autre': 'Autre'
    };
    return labels[name] || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Ouvrir les détails d'une procédure
function openProcedureDetails(procedureId) {
    // Fermer les résultats de recherche
    const resultsContainer = document.getElementById('procedure-search-results');
    resultsContainer.classList.remove('show');

    // Vider le champ de recherche
    const searchInput = document.getElementById('procedureQuickSearchInput');
    if (searchInput) searchInput.value = '';

    // Ouvrir l'éditeur de procédure
    editProcedure(procedureId);
}

// Afficher les résultats au focus
function showProcedureSearchResults() {
    const searchInput = document.getElementById('procedureQuickSearchInput');
    const query = searchInput?.value?.trim();

    if (query && query.length > 0) {
        const resultsContainer = document.getElementById('procedure-search-results');
        if (resultsContainer.children.length > 0) {
            resultsContainer.classList.add('show');
        }
    }
}

// Cacher les résultats si on clique ailleurs
document.addEventListener('click', (e) => {
    const searchContainer = document.querySelector('.procedure-search-container');
    if (searchContainer && !searchContainer.contains(e.target)) {
        const resultsContainer = document.getElementById('procedure-search-results');
        resultsContainer.classList.remove('show');
    }
});

// Charger les procédures au démarrage
loadAllProcedures();


// ============================================
// INTERFACE PROCÉDURES MODERNE (Style Claude.ai)
// ============================================

// Charger et afficher toutes les procédures
async function loadProceduresModern() {
    try {
        const procedures = await api.getProcedures();
        renderProcedureListModern(procedures);
        updateProcedureCount(procedures.length);
    } catch (error) {
        console.error('Error loading procedures:', error);
        showNotification('❌ Erreur lors du chargement des procédures', 'error');
    }
}

// Afficher la liste des procédures
function renderProcedureListModern(procedures) {
    const listContainer = document.getElementById('procedure-list');

    if (!procedures || procedures.length === 0) {
        listContainer.innerHTML = '<div class="procedure-empty-state"><div class="empty-state-icon">📖</div><div class="empty-state-text">Aucune procédure trouvée</div><div class="empty-state-subtext">Créez votre première procédure ou importez-en depuis un fichier</div></div>';
        return;
    }

    // Trier par usage récent (usage_count desc)
    const sortedProcedures = procedures.sort((a, b) => {
        return (b.usage_count || 0) - (a.usage_count || 0);
    });

    listContainer.innerHTML = sortedProcedures.map(proc => createProcedureItemHTML(proc)).join('');
}

// Créer le HTML d'un item de procédure
function createProcedureItemHTML(procedure) {
    const timestamp = getRelativeTime(procedure.updated_at || procedure.created_at);
    const usageCount = procedure.usage_count || 0;
    const positiveFeedback = procedure.positive_feedback_count || 0;
    const negativeFeedback = procedure.negative_feedback_count || 0;
    const totalFeedback = positiveFeedback + negativeFeedback;
    const successRate = totalFeedback > 0 ? Math.round((positiveFeedback / totalFeedback) * 100) : null;

    let html = '<div class="procedure-item" onclick="viewProcedureDetails(' + procedure.id + ')">';
    html += '<h3 class="procedure-item-title">' + escapeHtml(procedure.title || 'Sans titre') + '</h3>';
    html += '<div class="procedure-item-meta">';
    html += '<span class="procedure-item-timestamp">Dernier message il y a ' + timestamp + '</span>';

    if (procedure.category) {
        html += '<span class="procedure-item-category">📁 ' + escapeHtml(procedure.category) + '</span>';
    }

    html += '<div class="procedure-item-stats">';

    if (usageCount > 0) {
        html += '<span class="procedure-stat" title="Nombre d\'utilisations">';
        html += '<span class="procedure-stat-icon">👁️</span>';
        html += '<span>' + usageCount + '</span>';
        html += '</span>';
    }

    if (successRate !== null) {
        const icon = successRate >= 80 ? '✅' : (successRate >= 50 ? '👍' : '👎');
        html += '<span class="procedure-stat" title="Taux de succès">';
        html += '<span class="procedure-stat-icon">' + icon + '</span>';
        html += '<span>' + successRate + '%</span>';
        html += '</span>';
    }

    html += '</div></div></div>';
    return html;
}

// Calculer le temps relatif
function getRelativeTime(dateString) {
    if (!dateString) return 'date inconnue';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return "à l'instant";
    if (diffMinutes < 60) return diffMinutes + ' minute' + (diffMinutes > 1 ? 's' : '');
    if (diffHours < 24) return diffHours + ' heure' + (diffHours > 1 ? 's' : '');
    if (diffDays < 7) return diffDays + ' jour' + (diffDays > 1 ? 's' : '');
    if (diffDays < 30) return Math.floor(diffDays / 7) + ' semaine' + (Math.floor(diffDays / 7) > 1 ? 's' : '');
    return Math.floor(diffDays / 30) + ' mois';
}

// Mettre à jour le compteur de procédures
function updateProcedureCount(count) {
    const countElement = document.getElementById('procedure-count');
    if (countElement) {
        countElement.textContent = count + ' procédure' + (count > 1 ? 's' : '');
    }
}

// Recherche moderne avec debounce
let searchModernTimeout = null;
function searchProceduresModern(query) {
    clearTimeout(searchModernTimeout);

    searchModernTimeout = setTimeout(async () => {
        if (!query || query.trim().length === 0) {
            loadProceduresModern();
            return;
        }

        try {
            if (procedureSearchIndex.lastUpdate) {
                performModernSearch(query.trim());
            } else {
                const procedures = await api.getProcedures();
                const filtered = procedures.filter(proc => {
                    const searchText = (proc.title + ' ' + proc.description + ' ' + proc.category).toLowerCase();
                    return searchText.includes(query.toLowerCase());
                });
                renderProcedureListModern(filtered);
                updateProcedureCount(filtered.length);
            }
        } catch (error) {
            console.error('Error searching procedures:', error);
        }
    }, 300);
}

// Recherche utilisant l'index inversé
function performModernSearch(query) {
    const normalizedQuery = normalizeText(query);
    const queryWords = normalizedQuery.split(/\s+/).filter(w => w.length >= 2);

    const candidateScores = {};

    queryWords.forEach(queryWord => {
        Object.keys(procedureSearchIndex.invertedIndex).forEach(indexWord => {
            if (indexWord.includes(queryWord) || queryWord.includes(indexWord)) {
                const procedureIds = procedureSearchIndex.invertedIndex[indexWord];
                procedureIds.forEach(id => {
                    if (!candidateScores[id]) candidateScores[id] = 0;
                    const matchQuality = Math.min(indexWord.length, queryWord.length) / Math.max(indexWord.length, queryWord.length);
                    candidateScores[id] += matchQuality;
                });
            }
        });
    });

    const results = Object.keys(candidateScores).map(id => {
        return procedureSearchIndex.procedureMap[id];
    });

    renderProcedureListModern(results);
    updateProcedureCount(results.length);
}

// Voir les détails d'une procédure
function viewProcedureDetails(procedureId) {
    openProcedureModal(procedureId);
}

// Ouvrir le modal de création de procédure
function openCreateProcedureModal() {
    const modal = document.getElementById('procedureModal');
    const modalTitle = document.getElementById('procedureModalTitle');
    const form = document.getElementById('procedureForm');

    form.reset();
    document.getElementById('procedureId').value = '';
    modalTitle.textContent = 'Créer une procédure';
    modal.style.display = 'flex';
}

// Ouvrir le modal de procédure en mode lecture
async function openProcedureModal(procedureId) {
    try {
        const procedure = await api.getProcedure(procedureId);

        const modal = document.getElementById('procedureModal');
        const modalTitle = document.getElementById('procedureModalTitle');

        document.getElementById('procedureId').value = procedure.id;
        document.getElementById('procedureTitle').value = procedure.title || '';
        document.getElementById('procedureCategory').value = procedure.category || '';
        document.getElementById('procedureDescription').value = procedure.description || '';
        document.getElementById('procedureKeywords').value = (procedure.keywords || []).join(', ');

        const stepsContainer = document.getElementById('procedureSteps');
        if (stepsContainer && procedure.steps) {
            stepsContainer.innerHTML = procedure.steps.map((step, index) => {
                return '<div class="step-item"><span class="step-number">' + (index + 1) + '</span><input type="text" value="' + escapeHtml(step) + '" class="form-control"></div>';
            }).join('');
        }

        modalTitle.textContent = 'Détails de la procédure';
        modal.style.display = 'flex';

    } catch (error) {
        console.error('Error loading procedure details:', error);
        showNotification('❌ Erreur lors du chargement de la procédure', 'error');
    }
}

// Mode sélection
let selectionMode = false;
function toggleProcedureSelection() {
    selectionMode = !selectionMode;
    const listContainer = document.getElementById('procedure-list');
    const btn = document.querySelector('.btn-select-procedures');

    if (selectionMode) {
        listContainer.classList.add('selection-mode');
        btn.textContent = 'Annuler';
    } else {
        listContainer.classList.remove('selection-mode');
        btn.textContent = 'Sélectionner';
    }
}

// Helper: Échapper le HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Charger les procédures au démarrage
document.addEventListener('DOMContentLoaded', () => {
    loadProceduresModern();
});
