"""
Service de gestion des procédures
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.procedure import Procedure, normalize_text
from models.ticket import Ticket
from services.ai_service import AIService


# Seuil minimum de confiance pour suggérer une procédure (0-1)
# Les procédures avec un score < 0.25 ne seront pas suggérées
MIN_CONFIDENCE_THRESHOLD = 0.25

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

        # Rechercher par mots-clés (augmenté à 10 résultats)
        procedures = Procedure.search_by_keywords(keywords, limit=10)

        # Si aucune procédure n'est trouvée, retourner une liste vide
        if not procedures:
            self.logger.info(f"Aucune procédure trouvée pour les mots-clés: {keywords}")
            return []

        # Calculer un score de pertinence pour chaque procédure
        for proc in procedures:
            proc['confidence'] = self._calculate_confidence(ticket, proc)

        # Filtrer les procédures avec score trop faible (< seuil minimum)
        filtered_procedures = [p for p in procedures if p.get('confidence', 0) >= MIN_CONFIDENCE_THRESHOLD]

        if len(filtered_procedures) < len(procedures):
            removed = len(procedures) - len(filtered_procedures)
            self.logger.info(f"{removed} procédure(s) filtrée(s) (score < {MIN_CONFIDENCE_THRESHOLD})")

        # Trier par score de pertinence décroissant
        filtered_procedures.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        return filtered_procedures

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
        """Calcule un score de confiance amélioré entre un ticket et une procédure.

        Algorithme:
        - Catégorie: 35% (essentiel)
        - Mots-clés: 35% (essentiel)
        - Feedback: 20% (qualité)
        - Usage: 10% (popularité)

        Returns:
            float: Score entre 0 et 1
        """
        score = 0.0

        # 1. Correspondance de catégorie (poids : 0.35)
        if ticket.get('category') and ticket['category'] == procedure.get('category'):
            score += 0.35

        # 2. Correspondance de mots-clés avec normalisation (poids : 0.35)
        ticket_text = f"{ticket.get('subject', '')} {ticket.get('summary', '')} {ticket.get('body', '')[:500]}"
        normalized_ticket_text = normalize_text(ticket_text)

        procedure_keywords = procedure.get('keywords', [])
        if isinstance(procedure_keywords, list) and procedure_keywords:
            matching_keywords = 0
            for kw in procedure_keywords:
                normalized_kw = normalize_text(kw)
                if normalized_kw and normalized_kw in normalized_ticket_text:
                    matching_keywords += 1

            # Score proportionnel au nombre de mots-clés matchés
            keyword_ratio = matching_keywords / len(procedure_keywords)
            score += 0.35 * keyword_ratio

        # 3. Score basé sur les feedbacks (poids : 0.20)
        positive = procedure.get('positive_feedback_count', 0)
        negative = procedure.get('negative_feedback_count', 0)
        total_feedback = positive + negative

        if total_feedback >= 5:  # Seuil de confiance (au moins 5 feedbacks)
            feedback_score = positive / total_feedback
            score += 0.20 * feedback_score
        elif total_feedback > 0:
            # Feedbacks incomplets: pondération réduite
            feedback_score = positive / total_feedback
            score += 0.10 * feedback_score  # Seulement 10% au lieu de 20%
        else:
            # Nouvelles procédures: bonus de départ pour cold start
            score += 0.10

        # 4. Bonus pour les procédures populaires (poids : 0.10)
        usage_count = procedure.get('usage_count', 0)
        if usage_count > 0:
            # Normalisation logarithmique pour éviter la domination des vieilles procédures
            import math
            normalized_usage = min(1.0, math.log10(usage_count + 1) / 2)  # log10(100) = 2
            score += 0.10 * normalized_usage

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
