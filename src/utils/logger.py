"""
Configuration du logging
"""

import logging
import json
from datetime import datetime
from pathlib import Path
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
    """Configure le système de logging."""

    if log_dir is None:
        app_data = os.getenv('APPDATA', os.path.expanduser('~'))
        log_dir = Path(app_data) / "ITTicketManager" / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file avec rotation par jour
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    # Handler fichier (JSON)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(level)

    # Handler console (texte)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    console_handler.setLevel(level)

    # Configuration root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Réduire le niveau de logging des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)

    logging.info("Logging system initialized")
