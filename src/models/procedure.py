"""
Modèle Procedure
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from models.database import db
import json


class Procedure:
    """Modèle pour les procédures."""

    @staticmethod
    def create(procedure_data: Dict[str, Any]) -> int:
        """Crée une nouvelle procédure."""
        # Convertir la liste des steps en JSON
        if 'steps' in procedure_data and isinstance(procedure_data['steps'], list):
            procedure_data['steps'] = json.dumps(procedure_data['steps'], ensure_ascii=False)

        # Convertir la liste des keywords en JSON
        if 'keywords' in procedure_data and isinstance(procedure_data['keywords'], list):
            procedure_data['keywords'] = json.dumps(procedure_data['keywords'], ensure_ascii=False)

        return db.insert('procedures', procedure_data)

    @staticmethod
    def get_by_id(procedure_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une procédure par son ID."""
        procedure = db.fetchone("SELECT * FROM procedures WHERE id = ?", (procedure_id,))
        if procedure:
            procedure = dict(procedure)
            # Convertir les JSON en listes
            if procedure.get('steps'):
                try:
                    procedure['steps'] = json.loads(procedure['steps'])
                except:
                    procedure['steps'] = []
            if procedure.get('keywords'):
                try:
                    procedure['keywords'] = json.loads(procedure['keywords'])
                except:
                    procedure['keywords'] = []
        return procedure

    @staticmethod
    def update(procedure_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour une procédure."""
        data['updated_at'] = datetime.now().isoformat()

        # Convertir la liste des steps en JSON
        if 'steps' in data and isinstance(data['steps'], list):
            data['steps'] = json.dumps(data['steps'], ensure_ascii=False)

        # Convertir la liste des keywords en JSON
        if 'keywords' in data and isinstance(data['keywords'], list):
            data['keywords'] = json.dumps(data['keywords'], ensure_ascii=False)

        return db.update('procedures', data, "id = ?", (procedure_id,)) > 0

    @staticmethod
    def delete(procedure_id: int) -> bool:
        """Supprime une procédure."""
        return db.update('procedures', {'is_active': False}, "id = ?", (procedure_id,)) > 0

    @staticmethod
    def get_all(
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les procédures avec filtres."""
        query = "SELECT * FROM procedures WHERE 1=1"
        params = []

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY usage_count DESC, positive_feedback_count DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        procedures = db.fetchall(query, tuple(params))

        # Convertir les JSON en listes pour chaque procédure
        result = []
        for proc in procedures:
            proc = dict(proc)
            if proc.get('steps'):
                try:
                    proc['steps'] = json.loads(proc['steps'])
                except:
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except:
                    proc['keywords'] = []
            result.append(proc)

        return result

    @staticmethod
    def search_by_keywords(keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche des procédures par mots-clés."""
        if not keywords:
            return []

        # Créer une requête qui cherche les procédures contenant les mots-clés
        query = """
            SELECT *, 0 as match_score
            FROM procedures
            WHERE is_active = 1
        """
        params = []

        # Recherche dans le titre, la description et les keywords
        keyword_conditions = []
        for keyword in keywords:
            keyword_lower = f"%{keyword.lower()}%"
            keyword_conditions.append("""
                (LOWER(title) LIKE ? OR
                 LOWER(description) LIKE ? OR
                 LOWER(keywords) LIKE ? OR
                 LOWER(category) LIKE ?)
            """)
            params.extend([keyword_lower, keyword_lower, keyword_lower, keyword_lower])

        if keyword_conditions:
            query += " AND (" + " OR ".join(keyword_conditions) + ")"

        query += " ORDER BY usage_count DESC, positive_feedback_count DESC LIMIT ?"
        params.append(limit)

        procedures = db.fetchall(query, tuple(params))

        # Convertir les JSON en listes pour chaque procédure
        result = []
        for proc in procedures:
            proc = dict(proc)
            if proc.get('steps'):
                try:
                    proc['steps'] = json.loads(proc['steps'])
                except:
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except:
                    proc['keywords'] = []
            result.append(proc)

        return result

    @staticmethod
    def increment_usage(procedure_id: int):
        """Incrémente le compteur d'utilisation d'une procédure."""
        db.execute(
            "UPDATE procedures SET usage_count = usage_count + 1 WHERE id = ?",
            (procedure_id,)
        )

    @staticmethod
    def add_feedback(procedure_id: int, ticket_id: int, feedback_type: str) -> bool:
        """Ajoute un feedback pour une procédure."""
        # Vérifier si le feedback existe déjà
        existing = db.fetchone(
            "SELECT id, feedback_type FROM procedure_feedback WHERE procedure_id = ? AND ticket_id = ?",
            (procedure_id, ticket_id)
        )

        if existing:
            # Mise à jour du feedback existant
            if existing['feedback_type'] != feedback_type:
                # Décrémenter l'ancien type
                if existing['feedback_type'] == 'positive':
                    db.execute(
                        "UPDATE procedures SET positive_feedback_count = MAX(0, positive_feedback_count - 1) WHERE id = ?",
                        (procedure_id,)
                    )
                else:
                    db.execute(
                        "UPDATE procedures SET negative_feedback_count = MAX(0, negative_feedback_count - 1) WHERE id = ?",
                        (procedure_id,)
                    )

                # Incrémenter le nouveau type
                if feedback_type == 'positive':
                    db.execute(
                        "UPDATE procedures SET positive_feedback_count = positive_feedback_count + 1 WHERE id = ?",
                        (procedure_id,)
                    )
                else:
                    db.execute(
                        "UPDATE procedures SET negative_feedback_count = negative_feedback_count + 1 WHERE id = ?",
                        (procedure_id,)
                    )

                # Mettre à jour le feedback
                db.update(
                    'procedure_feedback',
                    {'feedback_type': feedback_type},
                    "id = ?",
                    (existing['id'],)
                )
        else:
            # Nouveau feedback
            db.insert('procedure_feedback', {
                'procedure_id': procedure_id,
                'ticket_id': ticket_id,
                'feedback_type': feedback_type
            })

            # Incrémenter le compteur approprié
            if feedback_type == 'positive':
                db.execute(
                    "UPDATE procedures SET positive_feedback_count = positive_feedback_count + 1 WHERE id = ?",
                    (procedure_id,)
                )
            else:
                db.execute(
                    "UPDATE procedures SET negative_feedback_count = negative_feedback_count + 1 WHERE id = ?",
                    (procedure_id,)
                )

        return True

    @staticmethod
    def get_feedback_for_ticket(procedure_id: int, ticket_id: int) -> Optional[str]:
        """Récupère le feedback d'une procédure pour un ticket donné."""
        result = db.fetchone(
            "SELECT feedback_type FROM procedure_feedback WHERE procedure_id = ? AND ticket_id = ?",
            (procedure_id, ticket_id)
        )
        return result['feedback_type'] if result else None

    @staticmethod
    def link_to_ticket(procedure_id: int, ticket_id: int, confidence: float = 0.0):
        """Lie une procédure à un ticket."""
        try:
            db.insert('ticket_procedures', {
                'ticket_id': ticket_id,
                'procedure_id': procedure_id,
                'confidence': confidence
            })
            return True
        except:
            # Déjà lié
            return False

    @staticmethod
    def get_procedures_for_ticket(ticket_id: int) -> List[Dict[str, Any]]:
        """Récupère les procédures suggérées pour un ticket."""
        query = """
            SELECT p.*, tp.confidence, pf.feedback_type as feedback
            FROM procedures p
            INNER JOIN ticket_procedures tp ON tp.procedure_id = p.id
            LEFT JOIN procedure_feedback pf ON pf.procedure_id = p.id AND pf.ticket_id = ?
            WHERE tp.ticket_id = ? AND p.is_active = 1
            ORDER BY tp.confidence DESC, p.usage_count DESC
        """

        procedures = db.fetchall(query, (ticket_id, ticket_id))

        # Convertir les JSON en listes pour chaque procédure
        result = []
        for proc in procedures:
            proc = dict(proc)
            if proc.get('steps'):
                try:
                    proc['steps'] = json.loads(proc['steps'])
                except:
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except:
                    proc['keywords'] = []
            result.append(proc)

        return result
