// Éditeur de procédures

let currentProcedureSteps = [];
let procedureMediaFiles = new Map(); // Map<stepIndex, File[]>
let quillEditors = new Map(); // Map<stepIndex, Quill>

/**
 * Ouvre la modal pour créer une nouvelle procédure
 */
function openProcedureModal(ticketId = null, procedureId = null) {
    const modal = document.getElementById('procedureModal');
    const modalTitle = document.getElementById('procedureModalTitle');

    // Réinitialiser le formulaire
    document.getElementById('procedureForm').reset();
    document.getElementById('procedureId').value = procedureId || '';
    document.getElementById('procedureSourceTicketId').value = ticketId || '';

    currentProcedureSteps = [];
    procedureMediaFiles.clear();

    if (procedureId) {
        // Mode édition
        modalTitle.textContent = 'Modifier la procédure';
        loadProcedureData(procedureId);
    } else {
        // Mode création
        modalTitle.textContent = 'Créer une procédure';

        // Pré-remplir la catégorie si on a un ticket source
        if (ticketId) {
            const ticket = allTickets.find(t => t.id === ticketId);
            if (ticket && ticket.category) {
                document.getElementById('procedureCategory').value = ticket.category;
            }
        }

        // Ajouter une première étape vide
        addProcedureStep();
    }

    modal.style.display = 'flex';
}

/**
 * Ferme la modal d'édition de procédure
 */
function closeProcedureModal() {
    const modal = document.getElementById('procedureModal');
    modal.style.display = 'none';

    // Réinitialiser
    currentProcedureSteps = [];
    procedureMediaFiles.clear();
}

/**
 * Charge les données d'une procédure existante
 */
async function loadProcedureData(procedureId) {
    try {
        const proc = await api.getProcedure(procedureId);

        if (!proc) {
            showNotification('❌ Procédure introuvable', 'error');
            closeProcedureModal();
            return;
        }

        // Remplir le formulaire
        document.getElementById('procedureTitle').value = proc.title || '';
        document.getElementById('procedureCategory').value = proc.category || '';

        // Mots-clés
        if (proc.keywords && Array.isArray(proc.keywords)) {
            document.getElementById('procedureKeywords').value = proc.keywords.join(', ');
        }

        // Étapes
        currentProcedureSteps = proc.steps || [];
        renderProcedureSteps();

    } catch (error) {
        console.error('Error loading procedure:', error);
        showNotification('❌ Erreur lors du chargement de la procédure', 'error');
    }
}

/**
 * Ajoute une nouvelle étape à la procédure
 */
function addProcedureStep(content = '', medias = []) {
    const step = {
        content: content,
        medias: medias
    };

    currentProcedureSteps.push(step);
    renderProcedureSteps();
}

/**
 * Supprime une étape
 */
function removeProcedureStep(index) {
    if (currentProcedureSteps.length <= 1) {
        showNotification('⚠️ Une procédure doit avoir au moins une étape', 'warning');
        return;
    }

    if (confirm('Supprimer cette étape ?')) {
        currentProcedureSteps.splice(index, 1);
        procedureMediaFiles.delete(index);
        renderProcedureSteps();
    }
}

/**
 * Déplace une étape vers le haut
 */
function moveStepUp(index) {
    if (index === 0) return;

    [currentProcedureSteps[index], currentProcedureSteps[index - 1]] =
        [currentProcedureSteps[index - 1], currentProcedureSteps[index]];

    renderProcedureSteps();
}

/**
 * Déplace une étape vers le bas
 */
function moveStepDown(index) {
    if (index === currentProcedureSteps.length - 1) return;

    [currentProcedureSteps[index], currentProcedureSteps[index + 1]] =
        [currentProcedureSteps[index + 1], currentProcedureSteps[index]];

    renderProcedureSteps();
}

/**
 * Affiche les étapes dans le formulaire
 */
function renderProcedureSteps() {
    const container = document.getElementById('procedureSteps');

    if (currentProcedureSteps.length === 0) {
        container.innerHTML = '<p class="form-help">Aucune étape. Cliquez sur "Ajouter une étape" pour commencer.</p>';
        quillEditors.clear();
        return;
    }

    // Nettoyer les anciens éditeurs
    quillEditors.clear();

    container.innerHTML = currentProcedureSteps.map((step, index) => `
        <div class="procedure-step-item" data-step-index="${index}">
            <div class="procedure-step-header">
                <span class="procedure-step-number">Étape ${index + 1}</span>
                <div class="procedure-step-actions">
                    ${index > 0 ? `<button type="button" class="btn-icon btn-move" onclick="moveStepUp(${index})" title="Monter">⬆️</button>` : ''}
                    ${index < currentProcedureSteps.length - 1 ? `<button type="button" class="btn-icon btn-move" onclick="moveStepDown(${index})" title="Descendre">⬇️</button>` : ''}
                    <button type="button" class="btn-icon btn-delete" onclick="removeProcedureStep(${index})" title="Supprimer">🗑️</button>
                </div>
            </div>

            <div id="editor-${index}" class="step-content-editor"></div>

            <div class="step-media-upload">
                <label class="media-upload-btn">
                    <span>📎 Ajouter une image/vidéo/GIF</span>
                    <input type="file"
                           accept="image/*,video/*,.gif"
                           multiple
                           onchange="handleMediaUpload(${index}, this.files)">
                </label>

                <div class="media-preview" id="media-preview-${index}">
                    ${renderMediaPreviews(index, step.medias || [])}
                </div>
            </div>
        </div>
    `).join('');

    // Initialiser les éditeurs Quill
    currentProcedureSteps.forEach((step, index) => {
        const editorContainer = document.getElementById(`editor-${index}`);
        if (editorContainer) {
            const quill = new Quill(`#editor-${index}`, {
                theme: 'snow',
                placeholder: 'Décrivez cette étape...',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'color': [] }, { 'background': [] }],
                        ['link', 'image'],
                        ['clean']
                    ]
                }
            });

            // Définir le contenu initial (support HTML)
            if (step.content) {
                quill.root.innerHTML = step.content;
            }

            // Sauvegarder les changements
            quill.on('text-change', () => {
                currentProcedureSteps[index].content = quill.root.innerHTML;
            });

            quillEditors.set(index, quill);
        }
    });
}

/**
 * Met à jour le contenu d'une étape
 */
function updateStepContent(index, content) {
    currentProcedureSteps[index].content = content;
}

/**
 * Gère l'upload de médias pour une étape
 */
function handleMediaUpload(stepIndex, files) {
    if (!files || files.length === 0) return;

    // Stocker les fichiers
    const existingFiles = procedureMediaFiles.get(stepIndex) || [];
    const newFiles = Array.from(files);
    procedureMediaFiles.set(stepIndex, [...existingFiles, ...newFiles]);

    // Ajouter les médias à l'étape
    if (!currentProcedureSteps[stepIndex].medias) {
        currentProcedureSteps[stepIndex].medias = [];
    }

    // Créer des URLs de prévisualisation
    newFiles.forEach(file => {
        const url = URL.createObjectURL(file);
        currentProcedureSteps[stepIndex].medias.push({
            url: url,
            type: file.type.startsWith('image') ? 'image' : 'video',
            filename: file.name,
            isNew: true
        });
    });

    // Re-render les previews
    const previewContainer = document.getElementById(`media-preview-${stepIndex}`);
    if (previewContainer) {
        previewContainer.innerHTML = renderMediaPreviews(stepIndex, currentProcedureSteps[stepIndex].medias);
    }
}

/**
 * Supprime un média d'une étape
 */
function removeMedia(stepIndex, mediaIndex) {
    if (!currentProcedureSteps[stepIndex].medias) return;

    const media = currentProcedureSteps[stepIndex].medias[mediaIndex];

    // Révoquer l'URL si c'est une nouvelle upload
    if (media.isNew && media.url) {
        URL.revokeObjectURL(media.url);
    }

    currentProcedureSteps[stepIndex].medias.splice(mediaIndex, 1);

    // Re-render
    const previewContainer = document.getElementById(`media-preview-${stepIndex}`);
    if (previewContainer) {
        previewContainer.innerHTML = renderMediaPreviews(stepIndex, currentProcedureSteps[stepIndex].medias);
    }
}

/**
 * Affiche les prévisualisations de médias
 */
function renderMediaPreviews(stepIndex, medias) {
    if (!medias || medias.length === 0) return '';

    return medias.map((media, index) => {
        const isImage = media.type === 'image' || media.url.match(/\.(jpg|jpeg|png|gif|webp)$/i);
        const tag = isImage
            ? `<img src="${media.url}" alt="${media.filename || 'Image'}">`
            : `<video src="${media.url}" controls></video>`;

        return `
            <div class="media-preview-item">
                ${tag}
                <button type="button" class="media-preview-remove" onclick="removeMedia(${stepIndex}, ${index})">✕</button>
            </div>
        `;
    }).join('');
}

/**
 * Sauvegarde la procédure
 */
async function saveProcedure(event) {
    event.preventDefault();

    console.log('💾 Starting procedure save...');

    // Récupérer les données du formulaire
    const procedureId = document.getElementById('procedureId').value;
    const sourceTicketId = document.getElementById('procedureSourceTicketId').value;
    const title = document.getElementById('procedureTitle').value.trim();
    const category = document.getElementById('procedureCategory').value;

    console.log('📝 Form data:', { procedureId, sourceTicketId, title, category });
    console.log('📋 Current steps:', currentProcedureSteps);

    // Validation
    if (!title) {
        showNotification('⚠️ Le titre est obligatoire', 'warning');
        return;
    }

    if (!category) {
        showNotification('⚠️ La catégorie est obligatoire', 'warning');
        return;
    }

    if (currentProcedureSteps.length === 0) {
        showNotification('⚠️ Ajoutez au moins une étape', 'warning');
        return;
    }

    // Mettre à jour le contenu depuis les éditeurs Quill avant validation
    quillEditors.forEach((quill, index) => {
        if (currentProcedureSteps[index]) {
            currentProcedureSteps[index].content = quill.root.innerHTML;
        }
    });

    console.log('📋 Steps after Quill update:', currentProcedureSteps);

    // Vérifier que toutes les étapes ont du contenu réel (pas juste du HTML vide)
    const emptySteps = currentProcedureSteps.filter((step, idx) => {
        if (!step.content) {
            console.log(`⚠️ Step ${idx + 1}: No content`);
            return true;
        }
        // Créer un élément temporaire pour extraire le texte
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = step.content;
        const textContent = tempDiv.textContent || tempDiv.innerText || '';
        const isEmpty = textContent.trim().length === 0;
        console.log(`📄 Step ${idx + 1} text length: ${textContent.trim().length}, isEmpty: ${isEmpty}`);
        return isEmpty;
    });

    if (emptySteps.length > 0) {
        console.log('⚠️ Empty steps found:', emptySteps.length);
        showNotification('⚠️ Toutes les étapes doivent avoir du contenu', 'warning');
        return;
    }

    // Préparer les étapes
    const steps = currentProcedureSteps.map(step => step.content);

    // Générer les mots-clés automatiquement avec l'IA
    showNotification('🤖 Génération des mots-clés...', 'info');
    console.log('🤖 Generating keywords...');

    let keywords = [];
    try {
        // Extraire le texte brut des étapes
        const stepsText = steps.map(step => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = step;
            return tempDiv.textContent || tempDiv.innerText || '';
        }).join(' ');

        console.log('📝 Steps text for keywords:', stepsText.substring(0, 100) + '...');

        const aiResponse = await fetch('/api/ai/generate-keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                category: category,
                content: stepsText.substring(0, 500) // Limiter la taille
            })
        });

        console.log('🔍 AI Response status:', aiResponse.status);

        if (aiResponse.ok) {
            const result = await aiResponse.json();
            keywords = result.keywords || [];
            console.log('✅ Keywords generated:', keywords);
        } else {
            const errorText = await aiResponse.text();
            console.warn('⚠️ AI Response error:', errorText);
            throw new Error(`API returned ${aiResponse.status}`);
        }
    } catch (error) {
        console.warn('⚠️ Could not generate keywords with AI:', error);
        // Fallback : extraire des mots du titre
        keywords = title.toLowerCase().split(/\s+/).filter(w => w.length > 3).slice(0, 5);
        console.log('📝 Fallback keywords:', keywords);
    }

    // Préparer les données (sans description)
    const procedureData = {
        title,
        category,
        description: '', // Toujours vide maintenant
        keywords,
        steps,
        source_ticket_id: sourceTicketId ? parseInt(sourceTicketId) : null
    };

    console.log('📦 Procedure data to save:', procedureData);

    try {
        let savedProcedure;

        if (procedureId) {
            // Mise à jour
            console.log('🔄 Updating procedure:', procedureId);
            await api.updateProcedure(procedureId, procedureData);
            savedProcedure = { id: procedureId, ...procedureData };
            showNotification('✅ Procédure mise à jour avec succès !', 'success');
        } else {
            // Création manuelle
            console.log('➕ Creating new procedure...');
            savedProcedure = await api.createProcedureManually(procedureData);
            console.log('✅ Procedure created:', savedProcedure);
            showNotification('✅ Procédure créée avec succès !', 'success');
        }

        console.log('🎉 Procedure saved successfully!');

        // Fermer la modal
        closeProcedureModal();

        // Recharger les procédures si on a un ticket source
        if (sourceTicketId) {
            await showProceduresForTicket(parseInt(sourceTicketId));
        }

    } catch (error) {
        console.error('❌ Error saving procedure:', error);
        showNotification('❌ Erreur lors de la sauvegarde de la procédure: ' + error.message, 'error');
    }
}
