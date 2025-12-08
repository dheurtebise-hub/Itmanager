"""
Routes API pour la gestion des techniciens
"""

from flask import Blueprint, request, jsonify
from models.database import db
from utils.rate_limiter import rate_limit
import logging

technician_bp = Blueprint('technicians', __name__)
logger = logging.getLogger(__name__)


@technician_bp.route('/api/technicians', methods=['GET'])
@rate_limit()
def get_technicians():
    """Récupère tous les techniciens actifs."""
    try:
        technicians = db.fetchall("""
            SELECT id, name, email, is_active, created_at
            FROM technicians
            WHERE is_active = 1
            ORDER BY name ASC
        """)

        return jsonify([dict(tech) for tech in technicians]), 200

    except Exception as e:
        logger.error(f"Error getting technicians: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@technician_bp.route('/api/technicians', methods=['POST'])
@rate_limit()
def create_technician():
    """Crée un nouveau technicien."""
    try:
        data = request.get_json()

        # Validation
        if not data or 'name' not in data:
            return jsonify({'error': 'Technician name is required'}), 400

        name = data.get('name', '').strip()
        email = data.get('email', '').strip() if data.get('email') else None

        if not name:
            return jsonify({'error': 'Technician name cannot be empty'}), 400

        # Insérer le technicien
        cursor = db.execute("""
            INSERT INTO technicians (name, email, is_active)
            VALUES (?, ?, 1)
        """, (name, email))

        technician_id = cursor.lastrowid

        # Récupérer le technicien créé
        technician = db.fetchone("SELECT * FROM technicians WHERE id = ?", (technician_id,))

        return jsonify(dict(technician)), 201

    except Exception as e:
        logger.error(f"Error creating technician: {e}")
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Technician name already exists'}), 400
        return jsonify({'error': 'Internal server error'}), 500


@technician_bp.route('/api/technicians/<int:technician_id>', methods=['PUT'])
@rate_limit()
def update_technician(technician_id):
    """Met à jour un technicien."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Champs autorisés
        allowed_fields = ['name', 'email', 'is_active']
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(technician_id)

        db.execute(f"""
            UPDATE technicians
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, tuple(params))

        # Récupérer le technicien mis à jour
        technician = db.fetchone("SELECT * FROM technicians WHERE id = ?", (technician_id,))

        if not technician:
            return jsonify({'error': 'Technician not found'}), 404

        return jsonify(dict(technician)), 200

    except Exception as e:
        logger.error(f"Error updating technician: {e}")
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Technician name already exists'}), 400
        return jsonify({'error': 'Internal server error'}), 500


@technician_bp.route('/api/technicians/<int:technician_id>', methods=['DELETE'])
@rate_limit()
def delete_technician(technician_id):
    """Désactive un technicien (soft delete)."""
    try:
        # Vérifier si le technicien existe
        technician = db.fetchone("SELECT * FROM technicians WHERE id = ?", (technician_id,))

        if not technician:
            return jsonify({'error': 'Technician not found'}), 404

        # Désactiver au lieu de supprimer
        db.execute("""
            UPDATE technicians
            SET is_active = 0
            WHERE id = ?
        """, (technician_id,))

        return jsonify({'status': 'success', 'message': 'Technician disabled'}), 200

    except Exception as e:
        logger.error(f"Error deleting technician: {e}")
        return jsonify({'error': 'Internal server error'}), 500
