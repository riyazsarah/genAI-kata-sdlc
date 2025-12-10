-- Migration: 006_add_user_role_column
-- Description: Add role column to users table for farmer/consumer distinction
-- User Story: US-004 (Farmer Registration)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- USER ROLE COLUMN
-- Distinguishes between consumer and farmer accounts
-- ============================================================================

-- Add role column with default 'consumer'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'role'
    ) THEN
        ALTER TABLE public.users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'consumer';
    END IF;
END $$;

-- Add check constraint for valid roles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'valid_user_role'
        AND table_name = 'users'
    ) THEN
        ALTER TABLE public.users ADD CONSTRAINT valid_user_role
            CHECK (role IN ('consumer', 'farmer'));
    END IF;
END $$;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for role-based queries
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN public.users.role IS 'User role: consumer (default) or farmer';
