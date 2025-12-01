-- ============================================
-- SCHEMA BASE DE DONNÉES - IT TICKET MANAGER
-- ============================================

-- Table des tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE,
    subject TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    sender_name TEXT,
    body TEXT,
    html_body TEXT,
    summary TEXT,
    category TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'new',
    source_folder TEXT,
    received_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    resolution TEXT,
    resolution_time_minutes INTEGER,
    ai_categorized BOOLEAN DEFAULT FALSE,
    ai_confidence REAL
);

-- Table de la base de connaissances
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT,
    content_type TEXT DEFAULT 'text',
    file_path TEXT,
    tags TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    source_ticket_id INTEGER,
    FOREIGN KEY (source_ticket_id) REFERENCES tickets(id)
);

-- Table des catégories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#0079BF',
    icon TEXT DEFAULT '📁',
    order_index INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- Catégories par défaut
INSERT OR IGNORE INTO categories (name, color, icon, order_index) VALUES
    ('installation_logiciel', '#0079BF', '💿', 1),
    ('depannage_materiel', '#70B500', '🔧', 2),
    ('demande_licence', '#FF9F1A', '🔑', 3),
    ('support_applicatif', '#EB5A46', '💻', 4),
    ('reseau', '#C377E0', '🌐', 5),
    ('securite', '#FF5733', '🔒', 6),
    ('autre', '#838C91', '📋', 7);

-- Table des coûts API
CREATE TABLE IF NOT EXISTS api_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_euros REAL,
    request_type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Configuration des SLA
CREATE TABLE IF NOT EXISTS sla_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority TEXT UNIQUE NOT NULL,
    response_time_minutes INTEGER NOT NULL,
    resolution_time_minutes INTEGER NOT NULL,
    escalation_email TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- SLA par défaut
INSERT OR IGNORE INTO sla_config (priority, response_time_minutes, resolution_time_minutes) VALUES
    ('urgent', 30, 240),
    ('high', 60, 480),
    ('medium', 240, 1440),
    ('low', 480, 2880);

-- Alertes SLA
CREATE TABLE IF NOT EXISTS sla_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    sla_type TEXT NOT NULL,
    notified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

-- Templates email
CREATE TABLE IF NOT EXISTS email_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables TEXT,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Templates par défaut
INSERT OR IGNORE INTO email_templates (name, subject_template, body_template, variables) VALUES
(
    'Accusé de réception',
    'Re: {subject} [Ticket #{ticket_id}]',
    'Bonjour {sender_name},

Nous avons bien reçu votre demande (ticket #{ticket_id}).

Notre équipe va l''analyser et reviendra vers vous rapidement.

Cordialement,
{agent_name}
Service IT',
    '["sender_name", "subject", "ticket_id", "agent_name"]'
),
(
    'Résolution standard',
    'Re: {subject} [Ticket #{ticket_id}] - RÉSOLU',
    'Bonjour {sender_name},

Votre demande a été traitée avec succès.

{resolution_details}

N''hésitez pas à nous contacter si besoin.

Cordialement,
{agent_name}
Service IT',
    '["sender_name", "subject", "ticket_id", "agent_name", "resolution_details"]'
);

-- Feedback IA
CREATE TABLE IF NOT EXISTS ai_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    suggestion_hash TEXT NOT NULL,
    was_helpful BOOLEAN NOT NULL,
    feedback_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

-- Statistiques journalières
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE UNIQUE NOT NULL,
    tickets_created INTEGER DEFAULT 0,
    tickets_resolved INTEGER DEFAULT 0,
    avg_resolution_time_minutes REAL,
    api_cost_euros REAL DEFAULT 0
);

-- ============================================
-- INDEX POUR OPTIMISATION
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_received_date ON tickets(received_date DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_sender_email ON tickets(sender_email);
CREATE INDEX IF NOT EXISTS idx_tickets_status_priority ON tickets(status, priority);
CREATE INDEX IF NOT EXISTS idx_tickets_dashboard ON tickets(status, category, priority, received_date DESC);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_usage ON knowledge_base(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_api_costs_date ON api_costs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sla_alerts_ticket ON sla_alerts(ticket_id);

-- Recherche full-text sur la base de connaissances
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search USING fts5(
    title,
    content,
    tags,
    content='knowledge_base',
    content_rowid='id'
);
