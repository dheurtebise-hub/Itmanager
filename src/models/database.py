"""
Gestion de la base de données SQLite
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
from contextlib import contextmanager

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
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

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

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert une ligne et retourne l'ID."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = self.execute(query, tuple(data.values()))
        return cursor.lastrowid

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = None) -> int:
        """Met à jour des lignes."""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = tuple(data.values())
        if where_params:
            params = params + where_params

        cursor = self.execute(query, params)
        return cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = None) -> int:
        """Supprime des lignes."""
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
