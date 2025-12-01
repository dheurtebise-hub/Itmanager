"""
Routes API pour les tickets
"""

from flask import Blueprint, request, jsonify
from models.database import db
from models.ticket import Ticket
from services.ai_service import ai_service
from services.sla_service import sla_service
from services.sync_service import sync_service
from utils.rate_limiter import rate_limit

ticket_bp = Blueprint('tickets', __name__)

@ticket_bp.route('/api/tickets', methods=['GET'])
@rate_limit()
def get_tickets():
    """Liste les tickets avec pagination et filtres."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    status = request.args.get('status')
    category = request.args.get('category')
    priority = request.args.get('priority')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'received_date')
    sort_order = request.args.get('sort_order', 'desc')

    allowed_sort = ['received_date', 'created_at', 'priority', 'status']
    if sort_by not in allowed_sort:
        sort_by = 'received_date'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'

    query = "SELECT * FROM tickets WHERE 1=1"
    count_query = "SELECT COUNT(*) as total FROM tickets WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)

    if category:
        query += " AND category = ?"
        count_query += " AND category = ?"
        params.append(category)

    if priority:
        query += " AND priority = ?"
        count_query += " AND priority = ?"
        params.append(priority)

    if search:
        pattern = f"%{search}%"
        query += " AND (subject LIKE ? OR summary LIKE ? OR sender_email LIKE ?)"
        count_query += " AND (subject LIKE ? OR summary LIKE ? OR sender_email LIKE ?)"
        params.extend([pattern, pattern, pattern])

    total = db.fetchone(count_query, tuple(params))['total']

    query += f" ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    tickets = db.fetchall(query, tuple(params))

    # Ajouter le statut SLA à chaque ticket
    for ticket in tickets:
        ticket['sla_status'] = sla_service.check_sla_status(ticket)

    return jsonify({
        'tickets': tickets,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@ticket_bp.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Récupère un ticket par son ID."""
    ticket = Ticket.get_by_id(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket non trouvé'}), 404

    ticket['sla_status'] = sla_service.check_sla_status(ticket)
    return jsonify(ticket)

@ticket_bp.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Met à jour un ticket."""
    data = request.json

    allowed = ['status', 'category', 'priority', 'resolution', 'summary']
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({'error': 'Aucun champ à mettre à jour'}), 400

    success = Ticket.update(ticket_id, updates)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Erreur mise à jour'}), 500

@ticket_bp.route('/api/tickets/<int:ticket_id>/suggest', methods=['GET'])
def get_suggestion(ticket_id):
    """Génère une suggestion de résolution."""
    ticket = Ticket.get_by_id(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket non trouvé'}), 404

    # Chercher des tickets similaires résolus
    similar = Ticket.get_similar(ticket_id, limit=3)

    # Chercher dans la base de connaissances
    knowledge = db.fetchall("""
        SELECT * FROM knowledge_base
        WHERE category = ? ORDER BY usage_count DESC LIMIT 3
    """, (ticket['category'],))

    suggestion = ai_service.suggest_resolution(ticket, similar, knowledge)

    return jsonify({'suggestion': suggestion})

@ticket_bp.route('/api/tickets/stats', methods=['GET'])
def get_stats():
    """Retourne les statistiques des tickets."""
    stats = {
        'by_status': db.fetchall("""
            SELECT status, COUNT(*) as count FROM tickets GROUP BY status
        """),
        'by_category': db.fetchall("""
            SELECT category, COUNT(*) as count FROM tickets GROUP BY category
        """),
        'by_priority': db.fetchall("""
            SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority
        """),
        'today': db.fetchone("""
            SELECT COUNT(*) as count FROM tickets WHERE date(created_at) = date('now')
        """)['count'],
        'this_week': db.fetchone("""
            SELECT COUNT(*) as count FROM tickets
            WHERE created_at >= date('now', '-7 days')
        """)['count'],
        'sla_report': sla_service.get_sla_report(30),
        'api_cost_this_month': ai_service.get_monthly_cost()
    }

    return jsonify(stats)

@ticket_bp.route('/api/sync', methods=['POST'])
def sync_now():
    """Déclenche une synchronisation manuelle."""
    result = sync_service.sync_now()
    return jsonify(result)

@ticket_bp.route('/api/sync/status', methods=['GET'])
def sync_status():
    """Retourne le statut de la synchronisation."""
    return jsonify({
        'is_running': sync_service.is_running(),
        'is_syncing': sync_service._is_syncing
    })
