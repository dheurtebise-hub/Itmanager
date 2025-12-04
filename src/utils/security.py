"""
Utilitaires de sécurité pour l'application
"""

import html
import re
from markupsafe import escape, Markup
from typing import Union


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
