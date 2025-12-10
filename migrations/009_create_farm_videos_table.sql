-- Migration: 009_create_farm_videos_table
-- Description: Create farm_videos table for YouTube/Vimeo URLs
-- User Story: US-005 (Farmer Profile Setup)
-- Created: 2025-12-10
-- Note: This script is idempotent and safe to run multiple times

-- ============================================================================
-- FARM VIDEOS TABLE
-- Stores farm video URLs (YouTube/Vimeo)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.farm_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL REFERENCES public.farmers(id) ON DELETE CASCADE,
    video_url VARCHAR(500) NOT NULL,
    video_platform VARCHAR(20) NOT NULL,
    video_id VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: Only valid video platforms
    CONSTRAINT valid_video_platform CHECK (video_platform IN ('youtube', 'vimeo'))
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for farmer lookups
CREATE INDEX IF NOT EXISTS idx_farm_videos_farmer_id ON public.farm_videos(farmer_id);

-- Index for ordering
CREATE INDEX IF NOT EXISTS idx_farm_videos_order ON public.farm_videos(farmer_id, display_order);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.farm_videos ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations (controlled at application level)
DROP POLICY IF EXISTS farm_videos_select ON public.farm_videos;
CREATE POLICY farm_videos_select ON public.farm_videos
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS farm_videos_insert ON public.farm_videos;
CREATE POLICY farm_videos_insert ON public.farm_videos
    FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS farm_videos_update ON public.farm_videos;
CREATE POLICY farm_videos_update ON public.farm_videos
    FOR UPDATE
    USING (true);

DROP POLICY IF EXISTS farm_videos_delete ON public.farm_videos;
CREATE POLICY farm_videos_delete ON public.farm_videos
    FOR DELETE
    USING (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE public.farm_videos IS 'Farm video URLs from YouTube or Vimeo (max 5 per farm)';
COMMENT ON COLUMN public.farm_videos.farmer_id IS 'Reference to farmers table';
COMMENT ON COLUMN public.farm_videos.video_url IS 'Full URL to the video';
COMMENT ON COLUMN public.farm_videos.video_platform IS 'Platform: youtube or vimeo';
COMMENT ON COLUMN public.farm_videos.video_id IS 'Extracted video ID for embedding';
COMMENT ON COLUMN public.farm_videos.title IS 'Optional title for the video';
COMMENT ON COLUMN public.farm_videos.display_order IS 'Order for displaying videos';
