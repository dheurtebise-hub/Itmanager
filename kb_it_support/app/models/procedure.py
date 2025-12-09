"""
Modèle Procedure pour KB_IT_Support
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.database import db


class Procedure:
    """Modèle pour les procédures."""

    @staticmethod
    def create(procedure_data: Dict[str, Any]) -> int:
        """Crée une nouvelle procédure."""
        # Champs requis
        required = ['title', 'content', 'category_id']
        for field in required:
            if field not in procedure_data:
                raise ValueError(f"Champ requis manquant: {field}")

        # Valeurs par défaut
        procedure_data.setdefault('description', '')
        procedure_data.setdefault('estimated_time', None)
        procedure_data.setdefault('created_by', 'manual')
        procedure_data.setdefault('created_at', datetime.now().isoformat())
        procedure_data.setdefault('updated_at', datetime.now().isoformat())
        procedure_data.setdefault('is_archived', False)
        procedure_data.setdefault('usage_count', 0)

        procedure_id = db.insert('procedures', procedure_data)

        # Créer la première version
        db.insert('procedure_versions', {
            'procedure_id': procedure_id,
            'version_number': 1,
            'content': procedure_data['content'],
            'changed_by': procedure_data['created_by'],
            'changed_at': procedure_data['created_at']
        })

        return procedure_id

    @staticmethod
    def get_by_id(procedure_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une procédure par son ID."""
        procedure = db.fetchone(
            "SELECT * FROM procedures WHERE id = ? AND is_archived = 0",
            (procedure_id,)
        )

        if procedure:
            # Ajouter les tags
            procedure = dict(procedure)
            procedure['tags'] = Procedure.get_tags(procedure_id)
            # Ajouter les fichiers joints
            procedure['attachments'] = Procedure.get_attachments(procedure_id)

        return procedure

    @staticmethod
    def get_all(
        category_id: Optional[int] = None,
        is_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les procédures avec filtres."""
        query = "SELECT * FROM procedures WHERE is_archived = ?"
        params = [is_archived]

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)

        if search:
            query += " AND (title LIKE ? OR content LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY usage_count DESC, updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        procedures = db.fetchall(query, tuple(params))

        # Ajouter les tags pour chaque procédure
        result = []
        for proc in procedures:
            proc = dict(proc)
            proc['tags'] = Procedure.get_tags(proc['id'])
            result.append(proc)

        return result

    @staticmethod
    def count_all(category_id: Optional[int] = None, is_archived: bool = False, search: Optional[str] = None) -> int:
        """Compte le nombre total de procédures avec filtres."""
        query = "SELECT COUNT(*) as total FROM procedures WHERE is_archived = ?"
        params = [is_archived]

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)

        if search:
            query += " AND (title LIKE ? OR content LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        result = db.fetchone(query, tuple(params))
        return result['total'] if result else 0

    @staticmethod
    def update(procedure_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour une procédure."""
        data['updated_at'] = datetime.now().isoformat()

        # Si le contenu a changé, créer une nouvelle version
        if 'content' in data:
            procedure = Procedure.get_by_id(procedure_id)
            if procedure and procedure['content'] != data['content']:
                # Récupérer le dernier numéro de version
                last_version = db.fetchone(
                    "SELECT MAX(version_number) as max_version FROM procedure_versions WHERE procedure_id = ?",
                    (procedure_id,)
                )
                next_version = (last_version['max_version'] if last_version and last_version['max_version'] else 0) + 1

                # Créer nouvelle version
                db.insert('procedure_versions', {
                    'procedure_id': procedure_id,
                    'version_number': next_version,
                    'content': data['content'],
                    'changed_by': data.get('changed_by', 'unknown'),
                    'changed_at': data['updated_at']
                })

        return db.update('procedures', data, "id = ?", (procedure_id,)) > 0

    @staticmethod
    def archive(procedure_id: int) -> bool:
        """Archive une procédure."""
        return db.update('procedures', {'is_archived': True}, "id = ?", (procedure_id,)) > 0

    @staticmethod
    def delete(procedure_id: int) -> bool:
        """Supprime définitivement une procédure (utiliser archive() plutôt)."""
        return db.delete('procedures', "id = ?", (procedure_id,)) > 0

    @staticmethod
    def increment_usage(procedure_id: int):
        """Incrémente le compteur d'utilisation."""
        db.execute(
            "UPDATE procedures SET usage_count = usage_count + 1 WHERE id = ?",
            (procedure_id,)
        )

    @staticmethod
    def get_tags(procedure_id: int) -> List[Dict[str, Any]]:
        """Récupère les tags d'une procédure."""
        query = """
            SELECT t.id, t.name, pt.is_ai_generated
            FROM tags t
            INNER JOIN procedure_tags pt ON pt.tag_id = t.id
            WHERE pt.procedure_id = ?
            ORDER BY t.name
        """
        return db.fetchall(query, (procedure_id,))

    @staticmethod
    def add_tag(procedure_id: int, tag_name: str, is_ai_generated: bool = False) -> bool:
        """Ajoute un tag à une procédure."""
        tag_name = tag_name.lower().strip()

        # Créer le tag s'il n'existe pas
        tag = db.fetchone("SELECT id FROM tags WHERE name = ?", (tag_name,))
        if not tag:
            tag_id = db.insert('tags', {'name': tag_name, 'usage_count': 0})
        else:
            tag_id = tag['id']

        # Lier le tag à la procédure
        try:
            db.insert('procedure_tags', {
                'procedure_id': procedure_id,
                'tag_id': tag_id,
                'is_ai_generated': is_ai_generated
            })
            # Incrémenter usage_count
            db.execute("UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?", (tag_id,))
            return True
        except:
            # Déjà lié
            return False

    @staticmethod
    def remove_tag(procedure_id: int, tag_id: int) -> bool:
        """Retire un tag d'une procédure."""
        result = db.delete('procedure_tags', "procedure_id = ? AND tag_id = ?", (procedure_id, tag_id))
        if result > 0:
            # Décrémenter usage_count
            db.execute("UPDATE tags SET usage_count = MAX(0, usage_count - 1) WHERE id = ?", (tag_id,))
        return result > 0

    @staticmethod
    def get_attachments(procedure_id: int) -> List[Dict[str, Any]]:
        """Récupère les fichiers joints d'une procédure."""
        return db.fetchall(
            "SELECT * FROM attachments WHERE procedure_id = ? ORDER BY uploaded_at DESC",
            (procedure_id,)
        )

    @staticmethod
    def add_attachment(procedure_id: int, filename: str, original_filename: str,
                       file_type: str, file_size: int, storage_path: str) -> int:
        """Ajoute un fichier joint à une procédure."""
        return db.insert('attachments', {
            'procedure_id': procedure_id,
            'filename': filename,
            'original_filename': original_filename,
            'file_type': file_type,
            'file_size': file_size,
            'storage_path': storage_path
        })

    @staticmethod
    def get_versions(procedure_id: int) -> List[Dict[str, Any]]:
        """Récupère l'historique des versions d'une procédure."""
        return db.fetchall(
            "SELECT * FROM procedure_versions WHERE procedure_id = ? ORDER BY version_number DESC",
            (procedure_id,)
        )

    @staticmethod
    def restore_version(procedure_id: int, version_number: int) -> bool:
        """Restaure une version spécifique d'une procédure."""
        # Récupérer la version
        version = db.fetchone(
            "SELECT * FROM procedure_versions WHERE procedure_id = ? AND version_number = ?",
            (procedure_id, version_number)
        )

        if not version:
            return False

        # Mettre à jour la procédure avec le contenu de cette version
        return Procedure.update(procedure_id, {
            'content': version['content'],
            'changed_by': 'restore'
        })
