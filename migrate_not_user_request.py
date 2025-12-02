"""
Script de migration pour ajouter le champ is_not_user_request
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_not_user_request():
    """Ajoute le champ is_not_user_request à la table tickets."""

    logger.info("Début de la migration is_not_user_request...")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Vérifier si la colonne existe déjà
            cursor.execute("PRAGMA table_info(tickets)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'is_not_user_request' in columns:
                logger.info("⚠️  La colonne is_not_user_request existe déjà")
                return True

            # Ajouter la colonne
            cursor.execute("""
                ALTER TABLE tickets
                ADD COLUMN is_not_user_request BOOLEAN DEFAULT FALSE
            """)

            conn.commit()

        logger.info("✅ Colonne is_not_user_request ajoutée avec succès !")

        # Vérifier l'ajout
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tickets)")
            columns = cursor.fetchall()

            logger.info(f"Colonnes dans la table tickets : {[col[1] for col in columns]}")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration : {e}")
        return False


if __name__ == '__main__':
    success = migrate_not_user_request()
    sys.exit(0 if success else 1)
