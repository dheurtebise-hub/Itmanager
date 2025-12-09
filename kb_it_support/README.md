# KB_IT_SUPPORT v1.0

Base de connaissances IT standalone avec interface dark theme terminal.

## 🎯 Vue d'ensemble

KB_IT_Support est une application de gestion de procédures IT extraite et améliorée depuis ITManager. Elle se concentre exclusivement sur la base de connaissances, sans système de ticketing.

## ✨ Fonctionnalités (Phase 1 - MVP)

### ✅ Implémenté

- **Base de données SQLite** avec schéma complet
  - Tables : procedures, categories (hiérarchiques), tags, procedure_tags, attachments, procedure_versions, settings
  - Support UTF-8 pour les accents français
  - Index optimisés pour les performances

- **Backend Flask** complet
  - API REST pour procédures, catégories, tags, paramètres
  - Modèles avec ORM simple
  - Services (AI, recherche - bases posées)
  - Versioning automatique des procédures

- **Frontend dark theme terminal**
  - Design system complet (voir cahier des charges)
  - Interface responsive
  - Navigation multi-vues (Home, Liste, Détail, Éditeur)
  - Police monospace (Fira Code) pour le style terminal

- **CRUD Procédures**
  - Création, lecture, édition, archivage
  - Éditeur markdown avec toolbar
  - Gestion des tags (manuels)
  - Upload de fichiers joints (structure prête)
  - Temps estimé
  - Description courte

- **Système de catégories hiérarchiques**
  - 6 catégories principales pré-remplies
  - 30+ sous-catégories
  - Arborescence dépliable dans la sidebar
  - Couleurs et icônes personnalisées

- **Système de tags**
  - Tags séparés en table dédiée
  - Auto-complétion (structure prête)
  - Usage count pour popularité

- **Recherche simple**
  - Par mots-clés dans titre/contenu/description
  - Filtrage par catégorie
  - Pagination

- **Versioning**
  - Sauvegarde automatique à chaque modification
  - Historique complet (interface à finaliser)
  - Restauration de versions

## 🚀 Installation

### Prérequis

- Python 3.8+
- pip

### Installation des dépendances

```bash
cd kb_it_support
pip install -r requirements.txt
```

### Lancement

```bash
python main.py
```

L'application sera accessible sur `http://localhost:5000`

## 📁 Structure du projet

```
kb_it_support/
├── app/
│   ├── __init__.py              # Initialisation Flask
│   ├── models/
│   │   ├── database.py          # Gestion SQLite
│   │   ├── procedure.py         # Modèle Procedure
│   │   ├── category.py          # Modèle Category
│   │   └── tag.py               # Modèle Tag
│   ├── routes/
│   │   ├── procedure_routes.py  # API procédures
│   │   ├── category_routes.py   # API catégories
│   │   ├── tag_routes.py        # API tags
│   │   └── settings_routes.py   # API paramètres
│   └── services/
│       └── ai_service.py        # Service IA (Claude)
├── database/
│   ├── schema.sql               # Schéma BDD
│   ├── kb_support.db            # Base SQLite (générée)
│   └── migrate_from_itmanager.py # Script de migration
├── static/
│   ├── css/
│   │   └── main.css             # Dark theme complet
│   └── js/
│       ├── api.js               # Client API
│       └── app.js               # Logique frontend
├── templates/
│   └── index.html               # SPA principale
├── storage/
│   └── procedures/              # Fichiers uploadés
├── config.py                    # Configuration
├── main.py                      # Point d'entrée
└── requirements.txt             # Dépendances
```

## 🔧 Configuration

### Clé API Claude (optionnel)

Pour utiliser la génération de tags par IA :

1. Obtenir une clé API sur https://console.anthropic.com
2. Dans l'interface : Settings (⚙) → Clé API Claude
3. Tester la connexion avec le bouton "Tester la connexion Claude"

Ou définir la variable d'environnement :
```bash
export CLAUDE_API_KEY="sk-ant-..."
```

### Paramètres disponibles

Dans la table `settings` :
- `claude_api_key` - Clé API Claude
- `claude_model` - Modèle utilisé (claude-sonnet-4-5-20250929)
- `claude_temperature` - Température (0.7)
- `claude_max_tokens` - Tokens max (1024)
- `company_name` - Nom de l'entreprise

## 📊 Catégories pré-remplies

### Principales (6)

1. **📧 Office 365** (#06b6d4)
   - Outlook, Teams, OneDrive, SharePoint, Exchange

2. **🖥️ Matériel** (#f97316)
   - Ordinateurs, Imprimantes, Périphériques, Téléphonie

3. **🌐 Réseau** (#10b981)
   - VPN, Wi-Fi, Partages réseau, Accès distant

4. **👤 Comptes et accès** (#fbbf24)
   - Active Directory, Création comptes, Reset passwords, Permissions

5. **💾 Logiciels** (#8b5cf6)
   - Installation, Désinstallation, Mises à jour, Licences, Maintenance

6. **⚙️ Système** (#ef4444)
   - Windows 10/11, PowerShell, GPO, Sauvegardes

## 🎨 Design System

### Palette de couleurs

```css
--bg-primary: #1f2937;      /* Fond principal */
--bg-secondary: #111827;    /* Sidebar */
--bg-cards: #374151;        /* Cards */
--accent-cyan: #06b6d4;     /* Primaire */
--accent-orange: #f97316;   /* Secondaire */
```

### Typographie

- **Primaire** : Fira Code (monospace) - Titres, boutons, labels
- **Secondaire** : Inter (sans-serif) - Contenu long

## 🧪 Tests

### Test API

```bash
# Liste des catégories
curl http://localhost:5000/api/categories

# Liste des procédures
curl http://localhost:5000/api/procedures

# Créer une procédure
curl -X POST http://localhost:5000/api/procedures \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "category_id": 7,
    "content": "## Test\n\nContenu de test",
    "tags": ["test"]
  }'
```

## 📝 Utilisation

### Créer une procédure

1. Cliquer sur **+ NEW**
2. Remplir les champs obligatoires :
   - Titre
   - Catégorie
   - Contenu (markdown)
3. Ajouter des tags (manuellement ou via IA si configuré)
4. (Optionnel) Ajouter des fichiers joints
5. Cliquer sur **SAVE**

### Éditer une procédure

1. Cliquer sur une procédure dans la liste
2. Cliquer sur **EDIT**
3. Modifier les champs
4. **SAVE**

### Rechercher

- Utiliser la barre de recherche en haut
- Ou naviguer par catégories dans la sidebar

## 🔄 Migration depuis ITManager

Un script de migration est disponible :

```bash
cd database
python migrate_from_itmanager.py
```

Le script :
- Migre toutes les procédures actives
- Convertit les steps (JSON) en contenu markdown
- Migre les keywords vers le système de tags
- Mappe les anciennes catégories vers les nouvelles
- Crée la première version de chaque procédure

## ⚠️ Limitations connues

### Phase 1 (MVP actuel)

- Pas de recherche IA sémantique (uniquement mots-clés)
- Génération tags IA non testée (nécessite clé API)
- Upload fichiers joints : backend OK, frontend à finaliser
- Historique versions : backend OK, interface à finaliser
- Pas de notifications toast (alerts simples)
- Pas d'export PDF
- Pas de multi-utilisateurs / authentification

## 🚧 Prochaines étapes (voir NEXT_STEPS.md)

### Phase 2 - Recherche avancée
- Auto-complétion recherche
- Filtres avancés
- Tri personnalisé

### Phase 3 - Tags IA
- Génération automatique tags
- Recherche sémantique

### Phase 4 - Multimédia
- Finaliser upload/download fichiers
- Preview images/PDF
- Coloration syntaxe PowerShell

### Phase 5 - Fonctionnalités avancées
- Interface historique versions
- Export PDF
- Import Word/PDF

### Phase 6 - Packaging
- PyInstaller .exe
- Documentation utilisateur
- Guide installation

## 🐛 Debug

### Logs

Les logs sont affichés dans la console :

```
2025-12-09 11:32:32,168 - app.models.database - INFO - Database initialized successfully
```

### Base de données

Emplacement : `/kb_it_support/database/kb_support.db`

Inspection :
```bash
sqlite3 database/kb_support.db
.tables
.schema procedures
SELECT * FROM procedures;
```

## 📄 Licence

Projet interne - Tous droits réservés

## 🤝 Contribution

Application développée par Claude (Anthropic) selon le cahier des charges fourni.

Pour toute modification, consulter `CLAUDE.md` dans le répertoire parent pour les instructions détaillées.

---

**Version** : 1.0.0
**Date** : Décembre 2024
**Statut** : Phase 1 MVP - ✅ Complète
