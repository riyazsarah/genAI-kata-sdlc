-- Migration: 008_create_farm_images_table
-- Description: Create farm_images table for farm gallery
-- User Story: US-005 (Farmer Profile Setup)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- FARM IMAGES TABLE
-- Stores farm gallery images with metadata
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farm_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL REFERENCES public.farmers(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    caption VARCHAR(200),
    alt_text VARCHAR(200),
    display_order INTEGER NOT NULL DEFAULT 0,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for farmer lookups
CREATE INDEX IF NOT EXISTS idx_farm_images_farmer_id ON public.farm_images(farmer_id);

-- Index for ordering
CREATE INDEX IF NOT EXISTS idx_farm_images_order ON public.farm_images(farmer_id, display_order);

-- Partial index for primary image lookup
CREATE INDEX IF NOT EXISTS idx_farm_images_primary ON public.farm_images(farmer_id, is_primary)
WHERE is_primary = TRUE;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.farm_images ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations (controlled at application level)
DROP POLICY IF EXISTS farm_images_select ON public.farm_images;
CREATE POLICY farm_images_select ON public.farm_images
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS farm_images_insert ON public.farm_images;
CREATE POLICY farm_images_insert ON public.farm_images
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS farm_images_update ON public.farm_images;
CREATE POLICY farm_images_update ON public.farm_images
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS farm_images_delete ON public.farm_images;
CREATE POLICY farm_images_delete ON public.farm_images
    FOR DELETE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.farm_images IS 'Farm gallery images (max 10 per farm, enforced at application level)';
COMMENT ON COLUMN public.farm_images.farmer_id IS 'Reference to farmers table';
COMMENT ON COLUMN public.farm_images.image_url IS 'URL to image in Supabase Storage';
COMMENT ON COLUMN public.farm_images.caption IS 'Optional caption for the image';
COMMENT ON COLUMN public.farm_images.alt_text IS 'Alt text for accessibility';
COMMENT ON COLUMN public.farm_images.display_order IS 'Order for displaying images in gallery';
COMMENT ON COLUMN public.farm_images.is_primary IS 'Whether this is the primary/featured farm image';
