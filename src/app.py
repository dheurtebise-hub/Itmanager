"""
Application Flask principale
"""

from flask import Flask, render_template, redirect, url_for
from flask_wtf.csrf import CSRFProtect
import logging
from pathlib import Path

from config import config
from routes.ticket_routes import ticket_bp
from routes.setup_routes import setup_bp
from routes.export_routes import export_bp
from routes.config_routes import config_bp
from routes.procedure_routes import procedure_bp
from routes.import_export_routes import import_export_bp
from routes.category_routes import category_bp

def create_app():
    """Factory pour créer l'application Flask."""

    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

    # CSRF Protection
    csrf = CSRFProtect(app)

    # Désactiver CSRF pour les routes API (on utilise rate limiting à la place)
    csrf.exempt(ticket_bp)
    csrf.exempt(export_bp)
    csrf.exempt(setup_bp)
    csrf.exempt(config_bp)
    csrf.exempt(procedure_bp)
    csrf.exempt(import_export_bp)
    csrf.exempt(category_bp)

    # Enregistrer les blueprints
    app.register_blueprint(ticket_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(procedure_bp)
    app.register_blueprint(import_export_bp)
    app.register_blueprint(category_bp)

    # Routes principales
    @app.route('/')
    def index():
        """Page principale - redirige vers setup si non configuré."""
        if not config.get('first_run_completed'):
            return redirect(url_for('setup.setup_wizard'))
        return render_template('index.html')

    @app.route('/knowledge')
    def knowledge_base():
        """Page base de connaissances."""
        return render_template('knowledge_base.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"Server error: {e}")
        return {'error': 'Internal server error'}, 500

    return app
