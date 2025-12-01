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
    const statuses = ['new', 'in_progress', 'resolved', 'closed'];

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
    const priorityBadge = getPriorityBadge(ticket.priority);
    const slaIndicator = getSLAIndicator(ticket.sla_status);
    const timeAgo = formatTimeAgo(ticket.received_date);

    return `
        <div class="ticket-card" onclick="openTicketModal(${ticket.id})">
            <div class="ticket-header">
                <span class="ticket-id">#${ticket.id}</span>
                ${priorityBadge}
            </div>
            <div class="ticket-subject">${escapeHtml(ticket.subject)}</div>
            ${ticket.summary ? `<div class="ticket-summary">${escapeHtml(ticket.summary)}</div>` : ''}
            <div class="ticket-meta">
                <div class="ticket-sender">
                    <span>👤</span>
                    <span>${escapeHtml(ticket.sender_email)}</span>
                </div>
                <span>${timeAgo}</span>
            </div>
            <div class="ticket-footer">
                ${ticket.category ? `<span class="category-tag">${ticket.category}</span>` : ''}
                ${slaIndicator}
            </div>
        </div>
    `;
}

function getPriorityBadge(priority) {
    const badges = {
        urgent: '<span class="badge badge-urgent">🔴 Urgent</span>',
        high: '<span class="badge badge-high">🟠 Élevée</span>',
        medium: '<span class="badge badge-medium">🟡 Moyenne</span>',
        low: '<span class="badge badge-low">🟢 Faible</span>',
    };
    return badges[priority] || '';
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
async function syncNow() {
    const button = document.querySelector('button[onclick="syncNow()"]');
    const icon = document.getElementById('syncIcon');

    if (button) button.disabled = true;
    if (icon) icon.innerHTML = '<span class="loading"></span>';

    try {
        await api.syncNow();
        await loadTickets();
        await loadStats();
    } catch (error) {
        alert('Erreur lors de la synchronisation');
    } finally {
        if (button) button.disabled = false;
        if (icon) icon.textContent = '🔄';
    }
}

// Stats
async function loadStats() {
    try {
        const stats = await api.getStats();

        document.getElementById('stat-today').textContent = stats.today || 0;
        document.getElementById('stat-week').textContent = stats.this_week || 0;

        if (stats.sla_report) {
            document.getElementById('stat-sla').textContent =
                `${stats.sla_report.sla_compliance_rate || 0}%`;
        }

        if (stats.api_cost_this_month !== undefined) {
            document.getElementById('stat-cost').textContent =
                `${stats.api_cost_this_month.toFixed(2)}€`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function showStats() {
    alert('Statistiques détaillées à venir dans une prochaine version');
}

// Export
function exportTickets(format) {
    const category = document.getElementById('categoryFilter')?.value || '';
    const priority = document.getElementById('priorityFilter')?.value || '';

    const filters = {};
    if (category) filters.category = category;
    if (priority) filters.priority = priority;

    const url = api.getExportURL(format, filters);
    window.open(url, '_blank');
}
