"""
Routes API pour les procédures
"""

from flask import Blueprint, request, jsonify, send_file
from app.models.procedure import Procedure
from app.models.tag import Tag
import logging
import os
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

procedure_bp = Blueprint('procedures', __name__)
logger = logging.getLogger(__name__)


@procedure_bp.route('/api/procedures', methods=['GET'])
def get_procedures():
    """Récupère toutes les procédures avec pagination et filtres."""
    try:
        # Paramètres de pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Paramètres de filtrage
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search')
        is_archived = request.args.get('archived', 'false').lower() == 'true'

        # Limites de sécurité
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        if per_page > 100:
            per_page = 100

        # Calculer l'offset
        offset = (page - 1) * per_page

        # Récupérer les procédures
        procedures = Procedure.get_all(
            category_id=category_id,
            is_archived=is_archived,
            limit=per_page,
            offset=offset,
            search=search
        )

        # Compter le total
        total = Procedure.count_all(
            category_id=category_id,
            is_archived=is_archived,
            search=search
        )

        total_pages = (total + per_page - 1) // per_page

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

    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['GET'])
def get_procedure(procedure_id):
    """Récupère une procédure par son ID."""
    try:
        procedure = Procedure.get_by_id(procedure_id)

        if not procedure:
            return jsonify({'error': 'Procedure not found'}), 404

        # Incrémenter le compteur d'utilisation
        Procedure.increment_usage(procedure_id)

        return jsonify(procedure), 200

    except Exception as e:
        logger.error(f"Error getting procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures', methods=['POST'])
def create_procedure():
    """Crée une nouvelle procédure."""
    try:
        data = request.get_json()

        # Validation
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['title', 'content', 'category_id']
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Créer la procédure
        procedure_id = Procedure.create({
            'title': data['title'],
            'content': data['content'],
            'description': data.get('description', ''),
            'category_id': data['category_id'],
            'estimated_time': data.get('estimated_time'),
            'created_by': data.get('created_by', 'manual')
        })

        # Ajouter les tags
        if 'tags' in data and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                if tag_name:
                    Procedure.add_tag(procedure_id, tag_name)

        # Retourner la procédure créée
        procedure = Procedure.get_by_id(procedure_id)
        return jsonify(procedure), 201

    except Exception as e:
        logger.error(f"Error creating procedure: {e}")
        return jsonify({'error': str(e)}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['PUT'])
def update_procedure(procedure_id):
    """Met à jour une procédure."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Champs autorisés
        allowed_fields = ['title', 'content', 'description', 'category_id', 'estimated_time']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        success = Procedure.update(procedure_id, update_data)

        if success:
            # Gérer les tags si fournis
            if 'tags' in data and isinstance(data['tags'], list):
                # Récupérer les tags actuels
                current_tags = {tag['name']: tag['id'] for tag in Procedure.get_tags(procedure_id)}
                new_tags = {tag.lower().strip() for tag in data['tags'] if tag}

                # Supprimer les tags non présents
                for tag_name, tag_id in current_tags.items():
                    if tag_name not in new_tags:
                        Procedure.remove_tag(procedure_id, tag_id)

                # Ajouter les nouveaux tags
                for tag_name in new_tags:
                    if tag_name not in current_tags:
                        Procedure.add_tag(procedure_id, tag_name)

            procedure = Procedure.get_by_id(procedure_id)
            return jsonify(procedure), 200
        else:
            return jsonify({'error': 'Failed to update procedure'}), 500

    except Exception as e:
        logger.error(f"Error updating procedure {procedure_id}: {e}")
        return jsonify({'error': str(e)}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>', methods=['DELETE'])
def delete_procedure(procedure_id):
    """Archive une procédure."""
    try:
        success = Procedure.archive(procedure_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Procedure archived'}), 200
        else:
            return jsonify({'error': 'Failed to archive procedure'}), 500

    except Exception as e:
        logger.error(f"Error archiving procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/tags', methods=['POST'])
def add_tag_to_procedure(procedure_id):
    """Ajoute un tag à une procédure."""
    try:
        data = request.get_json()

        if not data or 'tag' not in data:
            return jsonify({'error': 'Tag name required'}), 400

        tag_name = data['tag']
        is_ai_generated = data.get('is_ai_generated', False)

        success = Procedure.add_tag(procedure_id, tag_name, is_ai_generated)

        if success:
            return jsonify({'status': 'success', 'message': 'Tag added'}), 200
        else:
            return jsonify({'error': 'Tag already exists on this procedure'}), 400

    except Exception as e:
        logger.error(f"Error adding tag to procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_procedure(procedure_id, tag_id):
    """Retire un tag d'une procédure."""
    try:
        success = Procedure.remove_tag(procedure_id, tag_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Tag removed'}), 200
        else:
            return jsonify({'error': 'Failed to remove tag'}), 500

    except Exception as e:
        logger.error(f"Error removing tag from procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/attachments', methods=['POST'])
def upload_attachment(procedure_id):
    """Upload un fichier joint à une procédure."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Valider le fichier
        import config
        if not config.allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # Vérifier la taille
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > config.MAX_CONTENT_LENGTH:
            return jsonify({'error': f'File too large (max {config.MAX_UPLOAD_SIZE_MB}MB)'}), 400

        # Générer un nom de fichier unique
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4()}.{ext}"

        # Créer le dossier de la procédure
        procedure_dir = config.PROCEDURES_STORAGE / str(procedure_id)
        procedure_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder le fichier
        file_path = procedure_dir / unique_filename
        file.save(str(file_path))

        # Enregistrer dans la BDD
        attachment_id = Procedure.add_attachment(
            procedure_id=procedure_id,
            filename=unique_filename,
            original_filename=original_filename,
            file_type=ext,
            file_size=file_size,
            storage_path=str(file_path)
        )

        attachment = {
            'id': attachment_id,
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_type': ext,
            'file_size': file_size
        }

        return jsonify(attachment), 201

    except Exception as e:
        logger.error(f"Error uploading attachment: {e}")
        return jsonify({'error': str(e)}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/attachments/<int:attachment_id>', methods=['GET'])
def download_attachment(procedure_id, attachment_id):
    """Télécharge un fichier joint."""
    try:
        from app.models.database import db

        attachment = db.fetchone(
            "SELECT * FROM attachments WHERE id = ? AND procedure_id = ?",
            (attachment_id, procedure_id)
        )

        if not attachment:
            return jsonify({'error': 'Attachment not found'}), 404

        file_path = Path(attachment['storage_path'])

        if not file_path.exists():
            return jsonify({'error': 'File not found on disk'}), 404

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=attachment['original_filename']
        )

    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/versions', methods=['GET'])
def get_procedure_versions(procedure_id):
    """Récupère l'historique des versions d'une procédure."""
    try:
        versions = Procedure.get_versions(procedure_id)
        return jsonify(versions), 200

    except Exception as e:
        logger.error(f"Error getting versions for procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@procedure_bp.route('/api/procedures/<int:procedure_id>/versions/<int:version_number>', methods=['POST'])
def restore_procedure_version(procedure_id, version_number):
    """Restaure une version spécifique d'une procédure."""
    try:
        success = Procedure.restore_version(procedure_id, version_number)

        if success:
            procedure = Procedure.get_by_id(procedure_id)
            return jsonify(procedure), 200
        else:
            return jsonify({'error': 'Version not found'}), 404

    except Exception as e:
        logger.error(f"Error restoring version {version_number} for procedure {procedure_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
