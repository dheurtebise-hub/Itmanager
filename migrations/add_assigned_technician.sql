-- Migration: Ajout du champ technicien assigné et suppression des catégories

-- Ajouter la colonne assigned_to pour taguer un technicien
ALTER TABLE tickets ADD COLUMN assigned_to TEXT;

-- Index pour optimiser les recherches par technicien
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);
