-- Migration: Add is_not_user_request column to tickets table
-- Date: 2025-12-03

-- Add column to tickets table
ALTER TABLE tickets ADD COLUMN is_not_user_request BOOLEAN DEFAULT 0;

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_tickets_is_not_user_request ON tickets(is_not_user_request);
