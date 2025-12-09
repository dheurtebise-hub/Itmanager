"""
Point d'entrée de l'application KB_IT_Support
"""

from app import create_app
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Créer l'application
app = create_app()

if __name__ == '__main__':
    logger.info("Starting KB_IT_Support application...")
    logger.info(f"Database: {app.config['DATABASE_PATH']}")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
