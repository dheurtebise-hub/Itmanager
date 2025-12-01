"""
Point d'entrée principal de l'application IT Ticket Manager
"""

import sys
import os
import logging
import webbrowser
import threading
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging
from config import config
from app import create_app
from services.sync_service import sync_service
from services.backup_service import backup_service

def open_browser(port=5000):
    """Ouvre le navigateur après démarrage du serveur."""
    import time
    time.sleep(1.5)  # Attendre que le serveur soit prêt
    webbrowser.open(f'http://localhost:{port}')

def main():
    """Fonction principale."""

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("IT Ticket Manager - Démarrage")
    logger.info("=" * 50)

    # Créer l'application Flask
    app = create_app()

    # Démarrer les services en arrière-plan
    if config.get('auto_sync', True) and config.get('first_run_completed'):
        logger.info("Démarrage du service de synchronisation automatique")
        sync_service.start_auto_sync()

    # Démarrer le planificateur de backup
    logger.info("Démarrage du planificateur de backups")
    backup_service.start_scheduler()

    # Déterminer le port
    port = int(os.environ.get('PORT', 5000))

    # Ouvrir le navigateur dans un thread séparé
    if not os.environ.get('NO_BROWSER'):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Démarrer le serveur Flask
    logger.info(f"Serveur démarré sur http://localhost:{port}")
    logger.info("Appuyez sur Ctrl+C pour arrêter")

    try:
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,  # False en production
            use_reloader=False  # Éviter les doubles démarrages
        )
    except KeyboardInterrupt:
        logger.info("\nArrêt demandé par l'utilisateur")
    finally:
        # Arrêter les services
        logger.info("Arrêt des services...")
        sync_service.stop_auto_sync()
        logger.info("Application arrêtée proprement")

if __name__ == '__main__':
    main()
