"""
Routes pour la configuration de l'application
"""

from flask import Blueprint, request, jsonify, render_template
from config import config
from services.backup_service import backup_service
from services.email_connector import OutlookConnector
from services.outlook_folder_manager import folder_manager
from services.archive_service import archive_service
from models.database import db

config_bp = Blueprint('config', __name__)

@config_bp.route('/settings')
def settings_page():
    """Page des paramètres."""
    return render_template('settings.html')

@config_bp.route('/api/config', methods=['GET'])
def get_config():
    """Récupère la configuration actuelle."""
    safe_config = {k: v for k, v in config._config.items() if k != 'api_key'}
    safe_config['has_api_key'] = config.has_api_key()
    return jsonify(safe_config)

@config_bp.route('/api/config', methods=['PUT'])
def update_config():
    """Met à jour la configuration."""
    data = request.json

    # Champs autorisés
    allowed = [
        'sync_interval_minutes', 'auto_sync', 'theme',
        'notifications_enabled', 'sla_enabled', 'outlook_folders'
    ]

    for key in allowed:
        if key in data:
            config.set(key, data[key])

    if config.save():
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Erreur sauvegarde'}), 500

@config_bp.route('/api/backups', methods=['GET'])
def list_backups():
    """Liste les backups disponibles."""
    backups = backup_service.list_backups()
    return jsonify(backups)

@config_bp.route('/api/backups', methods=['POST'])
def create_backup():
    """Crée un nouveau backup."""
    backup_path = backup_service.create_backup()
    if backup_path:
        return jsonify({'success': True, 'path': str(backup_path)})
    else:
        return jsonify({'error': 'Erreur création backup'}), 500

@config_bp.route('/api/categories', methods=['GET'])
def get_categories():
    """Récupère toutes les catégories."""
    categories = db.fetchall("SELECT * FROM categories WHERE is_active = TRUE ORDER BY order_index")
    return jsonify(categories)

@config_bp.route('/api/categories', methods=['POST'])
def create_category():
    """Crée une nouvelle catégorie."""
    data = request.json

    required = ['name', 'color', 'icon']
    if not all(k in data for k in required):
        return jsonify({'error': 'Champs manquants'}), 400

    try:
        cat_id = db.insert('categories', {
            'name': data['name'],
            'color': data['color'],
            'icon': data['icon'],
            'order_index': data.get('order_index', 99)
        })
        return jsonify({'success': True, 'id': cat_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/api/outlook/folders', methods=['GET'])
def list_outlook_folders():
    """Liste les dossiers Outlook disponibles."""
    try:
        connector = OutlookConnector(config._config)
        folders = connector.list_available_folders()
        current_config = config.get('outlook_folders', [{'name': 'Inbox', 'enabled': True}])

        # Enrichir avec la config actuelle
        for folder in folders:
            existing = next((f for f in current_config if f['name'] == folder['name']), None)
            folder['enabled'] = existing.get('enabled', False) if existing else False
            folder['priority_boost'] = existing.get('priority_boost', 0) if existing else 0

        return jsonify(folders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/api/outlook/setup-folders', methods=['POST'])
def setup_outlook_folders():
    """Crée les dossiers Outlook de l'application s'ils n'existent pas."""
    try:
        success, message = folder_manager.ensure_folders_exist()

        if success:
            # Mettre à jour la config pour utiliser App-Import par défaut
            config.set('outlook_folders', [
                {'name': 'App-Import', 'enabled': True, 'priority_boost': 0}
            ])
            config.save()

            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@config_bp.route('/api/archive/run', methods=['POST'])
def run_archive():
    """Exécute manuellement l'archivage des tickets résolus depuis 7 jours."""
    try:
        result = archive_service.archive_old_resolved_tickets()
        return jsonify({
            'success': True,
            'archived': result['archived'],
            'moved_emails': result['moved_emails'],
            'errors': result['errors'],
            'error_details': result.get('error_details')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@config_bp.route('/api/archive/preview', methods=['GET'])
def preview_archive():
    """Retourne le nombre de tickets qui seront archivés."""
    try:
        count = archive_service.get_tickets_to_archive_count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

