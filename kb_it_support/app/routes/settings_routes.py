"""
Routes API pour les paramètres
"""

from flask import Blueprint, request, jsonify
from app.models.database import db
import logging

settings_bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Récupère tous les paramètres."""
    try:
        settings = db.fetchall("SELECT * FROM settings")
        settings_dict = {s['key']: s['value'] for s in settings}
        return jsonify(settings_dict), 200

    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@settings_bp.route('/api/settings/<key>', methods=['GET'])
def get_setting(key):
    """Récupère un paramètre spécifique."""
    try:
        value = db.get_setting(key)

        if value is None:
            return jsonify({'error': 'Setting not found'}), 404

        return jsonify({'key': key, 'value': value}), 200

    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@settings_bp.route('/api/settings/<key>', methods=['PUT'])
def update_setting(key):
    """Met à jour un paramètre."""
    try:
        data = request.get_json()

        if not data or 'value' not in data:
            return jsonify({'error': 'Value required'}), 400

        db.set_setting(key, data['value'])

        return jsonify({'status': 'success', 'key': key, 'value': data['value']}), 200

    except Exception as e:
        logger.error(f"Error updating setting {key}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@settings_bp.route('/api/settings/test-claude', methods=['GET'])
def test_claude():
    """Teste la connexion à l'API Claude."""
    try:
        api_key = db.get_setting('claude_api_key')

        if not api_key:
            return jsonify({'error': 'Claude API key not configured'}), 400

        # Tester l'API
        from app.services.ai_service import ai_service
        result = ai_service.test_connection()

        if result:
            return jsonify({'status': 'success', 'message': 'Claude API connection successful'}), 200
        else:
            return jsonify({'error': 'Claude API connection failed'}), 500

    except Exception as e:
        logger.error(f"Error testing Claude API: {e}")
        return jsonify({'error': str(e)}), 500
