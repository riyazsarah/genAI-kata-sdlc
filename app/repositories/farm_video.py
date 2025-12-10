"""Farm video repository for database operations."""

import re
from uuid import UUID

from supabase import Client

from app.models.farmer import FarmVideoInDB, VideoPlatform


class FarmVideoRepository:
    """Repository for farm video database operations."""

    TABLE_NAME = "farm_videos"
    MAX_VIDEOS = 5

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def get_by_id(self, video_id: UUID) -> FarmVideoInDB | None:
        """Get a farm video by ID.

        Args:
            video_id: Video UUID.

        Returns:
            FarmVideoInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(video_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmVideoInDB(**response.data[0])
        return None

    def get_by_farmer_id(self, farmer_id: UUID) -> list[FarmVideoInDB]:
        """Get all videos for a farmer, ordered by display_order.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            List of FarmVideoInDB instances.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("farmer_id", str(farmer_id))
            .order("display_order")
            .execute()
        )

        return [FarmVideoInDB(**vid) for vid in response.data] if response.data else []

    def count_by_farmer_id(self, farmer_id: UUID) -> int:
        """Count videos for a farmer.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Number of videos.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("id", count="exact")
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        return response.count if response.count else 0

    def create(
        self,
        farmer_id: UUID,
        video_url: str,
        title: str | None = None,
    ) -> FarmVideoInDB:
        """Create a new farm video.

        Args:
            farmer_id: Farmer's UUID.
            video_url: YouTube or Vimeo URL.
            title: Video title.

        Returns:
            Created FarmVideoInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # Extract platform and video ID
        platform, video_id = self._extract_video_info(video_url)

        # Get next display order
        existing = self.get_by_farmer_id(farmer_id)
        next_order = len(existing)

        video_data = {
            "farmer_id": str(farmer_id),
            "video_url": video_url,
            "video_platform": platform.value,
            "video_id": video_id,
            "title": title,
            "display_order": next_order,
        }

        response = self.db.table(self.TABLE_NAME).insert(video_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create farm video")

        return FarmVideoInDB(**response.data[0])

    def update(
        self,
        video_id: UUID,
        title: str | None = None,
    ) -> FarmVideoInDB | None:
        """Update a farm video title.

        Args:
            video_id: Video UUID.
            title: Video title.

        Returns:
            Updated FarmVideoInDB if successful, None otherwise.
        """
        if title is None:
            return self.get_by_id(video_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update({"title": title})
            .eq("id", str(video_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmVideoInDB(**response.data[0])
        return None

    def delete(self, video_id: UUID) -> bool:
        """Delete a farm video.

        Args:
            video_id: Video UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .delete()
            .eq("id", str(video_id))
            .execute()
        )

        return len(response.data) > 0 if response.data else False

    def _extract_video_info(self, url: str) -> tuple[VideoPlatform, str]:
        """Extract platform and video ID from URL.

        Args:
            url: YouTube or Vimeo URL.

        Returns:
            Tuple of (VideoPlatform, video_id).

        Raises:
            ValueError: If URL format is not recognized.
        """
        # YouTube patterns
        youtube_patterns = [
            r"youtube\.com/watch\?v=([\w-]+)",
            r"youtu\.be/([\w-]+)",
            r"youtube\.com/embed/([\w-]+)",
        ]

        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return VideoPlatform.YOUTUBE, match.group(1)

        # Vimeo patterns
        vimeo_patterns = [
            r"vimeo\.com/(\d+)",
            r"player\.vimeo\.com/video/(\d+)",
        ]

        for pattern in vimeo_patterns:
            match = re.search(pattern, url)
            if match:
                return VideoPlatform.VIMEO, match.group(1)

        raise ValueError(f"Could not extract video info from URL: {url}")
