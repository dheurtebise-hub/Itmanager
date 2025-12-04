"""
Routes pour le debugging et l'accès aux logs
"""

from flask import Blueprint, jsonify, request
from utils.logger import read_recent_logs, get_log_path
import logging

debug_bp = Blueprint('debug', __name__)
logger = logging.getLogger(__name__)


@debug_bp.route('/api/debug/logs', methods=['GET'])
def get_logs():
    """
    Récupère les logs récents

    Query params:
        - type: Type de log (app, sync, errors) - défaut: app
        - lines: Nombre de lignes (max 500) - défaut: 100
    """
    log_type = request.args.get('type', 'app')
    lines = min(int(request.args.get('lines', 100)), 500)

    if log_type not in ['app', 'sync', 'errors']:
        return jsonify({'error': 'Type de log invalide'}), 400

    try:
        log_lines = read_recent_logs(log_type, lines)
        return jsonify({
            'log_type': log_type,
            'lines_count': len(log_lines),
            'logs': ''.join(log_lines)
        })
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/api/debug/logs/path', methods=['GET'])
def get_log_path_route():
    """Retourne le chemin du répertoire de logs"""
    try:
        log_dir = get_log_path()
        return jsonify({
            'log_directory': str(log_dir),
            'exists': log_dir.exists()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/api/debug/test-log', methods=['POST'])
def test_log():
    """Écrit un message de test dans les logs"""
    data = request.json or {}
    message = data.get('message', 'Test log entry')

    logger.debug(f"DEBUG: {message}")
    logger.info(f"INFO: {message}")
    logger.warning(f"WARNING: {message}")
    logger.error(f"ERROR: {message}")

    sync_logger = logging.getLogger('sync')
    sync_logger.info(f"SYNC TEST: {message}")

    return jsonify({
        'status': 'success',
        'message': 'Messages de test écrits dans les logs'
    })
