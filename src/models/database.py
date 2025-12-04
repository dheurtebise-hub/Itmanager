"""
Gestion de la base de données SQLite
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
from contextlib import contextmanager

# Whitelist des tables autorisées pour prévenir l'injection SQL
ALLOWED_TABLES = {
    'tickets',
    'procedures',
    'categories',
    'knowledge_base',
    'api_costs',
    'sla_config',
    'sla_alerts',
    'email_templates',
    'ai_feedback',
    'daily_stats',
    'procedure_feedback',
    'ticket_procedures'
}

class Database:
    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger(__name__)

        if db_path is None:
            app_data = os.getenv('APPDATA', os.path.expanduser('~'))
            db_dir = Path(app_data) / "ITTicketManager" / "database"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_dir / "tickets.db")
        else:
            self.db_path = db_path

        self._connection = None
        self._init_database()

    def _init_database(self):
        """Initialise la base de données avec le schéma."""
        schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"

        if not schema_path.exists():
            self.logger.warning(f"Schema file not found: {schema_path}")
            return

        try:
            with self.get_connection() as conn:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                    conn.executescript(schema)
                conn.commit()
            self.logger.info("Database initialized successfully")

            # Exécuter les migrations
            self._run_migrations()

        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    def _run_migrations(self):
        """Exécute les migrations nécessaires."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Vérifier si la colonne is_not_user_request existe
                cursor.execute("PRAGMA table_info(tickets)")
                columns = [col[1] for col in cursor.fetchall()]

                if 'is_not_user_request' not in columns:
                    self.logger.info("Adding is_not_user_request column to tickets table")
                    cursor.execute("ALTER TABLE tickets ADD COLUMN is_not_user_request BOOLEAN DEFAULT 0")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_is_not_user_request ON tickets(is_not_user_request)")
                    conn.commit()
                    self.logger.info("Migration completed: is_not_user_request column added")

        except Exception as e:
            self.logger.error(f"Error running migrations: {e}")
            # Ne pas lever l'exception pour ne pas bloquer le démarrage

    @contextmanager
    def get_connection(self):
        """Context manager pour les connexions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Exécute une requête (INSERT, UPDATE, DELETE)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor

    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Récupère une seule ligne."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def fetchall(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Récupère toutes les lignes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _validate_table_name(self, table: str) -> None:
        """Valide que le nom de table est dans la whitelist (sécurité anti-injection SQL)."""
        if table not in ALLOWED_TABLES:
            raise ValueError(
                f"Table non autorisée: '{table}'. "
                f"Tables autorisées: {', '.join(sorted(ALLOWED_TABLES))}"
            )

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert une ligne et retourne l'ID."""
        self._validate_table_name(table)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = self.execute(query, tuple(data.values()))
        return cursor.lastrowid

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = None) -> int:
        """Met à jour des lignes."""
        self._validate_table_name(table)
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = tuple(data.values())
        if where_params:
            params = params + where_params

        cursor = self.execute(query, params)
        return cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = None) -> int:
        """Supprime des lignes."""
        self._validate_table_name(table)
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(query, params)
        return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Vérifie si une table existe."""
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Retourne les informations sur une table."""
        return self.fetchall(f"PRAGMA table_info({table_name})")

    def vacuum(self):
        """Optimise la base de données."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        self.logger.info("Database vacuumed")


# Instance globale
db = Database()
