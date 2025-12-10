-- Migration: 001_create_users_table
-- Description: Create users table for custom authentication
-- Created: 2025-12-10

-- Create users table for custom authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token UUID,
    email_verification_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create index on verification token for email verification
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(email_verification_token);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Allow reads for authentication purposes
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (true);

-- Policy: Allow inserts for registration
CREATE POLICY users_insert ON users
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow updates for email verification and profile updates
CREATE POLICY users_update ON users
    FOR UPDATE
    USING (true);

COMMENT ON TABLE users IS 'User accounts for Farm-to-Table Marketplace';
COMMENT ON COLUMN users.email_verification_token IS 'Token sent via email for verification, expires after 24 hours';
