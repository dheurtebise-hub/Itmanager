-- ============================================
-- MIGRATION: Add performance indexes
-- Date: 2025-12-04
-- ============================================

-- Index pour tri et filtrage par date de création
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

-- Index pour tri et filtrage par date de mise à jour
CREATE INDEX IF NOT EXISTS idx_tickets_updated_at ON tickets(updated_at DESC);

-- Index pour recherche de tickets résolus récemment
CREATE INDEX IF NOT EXISTS idx_tickets_resolved_at ON tickets(resolved_at DESC);

-- Index pour recherche de procédures récentes
CREATE INDEX IF NOT EXISTS idx_procedures_created_at ON procedures(created_at DESC);

-- Index pour tri de procédures par mise à jour
CREATE INDEX IF NOT EXISTS idx_procedures_updated_at ON procedures(updated_at DESC);

-- Index pour jointure feedback -> tickets
CREATE INDEX IF NOT EXISTS idx_ai_feedback_ticket ON ai_feedback(ticket_id);

-- Index composite pour alertes SLA par type
CREATE INDEX IF NOT EXISTS idx_sla_alerts_ticket_type ON sla_alerts(ticket_id, alert_type);

-- Index pour date des statistiques journalières
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date DESC);

-- Index pour recherche de catégories actives
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active, order_index);
