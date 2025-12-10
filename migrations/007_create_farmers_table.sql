-- Migration: 007_create_farmers_table
-- Description: Create farmers table for farm profile data
-- User Story: US-004, US-005 (Farmer Registration & Profile Setup)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- FARMERS TABLE
-- Stores farm-specific profile data linked to users table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farmers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,

    -- Farm Basic Info
    farm_name VARCHAR(200),
    farm_description TEXT,

    -- Farm Address
    farm_street VARCHAR(255),
    farm_city VARCHAR(100),
    farm_state VARCHAR(50),
    farm_zip_code VARCHAR(20),
    farm_latitude DECIMAL(10, 8),
    farm_longitude DECIMAL(11, 8),

    -- Farming Practices (array of values)
    -- Values: Organic, Sustainable, Conventional, Biodynamic, Regenerative
    farming_practices TEXT[] NOT NULL DEFAULT '{}',

    -- Profile completion tracking
    profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    profile_completion_step INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_farmers_user_id ON public.farmers(user_id);
CREATE INDEX IF NOT EXISTS idx_farmers_profile_completed ON public.farmers(profile_completed);
CREATE INDEX IF NOT EXISTS idx_farmers_farm_city ON public.farmers(farm_city);
CREATE INDEX IF NOT EXISTS idx_farmers_farm_state ON public.farmers(farm_state);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_farmers_updated_at ON public.farmers;
CREATE TRIGGER update_farmers_updated_at
    BEFORE UPDATE ON public.farmers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.farmers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow select for all (public farm profiles)
DROP POLICY IF EXISTS farmers_select ON public.farmers;
CREATE POLICY farmers_select ON public.farmers
    FOR SELECT
    USING (true);

-- Policy: Allow insert
DROP POLICY IF EXISTS farmers_insert ON public.farmers;
CREATE POLICY farmers_insert ON public.farmers
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow update
DROP POLICY IF EXISTS farmers_update ON public.farmers;
CREATE POLICY farmers_update ON public.farmers
    FOR UPDATE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.farmers IS 'Farm profile data for farmer users (1:1 with users table)';
COMMENT ON COLUMN public.farmers.user_id IS 'Reference to users table (unique constraint ensures 1:1)';
COMMENT ON COLUMN public.farmers.farm_name IS 'Display name of the farm';
COMMENT ON COLUMN public.farmers.farm_description IS 'Description of the farm, history, practices';
COMMENT ON COLUMN public.farmers.farming_practices IS 'Array of farming practices: Organic, Sustainable, Conventional, Biodynamic, Regenerative';
COMMENT ON COLUMN public.farmers.profile_completed IS 'Whether farmer has completed initial profile setup';
COMMENT ON COLUMN public.farmers.profile_completion_step IS 'Current step in profile setup wizard (0 = not started)';
