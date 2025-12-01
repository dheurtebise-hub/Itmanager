"""
Script de diagnostic - Vérifie le contenu de la base de données
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🔍 Diagnostic de la base de données IT Ticket Manager")
print("=" * 60)
print()

# Importer après avoir modifié le path
from models.database import db

print(f"📁 Base de données: {db.db_path}")
print()

# Vérifier les tickets
try:
    tickets = db.fetchall("SELECT * FROM tickets ORDER BY received_date DESC LIMIT 10")

    if tickets:
        print(f"✅ {len(tickets)} ticket(s) trouvé(s) dans la base :")
        print()
        for i, ticket in enumerate(tickets, 1):
            print(f"  {i}. [{ticket['status']}] {ticket['subject'][:50]}")
            print(f"     De: {ticket['sender_email']}")
            print(f"     Date: {ticket['received_date']}")
            print(f"     Pièces jointes: {'Oui' if ticket.get('has_attachments') else 'Non'}")
            print(f"     Importance: {ticket.get('importance', 0)}")
            print()
    else:
        print("⚠️  Aucun ticket dans la base de données")
        print()
        print("Cela signifie que :")
        print("1. Soit l'import n'a jamais fonctionné")
        print("2. Soit les tickets créés avant la migration ont échoué")
        print()
        print("👉 Solution: Relancez l'application et cliquez sur 'Import initial'")

    print()

    # Statistiques
    count_by_status = db.fetchall("""
        SELECT status, COUNT(*) as count
        FROM tickets
        GROUP BY status
    """)

    if count_by_status:
        print("📊 Répartition par statut :")
        for stat in count_by_status:
            print(f"   - {stat['status']}: {stat['count']} ticket(s)")

except Exception as e:
    print(f"❌ Erreur lors de la lecture: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
