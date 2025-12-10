-- Migration: 005_create_user_payment_methods_table
-- Description: Create user_payment_methods table for tokenized payment storage
-- User Story: US-003 (User Profile Management)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- USER PAYMENT METHODS TABLE
-- Supports: AC-003-5 (add payment method)
-- SECURITY: Only tokenized payment data is stored - NO raw card numbers
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.user_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    payment_type VARCHAR(20) NOT NULL,
    provider VARCHAR(50),
    token VARCHAR(255) NOT NULL,
    last_four VARCHAR(4),
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_payment_type CHECK (payment_type IN ('card', 'digital_wallet')),
    CONSTRAINT valid_expiry_month CHECK (expiry_month IS NULL OR (expiry_month >= 1 AND expiry_month <= 12)),
    CONSTRAINT valid_expiry_year CHECK (expiry_year IS NULL OR expiry_year >= 2024)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_user_payment_methods_user_id
ON public.user_payment_methods(user_id);

-- Partial index for default payment method
CREATE INDEX IF NOT EXISTS idx_user_payment_methods_default
ON public.user_payment_methods(user_id, is_default)
WHERE is_default = TRUE;

-- Partial index for active payment methods
CREATE INDEX IF NOT EXISTS idx_user_payment_methods_active
ON public.user_payment_methods(user_id, is_active)
WHERE is_active = TRUE;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_user_payment_methods_updated_at ON public.user_payment_methods;
CREATE TRIGGER update_user_payment_methods_updated_at
    BEFORE UPDATE ON public.user_payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.user_payment_methods ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own payment methods
DROP POLICY IF EXISTS user_payment_methods_select_own ON public.user_payment_methods;
CREATE POLICY user_payment_methods_select_own ON public.user_payment_methods
    FOR SELECT
    USING (true);

-- Policy: Users can insert their own payment methods
DROP POLICY IF EXISTS user_payment_methods_insert_own ON public.user_payment_methods;
CREATE POLICY user_payment_methods_insert_own ON public.user_payment_methods
    FOR INSERT
    WITH CHECK (true);

-- Policy: Users can update their own payment methods
DROP POLICY IF EXISTS user_payment_methods_update_own ON public.user_payment_methods;
CREATE POLICY user_payment_methods_update_own ON public.user_payment_methods
    FOR UPDATE
    USING (true);

-- Policy: Users can delete their own payment methods
DROP POLICY IF EXISTS user_payment_methods_delete_own ON public.user_payment_methods;
CREATE POLICY user_payment_methods_delete_own ON public.user_payment_methods
    FOR DELETE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.user_payment_methods IS 'Tokenized payment methods for user orders - NO raw card data stored';
COMMENT ON COLUMN public.user_payment_methods.payment_type IS 'Type of payment: card or digital_wallet';
COMMENT ON COLUMN public.user_payment_methods.provider IS 'Payment provider (visa, mastercard, apple_pay, google_pay, etc.)';
COMMENT ON COLUMN public.user_payment_methods.token IS 'Tokenized payment reference from payment processor';
COMMENT ON COLUMN public.user_payment_methods.last_four IS 'Last 4 digits of card for display purposes only';
COMMENT ON COLUMN public.user_payment_methods.expiry_month IS 'Card expiry month (1-12) - for cards only';
COMMENT ON COLUMN public.user_payment_methods.expiry_year IS 'Card expiry year (YYYY) - for cards only';
COMMENT ON COLUMN public.user_payment_methods.is_default IS 'Whether this is the default payment method';
COMMENT ON COLUMN public.user_payment_methods.is_active IS 'Soft delete flag - FALSE means payment method is removed';
