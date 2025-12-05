"""
Modèle Procedure
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from models.database import db
import json
import unicodedata


def normalize_text(text: str) -> str:
    """Normalise un texte en retirant les accents et en le mettant en minuscules.

    Exemple:
        normalize_text("Réception") -> "reception"
        normalize_text("Système d'exploitation") -> "systeme d'exploitation"
    """
    if not text:
        return ""
    # Décomposer les caractères Unicode (séparer lettres et accents)
    nfd = unicodedata.normalize('NFD', text)
    # Filtrer les marques diacritiques (accents)
    without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    # Mettre en minuscules
    return without_accents.lower()


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
                except (json.JSONDecodeError, TypeError):
                    procedure['steps'] = []
            if procedure.get('keywords'):
                try:
                    procedure['keywords'] = json.loads(procedure['keywords'])
                except (json.JSONDecodeError, TypeError):
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
                except (json.JSONDecodeError, TypeError):
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except (json.JSONDecodeError, TypeError):
                    proc['keywords'] = []
            result.append(proc)

        return result

    @staticmethod
    def count_all(category: Optional[str] = None, is_active: bool = True) -> int:
        """Compte le nombre total de procédures avec filtres."""
        query = "SELECT COUNT(*) as total FROM procedures WHERE 1=1"
        params = []

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        if category:
            query += " AND category = ?"
            params.append(category)

        result = db.fetchone(query, tuple(params))
        return result['total'] if result else 0

    @staticmethod
    def search_by_keywords(keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche des procédures par mots-clés (insensible aux accents)."""
        if not keywords:
            return []

        # Normaliser les keywords de recherche (retirer accents)
        normalized_keywords = [normalize_text(kw) for kw in keywords]

        # Récupérer toutes les procédures actives
        query = "SELECT * FROM procedures WHERE is_active = 1"
        procedures = db.fetchall(query)

        # Filtrer et scorer en Python avec normalisation
        scored_procedures = []
        for proc in procedures:
            proc_dict = dict(proc)

            # Créer un texte de recherche normalisé pour cette procédure
            search_text = ' '.join([
                proc_dict.get('title', ''),
                proc_dict.get('description', ''),
                proc_dict.get('keywords', ''),
                proc_dict.get('category', '')
            ])
            normalized_search_text = normalize_text(search_text)

            # Calculer le score de correspondance
            match_score = 0
            matches = 0
            for norm_keyword in normalized_keywords:
                if norm_keyword in normalized_search_text:
                    matches += 1
                    # Bonus si c'est dans le titre
                    if norm_keyword in normalize_text(proc_dict.get('title', '')):
                        match_score += 3
                    # Bonus si c'est dans la catégorie
                    elif norm_keyword in normalize_text(proc_dict.get('category', '')):
                        match_score += 2
                    else:
                        match_score += 1

            # Ajouter la procédure si au moins un mot-clé correspond
            if matches > 0:
                proc_dict['match_score'] = match_score
                scored_procedures.append(proc_dict)

        # Trier par score de match, puis par feedback/usage
        scored_procedures.sort(
            key=lambda p: (
                p['match_score'],
                p.get('usage_count', 0),
                p.get('positive_feedback_count', 0)
            ),
            reverse=True
        )

        # Limiter les résultats
        procedures = scored_procedures[:limit]

        # Convertir les JSON en listes pour chaque procédure
        result = []
        for proc in procedures:
            proc = dict(proc)
            if proc.get('steps'):
                try:
                    proc['steps'] = json.loads(proc['steps'])
                except (json.JSONDecodeError, TypeError):
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except (json.JSONDecodeError, TypeError):
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
        except Exception:
            # Déjà lié (UNIQUE constraint violation)
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
                except (json.JSONDecodeError, TypeError):
                    proc['steps'] = []
            if proc.get('keywords'):
                try:
                    proc['keywords'] = json.loads(proc['keywords'])
                except (json.JSONDecodeError, TypeError):
                    proc['keywords'] = []
            result.append(proc)

        return result
