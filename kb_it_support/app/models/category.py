"""
Modèle Category pour KB_IT_Support
"""

from typing import Optional, Dict, Any, List
from app.models.database import db


class Category:
    """Modèle pour les catégories hiérarchiques."""

    @staticmethod
    def get_all(is_active: bool = True) -> List[Dict[str, Any]]:
        """Récupère toutes les catégories actives."""
        query = "SELECT * FROM categories WHERE 1=1"
        params = []

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        query += " ORDER BY parent_id NULLS FIRST, display_order, name"

        return db.fetchall(query, tuple(params) if params else None)

    @staticmethod
    def get_tree() -> List[Dict[str, Any]]:
        """Récupère l'arborescence complète des catégories."""
        # Récupérer toutes les catégories
        all_categories = Category.get_all()

        # Construire l'arbre
        categories_by_id = {cat['id']: dict(cat) for cat in all_categories}

        # Ajouter une liste d'enfants à chaque catégorie
        for cat in categories_by_id.values():
            cat['children'] = []

        # Construire les relations parent-enfant
        root_categories = []
        for cat in categories_by_id.values():
            if cat['parent_id'] is None:
                root_categories.append(cat)
            else:
                if cat['parent_id'] in categories_by_id:
                    categories_by_id[cat['parent_id']]['children'].append(cat)

        return root_categories

    @staticmethod
    def get_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une catégorie par son ID."""
        return db.fetchone("SELECT * FROM categories WHERE id = ?", (category_id,))

    @staticmethod
    def get_children(parent_id: int) -> List[Dict[str, Any]]:
        """Récupère les sous-catégories d'une catégorie."""
        return db.fetchall(
            "SELECT * FROM categories WHERE parent_id = ? AND is_active = 1 ORDER BY display_order, name",
            (parent_id,)
        )

    @staticmethod
    def get_parents(category_id: int) -> List[Dict[str, Any]]:
        """Récupère la chaîne des parents d'une catégorie (pour breadcrumb)."""
        parents = []
        current_id = category_id

        while current_id:
            category = Category.get_by_id(current_id)
            if not category:
                break

            parents.insert(0, category)
            current_id = category['parent_id']

        return parents

    @staticmethod
    def create(category_data: Dict[str, Any]) -> int:
        """Crée une nouvelle catégorie."""
        required = ['name', 'short_name']
        for field in required:
            if field not in category_data:
                raise ValueError(f"Champ requis manquant: {field}")

        # Valeurs par défaut
        category_data.setdefault('parent_id', None)
        category_data.setdefault('display_order', 0)
        category_data.setdefault('color_code', '#06b6d4')
        category_data.setdefault('icon', '📁')
        category_data.setdefault('is_active', True)

        return db.insert('categories', category_data)

    @staticmethod
    def update(category_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour une catégorie."""
        return db.update('categories', data, "id = ?", (category_id,)) > 0

    @staticmethod
    def delete(category_id: int) -> bool:
        """Désactive une catégorie (soft delete)."""
        # Vérifier qu'il n'y a pas de procédures associées
        count = db.fetchone(
            "SELECT COUNT(*) as total FROM procedures WHERE category_id = ? AND is_archived = 0",
            (category_id,)
        )

        if count and count['total'] > 0:
            raise ValueError(f"Impossible de supprimer : {count['total']} procédures utilisent cette catégorie")

        # Vérifier qu'il n'y a pas de sous-catégories
        children = Category.get_children(category_id)
        if children:
            raise ValueError(f"Impossible de supprimer : cette catégorie a {len(children)} sous-catégories")

        return db.update('categories', {'is_active': False}, "id = ?", (category_id,)) > 0

    @staticmethod
    def get_procedure_count(category_id: int) -> int:
        """Compte le nombre de procédures dans une catégorie."""
        result = db.fetchone(
            "SELECT COUNT(*) as total FROM procedures WHERE category_id = ? AND is_archived = 0",
            (category_id,)
        )
        return result['total'] if result else 0
