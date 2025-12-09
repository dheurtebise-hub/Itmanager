-- ============================================
-- SCHEMA BASE DE DONNÉES - KB IT SUPPORT
-- Base de connaissances IT standalone
-- ============================================

-- Table des catégories (avec hiérarchie)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    parent_id INTEGER,
    display_order INTEGER,
    color_code TEXT DEFAULT '#06b6d4',
    icon TEXT DEFAULT '📁',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- Table des procédures
CREATE TABLE IF NOT EXISTS procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    category_id INTEGER NOT NULL,
    estimated_time INTEGER,
    created_by TEXT DEFAULT 'manual',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Table des tags
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table de liaison procédures-tags
CREATE TABLE IF NOT EXISTS procedure_tags (
    procedure_id INTEGER,
    tag_id INTEGER,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (procedure_id, tag_id),
    FOREIGN KEY (procedure_id) REFERENCES procedures(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Table des fichiers joints
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    storage_path TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (procedure_id) REFERENCES procedures(id) ON DELETE CASCADE
);

-- Table de versioning
CREATE TABLE IF NOT EXISTS procedure_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    changed_by TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (procedure_id) REFERENCES procedures(id) ON DELETE CASCADE
);

-- Table de configuration
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEX POUR OPTIMISATION
-- ============================================

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active, display_order);

CREATE INDEX IF NOT EXISTS idx_procedures_category ON procedures(category_id);
CREATE INDEX IF NOT EXISTS idx_procedures_archived ON procedures(is_archived);
CREATE INDEX IF NOT EXISTS idx_procedures_created_at ON procedures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_procedures_updated_at ON procedures(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_procedures_usage ON procedures(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_usage ON tags(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_procedure_tags_procedure ON procedure_tags(procedure_id);
CREATE INDEX IF NOT EXISTS idx_procedure_tags_tag ON procedure_tags(tag_id);

CREATE INDEX IF NOT EXISTS idx_attachments_procedure ON attachments(procedure_id);
CREATE INDEX IF NOT EXISTS idx_attachments_type ON attachments(file_type);

CREATE INDEX IF NOT EXISTS idx_versions_procedure ON procedure_versions(procedure_id);
CREATE INDEX IF NOT EXISTS idx_versions_date ON procedure_versions(changed_at DESC);

-- Recherche full-text sur les procédures
CREATE VIRTUAL TABLE IF NOT EXISTS procedures_search USING fts5(
    title,
    content,
    description,
    content='procedures',
    content_rowid='id'
);

-- ============================================
-- DONNÉES INITIALES
-- ============================================

-- Catégories principales (niveau 1)
INSERT OR IGNORE INTO categories (id, name, short_name, parent_id, display_order, color_code, icon) VALUES
    (1, 'Office 365', 'o365', NULL, 1, '#06b6d4', '📧'),
    (2, 'Matériel', 'hard', NULL, 2, '#f97316', '🖥️'),
    (3, 'Réseau', 'net', NULL, 3, '#10b981', '🌐'),
    (4, 'Comptes et accès', 'acct', NULL, 4, '#fbbf24', '👤'),
    (5, 'Logiciels', 'soft', NULL, 5, '#8b5cf6', '💾'),
    (6, 'Système', 'sys', NULL, 6, '#ef4444', '⚙️');

-- Sous-catégories Office 365 (parent_id = 1)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('Outlook', 'out', 1, 1, '#06b6d4', '📧'),
    ('Teams', 'team', 1, 2, '#06b6d4', '💬'),
    ('OneDrive', 'one', 1, 3, '#06b6d4', '☁️'),
    ('SharePoint', 'share', 1, 4, '#06b6d4', '📊'),
    ('Exchange', 'exch', 1, 5, '#06b6d4', '📬');

-- Sous-catégories Matériel (parent_id = 2)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('Ordinateurs', 'pc', 2, 1, '#f97316', '💻'),
    ('Imprimantes', 'print', 2, 2, '#f97316', '🖨️'),
    ('Périphériques', 'periph', 2, 3, '#f97316', '⌨️'),
    ('Téléphonie', 'phone', 2, 4, '#f97316', '📞');

-- Sous-catégories Réseau (parent_id = 3)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('VPN', 'vpn', 3, 1, '#10b981', '🔐'),
    ('Wi-Fi', 'wifi', 3, 2, '#10b981', '📡'),
    ('Partages réseau', 'netshare', 3, 3, '#10b981', '🗂️'),
    ('Accès distant', 'remote', 3, 4, '#10b981', '🌍');

-- Sous-catégories Comptes et accès (parent_id = 4)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('Active Directory', 'ad', 4, 1, '#fbbf24', '🗄️'),
    ('Création comptes', 'create', 4, 2, '#fbbf24', '➕'),
    ('Reset passwords', 'reset', 4, 3, '#fbbf24', '🔑'),
    ('Permissions', 'perms', 4, 4, '#fbbf24', '🛡️');

-- Sous-catégories Logiciels (parent_id = 5)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('Installation', 'inst', 5, 1, '#8b5cf6', '📥'),
    ('Désinstallation', 'uninst', 5, 2, '#8b5cf6', '🗑️'),
    ('Mises à jour', 'update', 5, 3, '#8b5cf6', '🔄'),
    ('Licences', 'lic', 5, 4, '#8b5cf6', '🎫'),
    ('Maintenance', 'maint', 5, 5, '#8b5cf6', '🔧');

-- Sous-catégories Système (parent_id = 6)
INSERT OR IGNORE INTO categories (name, short_name, parent_id, display_order, color_code, icon) VALUES
    ('Windows 10/11', 'win', 6, 1, '#ef4444', '🪟'),
    ('PowerShell', 'ps', 6, 2, '#ef4444', '⚡'),
    ('GPO', 'gpo', 6, 3, '#ef4444', '📜'),
    ('Sauvegardes', 'backup', 6, 4, '#ef4444', '💾');

-- Configuration par défaut
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('app_version', '1.0.0'),
    ('company_name', 'Service IT'),
    ('max_upload_size_mb', '50'),
    ('claude_api_key', ''),
    ('claude_model', 'claude-sonnet-4-5-20250929'),
    ('claude_temperature', '0.7'),
    ('claude_max_tokens', '1024'),
    ('claude_enabled', 'true');
