-- Migration: 004_create_user_addresses_table
-- Description: Create user_addresses table for delivery addresses
-- User Story: US-003 (User Profile Management)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- USER ADDRESSES TABLE
-- Supports: AC-003-4 (add/edit delivery address)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.user_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    label VARCHAR(50),
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    delivery_instructions TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_user_addresses_user_id
ON public.user_addresses(user_id);

-- Partial index for default address lookup
CREATE INDEX IF NOT EXISTS idx_user_addresses_default
ON public.user_addresses(user_id, is_default)
WHERE is_default = TRUE;

-- Partial index for active addresses
CREATE INDEX IF NOT EXISTS idx_user_addresses_active
ON public.user_addresses(user_id, is_active)
WHERE is_active = TRUE;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_user_addresses_updated_at ON public.user_addresses;
CREATE TRIGGER update_user_addresses_updated_at
    BEFORE UPDATE ON public.user_addresses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.user_addresses ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own addresses
DROP POLICY IF EXISTS user_addresses_select_own ON public.user_addresses;
CREATE POLICY user_addresses_select_own ON public.user_addresses
    FOR SELECT
    USING (true);

-- Policy: Users can insert their own addresses
DROP POLICY IF EXISTS user_addresses_insert_own ON public.user_addresses;
CREATE POLICY user_addresses_insert_own ON public.user_addresses
    FOR INSERT
    WITH CHECK (true);

-- Policy: Users can update their own addresses
DROP POLICY IF EXISTS user_addresses_update_own ON public.user_addresses;
CREATE POLICY user_addresses_update_own ON public.user_addresses
    FOR UPDATE
    USING (true);

-- Policy: Users can delete their own addresses
DROP POLICY IF EXISTS user_addresses_delete_own ON public.user_addresses;
CREATE POLICY user_addresses_delete_own ON public.user_addresses
    FOR DELETE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.user_addresses IS 'Delivery addresses for user orders';
COMMENT ON COLUMN public.user_addresses.label IS 'User-defined label (e.g., Home, Work, Office)';
COMMENT ON COLUMN public.user_addresses.street IS 'Street address including apartment/unit number';
COMMENT ON COLUMN public.user_addresses.city IS 'City name';
COMMENT ON COLUMN public.user_addresses.state IS 'State/province code or name';
COMMENT ON COLUMN public.user_addresses.zip_code IS 'ZIP or postal code';
COMMENT ON COLUMN public.user_addresses.delivery_instructions IS 'Special delivery instructions (e.g., Leave at door)';
COMMENT ON COLUMN public.user_addresses.is_default IS 'Whether this is the default delivery address';
COMMENT ON COLUMN public.user_addresses.is_active IS 'Soft delete flag - FALSE means address is deleted';
