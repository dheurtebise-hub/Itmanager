"""
Fonctions utilitaires
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import re

def format_datetime(dt: Optional[datetime], format_str: str = '%d/%m/%Y %H:%M') -> str:
    """Formate une datetime en string."""
    if dt is None:
        return ''
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    return dt.strftime(format_str)


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse une string en datetime."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except:
        return None


def time_ago(dt: Optional[datetime]) -> str:
    """Retourne une durée relative (ex: 'il y a 2 heures')."""
    if dt is None:
        return ''

    if isinstance(dt, str):
        dt = parse_datetime(dt)

    if dt is None:
        return ''

    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "à l'instant"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"il y a {minutes} min"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"il y a {hours}h"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"il y a {days}j"
    else:
        return format_datetime(dt, '%d/%m/%Y')


def sanitize_email(email: str) -> str:
    """Nettoie et valide une adresse email."""
    if not email:
        return ''
    email = email.strip().lower()
    # Simple validation
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return email
    return ''


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Tronque un texte à une longueur maximale."""
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def dict_to_json_safe(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convertit un dict en version JSON-safe (convertit les datetime, etc.)."""
    result = {}
    for key, value in d.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, (list, tuple)):
            result[key] = [dict_to_json_safe(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            result[key] = dict_to_json_safe(value)
        else:
            result[key] = value
    return result


def get_priority_order(priority: str) -> int:
    """Retourne l'ordre de priorité pour le tri."""
    priority_map = {
        'urgent': 0,
        'high': 1,
        'medium': 2,
        'low': 3
    }
    return priority_map.get(priority.lower(), 99)


def get_status_order(status: str) -> int:
    """Retourne l'ordre de statut pour le tri."""
    status_map = {
        'new': 0,
        'in_progress': 1,
        'resolved': 2,
        'closed': 3
    }
    return status_map.get(status.lower(), 99)
