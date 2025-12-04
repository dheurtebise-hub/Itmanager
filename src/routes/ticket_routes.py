"""
Routes API pour les tickets
"""

import re
from flask import Blueprint, request, jsonify
from models.database import db
from models.ticket import Ticket
from services.ai_service import ai_service
from services.sla_service import sla_service
from services.sync_service import sync_service
from utils.rate_limiter import rate_limit

ticket_bp = Blueprint('tickets', __name__)

def clean_message_content(text: str) -> str:
    """Nettoie le contenu d'un message en supprimant les espaces excessifs."""
    if not text:
        return text

    # Supprimer les lignes qui ne contiennent que des espaces
    lines = [line.rstrip() for line in text.split('\n')]

    # Filtrer les lignes vides consécutives
    cleaned_lines = []
    previous_was_empty = False

    for line in lines:
        is_empty = len(line.strip()) == 0

        # Garder la ligne si elle n'est pas vide, ou si c'est la première ligne vide
        if not is_empty:
            cleaned_lines.append(line)
            previous_was_empty = False
        elif not previous_was_empty:
            # Garder une seule ligne vide maximum
            cleaned_lines.append('')
            previous_was_empty = True

    # Rejoindre et enlever les espaces au début/fin
    result = '\n'.join(cleaned_lines).strip()

    # Supprimer les doubles sauts de ligne
    result = re.sub(r'\n\n+', '\n', result)

    return result

def parse_email_thread(body: str) -> list:
    """Parse le corps de l'email en messages séparés avec identification des expéditeurs."""
    if not body:
        return []

    # Patterns de séparation d'emails avec capture de l'expéditeur
    separator_pattern = r'^(?:De|From)\s*:\s*(.+?)(?:\s*<[^>]+>)?$'

    # Diviser le texte en sections
    messages = []
    current_message = []
    current_sender = None

    lines = body.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Vérifier si c'est une ligne "De:" ou "From:"
        match = re.match(separator_pattern, line.strip(), re.IGNORECASE)
        if match:
            # Sauvegarder le message précédent
            if current_message:
                msg_text = '\n'.join(current_message).strip()
                msg_text = clean_message_content(msg_text)
                if msg_text and len(msg_text) > 5:
                    messages.append({
                        'sender': current_sender or 'Inconnu',
                        'content': msg_text
                    })

            # Nouveau message
            current_sender = match.group(1).strip()
            current_message = []

            # Sauter les lignes d'en-tête (Envoyé:, À:, Objet:, etc.)
            i += 1
            while i < len(lines) and re.match(r'^(?:Envoyé|Sent|À|To|Objet|Subject|Cc)\s*:', lines[i].strip(), re.IGNORECASE):
                i += 1
            continue

        # Ignorer les lignes de séparation
        if re.match(r'^[_-]{5,}$', line.strip()):
            i += 1
            continue

        current_message.append(line)
        i += 1

    # Ajouter le dernier message
    if current_message:
        msg_text = '\n'.join(current_message).strip()
        msg_text = clean_message_content(msg_text)
        if msg_text and len(msg_text) > 5:
            messages.append({
                'sender': current_sender or 'Expéditeur',
                'content': msg_text
            })

    # Si aucun message parsé, retourner le corps entier sans expéditeur identifié
    if not messages:
        clean_body = clean_message_content(body.strip())
        messages = [{
            'sender': 'Message',
            'content': clean_body
        }]

    return messages

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

    # Ajouter le statut SLA à tous les tickets (batch processing pour performance)
    tickets = sla_service.check_sla_status_batch(tickets)

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

    # Parser le corps en messages séparés pour affichage type conversation
    if ticket.get('body'):
        ticket['messages'] = parse_email_thread(ticket['body'])
    else:
        ticket['messages'] = []

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

@ticket_bp.route('/api/tickets/<int:ticket_id>/mark-not-user-request', methods=['POST'])
def mark_not_user_request(ticket_id):
    """Marque un ticket comme non-demande utilisateur et le déplace dans App-à trier."""
    from services.outlook_folder_manager import folder_manager

    ticket = Ticket.get_by_id(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket non trouvé'}), 404

    # Mettre à jour le ticket
    updates = {
        'status': 'resolved',
        'is_not_user_request': True,
        'resolution': 'Marqué comme non-demande utilisateur'
    }

    success = Ticket.update(ticket_id, updates)
    if not success:
        return jsonify({'error': 'Erreur lors de la mise à jour du ticket'}), 500

    # Déplacer l'email dans le dossier "App-à trier"
    if ticket.get('message_id'):
        try:
            move_success, move_msg = folder_manager.move_email_to_non_user_request(ticket['message_id'])
            if not move_success:
                return jsonify({
                    'success': True,
                    'warning': f'Ticket mis à jour mais email non déplacé: {move_msg}'
                }), 200
        except Exception as e:
            return jsonify({
                'success': True,
                'warning': f'Ticket mis à jour mais erreur déplacement email: {str(e)}'
            }), 200

    return jsonify({
        'success': True,
        'message': 'Ticket marqué comme non-demande utilisateur'
    }), 200

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
    try:
        data = request.json or {}
        initial_import = data.get('initial_import', False)
        import_limit = data.get('import_limit', 50)

        result = sync_service.sync_now(
            initial_import=initial_import,
            import_limit=import_limit
        )

        # Retourner un statut HTTP approprié selon le résultat
        if result.get('status') == 'error':
            return jsonify(result), 500
        elif result.get('status') == 'already_syncing':
            return jsonify(result), 409  # Conflict
        else:
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in sync route: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }), 500

@ticket_bp.route('/api/sync/status', methods=['GET'])
def sync_status():
    """Retourne le statut de la synchronisation."""
    return jsonify({
        'is_running': sync_service.is_running(),
        'is_syncing': sync_service._is_syncing
    })
