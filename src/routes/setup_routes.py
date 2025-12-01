"""
Routes pour le wizard de configuration
"""

from flask import Blueprint, request, jsonify, render_template, redirect
from config import config
from services.email_connector import OutlookConnector
from services.ai_service import ai_service

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/setup')
def setup_wizard():
    """Page d'accueil du wizard."""
    if config.get('first_run_completed'):
        return redirect('/')
    return render_template('setup/welcome.html')

@setup_bp.route('/setup/api', methods=['GET', 'POST'])
def setup_api():
    """Configuration de l'API Claude."""
    if request.method == 'POST':
        data = request.json
        api_key = data.get('api_key', '').strip()

        if not api_key.startswith('sk-ant-'):
            return jsonify({'success': False, 'message': 'Format de clé invalide'})

        # Stocker de manière sécurisée
        config.claude_api_key = api_key
        ai_service._init_client()

        # Tester la connexion
        success, message = ai_service.test_connection()

        if success:
            config.set('api_configured', True)
            config.save()

        return jsonify({'success': success, 'message': message})

    return render_template('setup/api_config.html')

@setup_bp.route('/setup/outlook', methods=['GET', 'POST'])
def setup_outlook():
    """Configuration d'Outlook."""
    if request.method == 'POST':
        data = request.json
        folders = data.get('folders', [])

        config.set('outlook_folders', folders)
        config.save()

        connector = OutlookConnector(config._config)
        success, message = connector.test_connection()

        return jsonify({'success': success, 'message': message})

    connector = OutlookConnector(config._config)
    available_folders = connector.list_available_folders()

    return render_template('setup/outlook_config.html', folders=available_folders)

@setup_bp.route('/setup/outlook/folders', methods=['GET'])
def get_outlook_folders():
    """Liste les dossiers Outlook disponibles."""
    connector = OutlookConnector(config._config)
    folders = connector.list_available_folders()
    return jsonify(folders)

@setup_bp.route('/setup/personalization', methods=['GET', 'POST'])
def setup_personalization():
    """Personnalisation (catégories, notifications, etc.)."""
    if request.method == 'POST':
        data = request.json

        config.set('categories', data.get('categories', []))
        config.set('notifications_enabled', data.get('notifications_enabled', True))
        config.set('theme', data.get('theme', 'light'))
        config.set('sla_enabled', data.get('sla_enabled', True))
        config.save()

        return jsonify({'success': True})

    return render_template('setup/personalization.html')

@setup_bp.route('/setup/complete', methods=['GET', 'POST'])
def setup_complete():
    """Finalisation de la configuration."""
    if request.method == 'POST':
        data = request.json

        config.set('first_run_completed', True)
        config.set('auto_import_on_start', data.get('auto_import_on_start', True))
        config.save()

        return jsonify({'success': True, 'redirect': '/'})

    return render_template('setup/complete.html')
