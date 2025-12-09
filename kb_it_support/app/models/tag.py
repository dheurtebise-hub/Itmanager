"""
Modèle Tag pour KB_IT_Support
"""

from typing import List, Dict, Any, Optional
from app.models.database import db


class Tag:
    """Modèle pour les tags."""

    @staticmethod
    def get_all(limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupère tous les tags, triés par usage."""
        query = "SELECT * FROM tags ORDER BY usage_count DESC, name"

        if limit:
            query += f" LIMIT {limit}"

        return db.fetchall(query)

    @staticmethod
    def get_by_id(tag_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un tag par son ID."""
        return db.fetchone("SELECT * FROM tags WHERE id = ?", (tag_id,))

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Récupère un tag par son nom."""
        return db.fetchone("SELECT * FROM tags WHERE name = ?", (name.lower().strip(),))

    @staticmethod
    def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche des tags par nom (auto-complétion)."""
        return db.fetchall(
            "SELECT * FROM tags WHERE name LIKE ? ORDER BY usage_count DESC, name LIMIT ?",
            (f"%{query.lower()}%", limit)
        )

    @staticmethod
    def get_popular(limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les tags les plus utilisés."""
        return db.fetchall(
            "SELECT * FROM tags WHERE usage_count > 0 ORDER BY usage_count DESC, name LIMIT ?",
            (limit,)
        )

    @staticmethod
    def create(name: str) -> int:
        """Crée un nouveau tag."""
        name = name.lower().strip()

        # Vérifier s'il existe déjà
        existing = Tag.get_by_name(name)
        if existing:
            return existing['id']

        return db.insert('tags', {'name': name, 'usage_count': 0})

    @staticmethod
    def delete_unused() -> int:
        """Supprime les tags non utilisés."""
        return db.delete('tags', "usage_count = 0")

    @staticmethod
    def get_procedures_for_tag(tag_id: int) -> List[Dict[str, Any]]:
        """Récupère les procédures associées à un tag."""
        query = """
            SELECT p.*
            FROM procedures p
            INNER JOIN procedure_tags pt ON pt.procedure_id = p.id
            WHERE pt.tag_id = ? AND p.is_archived = 0
            ORDER BY p.usage_count DESC, p.updated_at DESC
        """
        return db.fetchall(query, (tag_id,))
