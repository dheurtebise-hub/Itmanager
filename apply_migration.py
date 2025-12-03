#!/usr/bin/env python3
"""
Script to apply database migrations
"""
import sqlite3
import os

def apply_migration():
    db_path = 'tickets.db'
    migration_file = 'migrations/add_is_not_user_request_column.sql'

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False

    if not os.path.exists(migration_file):
        print(f"Migration file not found: {migration_file}")
        return False

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Apply migration
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute each statement
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)

        conn.commit()
        conn.close()

        print("✅ Migration applied successfully!")
        return True

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Column already exists, skipping migration.")
            return True
        else:
            print(f"❌ Error applying migration: {e}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    apply_migration()
