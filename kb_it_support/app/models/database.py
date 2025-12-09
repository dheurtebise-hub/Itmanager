"""
Gestion de la base de données SQLite pour KB_IT_Support
"""

import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Whitelist des tables autorisées
ALLOWED_TABLES = {
    'procedures',
    'categories',
    'tags',
    'procedure_tags',
    'attachments',
    'procedure_versions',
    'settings'
}


class Database:
    """Gestionnaire de base de données SQLite."""

    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger(__name__)

        if db_path is None:
            import config
            self.db_path = str(config.DATABASE_PATH)
        else:
            self.db_path = db_path

        self.logger.info(f"Database path: {self.db_path}")

    def init_database(self):
        """Initialise la base de données avec le schéma."""
        schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"

        if not Path(self.db_path).exists():
            self.logger.info("Database not found, creating new database")

            if not schema_path.exists():
                self.logger.error(f"Schema file not found: {schema_path}")
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

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
        else:
            self.logger.info("Database already exists")

    @contextmanager
    def get_connection(self):
        """Context manager pour les connexions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Support UTF-8
        conn.execute("PRAGMA encoding = 'UTF-8'")
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
        """Valide que le nom de table est dans la whitelist."""
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

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        result = self.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return result['value'] if result else default

    def set_setting(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        from datetime import datetime
        self.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, str(value), datetime.now().isoformat()))

    def vacuum(self):
        """Optimise la base de données."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        self.logger.info("Database vacuumed")


# Instance globale
db = Database()
