"""
Routes API pour les procédures
"""

from flask import Blueprint, request, jsonify
from services.procedure_service import procedure_service
from utils.rate_limiter import rate_limit
import logging

procedure_bp = Blueprint('procedures', __name__)
logger = logging.getLogger(__name__)


@procedure_bp.route('/api/procedures/suggestions/<int:ticket_id>', methods=['GET'])
@rate_limit()
def get_procedure_suggestions(ticket_id):
    """Récupère les suggestions de procédures pour un ticket (avec pagination optionnelle)."""
    try:
        # Paramètres de pagination optionnels
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Limites de sécurité
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 50:
            per_page = 50

        suggestions = procedure_service.get_suggestions_for_ticket(ticket_id)

        # Si aucune suggestion, retourner une liste vide (pas d'erreur)
        if not suggestions:
            return jsonify({
                'suggestions': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }), 200

        # Appliquer la pagination aux suggestions
        total = len(suggestions)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_suggestions = suggestions[start:end]

        total_pages = (total + per_page - 1) // per_page

        response = {
            'suggestions': paginated_suggestions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

        return jsonify(response), 200

    except ValueError as e:
        logger.error(f"Error getting procedure suggestions for ticket {ticket_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting procedure suggestions for ticket {ticket_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/create', methods=['POST'])
@rate_limit()
def create_procedure():
    """Crée une nouvelle procédure basée sur un ticket."""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            return jsonify({'error': 'ticket_id is required'}), 400

        procedure = procedure_service.create_procedure_from_ticket(ticket_id)
        return jsonify(procedure), 201

    except ValueError as e:
        logger.error(f"Error creating procedure: {e}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error creating procedure: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/feedback', methods=['POST'])
@rate_limit()
def submit_procedure_feedback():
    """Enregistre un feedback pour une procédure."""
    try:
        data = request.get_json()
        procedure_id = data.get('procedure_id')
        ticket_id = data.get('ticket_id')
        feedback_type = data.get('feedback_type')

        if not all([procedure_id, ticket_id, feedback_type]):
            return jsonify({'error': 'procedure_id, ticket_id and feedback_type are required'}), 400

        if feedback_type not in ['positive', 'negative']:
            return jsonify({'error': 'feedback_type must be positive or negative'}), 400

        success = procedure_service.submit_feedback(procedure_id, ticket_id, feedback_type)

        if success:
            return jsonify({'status': 'success', 'message': 'Feedback enregistré'}), 200
        else:
            return jsonify({'error': 'Failed to submit feedback'}), 500

    except ValueError as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures', methods=['GET'])
@rate_limit()
def get_all_procedures():
    """Récupère toutes les procédures actives avec pagination."""
    try:
        category = request.args.get('category')

        # Paramètres de pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Limites de sécurité
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        if per_page > 100:
            per_page = 100

        # Calculer l'offset
        offset = (page - 1) * per_page

        # Récupérer les procédures avec pagination
        result = procedure_service.get_all_procedures_paginated(
            category=category,
            limit=per_page,
            offset=offset
        )

        # Construire la réponse avec métadonnées de pagination
        total = result['total']
        procedures = result['procedures']
        total_pages = (total + per_page - 1) // per_page  # Arrondi supérieur

        response = {
            'procedures': procedures,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

        return jsonify(response), 200

    except ValueError as ve:
        logger.error(f"Invalid pagination parameters: {ve}")
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures', methods=['POST'])
@rate_limit()
def create_procedure_manually():
    """Crée une nouvelle procédure manuellement."""
    try:
        data = request.get_json()

        # Validation
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['title', 'category', 'steps']
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Créer la procédure
        from models.procedure import Procedure
        procedure_id = Procedure.create({
            'title': data['title'],
            'description': data.get('description', ''),
            'category': data['category'],
            'steps': data['steps'],
            'keywords': data.get('keywords', []),
            'source_ticket_id': data.get('source_ticket_id'),
            'created_by': 'manual'
        })

        # Lier au ticket si spécifié
        if data.get('source_ticket_id'):
            Procedure.link_to_ticket(procedure_id, data['source_ticket_id'], confidence=0.9)

        # Retourner la procédure créée
        procedure = Procedure.get_by_id(procedure_id)
        return jsonify(procedure), 201

    except Exception as e:
        logger.error(f"Error creating procedure manually: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['GET'])
@rate_limit()
def get_procedure(procedure_id):
    """Récupère une procédure par son ID."""
    try:
        from models.procedure import Procedure
        procedure = Procedure.get_by_id(procedure_id)

        if not procedure:
            return jsonify({'error': 'Procedure not found'}), 404

        return jsonify(procedure), 200

    except Exception as e:
        logger.error(f"Error getting procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['PUT'])
@rate_limit()
def update_procedure(procedure_id):
    """Met à jour une procédure."""
    try:
        data = request.get_json()

        # Valider les données
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Champs autorisés
        allowed_fields = ['title', 'description', 'steps', 'category', 'keywords', 'is_active']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        success = procedure_service.update_procedure(procedure_id, update_data)

        if success:
            from models.procedure import Procedure
            procedure = Procedure.get_by_id(procedure_id)
            return jsonify(procedure), 200
        else:
            return jsonify({'error': 'Failed to update procedure'}), 500

    except Exception as e:
        logger.error(f"Error updating procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['DELETE'])
@rate_limit()
def delete_procedure(procedure_id):
    """Désactive une procédure."""
    try:
        success = procedure_service.delete_procedure(procedure_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Procedure deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete procedure'}), 500

    except Exception as e:
        logger.error(f"Error deleting procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/import/single', methods=['POST'])
@rate_limit()
def import_single_procedure():
    """Importe une procédure depuis un fichier."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        ai_reformulation = request.form.get('ai_reformulation', 'false').lower() == 'true'

        # Lire le contenu du fichier
        file_content = file.read()

        # Valider le fichier uploadé (sécurité)
        from utils.security import validate_uploaded_file
        is_valid, error_msg = validate_uploaded_file(file.filename, file_content)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Extraire le texte selon le format du fichier
        from utils.file_parser import extract_text_from_file
        content = extract_text_from_file(file_content, file.filename)

        if not content:
            return jsonify({'error': 'Impossible d\'extraire le texte du fichier. Vérifiez le format.'}), 400

        # Extraire le titre depuis le nom de fichier (sans extension)
        import os
        title = os.path.splitext(file.filename)[0]

        # Si reformulation IA activée
        if ai_reformulation:
            try:
                from services.ai_service import ai_service

                # Utiliser l'IA pour reformuler la procédure
                prompt = f"""Reformule cette procédure technique en gardant toutes les informations importantes.

Titre: {title}

Contenu:
{content}

Instructions:
1. Extrais et reformule la description principale
2. Identifie et structure les étapes clairement
3. Extrait les mots-clés pertinents
4. Détermine la catégorie (Logiciel, Matériel, Réseau, etc.)

Réponds au format JSON avec les clés suivantes:
{{
    "title": "titre reformulé",
    "description": "description courte et claire",
    "steps": ["étape 1", "étape 2", ...],
    "keywords": ["mot1", "mot2", ...],
    "category": "catégorie"
}}"""

                reformulation = ai_service.chat(prompt)

                # Parser la réponse JSON
                import json
                import re

                # Extraire le JSON de la réponse
                json_match = re.search(r'\{.*\}', reformulation, re.DOTALL)
                if json_match:
                    procedure_data = json.loads(json_match.group())
                else:
                    raise ValueError("Impossible de parser la réponse de l'IA")

            except Exception as e:
                logger.error(f"Error with AI reformulation: {e}")
                # Fallback : créer la procédure sans reformulation
                procedure_data = {
                    'title': title,
                    'description': content[:200] if len(content) > 200 else content,
                    'steps': [content],
                    'keywords': [title.lower()],
                    'category': 'Autre'
                }
        else:
            # Créer la procédure sans reformulation
            procedure_data = {
                'title': title,
                'description': content[:200] if len(content) > 200 else content,
                'steps': [content],
                'keywords': [title.lower()],
                'category': 'Autre'
            }

        # Ajouter created_by
        procedure_data['created_by'] = 'import'

        # Créer la procédure
        from models.procedure import Procedure
        procedure_id = Procedure.create(procedure_data)

        if procedure_id:
            procedure = Procedure.get_by_id(procedure_id)
            return jsonify({'status': 'success', 'procedure': procedure}), 200
        else:
            return jsonify({'error': 'Failed to create procedure'}), 500

    except Exception as e:
        logger.error(f"Error importing procedure: {e}")
        return jsonify({'error': str(e)}), 500


@procedure_bp.route('/api/ai/generate-keywords', methods=['POST'])
@rate_limit()
def generate_keywords():
    """Génère des mots-clés pour une procédure avec l'IA."""
    try:
        data = request.get_json()

        # Validation
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        title = data.get('title', '')
        category = data.get('category', '')
        content = data.get('content', '')

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        # Utiliser l'IA pour générer les mots-clés
        from services.ai_service import ai_service
        keywords = ai_service.generate_keywords(title, category, content)

        return jsonify({'keywords': keywords}), 200

    except Exception as e:
        logger.error(f"Error generating keywords: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/analytics', methods=['GET'])
@rate_limit()
def get_procedure_analytics(procedure_id):
    """Récupère les analytics d'une procédure spécifique."""
    try:
        analytics = procedure_service.get_procedure_analytics(procedure_id)
        return jsonify(analytics), 200

    except ValueError as e:
        logger.error(f"Error getting procedure analytics for {procedure_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting procedure analytics for {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/top', methods=['GET'])
@rate_limit()
def get_top_procedures():
    """Récupère les procédures les plus performantes."""
    try:
        limit = int(request.args.get('limit', 10))
        metric = request.args.get('metric', 'success_rate')

        # Validation
        if limit < 1 or limit > 50:
            limit = 10

        if metric not in ['success_rate', 'usage', 'effectiveness']:
            return jsonify({'error': 'Invalid metric. Must be: success_rate, usage, or effectiveness'}), 400

        top_procedures = procedure_service.get_top_procedures(limit=limit, metric=metric)
        return jsonify(top_procedures), 200

    except Exception as e:
        logger.error(f"Error getting top procedures: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/statistics', methods=['GET'])
@rate_limit()
def get_procedures_statistics():
    """Récupère les statistiques globales sur les procédures."""
    try:
        stats = procedure_service.get_procedures_statistics()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting procedures statistics: {e}")
        return jsonify({'error': 'Internal server error'}), 500
