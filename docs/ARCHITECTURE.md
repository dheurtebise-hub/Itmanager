# 🏗️ Architecture - IT Ticket Manager

## Vue d'ensemble

IT Ticket Manager est une application Desktop Windows construite avec une architecture client-serveur simple :

```
┌─────────────────────────────────────────────────────┐
│                  NAVIGATEUR WEB                      │
│              (Interface utilisateur)                 │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST
                   ▼
┌─────────────────────────────────────────────────────┐
│              SERVEUR FLASK LOCAL                     │
│               (Backend Python)                       │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │
│  │  Routes    │  │  Services  │  │   Models      │ │
│  │  (API)     │  │  (Métier)  │  │  (Données)    │ │
│  └────────────┘  └────────────┘  └───────────────┘ │
└──────────┬──────────────┬───────────────┬──────────┘
           │              │               │
           ▼              ▼               ▼
     ┌─────────┐    ┌─────────┐    ┌──────────┐
     │  SQLite │    │ Outlook │    │ Claude   │
     │   BDD   │    │  (COM)  │    │   API    │
     └─────────┘    └─────────┘    └──────────┘
```

## 📁 Structure du code

### Backend (Python)

#### **models/** - Couche de données
- `database.py` : Gestion SQLite avec context managers
- `ticket.py` : Modèle métier pour les tickets

#### **services/** - Couche métier
- `secure_storage.py` : Stockage sécurisé (Windows Credential Manager)
- `email_connector.py` : Connexion Outlook via COM
- `ai_service.py` : Intégration API Anthropic
- `suggestion_cache.py` : Cache LRU pour suggestions
- `sla_service.py` : Gestion des SLA
- `sync_service.py` : Synchronisation automatique
- `export_service.py` : Export CSV/Excel
- `backup_service.py` : Backups automatiques
- `notifications.py` : Notifications Windows

#### **routes/** - Couche API
- `ticket_routes.py` : CRUD tickets + stats
- `setup_routes.py` : Wizard de configuration
- `export_routes.py` : Export de données
- `config_routes.py` : Configuration application

#### **utils/** - Utilitaires
- `logger.py` : Logging JSON
- `rate_limiter.py` : Rate limiting API
- `helpers.py` : Fonctions utilitaires

### Frontend (JavaScript Vanilla)

#### **static/css/**
- `main.css` : Styles globaux
- `themes.css` : Système de thèmes (clair/sombre)
- `kanban.css` : Interface Kanban
- `setup.css` : Wizard de configuration

#### **static/js/**
- `api_client.js` : Client HTTP pour l'API
- `kanban.js` : Logique du Kanban
- `ticket_modal.js` : Modal de détails
- `theme.js` : Gestion des thèmes
- `keyboard_shortcuts.js` : Raccourcis clavier

#### **templates/**
- Template engine : Jinja2
- Structure : base.html + pages héritées

## 🔄 Flux de données principaux

### 1. Synchronisation des emails

```
Outlook → email_connector → ai_service (catégorisation)
         → ticket.create() → SQLite → notification_service
```

### 2. Suggestion de résolution

```
User click → API /suggest → ticket.get_similar()
           → knowledge_base.search() → ai_service.suggest()
           → suggestion_cache → Response
```

### 3. Mise à jour de ticket

```
User action → API /tickets/{id} → ticket.update()
            → SQLite → WebSocket refresh (si implémenté)
```

## 🔐 Sécurité

### Stockage des secrets
- Clé API Claude : Windows Credential Manager (keyring)
- Pas de stockage en clair

### API
- Rate limiting : 100 req/min (API), 20 req/min (IA)
- CSRF désactivé (app locale)
- Pas d'authentification (usage monoposte)

### Données
- SQLite avec transactions
- Backups automatiques quotidiens
- Pas de données sensibles loggées

## 📊 Base de données

### Schéma principal

```sql
tickets
├── id (PK)
├── message_id (UNIQUE, Outlook ID)
├── subject, sender_email, body
├── category, priority, status
├── ai_categorized, ai_confidence
├── resolution, resolution_time_minutes
└── timestamps (created, updated, resolved)

knowledge_base
├── id (PK)
├── title, category, content
├── usage_count
└── source_ticket_id (FK)

categories
├── id (PK)
├── name, color, icon
└── order_index

sla_config, email_templates, api_costs, etc.
```

### Index optimisés
- Composite : (status, category, priority)
- Individuels : status, category, priority, received_date
- Full-text search : knowledge_base (FTS5)

## 🚀 Déploiement

### Build
1. PyInstaller → .exe standalone
2. Inno Setup → Installeur Windows
3. Résultat : 1 fichier .exe pour installation

### Runtime
- Serveur Flask : localhost:5000
- Auto-start navigateur
- Tray icon (optionnel)

## 🔧 Configuration

### Fichiers de config
- `config.json` : %APPDATA%/ITTicketManager/
- `tickets.db` : %APPDATA%/ITTicketManager/database/
- Logs : %APPDATA%/ITTicketManager/logs/

### Variables d'environnement
- `PORT` : Port du serveur (défaut 5000)
- `NO_BROWSER` : Désactiver ouverture auto
- `APPDATA` : Répertoire de données

## 🧪 Tests

### Structure
- `tests/` : Tests unitaires (pytest)
- Couverture : Services critiques
- CI/CD : À implémenter

## 🔮 Évolutions futures

### Court terme
- WebSocket pour rafraîchissement temps réel
- Système de plugins
- API REST documentée (OpenAPI)

### Long terme
- Version multi-utilisateurs
- Application mobile
- Intégration autres sources (Teams, Slack)

## 📚 Dépendances principales

| Dépendance | Version | Usage |
|------------|---------|-------|
| Flask | 3.0.0 | Serveur web |
| anthropic | 0.25.0 | API Claude |
| pywin32 | 306 | Outlook COM |
| keyring | 24.3.0 | Stockage sécurisé |
| openpyxl | 3.1.2 | Export Excel |
| pytest | 7.4.3 | Tests |

## 🤝 Contribution

Voir [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📄 Licence

MIT - Voir [LICENSE](../LICENSE)
