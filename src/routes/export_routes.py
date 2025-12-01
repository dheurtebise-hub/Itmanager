"""
Routes pour l'export des données
"""

from flask import Blueprint, request, Response
from services.export_service import export_service
from models.database import db
from datetime import datetime

export_bp = Blueprint('export', __name__)

@export_bp.route('/api/export/tickets', methods=['GET'])
def export_tickets():
    """Exporte les tickets filtrés."""
    format = request.args.get('format', 'csv').lower()
    status = request.args.get('status')
    category = request.args.get('category')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if date_from:
        query += " AND date(received_date) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date(received_date) <= ?"
        params.append(date_to)

    query += " ORDER BY received_date DESC"
    tickets = db.fetchall(query, tuple(params))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if format == 'xlsx':
        content = export_service.export_excel(tickets)
        filename = f"tickets_{timestamp}.xlsx"
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        content = export_service.export_csv(tickets)
        filename = f"tickets_{timestamp}.csv"
        mimetype = 'text/csv; charset=utf-8'

    return Response(
        content,
        mimetype=mimetype,
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
