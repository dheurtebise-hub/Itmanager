"""
Routes API pour les tags
"""

from flask import Blueprint, request, jsonify
from app.models.tag import Tag
import logging

tag_bp = Blueprint('tags', __name__)
logger = logging.getLogger(__name__)


@tag_bp.route('/api/tags', methods=['GET'])
def get_tags():
    """Récupère tous les tags."""
    try:
        limit = request.args.get('limit', type=int)
        tags = Tag.get_all(limit=limit)
        return jsonify(tags), 200

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@tag_bp.route('/api/tags/search', methods=['GET'])
def search_tags():
    """Recherche des tags (auto-complétion)."""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify([]), 200

        tags = Tag.search(query, limit=limit)
        return jsonify(tags), 200

    except Exception as e:
        logger.error(f"Error searching tags: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@tag_bp.route('/api/tags/popular', methods=['GET'])
def get_popular_tags():
    """Récupère les tags les plus utilisés."""
    try:
        limit = int(request.args.get('limit', 20))
        tags = Tag.get_popular(limit=limit)
        return jsonify(tags), 200

    except Exception as e:
        logger.error(f"Error getting popular tags: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@tag_bp.route('/api/tags/<int:tag_id>/procedures', methods=['GET'])
def get_tag_procedures(tag_id):
    """Récupère les procédures associées à un tag."""
    try:
        procedures = Tag.get_procedures_for_tag(tag_id)
        return jsonify(procedures), 200

    except Exception as e:
        logger.error(f"Error getting procedures for tag {tag_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
