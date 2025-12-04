// Gestion du modal de détail de ticket

let currentTicket = null;

async function openTicketModal(ticketId) {
    try {
        const ticket = await api.getTicket(ticketId);
        currentTicket = ticket;

        const modal = document.getElementById('ticketModal');
        const detailsDiv = document.getElementById('ticketDetails');

        detailsDiv.innerHTML = await renderTicketDetails(ticket);
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

    // Utiliser le body complet comme demande initiale si pas de messages parsés
    const requestContent = messages.length > 0 && messages[messages.length - 1]
        ? (messages[messages.length - 1].content || messages[messages.length - 1])
        : (ticket.body || 'Pas de contenu');

    const sender = ticket.sender_name || ticket.sender_email || 'Demandeur';
    const initials = getSenderInitials(sender);
    const aiSummary = ticket.summary;

    let html = '';

    // Afficher la demande initiale
    html += `
    <div class="request-section">
        <div class="section-label">📩 Demande initiale</div>
        <div class="chat-message" style="background: #E3F2FD; border-left: 3px solid #2196F3;">
            <div class="chat-message-header">
                <div class="chat-avatar">${initials}</div>
                <div class="chat-sender">${escapeHtml(sender)}</div>
            </div>
            <div class="chat-message-content">
                ${escapeHtml(requestContent).replace(/\n/g, '<br>')}
            </div>
        </div>
    </div>
    `;

    // Afficher le résumé IA seulement s'il existe ET qu'il est différent du sujet
    if (aiSummary && aiSummary !== ticket.subject && aiSummary.length > 10) {
        html += `
        <div class="request-section">
            <div class="section-label">🤖 Reformulation IA</div>
            <div class="chat-message ai-reformulation" style="background: #F3E5F5; border-left: 3px solid #9C27B0;">
                <div class="chat-message-header">
                    <div class="chat-avatar">🤖</div>
                    <div class="chat-sender">Assistant IA</div>
                </div>
                <div class="chat-message-content">
                    ${escapeHtml(aiSummary).replace(/\n/g, '<br>')}
                </div>
            </div>
        </div>
        `;
    }

    return html;
}

async function renderTicketDetails(ticket) {
    const statusOptions = [
        { value: 'new', label: '📥 Nouveau' },
        { value: 'in_progress', label: '⚙️ En cours' },
        { value: 'resolved', label: '✅ Résolu' }
    ];

    // Charger les catégories pour le select
    const categories = await getCategories();

    return `
        <div class="ticket-modal-header">
            <h2>Ticket #${ticket.id}</h2>
        </div>

        <div class="ticket-modal-columns">
            <!-- Colonne gauche: Métadonnées -->
            <div class="ticket-metadata">
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
                    <label><strong>Catégorie</strong></label>
                    <select id="ticketCategory" onchange="updateTicketField('category', this.value)">
                        ${!ticket.category ? '<option value="">-- Sélectionner une catégorie --</option>' : ''}
                        ${categories.map(cat =>
                            `<option value="${cat.name}" ${ticket.category === cat.name ? 'selected' : ''}>${cat.icon} ${cat.label}</option>`
                        ).join('')}
                    </select>
                    ${ticket.ai_confidence ? `
                        <div class="form-help">Catégorisé par IA (${Math.round(ticket.ai_confidence * 100)}%)</div>
                    ` : ''}
                </div>

                <div class="flex gap-2 mt-3">
                    <button class="btn btn-secondary" onclick="closeTicketModal()">Fermer</button>
                    ${ticket.status === 'new' ? `
                        <button class="btn btn-primary" onclick="markAsInProgress(${ticket.id})">⚙️ Marquer comme En cours</button>
                    ` : ''}
                    ${ticket.status === 'in_progress' ? `
                        <button class="btn btn-success" onclick="resolveTicket(${ticket.id})">✅ Marquer comme résolu</button>
                    ` : ''}
                </div>
            </div>

            <!-- Colonne droite: Conversation -->
            <div class="ticket-conversation">
                <div class="conversation-header">
                    <label><strong>Conversation</strong></label>
                </div>
                <div class="email-thread-container">
                    ${renderEmailThread(ticket)}
                </div>
            </div>
        </div>
    `;
}

async function updateTicketField(field, value) {
    if (!currentTicket) return;

    try {
        await api.updateTicket(currentTicket.id, { [field]: value });
        await loadTickets(); // Recharger les tickets
        currentTicket[field] = value;

        // Afficher un message de confirmation
        const fieldLabels = {
            'status': 'Statut',
            'category': 'Catégorie',
            'priority': 'Priorité'
        };
        const fieldLabel = fieldLabels[field] || field;
        showNotification(`${fieldLabel} mis à jour avec succès`, 'success');
    } catch (error) {
        console.error('Error updating ticket:', error);
        showNotification('Erreur lors de la mise à jour', 'error');
    }
}

async function markAsInProgress(ticketId) {
    try {
        const updates = {
            status: 'in_progress'
        };

        await api.updateTicket(ticketId, updates);
        showNotification('Ticket marqué comme En cours', 'success');

        await loadTickets();
        closeTicketModal();
    } catch (error) {
        console.error('Error marking ticket as in progress:', error);
        showNotification('Erreur lors de la mise à jour du ticket', 'error');
        alert(`Erreur: ${error.message || 'Impossible de mettre à jour le ticket'}`);
    }
}

async function resolveTicket(ticketId) {
    const confirm = window.confirm('Marquer ce ticket comme résolu ?');
    if (!confirm) return;

    try {
        const updates = {
            status: 'resolved'
        };

        await api.updateTicket(ticketId, updates);
        showNotification('Ticket marqué comme résolu', 'success');

        await loadTickets();
        closeTicketModal();
    } catch (error) {
        console.error('Error resolving ticket:', error);
        showNotification('Erreur lors de la résolution du ticket', 'error');
        alert(`Erreur: ${error.message || 'Impossible de résoudre le ticket'}`);
    }
}

// Fermer le modal avec Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTicketModal();
    }
});
