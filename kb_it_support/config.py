"""
Configuration de l'application KB_IT_Support
"""

import os
from pathlib import Path

# Répertoire de base de l'application
BASE_DIR = Path(__file__).parent

# Configuration Flask
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Base de données
DATABASE_DIR = BASE_DIR / 'database'
DATABASE_PATH = DATABASE_DIR / 'kb_support.db'

# Stockage des fichiers
STORAGE_DIR = BASE_DIR / 'storage'
PROCEDURES_STORAGE = STORAGE_DIR / 'procedures'

# Taille maximale des uploads (50 MB par défaut)
MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', '50'))
MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {
    'ps1', 'sh', 'bat',                    # Scripts
    'pdf', 'doc', 'docx',                  # Documents
    'png', 'jpg', 'jpeg', 'gif', 'webp',   # Images
    'mp4', 'avi', 'mov',                   # Vidéos
    'ini', 'conf', 'xml', 'json', 'txt',   # Config
    'md',                                   # Markdown
    'zip', 'rar'                           # Archives
}

# Icônes par type de fichier
FILE_ICONS = {
    'ps1': '💾', 'sh': '💾', 'bat': '💾',
    'pdf': '📄', 'doc': '📄', 'docx': '📄',
    'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️', 'webp': '🖼️',
    'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
    'ini': '⚙️', 'conf': '⚙️', 'xml': '⚙️', 'json': '⚙️',
    'txt': '📝', 'md': '📝', 'log': '📝',
    'zip': '📦', 'rar': '📦'
}

# Configuration Claude API
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
CLAUDE_MODEL = 'claude-sonnet-4-5-20250929'
CLAUDE_MAX_TOKENS = 1024
CLAUDE_TEMPERATURE = 0.7

# Rate limiting
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60  # secondes

# Créer les répertoires nécessaires
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PROCEDURES_STORAGE.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """Vérifie si un fichier est autorisé."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_icon(filename):
    """Retourne l'icône appropriée pour un fichier."""
    if '.' not in filename:
        return '📄'
    ext = filename.rsplit('.', 1)[1].lower()
    return FILE_ICONS.get(ext, '📄')
