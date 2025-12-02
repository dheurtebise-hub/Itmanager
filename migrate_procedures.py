"""
Script de migration pour ajouter les tables de procédures
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_procedures():
    """Ajoute les tables de procédures à la base de données."""

    logger.info("Début de la migration des procédures...")

    # SQL pour créer les tables de procédures
    procedures_sql = """
    -- Table des procédures
    CREATE TABLE IF NOT EXISTS procedures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        steps TEXT,
        category TEXT,
        keywords TEXT,
        source_ticket_id INTEGER,
        created_by TEXT DEFAULT 'ai',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        usage_count INTEGER DEFAULT 0,
        positive_feedback_count INTEGER DEFAULT 0,
        negative_feedback_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (source_ticket_id) REFERENCES tickets(id)
    );

    -- Table des feedbacks sur les procédures
    CREATE TABLE IF NOT EXISTS procedure_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        procedure_id INTEGER NOT NULL,
        ticket_id INTEGER NOT NULL,
        feedback_type TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (procedure_id) REFERENCES procedures(id),
        FOREIGN KEY (ticket_id) REFERENCES tickets(id),
        UNIQUE (procedure_id, ticket_id)
    );

    -- Table pour associer les procédures aux tickets
    CREATE TABLE IF NOT EXISTS ticket_procedures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        procedure_id INTEGER NOT NULL,
        confidence REAL DEFAULT 0.0,
        was_suggested BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets(id),
        FOREIGN KEY (procedure_id) REFERENCES procedures(id),
        UNIQUE (ticket_id, procedure_id)
    );

    -- Index pour optimisation des recherches de procédures
    CREATE INDEX IF NOT EXISTS idx_procedures_category ON procedures(category);
    CREATE INDEX IF NOT EXISTS idx_procedures_active ON procedures(is_active);
    CREATE INDEX IF NOT EXISTS idx_procedures_usage ON procedures(usage_count DESC);
    CREATE INDEX IF NOT EXISTS idx_procedure_feedback_procedure ON procedure_feedback(procedure_id);
    CREATE INDEX IF NOT EXISTS idx_ticket_procedures_ticket ON ticket_procedures(ticket_id);
    CREATE INDEX IF NOT EXISTS idx_ticket_procedures_procedure ON ticket_procedures(procedure_id);
    """

    try:
        with db.get_connection() as conn:
            # Exécuter les commandes SQL
            conn.executescript(procedures_sql)
            conn.commit()

        logger.info("✅ Tables de procédures créées avec succès !")

        # Vérifier les tables
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%procedure%'")
            tables = cursor.fetchall()

            logger.info(f"Tables créées : {[t[0] for t in tables]}")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration : {e}")
        return False


if __name__ == '__main__':
    success = migrate_procedures()
    sys.exit(0 if success else 1)
