const KeyboardShortcuts = {
    shortcuts: {},

    init() {
        document.addEventListener('keydown', (e) => this.handle(e));
        this.registerDefaults();
    },

    register(keys, callback, desc) {
        this.shortcuts[keys.toLowerCase()] = { callback, desc };
    },

    handle(e) {
        const isInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);

        let keys = [];
        if (e.ctrlKey) keys.push('ctrl');
        if (e.shiftKey) keys.push('shift');
        if (e.altKey) keys.push('alt');
        keys.push(e.key.toLowerCase());

        const combo = keys.join('+');
        const shortcut = this.shortcuts[combo];

        if (shortcut && (!isInput || combo === 'escape')) {
            e.preventDefault();
            shortcut.callback();
        }
    },

    registerDefaults() {
        this.register('ctrl+n', () => syncNow(), 'Synchroniser');
        this.register('ctrl+f', () => document.getElementById('searchInput')?.focus(), 'Rechercher');
        this.register('escape', () => closeTicketModal(), 'Fermer');
        this.register('ctrl+shift+l', () => ThemeManager.toggle(), 'Thème');
        this.register('ctrl+/', () => this.showHelp(), 'Aide');

        ['1','2','3'].forEach((n, i) => {
            const statuses = ['new', 'in_progress', 'resolved'];
            this.register(n, () => focusColumn(statuses[i]), `Colonne ${n}`);
        });
    },

    showHelp() {
        const html = Object.entries(this.shortcuts)
            .map(([k, {desc}]) => `<tr><td style="padding: 0.5rem;"><kbd style="background: var(--bg-tertiary); padding: 0.25rem 0.5rem; border-radius: 4px;">${k}</kbd></td><td style="padding: 0.5rem;">${desc}</td></tr>`)
            .join('');

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <h2>⌨️ Raccourcis clavier</h2>
                <table style="width: 100%; margin: 1rem 0;">${html}</table>
                <button class="btn btn-primary" onclick="this.closest('.modal').remove()">Fermer</button>
            </div>`;
        document.body.appendChild(modal);
    }
};

function focusColumn(status) {
    const col = document.querySelector(`[data-status="${status}"]`);
    if (col) col.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.addEventListener('DOMContentLoaded', () => KeyboardShortcuts.init());
