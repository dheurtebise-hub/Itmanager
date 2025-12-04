"""
Configuration du logging
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os

class JSONFormatter(logging.Formatter):
    """Formatter JSON pour les logs."""

    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_dir: str = None, level: int = logging.INFO):
    """Configure le système de logging avec rotation et logs séparés."""

    if log_dir is None:
        app_data = os.getenv('APPDATA', os.path.expanduser('~'))
        log_dir = Path(app_data) / "ITTicketManager" / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    # Format détaillé pour les fichiers
    detailed_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Format console plus simple
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler principal (app.log) avec rotation
    app_log = log_dir / "app.log"
    app_handler = RotatingFileHandler(
        app_log,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setFormatter(detailed_format)
    app_handler.setLevel(logging.DEBUG)

    # Handler pour les erreurs uniquement (errors.log)
    error_log = log_dir / "errors.log"
    error_handler = RotatingFileHandler(
        error_log,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setFormatter(detailed_format)
    error_handler.setLevel(logging.ERROR)

    # Handler pour la synchronisation (sync.log)
    sync_log = log_dir / "sync.log"
    sync_handler = RotatingFileHandler(
        sync_log,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    sync_handler.setFormatter(detailed_format)
    sync_handler.setLevel(logging.DEBUG)

    # Filtre pour ne logger que les messages de sync
    class SyncFilter(logging.Filter):
        def filter(self, record):
            return 'sync' in record.name.lower() or 'outlook' in record.name.lower() or 'email' in record.name.lower()

    sync_handler.addFilter(SyncFilter())

    # Handler console (texte)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_format)
    console_handler.setLevel(level)

    # Configuration root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Nettoyer les handlers existants
    root_logger.handlers.clear()

    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(sync_handler)
    root_logger.addHandler(console_handler)

    # Réduire le niveau de logging des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Message de démarrage
    root_logger.info("=" * 80)
    root_logger.info(f"Logging system initialized - {datetime.now()}")
    root_logger.info(f"Log directory: {log_dir}")
    root_logger.info(f"Log files: app.log, errors.log, sync.log")
    root_logger.info("=" * 80)

    return log_dir


def get_log_path():
    """Retourne le chemin du répertoire de logs"""
    app_data = os.getenv('APPDATA', os.path.expanduser('~'))
    return Path(app_data) / "ITTicketManager" / "logs"


def read_recent_logs(log_type='app', lines=100):
    """
    Lit les dernières lignes d'un fichier de log

    Args:
        log_type: Type de log ('app', 'sync', 'errors')
        lines: Nombre de lignes à lire

    Returns:
        Liste des lignes de log
    """
    log_dir = get_log_path()
    log_files = {
        'app': log_dir / 'app.log',
        'sync': log_dir / 'sync.log',
        'errors': log_dir / 'errors.log'
    }

    log_file = log_files.get(log_type)
    if not log_file or not log_file.exists():
        return []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]  # Dernières N lignes
    except Exception as e:
        return [f"Erreur lecture logs: {e}"]

