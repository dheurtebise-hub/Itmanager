"""
Service de gestion des procédures
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.procedure import Procedure
from models.ticket import Ticket
from services.ai_service import AIService


class ProcedureService:
    """Service pour gérer les procédures et leurs suggestions."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_service = AIService()

    def get_suggestions_for_ticket(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les procédures suggérées pour un ticket donné.
        Si aucune procédure n'existe, retourne une liste vide.
        """
        # Récupérer le ticket
        ticket = Ticket.get_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        # Vérifier si des procédures sont déjà liées à ce ticket
        existing_procedures = Procedure.get_procedures_for_ticket(ticket_id)
        if existing_procedures:
            return existing_procedures

        # Sinon, chercher des procédures similaires basées sur le contenu du ticket
        suggestions = self._find_similar_procedures(ticket)

        # Lier les procédures trouvées au ticket
        for proc in suggestions:
            Procedure.link_to_ticket(proc['id'], ticket_id, proc.get('confidence', 0.0))
            Procedure.increment_usage(proc['id'])

        return suggestions

    def _find_similar_procedures(self, ticket: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trouve des procédures similaires basées sur le ticket."""
        # Extraire les mots-clés du ticket
        keywords = self._extract_keywords(ticket)

        # Rechercher par mots-clés
        procedures = Procedure.search_by_keywords(keywords, limit=5)

        # Si aucune procédure n'est trouvée, retourner une liste vide
        if not procedures:
            return []

        # Calculer un score de pertinence pour chaque procédure
        for proc in procedures:
            proc['confidence'] = self._calculate_confidence(ticket, proc)

        # Trier par score de pertinence
        procedures.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        return procedures

    def _extract_keywords(self, ticket: Dict[str, Any]) -> List[str]:
        """Extrait les mots-clés d'un ticket."""
        keywords = []

        # Ajouter la catégorie si disponible
        if ticket.get('category'):
            keywords.append(ticket['category'])

        # Extraire des mots-clés du sujet et du résumé
        text = f"{ticket.get('subject', '')} {ticket.get('summary', '')}"
        text = text.lower()

        # Liste de mots-clés techniques courants
        technical_keywords = [
            'installation', 'installer', 'logiciel', 'licence', 'activation',
            'ordinateur', 'pc', 'portable', 'imprimante', 'scanner',
            'réseau', 'wifi', 'internet', 'connexion', 'vpn',
            'email', 'outlook', 'messagerie', 'mot de passe', 'password',
            'accès', 'droits', 'permission', 'dossier', 'fichier',
            'erreur', 'problème', 'bug', 'plantage', 'lenteur',
            'mise à jour', 'update', 'upgrade', 'configuration',
            'sauvegarde', 'backup', 'restauration', 'récupération',
            'antivirus', 'sécurité', 'firewall', 'malware'
        ]

        for keyword in technical_keywords:
            if keyword in text:
                keywords.append(keyword)

        return keywords[:10]  # Limiter à 10 mots-clés

    def _calculate_confidence(self, ticket: Dict[str, Any], procedure: Dict[str, Any]) -> float:
        """Calcule un score de confiance entre un ticket et une procédure."""
        score = 0.0

        # Correspondance de catégorie (poids : 0.4)
        if ticket.get('category') and ticket['category'] == procedure.get('category'):
            score += 0.4

        # Correspondance de mots-clés (poids : 0.3)
        ticket_text = f"{ticket.get('subject', '')} {ticket.get('summary', '')}".lower()
        procedure_keywords = procedure.get('keywords', [])
        if isinstance(procedure_keywords, list):
            matching_keywords = sum(1 for kw in procedure_keywords if kw.lower() in ticket_text)
            if procedure_keywords:
                score += 0.3 * (matching_keywords / len(procedure_keywords))

        # Score basé sur les feedbacks précédents (poids : 0.2)
        positive = procedure.get('positive_feedback_count', 0)
        negative = procedure.get('negative_feedback_count', 0)
        total_feedback = positive + negative
        if total_feedback > 0:
            feedback_score = positive / total_feedback
            score += 0.2 * feedback_score

        # Bonus pour les procédures populaires (poids : 0.1)
        usage_count = procedure.get('usage_count', 0)
        if usage_count > 0:
            # Normaliser entre 0 et 0.1
            score += min(0.1, usage_count / 100)

        return min(1.0, score)

    def create_procedure_from_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """Crée une nouvelle procédure basée sur un ticket en utilisant l'IA."""
        # Récupérer le ticket
        ticket = Ticket.get_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        # Utiliser l'IA pour générer une procédure
        if not self.ai_service.is_configured():
            # Créer une procédure basique sans IA
            return self._create_basic_procedure(ticket)

        try:
            procedure_data = self._generate_procedure_with_ai(ticket)

            # Sauvegarder la procédure
            procedure_id = Procedure.create({
                'title': procedure_data['title'],
                'description': procedure_data['description'],
                'steps': procedure_data['steps'],
                'category': ticket.get('category', 'autre'),
                'keywords': procedure_data.get('keywords', []),
                'source_ticket_id': ticket_id,
                'created_by': 'ai'
            })

            # Lier la procédure au ticket
            Procedure.link_to_ticket(procedure_id, ticket_id, confidence=0.9)

            # Retourner la procédure créée
            return Procedure.get_by_id(procedure_id)

        except Exception as e:
            self.logger.error(f"Error creating procedure with AI: {e}")
            # Fallback: créer une procédure basique
            return self._create_basic_procedure(ticket)

    def _generate_procedure_with_ai(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une procédure avec l'IA."""
        from config import config

        model = config.get('ai_model_categorize', 'claude-haiku-4-5-20251001')

        prompt = f"""Basé sur ce ticket de support IT, crée une procédure détaillée pour résoudre ce type de problème.

TICKET:
- Sujet: {ticket.get('subject', '')}
- Catégorie: {ticket.get('category', '')}
- Résumé: {ticket.get('summary', '')}
- Contenu: {ticket.get('body', '')[:1000]}

Crée une procédure réutilisable qui pourra aider à résoudre des problèmes similaires à l'avenir.

Réponds UNIQUEMENT avec un JSON valide contenant:
- title: Un titre court et descriptif
- description: Une description claire du problème et de la solution
- steps: Une liste d'étapes numérotées pour résoudre le problème
- keywords: Une liste de mots-clés pertinents

Format JSON attendu:
{{
    "title": "...",
    "description": "...",
    "steps": ["Étape 1", "Étape 2", "Étape 3", ...],
    "keywords": ["mot-clé1", "mot-clé2", ...]
}}"""

        try:
            response = self.ai_service.client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            procedure_data = json.loads(result_text)

            # Traquer le coût
            self.ai_service._track_cost(model, response.usage)

            return procedure_data

        except Exception as e:
            self.logger.error(f"Error generating procedure with AI: {e}")
            raise

    def _create_basic_procedure(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une procédure basique sans IA."""
        procedure_id = Procedure.create({
            'title': f"Procédure pour: {ticket.get('subject', 'Sans titre')[:100]}",
            'description': ticket.get('summary') or ticket.get('subject') or 'Pas de description',
            'steps': [
                "Analyser le problème décrit",
                "Identifier la solution appropriée",
                "Appliquer la solution",
                "Vérifier que le problème est résolu",
                "Documenter la résolution"
            ],
            'category': ticket.get('category', 'autre'),
            'keywords': self._extract_keywords(ticket),
            'source_ticket_id': ticket['id'],
            'created_by': 'system'
        })

        # Lier la procédure au ticket
        Procedure.link_to_ticket(procedure_id, ticket['id'], confidence=0.5)

        return Procedure.get_by_id(procedure_id)

    def submit_feedback(self, procedure_id: int, ticket_id: int, feedback_type: str) -> bool:
        """Enregistre un feedback pour une procédure."""
        if feedback_type not in ['positive', 'negative']:
            raise ValueError("feedback_type must be 'positive' or 'negative'")

        return Procedure.add_feedback(procedure_id, ticket_id, feedback_type)

    def get_all_procedures(self, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère toutes les procédures actives."""
        return Procedure.get_all(category=category, is_active=True, limit=limit)

    def update_procedure(self, procedure_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour une procédure."""
        return Procedure.update(procedure_id, data)

    def delete_procedure(self, procedure_id: int) -> bool:
        """Désactive une procédure."""
        return Procedure.delete(procedure_id)


# Instance globale
procedure_service = ProcedureService()
