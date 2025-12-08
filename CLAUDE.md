# ITManager - Documentation Technique Complète

## Vue d'ensemble

**ITManager** est un système de gestion de tickets IT avec intelligence artificielle, conçu pour automatiser et optimiser le support informatique.

### Technologies principales
- **Backend**: Python 3.8+ / Flask
- **Base de données**: SQLite
- **Frontend**: Vanilla JavaScript (ES6+)
- **IA**: Claude (Anthropic) via API
- **Intégration**: Microsoft Outlook OAuth 2.0
- **Styling**: CSS custom avec variables CSS

## Architecture

```
ITManager/
├── src/
│   ├── app.py                    # Point d'entrée Flask
│   ├── config.py                 # Configuration centralisée
│   ├── models/
│   │   ├── database.py          # Gestion SQLite + ORM simple
│   │   ├── ticket.py            # Modèle Ticket
│   │   └── procedure.py         # Modèle Procedure
│   ├── routes/
│   │   ├── ticket_routes.py     # API CRUD tickets
│   │   ├── procedure_routes.py  # API CRUD procédures + analytics
│   │   ├── technician_routes.py # API CRUD techniciens
│   │   ├── category_routes.py   # API catégories (pour procédures)
│   │   ├── setup_routes.py      # Assistant configuration initiale
│   │   ├── config_routes.py     # Gestion configuration
│   │   ├── export_routes.py     # Export CSV/XLSX
│   │   └── import_export_routes.py # Import/export procédures
│   ├── services/
│   │   ├── ai_service.py        # Interface avec Claude API
│   │   ├── outlook_service.py   # Synchronisation Outlook
│   │   ├── procedure_service.py # Logique métier procédures
│   │   ├── search_service.py    # Index inversé + recherche
│   │   ├── sla_service.py       # Gestion SLA
│   │   └── backup_service.py    # Sauvegardes automatiques
│   ├── utils/
│   │   └── rate_limiter.py      # Rate limiting API
│   ├── templates/
│   │   └── index.html           # SPA principale
│   └── static/
│       ├── css/
│       │   └── kanban.css       # Styles globaux
│       └── js/
│           ├── api_client.js    # Client API REST
│           ├── kanban.js        # Interface Kanban
│           ├── ticket_modal.js  # Modal détail ticket
│           ├── technicians.js   # Gestion techniciens
│           ├── procedures_management.js # Interface procédures
│           └── ...
├── database/
│   └── schema.sql               # Schéma initial
├── migrations/
│   └── *.sql                    # Migrations SQL
└── backups/                     # Sauvegardes DB auto
```

## Schéma de Base de Données

### Table `tickets`
```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outlook_id TEXT UNIQUE,
    subject TEXT NOT NULL,
    body TEXT,
    sender_email TEXT,
    sender_name TEXT,
    received_date DATETIME,
    status TEXT DEFAULT 'new',           -- 'new', 'in_progress', 'resolved'
    priority TEXT DEFAULT 'medium',      -- 'low', 'medium', 'high'
    category TEXT,                       -- Catégorie IA (legacy)
    assigned_to TEXT,                    -- Technicien assigné (nouveau)
    ai_confidence REAL,                  -- Confiance IA catégorisation
    summary TEXT,                        -- Résumé IA
    resolution TEXT,                     -- Solution appliquée
    is_not_user_request BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assigned_to ON tickets(assigned_to);
```

### Table `procedures`
```sql
CREATE TABLE procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT,
    steps TEXT,                          -- JSON array des étapes
    keywords TEXT,                       -- Mots-clés séparés par virgules
    source_ticket_id INTEGER,
    usage_count INTEGER DEFAULT 0,
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_ticket_id) REFERENCES tickets(id)
);
```

### Table `technicians`
```sql
CREATE TABLE technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Table `categories`
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT '📁',
    color TEXT DEFAULT '#0079BF',
    order_index INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Tables Analytics
- `procedure_feedback` - Feedbacks utilisateurs sur procédures
- `ticket_procedures` - Liens tickets ↔ procédures appliquées
- `ai_feedback` - Feedback sur résumés IA
- `daily_stats` - Statistiques quotidiennes agrégées
- `api_costs` - Tracking coûts API Claude

### Tables SLA
- `sla_config` - Configuration SLA par priorité
- `sla_alerts` - Alertes SLA déclenchées

## Fonctionnalités Clés

### 1. Synchronisation Outlook

**Service**: `src/services/outlook_service.py`

- OAuth 2.0 Microsoft 365
- Synchronisation bidirectionnelle
- Mapping dossiers Outlook ↔ statuts internes
- Gestion tokens refresh automatique
- Parser emails en threads conversationnels

**Configuration requise**:
```python
config.set('outlook_client_id', '...')
config.set('outlook_client_secret', '...')
config.set('outlook_tenant_id', '...')
```

### 2. Intelligence Artificielle

**Service**: `src/services/ai_service.py`

**Modèle utilisé**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)

**Fonctionnalités IA**:

#### a) Catégorisation automatique
```python
categorize_ticket(ticket_data) -> {category, confidence, reasoning}
```
- Analyse sujet + corps du ticket
- Retourne catégorie + score de confiance (0-1)
- Utilise few-shot learning avec exemples

#### b) Génération de résumés
```python
generate_summary(ticket_body) -> str
```
- Résumé concis du problème utilisateur
- Format: 1-2 phrases max
- Extrait l'essentiel sans jargon technique

#### c) Génération de procédures
```python
generate_procedure(ticket, resolution) -> {title, steps, keywords}
```
- Crée procédure structurée depuis ticket résolu
- Étapes numérotées claires
- Extraction automatique keywords (3-7 mots-clés)
- Reformulation professionnelle

#### d) Réformulation de procédures importées
```python
reformulate_procedure(raw_text) -> {title, steps, keywords}
```
- Parse documents Word/PDF/TXT
- Structure en étapes claires
- Normalisation format

**Gestion des coûts**:
- Tracking tokens input/output dans `api_costs`
- Rate limiting: 20 requêtes/minute par défaut
- Cache des résumés pour éviter doublons

### 3. Système de Procédures

**Service**: `src/services/procedure_service.py`

#### Scoring de pertinence multi-facteurs
```python
calculate_score(ticket, procedure) -> float (0-100)
```

Algorithme de scoring:
1. **Mots-clés** (35%) - Jaccard similarity sur keywords
2. **Catégorie** (35%) - Match exact catégorie
3. **Feedback** (20%) - Taux de succès procédure
4. **Usage** (10%) - Popularité procédure

#### Analytics procédures
```python
get_procedure_analytics(procedure_id) -> {
    success_rate: float,           # positive / total feedback
    effectiveness_score: float,    # success_rate * min(1, usage/10)
    usage_count: int,
    feedback_stats: {...}
}
```

Métriques:
- **Taux de succès**: `positive_feedback / total_feedback * 100`
- **Score d'efficacité**: Combine succès + usage (min 5 feedbacks)
- **Top performers**: `/api/procedures/top?metric=success_rate&limit=10`

#### Recherche de similarité
```python
get_similar_procedures(procedure_id, limit=5) -> [...]
```

Algorithme:
1. Jaccard similarity sur keywords
2. Bonus catégorie commune (+0.3)
3. Bonus similarité titre (+0.2)
4. Seuil minimum: 0.2

### 4. Système de Recherche

**Service**: `src/services/search_service.py`

#### Index inversé en mémoire
```python
{
    "outlook": [proc_id_1, proc_id_4, proc_id_7],
    "email": [proc_id_1, proc_id_3],
    "installation": [proc_id_2, proc_id_5]
}
```

- Tokenization simple (split + lowercase + strip)
- Mise à jour en temps réel
- Score = nombre de termes matchés / total termes recherche

#### Recherche full-text
```python
search_procedures(query, limit=10) -> [...]
```

Recherche sur:
- Titre procédure
- Mots-clés
- Contenu des étapes (JSON)

### 5. Système d'Assignation Techniciens

**Nouveau système** (remplace partiellement les catégories pour tickets)

#### Endpoints API (`src/routes/technician_routes.py`)
- `GET /api/technicians` - Liste techniciens actifs
- `POST /api/technicians` - Créer technicien
- `PUT /api/technicians/:id` - Modifier technicien
- `DELETE /api/technicians/:id` - Désactiver (soft delete)

#### Frontend (`src/static/js/technicians.js`)
- Cache local 5 minutes
- Fonctions: `getTechnicians()`, `createTechnician()`, etc.
- Refresh automatique après modifications

#### Intégration tickets
- Dropdown "Assigné à" dans modal ticket
- Badge technicien sur cartes tickets
- Filtre par technicien dans toolbar
- Support `assigned_to` dans API tickets

**Techniciens par défaut**:
1. Non assigné
2. Support Niveau 1
3. Support Niveau 2
4. Administrateur Système

### 6. Interface Kanban

**Fichier**: `src/static/js/kanban.js`

#### Colonnes
- **Nouveau** (`new`) - Tickets non traités
- **En cours** (`in_progress`) - Tickets en cours de résolution
- **Résolu** (`resolved`) - Tickets fermés

#### Fonctionnalités
- **Drag & drop** - Changement statut par glisser-déposer
- **Double-clic** - Ouvre modal détail
- **Simple-clic** - Sélection (Shift pour multi-sélection)
- **Recherche temps réel** - Filtre sur sujet/email/résumé
- **Filtres** - Par technicien / priorité
- **Badge technicien** - Affichage assignation

#### Optimisations
- Batch rendering (évite reflow)
- Virtual scrolling si > 100 tickets
- Debounce recherche (300ms)

### 7. Interface Procédures Moderne

**Inspirée de Claude.ai** - Design épuré et moderne

**Fichier**: `src/static/js/procedures_management.js`

#### Structure
```html
<div class="procedure-header">
    <h2>Procédures</h2>
    <button class="btn-new-procedure">+ Nouvelle procédure</button>
</div>
<div class="procedure-search-wrapper">
    <input type="text" placeholder="Rechercher dans vos procédures...">
</div>
<div class="procedure-list">
    <!-- Cartes style conversation -->
</div>
```

#### Features
- **Cartes conversationnelles** - Style chat avec timestamp relatif
- **Recherche instantanée** - Full-text sur titre/keywords
- **Statistiques** - Badge taux de succès si ≥ 5 feedbacks
- **Animations** - Fade-in smooth, hover effects
- **Responsive** - Mobile-first design

#### Timestamp relatif
```javascript
getRelativeTime(date) -> "il y a 2 heures" / "hier" / "3 jours"
```

### 8. Import/Export

#### Export tickets (`/api/tickets/export/csv`)
Format CSV avec colonnes:
- ID, Sujet, Expéditeur, Date, Statut, Priorité, Catégorie, Technicien, Résolution

#### Export procédures (`/api/procedures/export/xlsx`)
Format Excel avec onglets:
- Liste procédures
- Statistiques usage
- Analytics feedback

#### Import procédures
Formats supportés:
- `.docx` - Parse via python-docx
- `.pdf` - Parse via PyPDF2
- `.txt`, `.md` - Parse texte brut
- Multi-fichiers batch

Options:
- Reformulation IA automatique
- Extraction visuels (pour DOCX)
- Catégorisation automatique

### 9. SLA (Service Level Agreement)

**Service**: `src/services/sla_service.py`

#### Configuration par priorité
```python
sla_config = {
    'high': {'response_time': 1, 'resolution_time': 4},    # heures
    'medium': {'response_time': 4, 'resolution_time': 24},
    'low': {'response_time': 24, 'resolution_time': 72}
}
```

#### Statuts SLA
- `ok` - Dans les temps
- `warning` - 75% du temps écoulé
- `critical` - 90% du temps écoulé
- `breached` - Temps dépassé

#### Alertes automatiques
```python
check_sla_alerts() -> [...]  # Lancé par cron
```
- Détection dépassements SLA
- Stockage dans `sla_alerts`
- Notifications (à implémenter)

### 10. Sauvegardes Automatiques

**Service**: `src/services/backup_service.py`

#### Stratégie
- **Fréquence**: Quotidienne (configurable)
- **Rétention**: 30 dernières sauvegardes
- **Format**: `backup_YYYYMMDD_HHMMSS.db`
- **Stockage**: `backups/`

#### Restauration
```python
restore_backup(backup_path) -> bool
```
- Arrêt connexions DB
- Copie fichier
- Redémarrage connexions

## API REST Endpoints

### Tickets

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/tickets` | Liste tickets (pagination, filtres) |
| GET | `/api/tickets/:id` | Détail ticket + parsing thread |
| POST | `/api/tickets` | Créer ticket manuel |
| PUT | `/api/tickets/:id` | Mettre à jour ticket |
| DELETE | `/api/tickets/:id` | Supprimer ticket |
| POST | `/api/tickets/sync` | Synchroniser avec Outlook |
| POST | `/api/tickets/:id/mark-not-user-request` | Marquer comme spam/hors-sujet |

**Filtres disponibles** (query params):
- `status` - new / in_progress / resolved
- `assigned_to` - Nom du technicien
- `priority` - low / medium / high
- `search` - Recherche full-text
- `page`, `per_page` - Pagination

### Procédures

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/procedures` | Liste procédures (pagination) |
| GET | `/api/procedures/:id` | Détail procédure |
| POST | `/api/procedures` | Créer procédure |
| PUT | `/api/procedures/:id` | Modifier procédure |
| DELETE | `/api/procedures/:id` | Supprimer procédure |
| GET | `/api/procedures/:id/analytics` | Analytics procédure |
| GET | `/api/procedures/top` | Top performers |
| GET | `/api/procedures/statistics` | Stats globales |
| GET | `/api/procedures/:id/similar` | Procédures similaires |
| POST | `/api/procedures/:id/feedback` | Ajouter feedback |
| POST | `/api/procedures/import` | Import fichier(s) |
| GET | `/api/procedures/export/xlsx` | Export Excel |

### Techniciens

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/technicians` | Liste techniciens actifs |
| POST | `/api/technicians` | Créer technicien |
| PUT | `/api/technicians/:id` | Modifier technicien |
| DELETE | `/api/technicians/:id` | Désactiver technicien |

### Catégories

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/categories` | Liste catégories actives |
| POST | `/api/categories` | Créer catégorie |
| PUT | `/api/categories/:id` | Modifier catégorie |
| DELETE | `/api/categories/:id` | Désactiver catégorie |

**Note**: Les catégories sont utilisées pour les procédures. L'assignation des tickets utilise maintenant le système de techniciens.

### Configuration

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/config` | Configuration complète |
| PUT | `/api/config/:key` | Mettre à jour clé |
| GET | `/api/config/test-claude` | Tester connexion Claude |
| GET | `/api/config/test-outlook` | Tester connexion Outlook |

## Patterns de Code Importants

### 1. Base de données

#### Context Manager obligatoire
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()
    conn.commit()
```

❌ **Ne JAMAIS faire**:
```python
conn = db.get_connection()  # Retourne context manager, pas connexion!
conn.execute(...)  # ERREUR
```

#### Méthodes pratiques
```python
# INSERT
ticket_id = db.insert('tickets', {
    'subject': 'Test',
    'status': 'new'
})

# UPDATE
db.update('tickets', {'status': 'resolved'}, 'id = ?', (ticket_id,))

# DELETE
db.delete('tickets', 'id = ?', (ticket_id,))

# SELECT
tickets = db.fetchall("SELECT * FROM tickets WHERE status = ?", ('new',))
ticket = db.fetchone("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
```

#### Whitelist tables (sécurité)
```python
ALLOWED_TABLES = {
    'tickets', 'procedures', 'categories', 'technicians',
    'knowledge_base', 'api_costs', 'sla_config', 'sla_alerts',
    'email_templates', 'ai_feedback', 'daily_stats',
    'procedure_feedback', 'ticket_procedures'
}
```

Toute table hors whitelist lèvera `ValueError`.

### 2. Frontend - API Client

#### Pattern singleton
```javascript
const api = new APIClient();

// Toutes les requêtes passent par api.*
const tickets = await api.getTickets();
const ticket = await api.getTicket(123);
await api.updateTicket(123, { status: 'resolved' });
```

#### Gestion erreurs centralisée
```javascript
async request(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) throw new Error(response.statusText);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}
```

### 3. Rate Limiting

#### Décorateur sur routes
```python
@ticket_bp.route('/api/tickets', methods=['POST'])
@rate_limit(limit=10, window=60)  # 10 req/min
def create_ticket():
    ...
```

#### Configuration
```python
# src/utils/rate_limiter.py
DEFAULT_LIMIT = 20
DEFAULT_WINDOW = 60  # secondes
```

### 4. Gestion Config

#### Lecture
```python
from config import config

api_key = config.get('claude_api_key')
first_run = config.get('first_run_completed', False)
```

#### Écriture
```python
config.set('claude_api_key', 'sk-...')
```

#### Stockage
- Format: JSON
- Fichier: `%APPDATA%/ITTicketManager/config/config.json` (Windows)
- Fichier: `~/ITTicketManager/config/config.json` (Linux/Mac)

## Configuration Requise

### Variables d'environnement

```bash
# Flask (obligatoire en production)
FLASK_SECRET_KEY=your-secret-key-here

# Claude API (obligatoire)
CLAUDE_API_KEY=sk-ant-...

# Outlook OAuth (optionnel si pas de synchro)
OUTLOOK_CLIENT_ID=...
OUTLOOK_CLIENT_SECRET=...
OUTLOOK_TENANT_ID=...
```

### Premier démarrage

Assistant de configuration (`/setup`):
1. Connexion API Claude (test)
2. Configuration Outlook OAuth (optionnel)
3. Import catégories par défaut
4. Création techniciens par défaut
5. Configuration SLA

## Commandes Utiles

### Lancement serveur
```bash
cd src
python app.py
# http://localhost:5000
```

### Migration base de données
```bash
python migrate_add_technician.py
```

### Tests API
```bash
# Test Claude
curl http://localhost:5000/api/config/test-claude

# Test Outlook
curl http://localhost:5000/api/config/test-outlook
```

### Sauvegarde manuelle
```python
from services.backup_service import backup_service
backup_service.create_backup()
```

## Évolutions Récentes

### Version actuelle: 2.0 - Système de Techniciens

**Date**: Décembre 2024

**Changements majeurs**:

1. **Ajout table `technicians`**
   - Migration: `migrations/add_assigned_technician.sql`
   - Colonne `assigned_to` dans tickets
   - 4 techniciens par défaut

2. **Nouvelles routes `/api/technicians`**
   - CRUD complet techniciens
   - Blueprint `technician_bp`

3. **UI modernisée**
   - Remplacement dropdowns catégories → techniciens (tickets uniquement)
   - Badge technicien sur cartes tickets
   - Filtre par technicien dans toolbar
   - `technicians.js` avec cache 5min

4. **Backend adapté**
   - `assigned_to` dans filtres GET /api/tickets
   - `assigned_to` dans allowed fields PUT /api/tickets/:id
   - Support recherche par technicien

**Notes de compatibilité**:
- Les catégories restent actives pour les **procédures**
- L'ancien champ `category` des tickets reste en base (legacy)
- Migration non-destructive

### Historique

**Version 1.5** - Interface Procédures Moderne
- Redesign complet UI procédures (style Claude.ai)
- Système d'analytics et métriques
- Détection similarité (Jaccard)

**Version 1.0** - Version initiale
- Interface Kanban
- Synchronisation Outlook
- IA Claude pour catégorisation

## Bonnes Pratiques

### 1. Ne jamais bloquer l'event loop
❌ Mauvais:
```javascript
while (!dataLoaded) {
    await sleep(100);
}
```

✅ Bon:
```javascript
async function loadData() {
    const data = await api.getData();
    renderData(data);
}
```

### 2. Toujours valider les entrées utilisateur
```python
@ticket_bp.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.json

    # Validation
    if not data or 'subject' not in data:
        return jsonify({'error': 'Subject required'}), 400

    # Sanitization
    subject = data['subject'].strip()[:200]
    ...
```

### 3. Gérer les cas null/undefined
```javascript
const assignedTo = ticket.assigned_to || 'Non assigné';
const badge = ticket.assigned_to
    ? `<div class="badge">${ticket.assigned_to}</div>`
    : '';
```

### 4. Utiliser les index SQL
```sql
-- Toujours créer des index sur colonnes de filtrage fréquent
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assigned_to ON tickets(assigned_to);
```

### 5. Cache intelligent
```javascript
// Cache avec expiration
let cache = null;
let cacheTime = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 min

async function getData() {
    if (cache && Date.now() - cacheTime < CACHE_DURATION) {
        return cache;
    }
    cache = await api.getData();
    cacheTime = Date.now();
    return cache;
}
```

## Debugging

### Logs Backend
```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Détail technique')
logger.info('Information générale')
logger.warning('Attention')
logger.error('Erreur critique')
```

### Console Frontend
```javascript
console.log('Info:', data);
console.error('Erreur:', error);
console.table(tickets);  // Affiche tableau
```

### Requêtes SQL
```python
# Activer logs SQL
import sqlite3
sqlite3.enable_callback_tracebacks(True)

# Dans database.py
self.logger.debug(f"Executing: {query} with params {params}")
```

## Limites Connues

1. **SQLite**:
   - Pas de connexions concurrentes en écriture
   - Max ~1TB de données (suffisant pour usage PME)
   - Pas de réplication native

2. **Outlook Sync**:
   - Tokens expirent après 90 jours d'inactivité
   - Rate limit Microsoft: 10k requêtes/heure
   - Nécessite admin consent pour permissions

3. **Claude API**:
   - Rate limit: 50 requêtes/minute (tier 1)
   - Coût: ~$3/1M tokens input, ~$15/1M tokens output
   - Timeout: 60 secondes max par requête

4. **Frontend**:
   - Pas de support IE11
   - Performances dégradées si > 1000 tickets affichés
   - WebSockets non implémentés (pas de real-time multi-users)

## Roadmap Future

### Court terme
- [ ] Notifications push navigateur
- [ ] Export PDF tickets
- [ ] Thème sombre
- [ ] Gestion pièces jointes

### Moyen terme
- [ ] Multi-utilisateurs avec authentification
- [ ] Historique complet modifications tickets
- [ ] Dashboard analytics avancés
- [ ] API REST complète (webhooks)

### Long terme
- [ ] Migration PostgreSQL (optionnelle)
- [ ] Mobile app (React Native)
- [ ] Intégration Teams/Slack
- [ ] IA prédictive (détection incidents majeurs)

## Support & Contact

**Documentation**: Ce fichier + `FONCTIONNALITES.md`
**Issues**: GitHub Issues
**Code**: Suivre conventions PEP 8 (Python) et ES6 (JavaScript)

---

*Dernière mise à jour: Décembre 2024*
*Version: 2.0 - Système de Techniciens*
