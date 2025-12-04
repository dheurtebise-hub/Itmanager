"""
Utilitaires de sécurité pour l'application
"""

import html
import re
from markupsafe import escape, Markup
from typing import Union, Tuple
import mimetypes


# Configuration des types de fichiers autorisés
ALLOWED_FILE_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'txt', 'odt'
}

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'application/vnd.oasis.opendocument.text'
}

# Taille maximale des fichiers (en bytes): 16 MB
MAX_FILE_SIZE = 16 * 1024 * 1024

# Taille maximale pour les bases de données: 50 MB
MAX_DB_SIZE = 50 * 1024 * 1024


def validate_uploaded_file(filename: str, file_content: bytes) -> Tuple[bool, str]:
    """
    Valide un fichier uploadé (extension, taille, MIME type).

    Args:
        filename: Nom du fichier
        file_content: Contenu du fichier en bytes

    Returns:
        Tuple (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_uploaded_file('doc.pdf', pdf_content)
        >>> if not is_valid:
        ...     return error, 400
    """
    # 1. Vérifier que le nom de fichier n'est pas vide
    if not filename or not filename.strip():
        return False, "Nom de fichier vide"

    # 2. Vérifier l'extension
    if '.' not in filename:
        return False, "Fichier sans extension"

    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_FILE_EXTENSIONS:
        return False, f"Extension non autorisée: .{extension}. Extensions autorisées: {', '.join(ALLOWED_FILE_EXTENSIONS)}"

    # 3. Vérifier la taille
    file_size = len(file_content)
    if file_size == 0:
        return False, "Fichier vide"

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"Fichier trop volumineux: {actual_mb:.1f} MB (max: {max_mb:.0f} MB)"

    # 4. Vérifier le MIME type (magic bytes)
    mime_type = detect_mime_type(file_content, filename)
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"Type de fichier non autorisé: {mime_type}"

    return True, ""


def validate_database_file(filename: str, file_content: bytes) -> Tuple[bool, str]:
    """
    Valide un fichier de base de données SQLite uploadé.

    Args:
        filename: Nom du fichier
        file_content: Contenu du fichier en bytes

    Returns:
        Tuple (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_database_file('backup.db', db_content)
        >>> if not is_valid:
        ...     return error, 400
    """
    # 1. Vérifier que le nom de fichier n'est pas vide
    if not filename or not filename.strip():
        return False, "Nom de fichier vide"

    # 2. Vérifier l'extension
    if not filename.lower().endswith(('.db', '.sqlite', '.sqlite3')):
        return False, "Extension non autorisée. Extensions autorisées: .db, .sqlite, .sqlite3"

    # 3. Vérifier la taille
    file_size = len(file_content)
    if file_size == 0:
        return False, "Fichier vide"

    if file_size > MAX_DB_SIZE:
        max_mb = MAX_DB_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"Fichier trop volumineux: {actual_mb:.1f} MB (max: {max_mb:.0f} MB)"

    # 4. Vérifier les magic bytes SQLite
    # SQLite 3 commence toujours par "SQLite format 3\x00"
    if not file_content.startswith(b'SQLite format 3\x00'):
        return False, "Le fichier n'est pas une base de données SQLite valide"

    return True, ""


def detect_mime_type(file_content: bytes, filename: str) -> str:
    """
    Détecte le MIME type d'un fichier à partir de son contenu (magic bytes).

    Args:
        file_content: Contenu du fichier
        filename: Nom du fichier (fallback)

    Returns:
        MIME type détecté
    """
    # Vérifier les magic bytes pour les formats courants
    if file_content[:4] == b'%PDF':
        return 'application/pdf'
    elif file_content[:2] == b'PK':  # ZIP-based formats (docx, odt)
        if b'word/' in file_content[:2000]:
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif b'odt' in file_content[:2000]:
            return 'application/vnd.oasis.opendocument.text'
    elif file_content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        return 'application/msword'  # Old .doc format

    # Fallback: utiliser l'extension
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def sanitize_html(text: Union[str, None]) -> str:
    """
    Échappe les caractères HTML pour prévenir les attaques XSS.

    Args:
        text: Texte à échapper (peut être None)

    Returns:
        Texte échappé (vide si None)

    Example:
        >>> sanitize_html('<script>alert("XSS")</script>')
        '&lt;script&gt;alert("XSS")&lt;/script&gt;'
    """
    if not text:
        return ""
    return escape(str(text))


def sanitize_html_list(items: list) -> list:
    """
    Échappe tous les éléments d'une liste.

    Args:
        items: Liste d'éléments à échapper

    Returns:
        Liste avec éléments échappés
    """
    return [sanitize_html(item) for item in items]


def strip_html_tags(text: Union[str, None]) -> str:
    """
    Supprime tous les tags HTML d'un texte.

    Args:
        text: Texte contenant du HTML

    Returns:
        Texte sans balises HTML

    Example:
        >>> strip_html_tags('<p>Hello <b>world</b></p>')
        'Hello world'
    """
    if not text:
        return ""

    # Supprimer les scripts et styles en entier
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Supprimer les commentaires HTML
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Supprimer toutes les balises
    text = re.sub(r'<[^>]+>', '', text)

    # Décoder les entités HTML
    text = html.unescape(text)

    return text.strip()


def validate_filename(filename: str) -> str:
    """
    Valide et nettoie un nom de fichier pour éviter les attaques path traversal.

    Args:
        filename: Nom de fichier à valider

    Returns:
        Nom de fichier nettoyé

    Raises:
        ValueError: Si le nom de fichier est invalide
    """
    if not filename:
        raise ValueError("Le nom de fichier ne peut pas être vide")

    # Supprimer les caractères dangereux
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Supprimer les chemins (../, /, \)
    filename = filename.replace('/', '').replace('\\', '').replace('..', '')

    if not filename:
        raise ValueError("Le nom de fichier ne contient que des caractères invalides")

    # Limiter la longueur
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename


def is_safe_redirect_url(url: str) -> bool:
    """
    Vérifie si une URL de redirection est sûre (même domaine).

    Args:
        url: URL à vérifier

    Returns:
        True si l'URL est sûre, False sinon
    """
    if not url:
        return False

    # Autoriser uniquement les chemins relatifs et les URLs du même domaine
    if url.startswith('/'):
        return True

    # Bloquer les URLs externes
    if url.startswith(('http://', 'https://', '//', 'javascript:', 'data:')):
        return False

    return True


def sanitize_email(email: str) -> str:
    """
    Valide et nettoie une adresse email.

    Args:
        email: Adresse email à valider

    Returns:
        Adresse email nettoyée

    Raises:
        ValueError: Si l'email est invalide
    """
    if not email:
        raise ValueError("L'adresse email ne peut pas être vide")

    email = email.strip().lower()

    # Validation basique
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        raise ValueError(f"Adresse email invalide: {email}")

    return email


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Tronque un texte à une longueur maximale.

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué

    Returns:
        Texte tronqué
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
