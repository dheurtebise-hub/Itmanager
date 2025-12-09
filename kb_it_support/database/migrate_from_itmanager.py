"""
Script de migration des données d'ITManager vers KB_IT_Support
Migre les procédures, catégories et tags
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

def migrate_data(source_db_path, target_db_path):
    """Migre les données de la base ITManager vers KB_IT_Support."""

    print("🚀 Début de la migration...")
    print(f"Source: {source_db_path}")
    print(f"Cible: {target_db_path}")

    # Connexion aux deux bases
    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    target_conn = sqlite3.connect(target_db_path)
    target_conn.row_factory = sqlite3.Row

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    try:
        # 1. Migrer les catégories (adapter l'ancien format au nouveau)
        print("\n📁 Migration des catégories...")

        # Les catégories sont déjà pré-remplies dans le nouveau schéma
        # On va juste vérifier s'il y a des catégories personnalisées dans l'ancien
        source_cursor.execute("""
            SELECT name, color, icon, order_index, is_active
            FROM categories
            WHERE name NOT IN (
                'installation_logiciel', 'depannage_materiel', 'demande_licence',
                'support_applicatif', 'reseau', 'securite', 'autre'
            )
        """)

        custom_categories = source_cursor.fetchall()

        if custom_categories:
            print(f"  ⚠️  Trouvé {len(custom_categories)} catégories personnalisées")
            for cat in custom_categories:
                # Ajouter comme catégorie de niveau 1 dans la nouvelle base
                target_cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon, is_active)
                    VALUES (?, ?, NULL, ?, ?, ?, ?)
                """, (
                    cat['name'],
                    cat['name'][:8].lower().replace(' ', '_'),  # Générer short_name
                    cat['order_index'] if cat['order_index'] else 99,
                    cat['color'],
                    cat['icon'],
                    cat['is_active']
                ))

        # Mapping ancien nom catégorie -> nouvelle catégorie ID
        category_mapping = {
            'installation_logiciel': 22,  # Logiciels > Installation
            'depannage_materiel': 13,     # Matériel > Ordinateurs
            'demande_licence': 25,        # Logiciels > Licences
            'support_applicatif': 5,      # Logiciels (parent)
            'reseau': 3,                  # Réseau (parent)
            'securite': 17,               # Réseau > VPN (sécurité)
            'autre': 5                    # Par défaut: Logiciels
        }

        print(f"  ✅ Catégories prêtes")

        # 2. Migrer les procédures
        print("\n📄 Migration des procédures...")

        source_cursor.execute("""
            SELECT id, title, description, steps, category, keywords, source_ticket_id,
                   created_by, created_at, updated_at, usage_count, is_active
            FROM procedures
            WHERE is_active = 1
        """)

        procedures = source_cursor.fetchall()
        print(f"  Trouvé {len(procedures)} procédures actives")

        procedure_id_mapping = {}  # Ancien ID -> Nouveau ID

        for proc in procedures:
            # Parser les steps (JSON) et les convertir en contenu markdown
            try:
                steps = json.loads(proc['steps']) if proc['steps'] else []
            except:
                steps = []

            # Créer le contenu markdown
            content = ""
            if proc['description']:
                content += f"## Description\n\n{proc['description']}\n\n"

            if steps:
                content += "## Étapes\n\n"
                for i, step in enumerate(steps, 1):
                    content += f"{i}. {step}\n"

            # Déterminer la catégorie cible
            old_category = proc['category'] if proc['category'] else 'autre'
            new_category_id = category_mapping.get(old_category, 5)

            # Insérer la procédure
            target_cursor.execute("""
                INSERT INTO procedures (
                    title, content, description, category_id, created_by,
                    created_at, updated_at, usage_count, is_archived
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proc['title'],
                content,
                proc['description'],
                new_category_id,
                proc['created_by'] if proc['created_by'] else 'migrated',
                proc['created_at'],
                proc['updated_at'],
                proc['usage_count'] if proc['usage_count'] else 0,
                not proc['is_active']
            ))

            new_proc_id = target_cursor.lastrowid
            procedure_id_mapping[proc['id']] = new_proc_id

            # Créer la première version
            target_cursor.execute("""
                INSERT INTO procedure_versions (
                    procedure_id, version_number, content, changed_by, changed_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                new_proc_id,
                1,
                content,
                proc['created_by'] if proc['created_by'] else 'migrated',
                proc['created_at']
            ))

            # Migrer les keywords vers tags
            if proc['keywords']:
                try:
                    keywords = json.loads(proc['keywords']) if isinstance(proc['keywords'], str) else proc['keywords']
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            if keyword and isinstance(keyword, str):
                                # Insérer ou récupérer le tag
                                target_cursor.execute("""
                                    INSERT OR IGNORE INTO tags (name, usage_count)
                                    VALUES (?, 0)
                                """, (keyword.lower().strip(),))

                                target_cursor.execute("""
                                    SELECT id FROM tags WHERE name = ?
                                """, (keyword.lower().strip(),))

                                tag_row = target_cursor.fetchone()
                                if tag_row:
                                    tag_id = tag_row['id']

                                    # Lier le tag à la procédure
                                    target_cursor.execute("""
                                        INSERT OR IGNORE INTO procedure_tags (
                                            procedure_id, tag_id, is_ai_generated
                                        ) VALUES (?, ?, ?)
                                    """, (new_proc_id, tag_id, True))

                                    # Incrémenter usage_count du tag
                                    target_cursor.execute("""
                                        UPDATE tags SET usage_count = usage_count + 1
                                        WHERE id = ?
                                    """, (tag_id,))
                except Exception as e:
                    print(f"  ⚠️  Erreur migration keywords pour procédure {proc['id']}: {e}")

        print(f"  ✅ {len(procedures)} procédures migrées")

        # 3. Statistiques finales
        print("\n📊 Statistiques de migration:")

        target_cursor.execute("SELECT COUNT(*) as count FROM procedures WHERE is_archived = 0")
        proc_count = target_cursor.fetchone()['count']
        print(f"  Procédures actives: {proc_count}")

        target_cursor.execute("SELECT COUNT(*) as count FROM tags")
        tag_count = target_cursor.fetchone()['count']
        print(f"  Tags uniques: {tag_count}")

        target_cursor.execute("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
        cat_count = target_cursor.fetchone()['count']
        print(f"  Catégories actives: {cat_count}")

        # Commit et fermeture
        target_conn.commit()
        print("\n✅ Migration terminée avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur durant la migration: {e}")
        target_conn.rollback()
        raise

    finally:
        source_conn.close()
        target_conn.close()


def main():
    """Point d'entrée du script."""

    # Chemins par défaut
    script_dir = Path(__file__).parent

    # Base source (ITManager)
    import os
    app_data = os.getenv('APPDATA', os.path.expanduser('~'))
    source_db = Path(app_data) / "ITTicketManager" / "database" / "tickets.db"

    # Base cible (KB_IT_Support)
    target_db = script_dir / "kb_support.db"

    # Vérifier que la source existe
    if not source_db.exists():
        print(f"❌ Base de données source non trouvée: {source_db}")
        print("Veuillez vérifier le chemin ou spécifier un chemin personnalisé.")
        sys.exit(1)

    # Créer le schéma de la base cible si elle n'existe pas
    if not target_db.exists():
        print(f"📦 Création de la base de données cible: {target_db}")

        # Lire et exécuter le schéma SQL
        schema_path = script_dir / "schema.sql"
        if not schema_path.exists():
            print(f"❌ Fichier schema.sql non trouvé: {schema_path}")
            sys.exit(1)

        conn = sqlite3.connect(target_db)
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.close()

        print(f"✅ Base de données créée")

    # Lancer la migration
    migrate_data(str(source_db), str(target_db))


if __name__ == "__main__":
    main()
