"""
Service d'intégration avec l'API Claude d'Anthropic
"""

import logging
import json
import requests
from typing import List, Dict, Any, Optional
from app.models.database import db

logger = logging.getLogger(__name__)


class AIService:
    """Service pour interagir avec l'API Claude."""

    def __init__(self):
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.api_version = "2023-06-01"

    def _get_api_key(self) -> Optional[str]:
        """Récupère la clé API depuis la configuration."""
        api_key = db.get_setting('claude_api_key')

        if not api_key:
            logger.warning("Claude API key not configured")
            return None

        return api_key

    def _make_request(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """Effectue une requête à l'API Claude."""
        api_key = self._get_api_key()

        if not api_key:
            return None

        model = db.get_setting('claude_model', 'claude-sonnet-4-5-20250929')
        temperature = float(db.get_setting('claude_temperature', '0.7'))

        try:
            response = requests.post(
                self.api_url,
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': self.api_version,
                    'content-type': 'application/json'
                },
                json={
                    'model': model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                },
                timeout=60
            )

            response.raise_for_status()

            result = response.json()
            content = result['content'][0]['text']

            logger.info(f"Claude API request successful")
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Claude API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Claude API: {e}")
            return None

    def test_connection(self) -> bool:
        """Teste la connexion à l'API Claude."""
        response = self._make_request("Hello, respond with OK if you can hear me.", max_tokens=10)
        return response is not None

    def generate_keywords(self, title: str, category: str = '', content: str = '') -> List[str]:
        """Génère des mots-clés pour une procédure."""
        prompt = f"""Tu es un assistant qui analyse des procédures IT et génère des tags pertinents.

Analyse ce titre et contenu de procédure.
Extrais 4 à 8 tags basés sur :
- Mots-clés récurrents (apparaissant plus de 3 fois)
- Termes techniques (logiciels, commandes, technologies)
- Actions principales (installation, configuration, dépannage)
- Contexte général

Titre : {title}
Catégorie : {category}
Contenu : {content[:500] if content else 'Non fourni'}

Retourne UNIQUEMENT un objet JSON avec cette structure :
{{
  "tags": ["tag1", "tag2", "tag3", ...]
}}

Les tags doivent être en minuscules, sans accents, et séparés par des tirets si composés (ex: "boite-partagee").
"""

        response = self._make_request(prompt)

        if not response:
            # Fallback : extraire les mots du titre
            return self._extract_keywords_fallback(title, content)

        try:
            # Extraire le JSON de la réponse
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group())
                tags = data.get('tags', [])

                if isinstance(tags, list) and len(tags) > 0:
                    # Normaliser les tags
                    return [tag.lower().strip() for tag in tags if isinstance(tag, str) and tag.strip()]

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Claude response: {e}")

        # Fallback en cas d'erreur
        return self._extract_keywords_fallback(title, content)

    def _extract_keywords_fallback(self, title: str, content: str = '') -> List[str]:
        """Extrait des mots-clés basiques sans IA."""
        import unicodedata
        import re

        def normalize(text):
            """Normalise un texte en retirant les accents."""
            nfd = unicodedata.normalize('NFD', text)
            without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
            return without_accents.lower()

        # Combiner titre et contenu
        text = f"{title} {content[:200]}"
        text = normalize(text)

        # Supprimer la ponctuation et diviser en mots
        words = re.findall(r'\b\w+\b', text)

        # Filtrer les mots trop courts et les mots courants
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
            'de', 'du', 'pour', 'par', 'avec', 'dans', 'sur', 'sous', 'entre', 'vers', 'chez',
            'est', 'sont', 'a', 'ont', 'fait', 'faire', 'comment', 'que', 'qui', 'quoi', 'dont'
        }

        keywords = []
        word_counts = {}

        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Trier par fréquence
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Prendre les 5 mots les plus fréquents
        keywords = [word for word, count in sorted_words[:5]]

        return keywords if keywords else [normalize(title.split()[0])] if title else []

    def semantic_search(self, query: str, procedures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Effectue une recherche sémantique sur les procédures."""
        if not procedures:
            return []

        # Pour simplifier, on utilise une recherche simple basée sur l'IA
        # pour scorer chaque procédure

        results = []

        for proc in procedures[:20]:  # Limiter à 20 procédures pour éviter les coûts
            prompt = f"""Question utilisateur : {query}

Titre procédure : {proc.get('title', '')}
Description : {proc.get('description', '')}[:200]

Cette procédure répond-elle à la question ?
Réponds UNIQUEMENT par un score de 0 à 100 (juste le nombre).
"""

            response = self._make_request(prompt, max_tokens=10)

            if response:
                try:
                    score = int(response.strip())
                    if score > 50:
                        proc_copy = proc.copy()
                        proc_copy['relevance_score'] = score
                        results.append(proc_copy)
                except ValueError:
                    pass

        # Trier par score de pertinence
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return results


# Instance globale
ai_service = AIService()
