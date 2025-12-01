"""
Script pour vider tous les tickets
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🗑️  Suppression de tous les tickets...")
print()

# Importer après avoir modifié le path
from models.database import db

try:
    # Compter les tickets
    count = db.fetchone("SELECT COUNT(*) as count FROM tickets")
    ticket_count = count['count']

    if ticket_count == 0:
        print("✅ Aucun ticket à supprimer")
        sys.exit(0)

    print(f"⚠️  {ticket_count} ticket(s) vont être supprimés")

    # Supprimer tous les tickets
    db.execute("DELETE FROM tickets")

    print(f"✅ {ticket_count} ticket(s) supprimé(s)")
    print()
    print("Vous pouvez maintenant réimporter vos emails avec 'Import initial'")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
