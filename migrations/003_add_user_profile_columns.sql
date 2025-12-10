-- Migration: 003_add_user_profile_columns
-- Description: Add profile management columns to users table
-- User Story: US-003 (User Profile Management)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- PROFILE COLUMNS
-- Supports: AC-003-2 (update basic information), AC-003-3 (profile picture)
-- ============================================================================

-- Add date of birth column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'date_of_birth'
    ) THEN
        ALTER TABLE public.users ADD COLUMN date_of_birth DATE;
    END IF;
END $$;

-- Add profile picture URL column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'profile_picture_url'
    ) THEN
        ALTER TABLE public.users ADD COLUMN profile_picture_url VARCHAR(500);
    END IF;
END $$;

-- ============================================================================
-- DIETARY PREFERENCES
-- Supports: AC-003-6 (set dietary preferences)
-- Values: Vegetarian, Vegan, Gluten-Free, Dairy-Free, Nut-Free, Organic, Keto, Paleo
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'dietary_preferences'
    ) THEN
        ALTER TABLE public.users ADD COLUMN dietary_preferences TEXT[] NOT NULL DEFAULT '{}';
    END IF;
END $$;

-- ============================================================================
-- COMMUNICATION PREFERENCES
-- Supports: AC-003-7 (set communication preferences)
-- Structure: {"email": true, "sms": false, "push": false}
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'communication_preferences'
    ) THEN
        ALTER TABLE public.users ADD COLUMN communication_preferences JSONB NOT NULL DEFAULT '{"email": true, "sms": false, "push": false}';
    END IF;
END $$;

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN public.users.date_of_birth IS 'User date of birth for age verification and personalization';
COMMENT ON COLUMN public.users.profile_picture_url IS 'URL to user profile picture stored in Supabase Storage';
COMMENT ON COLUMN public.users.dietary_preferences IS 'Array of dietary preference tags (Vegetarian, Vegan, Gluten-Free, etc.)';
COMMENT ON COLUMN public.users.communication_preferences IS 'JSONB object with email, sms, push notification preferences';
