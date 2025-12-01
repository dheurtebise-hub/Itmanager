// Gestion du modal de détail de ticket

let currentTicket = null;

async function openTicketModal(ticketId) {
    try {
        const ticket = await api.getTicket(ticketId);
        currentTicket = ticket;

        const modal = document.getElementById('ticketModal');
        const detailsDiv = document.getElementById('ticketDetails');

        detailsDiv.innerHTML = renderTicketDetails(ticket);
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading ticket:', error);
        alert('Erreur lors du chargement du ticket');
    }
}

function closeTicketModal() {
    const modal = document.getElementById('ticketModal');
    modal.style.display = 'none';
    currentTicket = null;
}

function getSenderColor(sender) {
    // Générer une couleur cohérente pour chaque expéditeur
    const colors = [
        '#E3F2FD', // Bleu clair
        '#F3E5F5', // Violet clair
        '#E8F5E9', // Vert clair
        '#FFF3E0', // Orange clair
        '#FCE4EC', // Rose clair
        '#E0F2F1', // Cyan clair
    ];

    // Hash simple du nom pour choisir une couleur
    let hash = 0;
    for (let i = 0; i < sender.length; i++) {
        hash = sender.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colors.length;
    return colors[index];
}

function getSenderInitials(sender) {
    // Extraire les initiales du nom
    const words = sender.trim().split(/\s+/);
    if (words.length >= 2) {
        return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    }
    return sender.substring(0, 2).toUpperCase();
}

function renderEmailThread(ticket) {
    const messages = ticket.messages || [];

    if (messages.length === 0) {
        return '<div class="chat-message">Pas de contenu</div>';
    }

    // Afficher les messages dans l'ordre chronologique (plus ancien en haut)
    return messages.reverse().map((msg, index) => {
        const sender = msg.sender || 'Inconnu';
        const content = msg.content || msg;
        const bgColor = getSenderColor(sender);
        const initials = getSenderInitials(sender);
        const isLatest = index === messages.length - 1;

        return `
        <div class="chat-message" style="background: ${bgColor}; ${isLatest ? 'border-left: 3px solid #2196F3;' : ''}">
            <div class="chat-message-header">
                <div class="chat-avatar">${initials}</div>
                <div class="chat-sender">${escapeHtml(sender)}</div>
            </div>
            <div class="chat-message-content">
                ${escapeHtml(typeof content === 'string' ? content : JSON.stringify(content)).replace(/\n/g, '<br>')}
            </div>
        </div>
    `;
    }).join('');
}

function renderTicketDetails(ticket) {
    const statusOptions = [
        { value: 'new', label: '📥 Nouveau' },
        { value: 'in_progress', label: '⚙️ En cours' },
        { value: 'resolved', label: '✅ Résolu' },
        { value: 'closed', label: '🔒 Fermé' }
    ];

    const priorityOptions = [
        { value: 'urgent', label: '🔴 Urgent' },
        { value: 'high', label: '🟠 Élevée' },
        { value: 'medium', label: '🟡 Moyenne' },
        { value: 'low', label: '🟢 Faible' }
    ];

    return `
        <h2>Ticket #${ticket.id}</h2>

        <div class="form-group">
            <label><strong>Sujet</strong></label>
            <div>${escapeHtml(ticket.subject)}</div>
        </div>

        <div class="form-group">
            <label><strong>De</strong></label>
            <div>${escapeHtml(ticket.sender_name || ticket.sender_email)}</div>
            <div class="form-help">${escapeHtml(ticket.sender_email)}</div>
        </div>

        <div class="form-group">
            <label><strong>Reçu le</strong></label>
            <div>${new Date(ticket.received_date).toLocaleString('fr-FR')}</div>
        </div>

        <div class="form-group">
            <label><strong>Statut</strong></label>
            <select id="ticketStatus" onchange="updateTicketField('status', this.value)">
                ${statusOptions.map(opt =>
                    `<option value="${opt.value}" ${ticket.status === opt.value ? 'selected' : ''}>${opt.label}</option>`
                ).join('')}
            </select>
        </div>

        <div class="form-group">
            <label><strong>Priorité</strong></label>
            <select id="ticketPriority" onchange="updateTicketField('priority', this.value)">
                ${priorityOptions.map(opt =>
                    `<option value="${opt.value}" ${ticket.priority === opt.value ? 'selected' : ''}>${opt.label}</option>`
                ).join('')}
            </select>
        </div>

        ${ticket.category ? `
        <div class="form-group">
            <label><strong>Catégorie</strong></label>
            <div>${escapeHtml(ticket.category)}</div>
            ${ticket.ai_confidence ? `
                <div class="form-help">Catégorisé par IA (confiance: ${Math.round(ticket.ai_confidence * 100)}%)</div>
            ` : ''}
        </div>
        ` : ''}

        ${ticket.summary ? `
        <div class="form-group">
            <label><strong>Résumé</strong></label>
            <div>${escapeHtml(ticket.summary)}</div>
        </div>
        ` : ''}

        <div class="form-group">
            <label><strong>Conversation</strong></label>
            <div class="email-thread-container">
                ${renderEmailThread(ticket)}
            </div>
        </div>

        ${ticket.resolution ? `
        <div class="form-group">
            <label><strong>Résolution</strong></label>
            <textarea id="ticketResolution" rows="4" onchange="updateTicketField('resolution', this.value)">${escapeHtml(ticket.resolution)}</textarea>
        </div>
        ` : `
        <div class="form-group">
            <label><strong>Résolution</strong></label>
            <textarea id="ticketResolution" rows="4" placeholder="Décrivez la résolution..." onchange="updateTicketField('resolution', this.value)"></textarea>
        </div>
        `}

        <div class="form-group">
            <button class="btn btn-primary" onclick="getSuggestion(${ticket.id})">
                🤖 Obtenir une suggestion IA
            </button>
            <div id="suggestionResult" class="mt-2"></div>
        </div>

        <div class="flex gap-2 mt-3">
            <button class="btn btn-secondary" onclick="closeTicketModal()">Fermer</button>
            ${ticket.status !== 'closed' ? `
                <button class="btn btn-success" onclick="resolveTicket(${ticket.id})">✅ Marquer comme résolu</button>
            ` : ''}
        </div>
    `;
}

async function updateTicketField(field, value) {
    if (!currentTicket) return;

    try {
        await api.updateTicket(currentTicket.id, { [field]: value });
        await loadTickets(); // Recharger les tickets
        currentTicket[field] = value;
    } catch (error) {
        console.error('Error updating ticket:', error);
        alert('Erreur lors de la mise à jour');
    }
}

async function getSuggestion(ticketId) {
    const resultDiv = document.getElementById('suggestionResult');
    resultDiv.innerHTML = '<div class="loading"></div> Génération de la suggestion...';

    try {
        const data = await api.getSuggestion(ticketId);
        resultDiv.innerHTML = `
            <div class="card" style="background: var(--bg-tertiary); white-space: pre-wrap;">
                ${escapeHtml(data.suggestion)}
            </div>
        `;
    } catch (error) {
        console.error('Error getting suggestion:', error);
        resultDiv.innerHTML = '<div class="status-message status-error">Erreur lors de la génération de la suggestion</div>';
    }
}

async function resolveTicket(ticketId) {
    const resolution = document.getElementById('ticketResolution')?.value;

    if (!resolution || resolution.trim() === '') {
        alert('Veuillez entrer une résolution avant de marquer le ticket comme résolu');
        return;
    }

    try {
        await api.updateTicket(ticketId, {
            status: 'resolved',
            resolution: resolution.trim()
        });

        await loadTickets();
        closeTicketModal();
    } catch (error) {
        console.error('Error resolving ticket:', error);
        alert('Erreur lors de la résolution du ticket');
    }
}

// Fermer le modal avec Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTicketModal();
    }
});
