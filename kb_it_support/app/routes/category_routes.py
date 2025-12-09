"""
Routes API pour les catégories
"""

from flask import Blueprint, request, jsonify
from app.models.category import Category
import logging

category_bp = Blueprint('categories', __name__)
logger = logging.getLogger(__name__)


@category_bp.route('/api/categories', methods=['GET'])
def get_categories():
    """Récupère toutes les catégories."""
    try:
        tree = request.args.get('tree', 'false').lower() == 'true'

        if tree:
            # Retourner l'arborescence complète
            categories = Category.get_tree()
        else:
            # Retourner une liste plate
            categories = Category.get_all()

        return jsonify(categories), 200

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Récupère une catégorie par son ID."""
    try:
        category = Category.get_by_id(category_id)

        if not category:
            return jsonify({'error': 'Category not found'}), 404

        # Ajouter le nombre de procédures
        category = dict(category)
        category['procedure_count'] = Category.get_procedure_count(category_id)
        category['parents'] = Category.get_parents(category_id)

        return jsonify(category), 200

    except Exception as e:
        logger.error(f"Error getting category {category_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@category_bp.route('/api/categories', methods=['POST'])
def create_category():
    """Crée une nouvelle catégorie."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['name', 'short_name']
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        category_id = Category.create({
            'name': data['name'],
            'short_name': data['short_name'],
            'parent_id': data.get('parent_id'),
            'display_order': data.get('display_order', 0),
            'color_code': data.get('color_code', '#06b6d4'),
            'icon': data.get('icon', '📁')
        })

        category = Category.get_by_id(category_id)
        return jsonify(category), 201

    except Exception as e:
        logger.error(f"Error creating category: {e}")
        return jsonify({'error': str(e)}), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Met à jour une catégorie."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        allowed_fields = ['name', 'short_name', 'parent_id', 'display_order', 'color_code', 'icon', 'is_active']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        success = Category.update(category_id, update_data)

        if success:
            category = Category.get_by_id(category_id)
            return jsonify(category), 200
        else:
            return jsonify({'error': 'Failed to update category'}), 500

    except Exception as e:
        logger.error(f"Error updating category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Désactive une catégorie."""
    try:
        success = Category.delete(category_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Category deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete category'}), 500

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
