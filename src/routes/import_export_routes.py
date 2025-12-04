"""
Routes API pour l'import/export de données
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import shutil
import json
import csv
from io import StringIO
from pathlib import Path
from models.database import db
from models.procedure import Procedure
from models.ticket import Ticket
from utils.rate_limiter import rate_limit
import logging

import_export_bp = Blueprint('import_export', __name__)
logger = logging.getLogger(__name__)


@import_export_bp.route('/api/export/database', methods=['GET'])
@rate_limit()
def export_database():
    """Exporte la base de données complète."""
    try:
        db_path = db.db_path

        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404

        return send_file(
            db_path,
            as_attachment=True,
            download_name=f'itmanager_database_{Path(db_path).stem}.db',
            mimetype='application/x-sqlite3'
        )

    except Exception as e:
        logger.error(f"Error exporting database: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@import_export_bp.route('/api/export/procedures', methods=['GET'])
@rate_limit()
def export_procedures():
    """Exporte toutes les procédures au format JSON."""
    try:
        procedures = Procedure.get_all(is_active=True, limit=1000)

        # Nettoyer les données pour l'export
        export_data = []
        for proc in procedures:
            export_data.append({
                'title': proc['title'],
                'description': proc.get('description', ''),
                'category': proc.get('category', ''),
                'steps': proc.get('steps', []),
                'keywords': proc.get('keywords', []),
                'created_by': proc.get('created_by', 'manual')
            })

        return jsonify(export_data), 200

    except Exception as e:
        logger.error(f"Error exporting procedures: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@import_export_bp.route('/api/import/database', methods=['POST'])
@rate_limit()
def import_database():
    """Importe une base de données complète."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Lire le contenu pour validation
        file_content = file.read()

        # Valider le fichier de base de données (sécurité)
        from utils.security import validate_database_file
        is_valid, error_msg = validate_database_file(file.filename, file_content)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Créer une sauvegarde avant l'import
        db_path = db.db_path
        backup_path = str(Path(db_path).parent / f'backup_before_import_{Path(db_path).stem}.db')
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backup created at {backup_path}")

        # Sauvegarder le fichier importé temporairement
        temp_path = str(Path(db_path).parent / 'temp_import.db')
        with open(temp_path, 'wb') as f:
            f.write(file_content)

        # Remplacer la base de données actuelle
        shutil.move(temp_path, db_path)

        return jsonify({
            'message': 'Database imported successfully',
            'backup_location': backup_path
        }), 200

    except Exception as e:
        logger.error(f"Error importing database: {e}")
        return jsonify({'error': str(e)}), 500


@import_export_bp.route('/api/import/procedures', methods=['POST'])
@rate_limit()
def import_procedures():
    """Importe des procédures depuis un fichier JSON."""
    try:
        data = request.get_json()

        if not data or 'procedures' not in data:
            return jsonify({'error': 'No procedures data provided'}), 400

        procedures = data['procedures']

        if not isinstance(procedures, list):
            return jsonify({'error': 'Invalid format: procedures must be an array'}), 400

        imported_count = 0
        for proc_data in procedures:
            try:
                # Valider les champs requis
                if not proc_data.get('title') or not proc_data.get('category'):
                    logger.warning(f"Skipping procedure without title or category")
                    continue

                # Créer la procédure
                Procedure.create({
                    'title': proc_data['title'],
                    'description': proc_data.get('description', ''),
                    'category': proc_data['category'],
                    'steps': proc_data.get('steps', []),
                    'keywords': proc_data.get('keywords', []),
                    'created_by': 'imported'
                })
                imported_count += 1

            except Exception as e:
                logger.error(f"Error importing procedure '{proc_data.get('title', 'unknown')}': {e}")
                continue

        return jsonify({
            'message': f'{imported_count} procedures imported successfully',
            'imported': imported_count
        }), 200

    except Exception as e:
        logger.error(f"Error importing procedures: {e}")
        return jsonify({'error': str(e)}), 500


@import_export_bp.route('/api/import/tickets', methods=['POST'])
@rate_limit()
def import_tickets():
    """Importe des tickets depuis un fichier CSV ou JSON."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filename = secure_filename(file.filename)
        imported_count = 0

        # Import JSON
        if filename.endswith('.json'):
            content = file.read().decode('utf-8')
            tickets = json.loads(content)

            if not isinstance(tickets, list):
                return jsonify({'error': 'Invalid JSON format: expected array of tickets'}), 400

            for ticket_data in tickets:
                try:
                    # Créer le ticket
                    Ticket.create({
                        'subject': ticket_data.get('subject', 'Imported ticket'),
                        'sender_email': ticket_data.get('sender_email', 'unknown@imported.com'),
                        'sender_name': ticket_data.get('sender_name', ''),
                        'body': ticket_data.get('body', ''),
                        'summary': ticket_data.get('summary', ''),
                        'category': ticket_data.get('category', 'autre'),
                        'priority': ticket_data.get('priority', 'medium'),
                        'status': ticket_data.get('status', 'new'),
                    })
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing ticket: {e}")
                    continue

        # Import CSV
        elif filename.endswith('.csv'):
            content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(content))

            for row in csv_reader:
                try:
                    Ticket.create({
                        'subject': row.get('subject', 'Imported ticket'),
                        'sender_email': row.get('sender_email', 'unknown@imported.com'),
                        'sender_name': row.get('sender_name', ''),
                        'body': row.get('body', ''),
                        'summary': row.get('summary', ''),
                        'category': row.get('category', 'autre'),
                        'priority': row.get('priority', 'medium'),
                        'status': row.get('status', 'new'),
                    })
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing ticket from CSV: {e}")
                    continue

        else:
            return jsonify({'error': 'Invalid file format. Expected .json or .csv'}), 400

        return jsonify({
            'message': f'{imported_count} tickets imported successfully',
            'imported': imported_count
        }), 200

    except Exception as e:
        logger.error(f"Error importing tickets: {e}")
        return jsonify({'error': str(e)}), 500
