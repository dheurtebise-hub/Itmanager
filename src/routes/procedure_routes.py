"""
Routes API pour les procédures
"""

from flask import Blueprint, request, jsonify
from services.procedure_service import procedure_service
from utils.rate_limiter import rate_limit
import logging

procedure_bp = Blueprint('procedures', __name__)
logger = logging.getLogger(__name__)


@procedure_bp.route('/api/procedures/suggestions/<int:ticket_id>', methods=['GET'])
@rate_limit()
def get_procedure_suggestions(ticket_id):
    """Récupère les suggestions de procédures pour un ticket."""
    try:
        suggestions = procedure_service.get_suggestions_for_ticket(ticket_id)

        # Si aucune suggestion, retourner une liste vide (pas d'erreur)
        if not suggestions:
            return jsonify([]), 200

        return jsonify(suggestions), 200

    except ValueError as e:
        logger.error(f"Error getting procedure suggestions for ticket {ticket_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting procedure suggestions for ticket {ticket_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/create', methods=['POST'])
@rate_limit()
def create_procedure():
    """Crée une nouvelle procédure basée sur un ticket."""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            return jsonify({'error': 'ticket_id is required'}), 400

        procedure = procedure_service.create_procedure_from_ticket(ticket_id)
        return jsonify(procedure), 201

    except ValueError as e:
        logger.error(f"Error creating procedure: {e}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error creating procedure: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/feedback', methods=['POST'])
@rate_limit()
def submit_procedure_feedback():
    """Enregistre un feedback pour une procédure."""
    try:
        data = request.get_json()
        procedure_id = data.get('procedure_id')
        ticket_id = data.get('ticket_id')
        feedback_type = data.get('feedback_type')

        if not all([procedure_id, ticket_id, feedback_type]):
            return jsonify({'error': 'procedure_id, ticket_id and feedback_type are required'}), 400

        if feedback_type not in ['positive', 'negative']:
            return jsonify({'error': 'feedback_type must be positive or negative'}), 400

        success = procedure_service.submit_feedback(procedure_id, ticket_id, feedback_type)

        if success:
            return jsonify({'status': 'success', 'message': 'Feedback enregistré'}), 200
        else:
            return jsonify({'error': 'Failed to submit feedback'}), 500

    except ValueError as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures', methods=['GET'])
@rate_limit()
def get_all_procedures():
    """Récupère toutes les procédures actives."""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 100))

        procedures = procedure_service.get_all_procedures(category=category, limit=limit)
        return jsonify(procedures), 200

    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures', methods=['POST'])
@rate_limit()
def create_procedure_manually():
    """Crée une nouvelle procédure manuellement."""
    try:
        data = request.get_json()

        # Validation
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['title', 'category', 'steps']
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Créer la procédure
        from models.procedure import Procedure
        procedure_id = Procedure.create({
            'title': data['title'],
            'description': data.get('description', ''),
            'category': data['category'],
            'steps': data['steps'],
            'keywords': data.get('keywords', []),
            'source_ticket_id': data.get('source_ticket_id'),
            'created_by': 'manual'
        })

        # Lier au ticket si spécifié
        if data.get('source_ticket_id'):
            Procedure.link_to_ticket(procedure_id, data['source_ticket_id'], confidence=0.9)

        # Retourner la procédure créée
        procedure = Procedure.get_by_id(procedure_id)
        return jsonify(procedure), 201

    except Exception as e:
        logger.error(f"Error creating procedure manually: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['GET'])
@rate_limit()
def get_procedure(procedure_id):
    """Récupère une procédure par son ID."""
    try:
        from models.procedure import Procedure
        procedure = Procedure.get_by_id(procedure_id)

        if not procedure:
            return jsonify({'error': 'Procedure not found'}), 404

        return jsonify(procedure), 200

    except Exception as e:
        logger.error(f"Error getting procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['PUT'])
@rate_limit()
def update_procedure(procedure_id):
    """Met à jour une procédure."""
    try:
        data = request.get_json()

        # Valider les données
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Champs autorisés
        allowed_fields = ['title', 'description', 'steps', 'category', 'keywords', 'is_active']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        success = procedure_service.update_procedure(procedure_id, update_data)

        if success:
            from models.procedure import Procedure
            procedure = Procedure.get_by_id(procedure_id)
            return jsonify(procedure), 200
        else:
            return jsonify({'error': 'Failed to update procedure'}), 500

    except Exception as e:
        logger.error(f"Error updating procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['DELETE'])
@rate_limit()
def delete_procedure(procedure_id):
    """Désactive une procédure."""
    try:
        success = procedure_service.delete_procedure(procedure_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Procedure deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete procedure'}), 500

    except Exception as e:
        logger.error(f"Error deleting procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
