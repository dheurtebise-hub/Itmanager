"""
Initialisation de l'application Flask KB_IT_Support
"""

from flask import Flask
from pathlib import Path
import logging

def create_app():
    """Crée et configure l'application Flask."""

    app = Flask(__name__,
                template_folder=str(Path(__file__).parent.parent / 'templates'),
                static_folder=str(Path(__file__).parent.parent / 'static'))

    # Configuration
    import config
    app.config.from_object(config)

    # Encodage UTF-8 pour JSON
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialiser la base de données
    from app.models.database import db
    db.init_database()

    # Enregistrer les blueprints
    from app.routes.procedure_routes import procedure_bp
    from app.routes.category_routes import category_bp
    from app.routes.tag_routes import tag_bp
    from app.routes.settings_routes import settings_bp

    app.register_blueprint(procedure_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(tag_bp)
    app.register_blueprint(settings_bp)

    # Route principale
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    return app
