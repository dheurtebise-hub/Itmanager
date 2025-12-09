# KB_IT_SUPPORT - Prochaines étapes

## ✅ Phase 1 - MVP (COMPLÉTÉE)

### Ce qui a été fait

- [x] Base de données SQLite complète avec schéma hiérarchique
- [x] Backend Flask avec API REST complète
- [x] Modèles Procedure, Category, Tag avec ORM
- [x] Routes API pour toutes les entités
- [x] Service IA (structure + génération tags)
- [x] Frontend HTML/CSS/JS avec dark theme terminal
- [x] Interface multi-vues (Home, Liste, Détail, Éditeur)
- [x] CRUD procédures complet
- [x] Système de tags manuels
- [x] Recherche simple par mots-clés
- [x] Versioning automatique (backend)
- [x] Upload fichiers joints (backend)
- [x] Éditeur markdown avec toolbar
- [x] Pagination
- [x] Catégories hiérarchiques avec arborescence
- [x] Tests API validés

## 🚧 Phase 2 - Recherche avancée

### À implémenter

#### Auto-complétion recherche

**Frontend** (`static/js/app.js`)

```javascript
handleSearch(query) {
    // Ajouter debounce
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(async () => {
        if (query.length >= 3) {
            // Appeler API de suggestions
            const suggestions = await api.searchProcedures(query);
            this.showSearchSuggestions(suggestions);
        }
    }, 300);
}

showSearchSuggestions(suggestions) {
    // Créer dropdown sous la barre de recherche
    // Afficher les résultats avec highlight
}
```

**Backend** (nouveau endpoint dans `procedure_routes.py`)

```python
@procedure_bp.route('/api/procedures/search-suggest', methods=['GET'])
def search_suggest():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 5))

    # Rechercher dans titre et tags
    procedures = Procedure.search_by_keywords([query], limit=limit)

    return jsonify([{
        'id': p['id'],
        'title': p['title'],
        'category': get_category_name(p['category_id']),
        'relevance': calculate_relevance(p, query)
    } for p in procedures])
```

#### Filtres avancés

**Frontend** : Ajouter panneau filtres dans `listView`

```html
<div class="filters-panel">
    <div class="filter-group">
        <label>Date création</label>
        <input type="date" id="filterDateFrom">
        <input type="date" id="filterDateTo">
    </div>
    <div class="filter-group">
        <label>Auteur</label>
        <select id="filterAuthor">
            <option value="">Tous</option>
            <!-- Généré dynamiquement -->
        </select>
    </div>
    <button id="applyFilters">Appliquer</button>
</div>
```

**Backend** : Étendre `GET /api/procedures`

```python
# Ajouter paramètres
date_from = request.args.get('date_from')
date_to = request.args.get('date_to')
author = request.args.get('author')

# Ajouter conditions SQL
if date_from:
    query += " AND created_at >= ?"
    params.append(date_from)
```

#### Tri personnalisé

Frontend : Dropdown tri étendu

```javascript
<select id="sortSelect">
    <option value="updated_at">Date modification</option>
    <option value="created_at">Date création</option>
    <option value="title">Titre (A→Z)</option>
    <option value="usage_count">Popularité</option>
    <option value="estimated_time">Temps estimé</option>
</select>
```

**Temps estimé** : ~4h

## 🤖 Phase 3 - Tags IA

### À finaliser

#### Génération automatique tags

**Statut** : Backend OK, à tester avec clé API réelle

**Tester** :

```javascript
// Dans l'éditeur
document.getElementById('btnGenerateTags').addEventListener('click', async () => {
    // Déjà implémenté dans app.js
    await App.generateTags();
});
```

**Améliorer le prompt** (`ai_service.py`) :

```python
def generate_keywords(self, title, category, content):
    prompt = f"""Analyse cette procédure IT et génère 4-8 tags pertinents.

CRITÈRES :
- Mots-clés techniques récurrents (apparaissant 3+ fois)
- Logiciels/commandes mentionnés
- Actions principales (installation, config, dépannage)
- Contexte métier

PROCÉDURE :
Titre: {title}
Catégorie: {category}
Contenu: {content[:800]}

RÈGLES :
- Tags en minuscules sans accents
- Format: mot-simple ou mot-compose
- Éviter les mots trop génériques (système, réseau, etc.)

Retourne JSON : {{"tags": ["tag1", "tag2", ...]}}
"""
```

#### Recherche sémantique IA

**Backend** : Nouveau endpoint

```python
@procedure_bp.route('/api/procedures/ai-search', methods=['POST'])
@rate_limit()
def ai_search():
    """Recherche sémantique par question en langage naturel."""
    data = request.get_json()
    query = data.get('query')

    # Récupérer toutes les procédures
    all_procedures = Procedure.get_all(limit=100)

    # Utiliser l'IA pour scorer
    from services.ai_service import ai_service
    results = ai_service.semantic_search(query, all_procedures)

    return jsonify(results), 200
```

**Frontend** : Mode recherche IA

```javascript
// Détection question (commence par comment, pourquoi, etc.)
if (query.match(/^(comment|pourquoi|où|quand|qui)/i)) {
    // Recherche IA
    const results = await api.aiSearch(query);
    this.renderAISearchResults(results);
} else {
    // Recherche classique
    await this.loadProcedures();
}
```

**Temps estimé** : ~6h (incluant tests avec API réelle)

## 📎 Phase 4 - Multimédia

### À implémenter

#### Finaliser upload/download fichiers

**Frontend** : Compléter la fonction `handleFileUpload`

```javascript
async handleFileUpload(files) {
    const filesList = document.getElementById('filesList');

    for (const file of files) {
        // Vérifier type et taille
        if (!this.isFileAllowed(file)) {
            this.showNotification(`${file.name} : type non autorisé`, 'error');
            continue;
        }

        if (file.size > 50 * 1024 * 1024) {
            this.showNotification(`${file.name} : fichier trop volumineux`, 'error');
            continue;
        }

        // Ajouter à la liste (stockage temporaire)
        const fileItem = this.createFileItemHTML(file);
        filesList.appendChild(fileItem);
    }

    // Les fichiers seront uploadés lors du save de la procédure
}

async saveProcedure() {
    // ... code existant ...

    // Upload des fichiers après création de la procédure
    if (this.tempFiles && this.tempFiles.length > 0) {
        for (const file of this.tempFiles) {
            await api.uploadAttachment(procedureId, file);
        }
    }
}
```

#### Preview images/PDF

```javascript
createAttachmentHTML(attachment, procedureId) {
    const icon = this.getFileIcon(attachment.file_type);

    let previewBtn = '';
    if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(attachment.file_type)) {
        previewBtn = `<button class="btn-secondary btn-sm" onclick="App.previewImage(${procedureId}, ${attachment.id})">👁 Voir</button>`;
    }

    return `
        <div class="file-item">
            ...
            ${previewBtn}
            <a href="/api/procedures/${procedureId}/attachments/${attachment.id}" class="btn-secondary btn-sm" download>↓</a>
        </div>
    `;
}

previewImage(procedureId, attachmentId) {
    // Ouvrir modal avec image
    const imgUrl = `/api/procedures/${procedureId}/attachments/${attachmentId}`;
    // ... afficher dans modal
}
```

#### Coloration syntaxe PowerShell

Utiliser une bibliothèque légère comme Prism.js :

```html
<!-- Dans index.html -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-powershell.min.js"></script>
```

```javascript
markdownToHtml(markdown) {
    // ... code existant ...

    // Après conversion des code blocks
    document.querySelectorAll('pre code').forEach((block) => {
        // Détecter le langage (powershell, bash, etc.)
        Prism.highlightElement(block);
    });
}
```

**Temps estimé** : ~8h

## 📜 Phase 5 - Fonctionnalités avancées

### À implémenter

#### Interface historique versions

**Frontend** : Modal historique

```html
<div id="modalHistory" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>📜 Historique des versions</h2>
            <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
            <div id="versionsList" class="versions-list">
                <!-- Généré dynamiquement -->
            </div>
        </div>
    </div>
</div>
```

```javascript
async showHistory(procedureId) {
    const versions = await api.getProcedureVersions(procedureId);

    const modal = document.getElementById('modalHistory');
    const list = document.getElementById('versionsList');

    list.innerHTML = versions.map(v => `
        <div class="version-item">
            <div class="version-header">
                <strong>v${v.version_number}</strong>
                <span>${new Date(v.changed_at).toLocaleString('fr-FR')}</span>
                <span>par ${v.changed_by}</span>
            </div>
            <div class="version-actions">
                <button onclick="App.showDiff(${v.procedure_id}, ${v.version_number})">Voir diff</button>
                <button onclick="App.restoreVersion(${v.procedure_id}, ${v.version_number})">Restaurer</button>
            </div>
        </div>
    `).join('');

    modal.style.display = 'flex';
}
```

#### Export PDF

**Backend** : Nouvelle dépendance

```txt
# requirements.txt
weasyprint==60.0
```

```python
# procedure_routes.py
from weasyprint import HTML

@procedure_bp.route('/api/procedures/<int:procedure_id>/export/pdf', methods=['GET'])
def export_pdf(procedure_id):
    procedure = Procedure.get_by_id(procedure_id)

    # Template HTML pour PDF
    html_content = render_template('pdf_procedure.html', procedure=procedure)

    # Générer PDF
    pdf = HTML(string=html_content).write_pdf()

    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{procedure["title"]}.pdf'
    )
```

**Frontend** :

```javascript
document.getElementById('btnExport').onclick = () => {
    window.open(`/api/procedures/${procedureId}/export/pdf`);
};
```

#### Import Word/PDF

**Backend** : Parser de fichiers

```python
# utils/file_parser.py
from docx import Document
import PyPDF2

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return '\n'.join([p.text for p in doc.paragraphs])

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text
```

**Frontend** : Import assistant

```html
<div class="import-wizard">
    <h2>Import de procédures</h2>
    <input type="file" id="importFiles" multiple accept=".docx,.pdf,.txt,.md">
    <label>
        <input type="checkbox" id="aiReformulation">
        Reformuler avec l'IA
    </label>
    <button onclick="App.importProcedures()">Importer</button>
</div>
```

**Temps estimé** : ~10h

## 📦 Phase 6 - Packaging

### À implémenter

#### PyInstaller .exe

**Fichier** : `build.spec`

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('templates', 'templates'),
        ('database/schema.sql', 'database'),
    ],
    hiddenimports=[
        'flask',
        'requests',
        'app.models.procedure',
        'app.models.category',
        'app.models.tag',
        'app.routes.procedure_routes',
        'app.routes.category_routes',
        'app.routes.tag_routes',
        'app.routes.settings_routes',
        'app.services.ai_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KB_IT_Support',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/icon.ico',  # À créer
)
```

**Build** :

```bash
pip install pyinstaller
pyinstaller build.spec
# → dist/KB_IT_Support.exe
```

#### Documentation utilisateur

Créer `GUIDE_UTILISATEUR.md` avec :
- Screenshots de l'interface
- Guide pas-à-pas pour chaque fonctionnalité
- FAQ
- Troubleshooting

#### Guide installation

Créer `INSTALL.md` avec :
- Configuration système requise
- Installation .exe standalone
- Configuration initiale (clé API Claude)
- Migration depuis ITManager
- Backup/restauration

**Temps estimé** : ~6h

## 🎯 Résumé des temps estimés

| Phase | Temps estimé | Priorité |
|-------|--------------|----------|
| Phase 2 - Recherche avancée | ~4h | Haute |
| Phase 3 - Tags IA | ~6h | Haute |
| Phase 4 - Multimédia | ~8h | Moyenne |
| Phase 5 - Avancé | ~10h | Moyenne |
| Phase 6 - Packaging | ~6h | Basse |
| **TOTAL** | **~34h** | - |

## 🐛 Bugs connus à corriger

### Critiques

Aucun identifié pour le moment.

### Mineurs

- [ ] Notifications toast à implémenter (actuellement alerts)
- [ ] Upload fichiers : interface à finaliser
- [ ] Markdown preview en temps réel
- [ ] Auto-save toutes les 2 minutes (structure prête, à activer)
- [ ] Responsive mobile à améliorer

## 💡 Améliorations futures (hors cahier des charges)

### Nice to have

- [ ] Thème clair en option
- [ ] Export markdown
- [ ] Import depuis URL
- [ ] Statistiques avancées (dashboard)
- [ ] Favoris / bookmarks
- [ ] Commentaires sur procédures
- [ ] Workflow d'approbation
- [ ] API tokens pour intégrations externes
- [ ] Webhooks
- [ ] Multi-langue (i18n)
- [ ] Mode hors-ligne (PWA)
- [ ] Synchronisation cloud

### Optimisations

- [ ] Cache Redis pour recherches fréquentes
- [ ] Compression des images uploadées
- [ ] Lazy loading des procédures
- [ ] WebSockets pour real-time multi-users
- [ ] Migration PostgreSQL (scalabilité)

## 📅 Planning suggéré

### Semaine 1
- Phase 2 : Recherche avancée
- Phase 3 : Tests IA avec clé API réelle

### Semaine 2
- Phase 4 : Multimédia (upload + preview)
- Corrections bugs mineurs

### Semaine 3
- Phase 5 : Fonctionnalités avancées
- Tests utilisateurs

### Semaine 4
- Phase 6 : Packaging
- Documentation
- Release v1.0

---

**Dernière mise à jour** : Décembre 2024
**Statut global** : Phase 1 MVP - ✅ 100% complète
