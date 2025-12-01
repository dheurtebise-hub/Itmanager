"""
Modèle Ticket
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from models.database import db

class Ticket:
    """Modèle pour les tickets."""

    @staticmethod
    def create(ticket_data: Dict[str, Any]) -> int:
        """Crée un nouveau ticket."""
        # Vérifier si le ticket existe déjà (par message_id)
        if ticket_data.get('message_id'):
            existing = db.fetchone(
                "SELECT id FROM tickets WHERE message_id = ?",
                (ticket_data['message_id'],)
            )
            if existing:
                return existing['id']

        return db.insert('tickets', ticket_data)

    @staticmethod
    def get_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un ticket par son ID."""
        return db.fetchone("SELECT * FROM tickets WHERE id = ?", (ticket_id,))

    @staticmethod
    def update(ticket_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour un ticket."""
        data['updated_at'] = datetime.now().isoformat()

        # Si le statut passe à 'resolved', enregistrer la date
        if data.get('status') == 'resolved':
            ticket = Ticket.get_by_id(ticket_id)
            if ticket and ticket['status'] != 'resolved':
                data['resolved_at'] = datetime.now().isoformat()

                # Calculer le temps de résolution
                if ticket.get('received_date'):
                    received = datetime.fromisoformat(ticket['received_date'])
                    resolved = datetime.fromisoformat(data['resolved_at'])
                    resolution_time = (resolved - received).total_seconds() / 60
                    data['resolution_time_minutes'] = int(resolution_time)

        return db.update('tickets', data, "id = ?", (ticket_id,)) > 0

    @staticmethod
    def delete(ticket_id: int) -> bool:
        """Supprime un ticket."""
        return db.delete('tickets', "id = ?", (ticket_id,)) > 0

    @staticmethod
    def get_all(
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Récupère tous les tickets avec filtres."""
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if category:
            query += " AND category = ?"
            params.append(category)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY received_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return db.fetchall(query, tuple(params))

    @staticmethod
    def get_by_status(status: str) -> List[Dict[str, Any]]:
        """Récupère tous les tickets d'un statut donné."""
        return db.fetchall(
            "SELECT * FROM tickets WHERE status = ? ORDER BY received_date DESC",
            (status,)
        )

    @staticmethod
    def search(query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Recherche des tickets."""
        pattern = f"%{query}%"
        return db.fetchall(
            """SELECT * FROM tickets
               WHERE subject LIKE ? OR summary LIKE ? OR sender_email LIKE ?
               ORDER BY received_date DESC LIMIT ?""",
            (pattern, pattern, pattern, limit)
        )

    @staticmethod
    def get_similar(ticket_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Trouve des tickets similaires résolus."""
        ticket = Ticket.get_by_id(ticket_id)
        if not ticket:
            return []

        category = ticket.get('category')
        if not category:
            return []

        return db.fetchall(
            """SELECT * FROM tickets
               WHERE category = ? AND id != ? AND status = 'resolved' AND resolution IS NOT NULL
               ORDER BY resolved_at DESC LIMIT ?""",
            (category, ticket_id, limit)
        )

    @staticmethod
    def count_by_status() -> Dict[str, int]:
        """Compte les tickets par statut."""
        rows = db.fetchall("SELECT status, COUNT(*) as count FROM tickets GROUP BY status")
        return {row['status']: row['count'] for row in rows}

    @staticmethod
    def count_by_category() -> Dict[str, int]:
        """Compte les tickets par catégorie."""
        rows = db.fetchall("SELECT category, COUNT(*) as count FROM tickets GROUP BY category")
        return {row['category']: row['count'] for row in rows}
