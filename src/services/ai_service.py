"""
Intégration API Claude pour catégorisation et suggestions
"""

import anthropic
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from config import config
from services.suggestion_cache import suggestion_cache

class AIService:
    # Coûts par million de tokens (approximatifs)
    COSTS = {
        'claude-haiku-4-5-20251001': {'input': 0.25, 'output': 1.25},
        'claude-sonnet-4-5-20250929': {'input': 3.0, 'output': 15.0}
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._init_client()

    def _init_client(self):
        api_key = config.claude_api_key
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    def is_configured(self) -> bool:
        return self.client is not None

    def test_connection(self) -> tuple:
        if not self.client:
            return False, "Clé API non configurée"

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            return True, "Connexion réussie"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def categorize_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Catégorise un ticket avec l'IA."""
        if not self.client:
            return {'category': 'autre', 'priority': 'medium', 'confidence': 0}

        # D'abord essayer les règles simples pour catégorie/priorité
        simple_result = self._simple_categorization(ticket_data)
        use_simple_category = simple_result['confidence'] > 0.8

        # Toujours utiliser l'IA pour générer un résumé de qualité
        model = config.get('ai_model_categorize', 'claude-haiku-4-5-20251001')

        categories = [
            "installation_logiciel", "depannage_materiel", "demande_licence",
            "support_applicatif", "reseau", "securite", "autre"
        ]

        prompt = f"""Analyse cet email de support IT et catégorise-le.

SUJET: {ticket_data.get('subject', '')}
EXPÉDITEUR: {ticket_data.get('sender_email', '')}
CONTENU: {ticket_data.get('body', '')[:1500]}

Catégories possibles: {', '.join(categories)}
Priorités possibles: urgent, high, medium, low

Réponds UNIQUEMENT avec un JSON valide:
{{"category": "...", "priority": "...", "confidence": 0.0-1.0, "summary": "Résumé en 1-2 phrases"}}"""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)

            self._track_cost(model, response.usage)

            # Si les règles simples ont donné une catégorie fiable, on les utilise
            # mais on garde le résumé généré par l'IA
            if use_simple_category:
                result['category'] = simple_result['category']
                result['priority'] = simple_result['priority']
                result['confidence'] = simple_result['confidence']

            return result
        except Exception as e:
            self.logger.error(f"Erreur catégorisation IA: {e}")
            # En cas d'erreur, utiliser au moins les règles simples si disponibles
            if use_simple_category:
                return simple_result
            return {'category': 'autre', 'priority': 'medium', 'confidence': 0}

    def _simple_categorization(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Catégorisation par règles simples."""
        subject = (ticket_data.get('subject', '') + ' ' + ticket_data.get('body', '')).lower()

        rules = [
            (['installer', 'installation', 'install', 'setup'], 'installation_logiciel', 0.85),
            (['licence', 'license', 'clé', 'activation'], 'demande_licence', 0.85),
            (['panne', 'casse', 'écran', 'clavier', 'souris', 'imprimante'], 'depannage_materiel', 0.85),
            (['réseau', 'network', 'wifi', 'internet', 'vpn', 'connexion'], 'reseau', 0.85),
            (['mot de passe', 'password', 'accès', 'compte', 'bloqué'], 'securite', 0.85),
            (['urgent', 'urgence', 'critique', 'bloquant'], None, 0.9),  # Juste priorité
        ]

        for keywords, category, confidence in rules:
            if any(kw in subject for kw in keywords):
                result = {
                    'category': category or 'autre',
                    'confidence': confidence,
                    'priority': 'medium'
                }

                if 'urgent' in subject or 'critique' in subject:
                    result['priority'] = 'urgent'
                elif 'important' in subject:
                    result['priority'] = 'high'

                return result

        return {'category': 'autre', 'priority': 'medium', 'confidence': 0.3}

    def suggest_resolution(self, ticket_data: Dict[str, Any],
                          similar_tickets: List[Dict] = None,
                          knowledge_base: List[Dict] = None) -> str:
        """Génère une suggestion de résolution."""
        if not self.client:
            return "Service IA non configuré."

        category = ticket_data.get('category', '')
        summary = ticket_data.get('summary', '')
        priority = ticket_data.get('priority', '')

        # Vérifier le cache
        cached = suggestion_cache.get(category, summary, priority)
        if cached:
            self.logger.info("Suggestion depuis le cache")
            return cached

        model = config.get('ai_model_suggest', 'claude-sonnet-4-5-20250929')

        # Construire le contexte
        context = ""
        if similar_tickets:
            context += "\n\nTICKETS SIMILAIRES RÉSOLUS:\n"
            for i, t in enumerate(similar_tickets[:3], 1):
                context += f"{i}. {t.get('summary', '')} → {t.get('resolution', '')}\n"

        if knowledge_base:
            context += "\n\nBASE DE CONNAISSANCES:\n"
            for i, kb in enumerate(knowledge_base[:3], 1):
                context += f"{i}. {kb.get('title', '')}: {kb.get('content', '')[:300]}...\n"

        prompt = f"""Tu es un assistant IT expert. Voici une demande de support:

TITRE: {ticket_data.get('subject', '')}
CATÉGORIE: {category}
PRIORITÉ: {priority}
DESCRIPTION: {summary or ticket_data.get('body', '')[:1000]}
{context}

Propose une solution CONCRÈTE en français:
1. **Diagnostic probable**: Identifie la cause
2. **Solution recommandée**: Décris la solution
3. **Étapes détaillées**: Liste les étapes numérotées
4. **Commandes/Actions**: Commandes précises si applicable
5. **Temps estimé**: Durée approximative
6. **Validation**: Comment vérifier que ça fonctionne

Sois PRÉCIS et CONCRET. Maximum 400 mots."""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            suggestion = response.content[0].text
            self._track_cost(model, response.usage)

            # Mettre en cache
            suggestion_cache.set(category, summary, priority, suggestion)

            return suggestion
        except Exception as e:
            self.logger.error(f"Erreur suggestion IA: {e}")
            return "Impossible de générer une suggestion pour le moment."

    def generate_email_response(self, ticket_data: Dict[str, Any], resolution: str) -> str:
        """Génère un brouillon de réponse email."""
        if not self.client:
            return ""

        model = config.get('ai_model_categorize', 'claude-haiku-4-5-20251001')

        prompt = f"""Génère une réponse email professionnelle pour ce ticket résolu.

DEMANDE ORIGINALE: {ticket_data.get('subject', '')}
EXPÉDITEUR: {ticket_data.get('sender_name', '')}
RÉSOLUTION: {resolution}

Écris un email court, professionnel et amical en français.
Commence par "Bonjour" et termine par une formule de politesse.
Maximum 150 mots."""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            self._track_cost(model, response.usage)
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Erreur génération email: {e}")
            return ""

    def _track_cost(self, model: str, usage):
        """Enregistre les coûts API."""
        from models.database import db

        costs = self.COSTS.get(model, {'input': 1.0, 'output': 5.0})
        cost = (usage.input_tokens * costs['input'] + usage.output_tokens * costs['output']) / 1_000_000

        db.execute("""
            INSERT INTO api_costs (model, input_tokens, output_tokens, cost_euros, request_type)
            VALUES (?, ?, ?, ?, ?)
        """, (model, usage.input_tokens, usage.output_tokens, cost, 'suggestion'))

    def get_monthly_cost(self) -> float:
        """Retourne le coût du mois en cours."""
        from models.database import db

        result = db.fetchone("""
            SELECT COALESCE(SUM(cost_euros), 0) as total
            FROM api_costs
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """)
        return result['total'] if result else 0.0


ai_service = AIService()
