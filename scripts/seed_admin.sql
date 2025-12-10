-- ============================================================================
-- Create Admin User for Farm-to-Table Marketplace
-- Run this in Supabase SQL Editor
-- ============================================================================

-- First, add 'admin' to role if not exists (update enum or just allow it)
-- Note: Since role is likely VARCHAR, no enum update needed

-- Create admin user
INSERT INTO users (
    id, email, password_hash, full_name, phone,
    email_verified, role, failed_login_attempts, locked_until,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'admin@farmtotable.com',
    '$2b$12$WkdpLNzVI1DD1.qQ1CWa3er3OuT0Jqh.ETfL3AOrvRlc51VEaMi3m', -- TestPassword123!
    'Platform Admin',
    '+1000000000',
    TRUE,
    'admin',
    0,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    email_verified = TRUE,
    role = 'admin',
    failed_login_attempts = 0,
    locked_until = NULL;

-- Verify admin was created
SELECT id, email, full_name, role, email_verified
FROM users
WHERE email = 'admin@farmtotable.com';

-- ============================================================================
-- Also ensure test farmer exists with correct credentials
-- ============================================================================
INSERT INTO users (
    id, email, password_hash, full_name, phone,
    email_verified, role, failed_login_attempts, locked_until,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'testfarmer@example.com',
    '$2b$12$WkdpLNzVI1DD1.qQ1CWa3er3OuT0Jqh.ETfL3AOrvRlc51VEaMi3m', -- TestPassword123!
    'Green Valley Farm',
    '+1234567890',
    TRUE,
    'farmer',
    0,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    email_verified = TRUE,
    role = 'farmer',
    failed_login_attempts = 0,
    locked_until = NULL;

-- Show all test users
SELECT id, email, full_name, role, email_verified
FROM users
WHERE email IN ('admin@farmtotable.com', 'testfarmer@example.com');
