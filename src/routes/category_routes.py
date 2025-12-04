"""
Routes API pour la gestion des catégories
"""

from flask import Blueprint, request, jsonify
from models.database import db
from utils.rate_limiter import rate_limit
import logging

category_bp = Blueprint('categories', __name__)
logger = logging.getLogger(__name__)


@category_bp.route('/api/categories', methods=['GET'])
@rate_limit()
def get_categories():
    """Récupère toutes les catégories actives."""
    try:
        categories = db.fetchall("""
            SELECT id, name, icon, color, order_index, is_active
            FROM categories
            WHERE is_active = 1
            ORDER BY order_index ASC, name ASC
        """)

        return jsonify([dict(cat) for cat in categories]), 200

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@category_bp.route('/api/categories', methods=['POST'])
@rate_limit()
def create_category():
    """Crée une nouvelle catégorie."""
    try:
        data = request.get_json()

        # Validation
        if not data or 'name' not in data:
            return jsonify({'error': 'Category name is required'}), 400

        name = data.get('name', '').strip()
        icon = data.get('icon', '📁')
        color = data.get('color', '#0079BF')

        if not name:
            return jsonify({'error': 'Category name cannot be empty'}), 400

        # Obtenir le prochain order_index
        max_order = db.fetchone("SELECT MAX(order_index) as max_order FROM categories")
        next_order = (max_order['max_order'] or 0) + 1

        # Insérer la catégorie
        cursor = db.execute("""
            INSERT INTO categories (name, icon, color, order_index, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (name, icon, color, next_order))

        category_id = cursor.lastrowid

        # Récupérer la catégorie créée
        category = db.fetchone("SELECT * FROM categories WHERE id = ?", (category_id,))

        return jsonify(dict(category)), 201

    except Exception as e:
        logger.error(f"Error creating category: {e}")
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Category name already exists'}), 400
        return jsonify({'error': 'Internal server error'}), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@rate_limit()
def update_category(category_id):
    """Met à jour une catégorie."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Champs autorisés
        allowed_fields = ['name', 'icon', 'color', 'order_index']
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(category_id)

        db.execute(f"""
            UPDATE categories
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, tuple(params))

        # Récupérer la catégorie mise à jour
        category = db.fetchone("SELECT * FROM categories WHERE id = ?", (category_id,))

        if not category:
            return jsonify({'error': 'Category not found'}), 404

        return jsonify(dict(category)), 200

    except Exception as e:
        logger.error(f"Error updating category: {e}")
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Category name already exists'}), 400
        return jsonify({'error': 'Internal server error'}), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@rate_limit()
def delete_category(category_id):
    """Désactive une catégorie (soft delete)."""
    try:
        # Vérifier si la catégorie existe
        category = db.fetchone("SELECT * FROM categories WHERE id = ?", (category_id,))

        if not category:
            return jsonify({'error': 'Category not found'}), 404

        # Désactiver au lieu de supprimer
        db.execute("""
            UPDATE categories
            SET is_active = 0
            WHERE id = ?
        """, (category_id,))

        return jsonify({'status': 'success', 'message': 'Category disabled'}), 200

    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return jsonify({'error': 'Internal server error'}), 500
