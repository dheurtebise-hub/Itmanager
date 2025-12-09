/**
 * Application principale KB_IT_Support
 */

const App = {
    // État de l'application
    state: {
        currentView: 'home',
        currentCategory: null,
        currentProcedure: null,
        categories: [],
        procedures: [],
        currentPage: 1,
        searchQuery: '',
        editingProcedure: null
    },

    // ============================================
    // Initialisation
    // ============================================

    async init() {
        console.log('Initializing KB_IT_Support...');

        // Charger les catégories
        await this.loadCategories();

        // Charger la vue home
        this.showHome();

        // Event listeners
        this.setupEventListeners();

        console.log('Application ready!');
    },

    setupEventListeners() {
        // Header
        document.getElementById('btnNew').addEventListener('click', () => this.showEditor());
        document.getElementById('btnSettings').addEventListener('click', () => this.showSettings());
        document.getElementById('searchInput').addEventListener('input', (e) => this.handleSearch(e.target.value));

        // Sidebar
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                const category = e.currentTarget.dataset.category;

                if (view === 'home') {
                    this.showHome();
                } else if (category) {
                    if (category === 'all') {
                        this.showProcedureList();
                    } else {
                        this.showProcedureList(parseInt(category));
                    }
                }
            });
        });

        // Éditeur
        const btnEditorBack = document.getElementById('btnEditorBack');
        const btnCancel = document.getElementById('btnCancel');
        if (btnEditorBack) btnEditorBack.addEventListener('click', () => this.showProcedureList());
        if (btnCancel) btnCancel.addEventListener('click', () => this.showProcedureList());

        document.getElementById('procedureForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProcedure();
        });

        document.getElementById('btnGenerateTags').addEventListener('click', () => this.generateTags());

        // Tag input
        document.getElementById('tagInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag(e.target.value);
                e.target.value = '';
            }
        });

        // Upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e.target.files));

        // Drag & drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFileUpload(e.dataTransfer.files);
        });

        // Toolbar markdown
        document.querySelectorAll('.toolbar-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = e.currentTarget.dataset.action;
                this.applyMarkdownFormat(action);
            });
        });

        // Détail procédure
        const btnBack = document.getElementById('btnBack');
        if (btnBack) btnBack.addEventListener('click', () => this.showProcedureList());

        // Settings modal
        document.getElementById('btnCloseSettings').addEventListener('click', () => this.hideSettings());
        document.getElementById('btnCancelSettings').addEventListener('click', () => this.hideSettings());
        document.getElementById('btnSaveSettings').addEventListener('click', () => this.saveSettings());
        document.getElementById('btnTestClaude').addEventListener('click', () => this.testClaude());
    },

    // ============================================
    // Navigation
    // ============================================

    showView(viewId) {
        // Cacher toutes les vues
        document.querySelectorAll('.view').forEach(v => v.style.display = 'none');

        // Afficher la vue demandée
        document.getElementById(viewId).style.display = 'block';

        this.state.currentView = viewId;
    },

    async showHome() {
        this.showView('homeView');

        // Charger les statistiques
        await this.loadHomeStats();

        // Charger les procédures récentes
        await this.loadRecentProcedures();

        // Afficher les catégories principales
        this.renderCategoryGrid();

        // Mettre à jour la sidebar
        this.updateSidebarActive('home');
    },

    async showProcedureList(categoryId = null) {
        this.state.currentCategory = categoryId;
        this.state.currentPage = 1;

        this.showView('listView');

        // Titre de la vue
        let title = '// Procédures';
        if (categoryId) {
            const category = this.state.categories.find(c => c.id === categoryId);
            if (category) {
                title = `// ${category.name}`;
            }
        }
        document.getElementById('listViewTitle').textContent = title;

        // Charger les procédures
        await this.loadProcedures();

        // Mettre à jour la sidebar
        this.updateSidebarActive(categoryId ? categoryId.toString() : 'all');
    },

    async showProcedureDetail(procedureId) {
        this.showView('detailView');

        try {
            const procedure = await api.getProcedure(procedureId);
            this.state.currentProcedure = procedure;

            this.renderProcedureDetail(procedure);

            // Event listeners pour les boutons
            document.getElementById('btnEdit').onclick = () => this.showEditor(procedureId);
            document.getElementById('btnArchive').onclick = () => this.archiveProcedure(procedureId);
            document.getElementById('btnHistory').onclick = () => this.showHistory(procedureId);

        } catch (error) {
            console.error('Error loading procedure:', error);
            this.showNotification('Erreur de chargement de la procédure', 'error');
        }
    },

    showEditor(procedureId = null) {
        this.showView('editorView');

        if (procedureId) {
            // Édition
            document.getElementById('editorViewTitle').textContent = '// Éditer procédure';
            this.loadProcedureInEditor(procedureId);
        } else {
            // Nouvelle procédure
            document.getElementById('editorViewTitle').textContent = '// Nouvelle procédure';
            this.clearEditor();
        }
    },

    // ============================================
    // Catégories
    // ============================================

    async loadCategories() {
        try {
            this.state.categories = await api.getCategories();
            this.renderCategoryTree();
            this.renderCategoryDropdown();
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    },

    renderCategoryTree() {
        const treeContainer = document.getElementById('categoryTree');
        treeContainer.innerHTML = '';

        // Récupérer les catégories parentes
        const parents = this.state.categories.filter(c => c.parent_id === null);

        parents.forEach(parent => {
            // Parent
            const parentDiv = document.createElement('div');
            parentDiv.className = 'category-item category-parent';
            parentDiv.dataset.category = parent.id;
            parentDiv.innerHTML = `
                <span>${parent.icon || '📁'}</span>
                <span>${parent.short_name}</span>
            `;
            parentDiv.addEventListener('click', () => this.showProcedureList(parent.id));
            treeContainer.appendChild(parentDiv);

            // Enfants
            const children = this.state.categories.filter(c => c.parent_id === parent.id);
            children.forEach(child => {
                const childDiv = document.createElement('div');
                childDiv.className = 'category-item category-child';
                childDiv.dataset.category = child.id;
                childDiv.innerHTML = `
                    <span>├─${child.short_name}</span>
                `;
                childDiv.addEventListener('click', () => this.showProcedureList(child.id));
                treeContainer.appendChild(childDiv);
            });
        });
    },

    renderCategoryDropdown() {
        const select = document.getElementById('procCategory');
        select.innerHTML = '<option value="">Sélectionner une catégorie</option>';

        // Catégories parentes
        const parents = this.state.categories.filter(c => c.parent_id === null);

        parents.forEach(parent => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${parent.icon} ${parent.name}`;

            // Enfants
            const children = this.state.categories.filter(c => c.parent_id === parent.id);
            children.forEach(child => {
                const option = document.createElement('option');
                option.value = child.id;
                option.textContent = `  ${child.name}`;
                optgroup.appendChild(option);
            });

            // Si pas d'enfants, ajouter le parent
            if (children.length === 0) {
                const option = document.createElement('option');
                option.value = parent.id;
                option.textContent = parent.name;
                select.appendChild(option);
            } else {
                select.appendChild(optgroup);
            }
        });
    },

    renderCategoryGrid() {
        const grid = document.getElementById('categoryGrid');
        grid.innerHTML = '';

        // Catégories principales uniquement
        const parents = this.state.categories.filter(c => c.parent_id === null);

        parents.forEach(cat => {
            const tile = document.createElement('div');
            tile.className = 'category-tile';
            tile.innerHTML = `
                <div class="category-tile-icon">${cat.icon}</div>
                <div class="category-tile-name">${cat.name}</div>
            `;
            tile.addEventListener('click', () => this.showProcedureList(cat.id));
            grid.appendChild(tile);
        });
    },

    updateSidebarActive(identifier) {
        // Retirer l'active de tous
        document.querySelectorAll('.sidebar-item, .category-item').forEach(item => {
            item.classList.remove('active');
        });

        // Ajouter l'active
        if (identifier === 'home') {
            const homeItem = document.querySelector('.sidebar-item[data-view="home"]');
            if (homeItem) homeItem.classList.add('active');
        } else if (identifier === 'all') {
            const allItem = document.querySelector('.sidebar-item[data-category="all"]');
            if (allItem) allItem.classList.add('active');
        } else {
            const catItem = document.querySelector(`.category-item[data-category="${identifier}"]`);
            if (catItem) catItem.classList.add('active');
        }
    },

    // ============================================
    // Procédures
    // ============================================

    async loadProcedures() {
        try {
            const params = {
                page: this.state.currentPage,
                per_page: 20
            };

            if (this.state.currentCategory) {
                params.category_id = this.state.currentCategory;
            }

            if (this.state.searchQuery) {
                params.search = this.state.searchQuery;
            }

            const response = await api.getProcedures(params);
            this.state.procedures = response.procedures;

            this.renderProcedureList(response.procedures);
            this.renderPagination(response.pagination);

        } catch (error) {
            console.error('Error loading procedures:', error);
            this.showNotification('Erreur de chargement des procédures', 'error');
        }
    },

    renderProcedureList(procedures) {
        const container = document.getElementById('procedureList');
        container.innerHTML = '';

        if (procedures.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 48px;">Aucune procédure trouvée</p>';
            return;
        }

        procedures.forEach(proc => {
            const card = this.createProcedureCard(proc);
            container.appendChild(card);
        });
    },

    createProcedureCard(procedure) {
        const card = document.createElement('div');
        card.className = 'procedure-card';

        // Catégorie pour la couleur
        const category = this.state.categories.find(c => c.id === procedure.category_id);
        if (category && category.color_code) {
            card.style.borderLeftColor = category.color_code;
        }

        // Tags HTML
        const tagsHTML = procedure.tags && procedure.tags.length > 0
            ? procedure.tags.map(tag => `<span class="tag">${tag.name}</span>`).join('')
            : '';

        // Temps relatif
        const timeAgo = this.getRelativeTime(procedure.updated_at);

        card.innerHTML = `
            <div class="procedure-card-header">
                <div>
                    <span class="procedure-id">[PROC-${String(procedure.id).padStart(3, '0')}]</span>
                    <span class="procedure-title">${this.escapeHtml(procedure.title)}</span>
                </div>
            </div>
            <div class="procedure-meta">
                ${procedure.estimated_time ? `🕐 ${procedure.estimated_time}min` : ''}
                ${procedure.description ? `| ${this.escapeHtml(procedure.description.substring(0, 100))}` : ''}
            </div>
            <div class="procedure-tags">${tagsHTML}</div>
            <div class="procedure-footer">
                ${procedure.created_by || 'unknown'} | ${timeAgo}
            </div>
        `;

        card.addEventListener('click', () => this.showProcedureDetail(procedure.id));

        return card;
    },

    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        container.innerHTML = '';

        if (pagination.total_pages <= 1) return;

        // Bouton précédent
        const prevBtn = document.createElement('button');
        prevBtn.className = 'pagination-btn';
        prevBtn.textContent = '←';
        prevBtn.disabled = !pagination.has_prev;
        prevBtn.addEventListener('click', () => this.changePage(pagination.page - 1));
        container.appendChild(prevBtn);

        // Numéros de pages
        for (let i = 1; i <= pagination.total_pages; i++) {
            // Afficher seulement quelques pages autour de la page actuelle
            if (i === 1 || i === pagination.total_pages ||
                (i >= pagination.page - 2 && i <= pagination.page + 2)) {

                const pageBtn = document.createElement('button');
                pageBtn.className = 'pagination-btn' + (i === pagination.page ? ' active' : '');
                pageBtn.textContent = i;
                pageBtn.addEventListener('click', () => this.changePage(i));
                container.appendChild(pageBtn);
            } else if (i === pagination.page - 3 || i === pagination.page + 3) {
                const ellipsis = document.createElement('span');
                ellipsis.textContent = '...';
                ellipsis.style.padding = '0 8px';
                container.appendChild(ellipsis);
            }
        }

        // Bouton suivant
        const nextBtn = document.createElement('button');
        nextBtn.className = 'pagination-btn';
        nextBtn.textContent = '→';
        nextBtn.disabled = !pagination.has_next;
        nextBtn.addEventListener('click', () => this.changePage(pagination.page + 1));
        container.appendChild(nextBtn);
    },

    async changePage(page) {
        this.state.currentPage = page;
        await this.loadProcedures();
        // Scroll to top
        document.getElementById('mainContent').scrollTop = 0;
    },

    renderProcedureDetail(procedure) {
        const container = document.getElementById('procedureDetail');

        const category = this.state.categories.find(c => c.id === procedure.category_id);
        const categoryName = category ? category.name : 'Aucune';

        // Tags HTML
        const tagsHTML = procedure.tags && procedure.tags.length > 0
            ? procedure.tags.map(tag => `<span class="tag">${tag.name}</span>`).join('')
            : '<span style="color: var(--text-secondary);">Aucun tag</span>';

        // Convertir markdown en HTML (simple)
        const contentHTML = this.markdownToHtml(procedure.content);

        container.innerHTML = `
            <div class="content-card">
                <div style="margin-bottom: 16px;">
                    <span class="procedure-id" style="font-size: var(--text-lg);">[PROC-${String(procedure.id).padStart(3, '0')}]</span>
                </div>
                <h1 style="font-size: var(--text-2xl); margin-bottom: 16px;">${this.escapeHtml(procedure.title)}</h1>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px; font-size: var(--text-sm);">
                    <div>
                        <span style="color: var(--text-secondary);">🕐 Temps estimé:</span>
                        <span>${procedure.estimated_time || '-'} min</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">📁 Catégorie:</span>
                        <span>${categoryName}</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px;">
                    <span style="color: var(--text-secondary); display: block; margin-bottom: 8px;">Tags:</span>
                    <div class="procedure-tags">${tagsHTML}</div>
                </div>

                <div style="border-top: 1px solid var(--bg-hover); padding-top: 16px; margin-top: 16px;">
                    <span style="color: var(--text-secondary); font-size: var(--text-xs);">
                        👤 ${procedure.created_by || 'unknown'} |
                        📅 ${new Date(procedure.created_at).toLocaleDateString('fr-FR')}
                    </span>
                </div>
            </div>

            <div class="content-card">
                <h2 class="card-title">📋 CONTENU</h2>
                <div style="font-family: var(--font-secondary); line-height: 1.8;">
                    ${contentHTML}
                </div>
            </div>

            ${procedure.attachments && procedure.attachments.length > 0 ? `
                <div class="content-card">
                    <h2 class="card-title">📎 FICHIERS JOINTS (${procedure.attachments.length})</h2>
                    <div class="files-list">
                        ${procedure.attachments.map(att => this.createAttachmentHTML(att, procedure.id)).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    },

    createAttachmentHTML(attachment, procedureId) {
        const icon = this.getFileIcon(attachment.file_type);
        const size = this.formatFileSize(attachment.file_size);

        return `
            <div class="file-item">
                <div class="file-info">
                    <span class="file-icon">${icon}</span>
                    <div>
                        <div class="file-name">${this.escapeHtml(attachment.original_filename)}</div>
                        <div class="file-size">${size}</div>
                    </div>
                </div>
                <a href="/api/procedures/${procedureId}/attachments/${attachment.id}"
                   class="btn-secondary btn-sm"
                   download>
                    ↓ Télécharger
                </a>
            </div>
        `;
    },

    // ============================================
    // Éditeur
    // ============================================

    clearEditor() {
        document.getElementById('procTitle').value = '';
        document.getElementById('procCategory').value = '';
        document.getElementById('procEstimatedTime').value = '';
        document.getElementById('procDescription').value = '';
        document.getElementById('procContent').value = '';
        document.getElementById('tagsList').innerHTML = '';
        document.getElementById('filesList').innerHTML = '';

        this.state.editingProcedure = null;
    },

    async loadProcedureInEditor(procedureId) {
        try {
            const procedure = await api.getProcedure(procedureId);
            this.state.editingProcedure = procedure;

            document.getElementById('procTitle').value = procedure.title || '';
            document.getElementById('procCategory').value = procedure.category_id || '';
            document.getElementById('procEstimatedTime').value = procedure.estimated_time || '';
            document.getElementById('procDescription').value = procedure.description || '';
            document.getElementById('procContent').value = procedure.content || '';

            // Tags
            const tagsList = document.getElementById('tagsList');
            tagsList.innerHTML = '';
            if (procedure.tags && procedure.tags.length > 0) {
                procedure.tags.forEach(tag => {
                    this.addTagToUI(tag.name, tag.id);
                });
            }

            // TODO: Fichiers joints

        } catch (error) {
            console.error('Error loading procedure in editor:', error);
            this.showNotification('Erreur de chargement', 'error');
        }
    },

    async saveProcedure() {
        const title = document.getElementById('procTitle').value.trim();
        const categoryId = parseInt(document.getElementById('procCategory').value);
        const estimatedTime = parseInt(document.getElementById('procEstimatedTime').value) || null;
        const description = document.getElementById('procDescription').value.trim();
        const content = document.getElementById('procContent').value.trim();

        if (!title || !categoryId || !content) {
            this.showNotification('Veuillez remplir tous les champs obligatoires', 'error');
            return;
        }

        // Récupérer les tags
        const tags = Array.from(document.querySelectorAll('#tagsList .tag-removable'))
            .map(tag => tag.dataset.tagName);

        const data = {
            title,
            category_id: categoryId,
            estimated_time: estimatedTime,
            description,
            content,
            tags
        };

        try {
            if (this.state.editingProcedure) {
                // Mise à jour
                await api.updateProcedure(this.state.editingProcedure.id, data);
                this.showNotification('Procédure mise à jour', 'success');
                this.showProcedureDetail(this.state.editingProcedure.id);
            } else {
                // Création
                const result = await api.createProcedure(data);
                this.showNotification('Procédure créée', 'success');
                this.showProcedureDetail(result.id);
            }
        } catch (error) {
            console.error('Error saving procedure:', error);
            this.showNotification('Erreur lors de la sauvegarde', 'error');
        }
    },

    async archiveProcedure(procedureId) {
        if (!confirm('Êtes-vous sûr de vouloir archiver cette procédure ?')) {
            return;
        }

        try {
            await api.deleteProcedure(procedureId);
            this.showNotification('Procédure archivée', 'success');
            this.showProcedureList();
        } catch (error) {
            console.error('Error archiving procedure:', error);
            this.showNotification('Erreur lors de l\'archivage', 'error');
        }
    },

    // ============================================
    // Tags
    // ============================================

    addTag(tagName) {
        if (!tagName || !tagName.trim()) return;

        tagName = tagName.toLowerCase().trim();

        // Vérifier si déjà présent
        const existing = Array.from(document.querySelectorAll('#tagsList .tag-removable'))
            .some(tag => tag.dataset.tagName === tagName);

        if (existing) {
            this.showNotification('Ce tag existe déjà', 'error');
            return;
        }

        this.addTagToUI(tagName);
    },

    addTagToUI(tagName, tagId = null) {
        const tagsList = document.getElementById('tagsList');

        const tagDiv = document.createElement('div');
        tagDiv.className = 'tag-removable';
        tagDiv.dataset.tagName = tagName;
        if (tagId) tagDiv.dataset.tagId = tagId;

        tagDiv.innerHTML = `
            <span>${tagName}</span>
            <span class="tag-remove">×</span>
        `;

        tagDiv.querySelector('.tag-remove').addEventListener('click', () => {
            tagDiv.remove();
        });

        tagsList.appendChild(tagDiv);
    },

    async generateTags() {
        const title = document.getElementById('procTitle').value.trim();
        const categoryId = parseInt(document.getElementById('procCategory').value);
        const content = document.getElementById('procContent').value.trim();

        if (!title) {
            this.showNotification('Veuillez remplir au moins le titre', 'error');
            return;
        }

        const category = this.state.categories.find(c => c.id === categoryId);
        const categoryName = category ? category.name : '';

        try {
            this.showNotification('Génération des tags en cours...', 'info');

            const result = await api.generateKeywords(title, categoryName, content);
            const keywords = result.keywords || [];

            // Ajouter les tags
            keywords.forEach(keyword => {
                this.addTag(keyword);
            });

            this.showNotification(`${keywords.length} tags générés`, 'success');

        } catch (error) {
            console.error('Error generating tags:', error);
            this.showNotification('Erreur lors de la génération des tags', 'error');
        }
    },

    // ============================================
    // Fichiers
    // ============================================

    handleFileUpload(files) {
        // TODO: Implémenter l'upload de fichiers
        console.log('Files to upload:', files);
    },

    // ============================================
    // Markdown
    // ============================================

    applyMarkdownFormat(action) {
        const textarea = document.getElementById('procContent');
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        let replacement = '';

        switch (action) {
            case 'bold':
                replacement = `**${selectedText || 'texte'}**`;
                break;
            case 'italic':
                replacement = `*${selectedText || 'texte'}*`;
                break;
            case 'heading1':
                replacement = `# ${selectedText || 'Titre'}`;
                break;
            case 'heading2':
                replacement = `## ${selectedText || 'Titre'}`;
                break;
            case 'list':
                replacement = `- ${selectedText || 'élément'}`;
                break;
            case 'numberedList':
                replacement = `1. ${selectedText || 'élément'}`;
                break;
            case 'code':
                replacement = `\`\`\`\n${selectedText || 'code'}\n\`\`\``;
                break;
            case 'link':
                replacement = `[${selectedText || 'texte'}](url)`;
                break;
        }

        textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
        textarea.focus();
    },

    markdownToHtml(markdown) {
        if (!markdown) return '';

        let html = markdown;

        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

        // Inline code
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');

        // Lists
        html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Numbered lists
        html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    },

    // ============================================
    // Recherche
    // ============================================

    handleSearch(query) {
        this.state.searchQuery = query.trim();

        if (this.state.currentView === 'listView') {
            // Debounce
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.state.currentPage = 1;
                this.loadProcedures();
            }, 300);
        }
    },

    // ============================================
    // Settings
    // ============================================

    showSettings() {
        document.getElementById('modalSettings').style.display = 'flex';
        this.loadSettingsData();
    },

    hideSettings() {
        document.getElementById('modalSettings').style.display = 'none';
    },

    async loadSettingsData() {
        try {
            const settings = await api.getSettings();
            document.getElementById('settingClaudeKey').value = settings.claude_api_key || '';
            document.getElementById('settingCompanyName').value = settings.company_name || '';
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    },

    async saveSettings() {
        const claudeKey = document.getElementById('settingClaudeKey').value.trim();
        const companyName = document.getElementById('settingCompanyName').value.trim();

        try {
            if (claudeKey) {
                await api.updateSetting('claude_api_key', claudeKey);
            }
            if (companyName) {
                await api.updateSetting('company_name', companyName);
            }

            this.showNotification('Paramètres enregistrés', 'success');
            this.hideSettings();
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Erreur lors de la sauvegarde', 'error');
        }
    },

    async testClaude() {
        try {
            this.showNotification('Test de connexion en cours...', 'info');
            await api.testClaude();
            this.showNotification('Connexion réussie !', 'success');
        } catch (error) {
            console.error('Error testing Claude:', error);
            this.showNotification('Échec de la connexion', 'error');
        }
    },

    // ============================================
    // Home
    // ============================================

    async loadHomeStats() {
        try {
            const response = await api.getProcedures({ per_page: 1 });
            document.getElementById('statTotal').textContent = response.pagination.total || 0;

            // TODO: Calculer les procédures de la semaine
            document.getElementById('statWeek').textContent = '-';
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    },

    async loadRecentProcedures() {
        try {
            const response = await api.getProcedures({ per_page: 5 });
            const container = document.getElementById('recentProcedures');
            container.innerHTML = '';

            if (response.procedures.length === 0) {
                container.innerHTML = '<p style="color: var(--text-secondary);">Aucune procédure</p>';
                return;
            }

            response.procedures.forEach(proc => {
                const card = this.createProcedureCard(proc);
                container.appendChild(card);
            });
        } catch (error) {
            console.error('Error loading recent procedures:', error);
        }
    },

    // ============================================
    // Utilitaires
    // ============================================

    getRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // secondes

        if (diff < 60) return 'à l\'instant';
        if (diff < 3600) return `il y a ${Math.floor(diff / 60)}min`;
        if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`;
        if (diff < 172800) return 'hier';
        if (diff < 604800) return `il y a ${Math.floor(diff / 86400)}j`;
        if (diff < 2592000) return `il y a ${Math.floor(diff / 604800)}sem`;

        return date.toLocaleDateString('fr-FR');
    },

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    },

    getFileIcon(fileType) {
        const icons = {
            'ps1': '💾', 'sh': '💾', 'bat': '💾',
            'pdf': '📄', 'doc': '📄', 'docx': '📄',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️', 'webp': '🖼️',
            'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
            'ini': '⚙️', 'conf': '⚙️', 'xml': '⚙️', 'json': '⚙️',
            'txt': '📝', 'md': '📝',
            'zip': '📦', 'rar': '📦'
        };

        return icons[fileType] || '📄';
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    showNotification(message, type = 'info') {
        // TODO: Implémenter un système de notifications toast
        console.log(`[${type.toUpperCase()}] ${message}`);

        // Version simple avec alert pour le MVP
        if (type === 'error') {
            alert('❌ ' + message);
        } else if (type === 'success') {
            console.log('✅ ' + message);
        }
    },

    showHistory(procedureId) {
        // TODO: Implémenter l'affichage de l'historique
        console.log('Show history for procedure', procedureId);
    }
};

// Initialiser l'application au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
