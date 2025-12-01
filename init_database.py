"""
Script d'initialisation de la base de données
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🔧 Initialisation de la base de données IT Ticket Manager...")
print()

# Importer après avoir modifié le path
from models.database import db

print(f"📁 Base de données: {db.db_path}")
print()

# Vérifier si les tables existent
try:
    count = db.fetchone("SELECT COUNT(*) as count FROM tickets")
    print(f"✅ Base déjà initialisée ({count['count']} tickets)")
except:
    print("⚠️  Base non initialisée, création des tables...")

    # Forcer la réinitialisation
    db._init_database()

    # Vérifier
    try:
        count = db.fetchone("SELECT COUNT(*) as count FROM tickets")
        print(f"✅ Base initialisée avec succès ! ({count['count']} tickets)")

        # Vérifier les catégories
        categories = db.fetchall("SELECT name FROM categories")
        print(f"✅ {len(categories)} catégories par défaut créées")

        # Vérifier les templates
        templates = db.fetchall("SELECT name FROM email_templates")
        print(f"✅ {len(templates)} templates email créés")

    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        sys.exit(1)

print()
print("✨ Initialisation terminée !")
print()
print("Vous pouvez maintenant lancer l'application avec: python src/main.py")
