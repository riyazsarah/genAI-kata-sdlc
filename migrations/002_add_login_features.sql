-- Migration: 002_add_login_features
-- Description: Add login tracking, account lockout, and password reset columns to users table
-- User Story: US-002 (User Login)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- LOGIN TRACKING & ACCOUNT LOCKOUT COLUMNS
-- Supports: AC-002-5 (account lockout after 5 failed attempts)
-- ============================================================================

-- Add failed login attempts counter
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'failed_login_attempts'
    ) THEN
        ALTER TABLE public.users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Add account lockout timestamp
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'locked_until'
    ) THEN
        ALTER TABLE public.users ADD COLUMN locked_until TIMESTAMPTZ;
    END IF;
END $$;

-- ============================================================================
-- PASSWORD RESET COLUMNS
-- Supports: AC-002-5 (password reset flow)
-- ============================================================================

-- Add password reset token
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'password_reset_token'
    ) THEN
        ALTER TABLE public.users ADD COLUMN password_reset_token UUID;
    END IF;
END $$;

-- Add password reset expiration
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'password_reset_expires_at'
    ) THEN
        ALTER TABLE public.users ADD COLUMN password_reset_expires_at TIMESTAMPTZ;
    END IF;
END $$;

-- ============================================================================
-- LAST LOGIN TRACKING
-- Supports: AC-002-6 (session management)
-- ============================================================================

-- Add last login timestamp for session tracking
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE public.users ADD COLUMN last_login_at TIMESTAMPTZ;
    END IF;
END $$;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for password reset token lookups (partial index for non-null values)
CREATE INDEX IF NOT EXISTS idx_users_password_reset_token
ON public.users (password_reset_token)
WHERE password_reset_token IS NOT NULL;

-- Index for finding locked accounts (partial index for non-null values)
CREATE INDEX IF NOT EXISTS idx_users_locked_until
ON public.users (locked_until)
WHERE locked_until IS NOT NULL;

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN public.users.failed_login_attempts IS 'Number of consecutive failed login attempts. Resets to 0 on successful login.';
COMMENT ON COLUMN public.users.locked_until IS 'Account is locked until this timestamp after exceeding max failed login attempts (5).';
COMMENT ON COLUMN public.users.password_reset_token IS 'UUID token for password reset, sent via email. Single use.';
COMMENT ON COLUMN public.users.password_reset_expires_at IS 'Password reset token expiration (typically 1 hour from request).';
COMMENT ON COLUMN public.users.last_login_at IS 'Timestamp of the user last successful login.';
