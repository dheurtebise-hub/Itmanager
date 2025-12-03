// Gestion de l'importation de procédures

// Modal import unique
function openImportSingleProcedureModal() {
    document.getElementById('importSingleModal').style.display = 'flex';
    document.getElementById('importSingleForm').reset();
}

function closeImportSingleModal() {
    document.getElementById('importSingleModal').style.display = 'none';
}

// Modal import batch
function openImportBatchProceduresModal() {
    document.getElementById('importBatchModal').style.display = 'flex';
    document.getElementById('importBatchForm').reset();
    document.getElementById('batchImportProgress').style.display = 'none';
}

function closeImportBatchModal() {
    document.getElementById('importBatchModal').style.display = 'none';
}

// Import procédure unique
async function importSingleProcedure(event) {
    event.preventDefault();

    const fileInput = document.getElementById('singleProcedureFile');
    const aiReformulation = document.getElementById('aiReformulation').checked;
    const file = fileInput.files[0];

    if (!file) {
        alert('Veuillez sélectionner un fichier');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('ai_reformulation', aiReformulation);

    try {
        showNotification('Importation en cours...', 'info');

        const response = await fetch('/api/procedures/import/single', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erreur lors de l\'importation');
        }

        const result = await response.json();
        showNotification(`✅ Procédure "${result.procedure.title}" importée avec succès`, 'success');

        closeImportSingleModal();

        // Recharger les stats pour mettre à jour le compteur de procédures
        loadStats();
    } catch (error) {
        console.error('Error importing procedure:', error);
        showNotification(`❌ ${error.message}`, 'error');
    }
}

// Import procédures en groupe
async function importBatchProcedures(event) {
    event.preventDefault();

    const filesInput = document.getElementById('batchProcedureFiles');
    const aiReformulation = document.getElementById('batchAiReformulation').checked;
    const files = Array.from(filesInput.files);

    if (files.length === 0) {
        alert('Veuillez sélectionner au moins un fichier');
        return;
    }

    const progressDiv = document.getElementById('batchImportProgress');
    const progressBar = document.getElementById('batchProgressBar');
    const progressText = document.getElementById('batchProgressText');
    const importBtn = document.getElementById('batchImportBtn');

    progressDiv.style.display = 'block';
    importBtn.disabled = true;

    let imported = 0;
    const total = files.length;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('ai_reformulation', aiReformulation);

            const response = await fetch('/api/procedures/import/single', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                imported++;
            } else {
                console.error(`Failed to import ${file.name}`);
            }

        } catch (error) {
            console.error(`Error importing ${file.name}:`, error);
        }

        // Mettre à jour la progress bar
        const progress = ((i + 1) / total) * 100;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${imported} / ${total} procédures importées`;
    }

    showNotification(`✅ ${imported} / ${total} procédures importées avec succès`, 'success');

    setTimeout(() => {
        closeImportBatchModal();
        loadStats();
    }, 2000);

    importBtn.disabled = false;
}
