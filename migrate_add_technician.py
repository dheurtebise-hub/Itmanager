#!/usr/bin/env python3
"""
Migration: Ajout du système de tagging des techniciens
"""

import sqlite3
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.database import Database

def main():
    print("🔧 Migration: Ajout du système de techniciens")
    print("=" * 50)

    db = Database()

    # Vérifier si la colonne existe déjà
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tickets)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'assigned_to' in columns:
            print("✅ La colonne 'assigned_to' existe déjà")
        else:
            print("📝 Ajout de la colonne 'assigned_to'...")
            cursor.execute("ALTER TABLE tickets ADD COLUMN assigned_to TEXT")
            conn.commit()
            print("✅ Colonne 'assigned_to' ajoutée")

        # Créer l'index
        print("📝 Création de l'index...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to)")
        conn.commit()
        print("✅ Index créé")

        # Créer une table pour les techniciens (optionnel, pour liste prédéfinie)
        print("📝 Création de la table des techniciens...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Table 'technicians' créée")

        # Ajouter quelques techniciens par défaut si la table est vide
        cursor.execute("SELECT COUNT(*) as count FROM technicians")
        count = cursor.fetchone()[0]

        if count == 0:
            print("📝 Ajout des techniciens par défaut...")
            default_technicians = [
                ('Non assigné', None),
                ('Support Niveau 1', 'support-n1@example.com'),
                ('Support Niveau 2', 'support-n2@example.com'),
                ('Administrateur Système', 'admin@example.com'),
            ]
            for name, email in default_technicians:
                cursor.execute(
                    "INSERT INTO technicians (name, email) VALUES (?, ?)",
                    (name, email)
                )
            conn.commit()
            print(f"✅ {len(default_technicians)} techniciens par défaut ajoutés")
        else:
            print(f"ℹ️  {count} techniciens déjà présents dans la base")

    print()
    print("✅ Migration terminée avec succès!")
    print()
    print("💡 Vous pouvez maintenant:")
    print("   - Assigner des techniciens aux tickets")
    print("   - Filtrer les tickets par technicien")
    print("   - Gérer la liste des techniciens dans les paramètres")

if __name__ == '__main__':
    main()
