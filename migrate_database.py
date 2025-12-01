"""
Script de migration de la base de données
Ajoute les colonnes manquantes has_attachments et importance
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🔧 Migration de la base de données IT Ticket Manager...")
print()

# Importer après avoir modifié le path
from models.database import db

print(f"📁 Base de données: {db.db_path}")
print()

# Vérifier les colonnes existantes
try:
    # Récupérer les infos de la table
    columns_info = db.fetchall("PRAGMA table_info(tickets)")
    existing_columns = [col['name'] for col in columns_info]

    print(f"✅ Table 'tickets' trouvée avec {len(existing_columns)} colonnes")

    # Vérifier si les colonnes manquent
    needs_has_attachments = 'has_attachments' not in existing_columns
    needs_importance = 'importance' not in existing_columns

    if not needs_has_attachments and not needs_importance:
        print("✅ Base de données déjà à jour !")
        print()
        sys.exit(0)

    print()
    print("⚠️  Colonnes manquantes détectées :")
    if needs_has_attachments:
        print("   - has_attachments")
    if needs_importance:
        print("   - importance")

    print()
    print("🔨 Ajout des colonnes...")

    # Ajouter les colonnes manquantes
    if needs_has_attachments:
        db.execute("ALTER TABLE tickets ADD COLUMN has_attachments BOOLEAN DEFAULT FALSE")
        print("   ✅ Colonne 'has_attachments' ajoutée")

    if needs_importance:
        db.execute("ALTER TABLE tickets ADD COLUMN importance INTEGER DEFAULT 0")
        print("   ✅ Colonne 'importance' ajoutée")

    print()

    # Vérifier
    columns_info = db.fetchall("PRAGMA table_info(tickets)")
    existing_columns = [col['name'] for col in columns_info]

    if 'has_attachments' in existing_columns and 'importance' in existing_columns:
        print(f"✅ Migration réussie ! Table 'tickets' a maintenant {len(existing_columns)} colonnes")
    else:
        print("❌ Erreur : Les colonnes n'ont pas été ajoutées correctement")
        sys.exit(1)

except Exception as e:
    print(f"❌ Erreur lors de la migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("✨ Migration terminée !")
print()
print("Vous pouvez maintenant lancer l'application avec: python src/main.py")
