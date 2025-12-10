-- Migration: 010_create_farmer_bank_accounts_table
-- Description: Create farmer_bank_accounts table with encrypted data
-- User Story: US-005 (Farmer Profile Setup)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times
-- SECURITY: Account numbers are encrypted at application level (AES-128)

-- ============================================================================
-- FARMER BANK ACCOUNTS TABLE
-- Stores encrypted bank account details for farmer payouts
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farmer_bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL UNIQUE REFERENCES public.farmers(id) ON DELETE CASCADE,
    account_holder_name VARCHAR(200) NOT NULL,

    -- Encrypted fields (AES-128 via Fernet)
    -- These store base64-encoded encrypted data
    account_number_encrypted TEXT NOT NULL,
    routing_number_encrypted TEXT NOT NULL,

    -- Display-only fields (not sensitive)
    account_last_four VARCHAR(4) NOT NULL,
    bank_name VARCHAR(100),
    account_type VARCHAR(20) NOT NULL DEFAULT 'checking',

    -- Verification status (for future Stripe/Plaid integration)
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_account_type CHECK (account_type IN ('checking', 'savings')),
    CONSTRAINT valid_last_four CHECK (account_last_four ~ '^[0-9]{4}$')
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for farmer lookups (unique constraint already creates one)
CREATE INDEX IF NOT EXISTS idx_farmer_bank_accounts_farmer_id ON public.farmer_bank_accounts(farmer_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_farmer_bank_accounts_updated_at ON public.farmer_bank_accounts;
CREATE TRIGGER update_farmer_bank_accounts_updated_at
    BEFORE UPDATE ON public.farmer_bank_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.farmer_bank_accounts ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations (controlled at application level with user validation)
DROP POLICY IF EXISTS farmer_bank_accounts_select ON public.farmer_bank_accounts;
CREATE POLICY farmer_bank_accounts_select ON public.farmer_bank_accounts
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS farmer_bank_accounts_insert ON public.farmer_bank_accounts;
CREATE POLICY farmer_bank_accounts_insert ON public.farmer_bank_accounts
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS farmer_bank_accounts_update ON public.farmer_bank_accounts;
CREATE POLICY farmer_bank_accounts_update ON public.farmer_bank_accounts
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS farmer_bank_accounts_delete ON public.farmer_bank_accounts;
CREATE POLICY farmer_bank_accounts_delete ON public.farmer_bank_accounts
    FOR DELETE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.farmer_bank_accounts IS 'Encrypted bank account details for farmer payouts (1:1 with farmers)';
COMMENT ON COLUMN public.farmer_bank_accounts.farmer_id IS 'Reference to farmers table (unique ensures 1:1)';
COMMENT ON COLUMN public.farmer_bank_accounts.account_holder_name IS 'Name on the bank account';
COMMENT ON COLUMN public.farmer_bank_accounts.account_number_encrypted IS 'AES-128 encrypted account number (Fernet)';
COMMENT ON COLUMN public.farmer_bank_accounts.routing_number_encrypted IS 'AES-128 encrypted routing number (Fernet)';
COMMENT ON COLUMN public.farmer_bank_accounts.account_last_four IS 'Last 4 digits of account number for display';
COMMENT ON COLUMN public.farmer_bank_accounts.bank_name IS 'Name of the bank (optional)';
COMMENT ON COLUMN public.farmer_bank_accounts.account_type IS 'checking or savings';
COMMENT ON COLUMN public.farmer_bank_accounts.is_verified IS 'Whether bank account has been verified (future feature)';
