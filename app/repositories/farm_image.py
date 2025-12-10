"""Farm image repository for database operations."""

from uuid import UUID

from supabase import Client

from app.models.farmer import FarmImageInDB


class FarmImageRepository:
    """Repository for farm image database operations."""

    TABLE_NAME = "farm_images"
    MAX_IMAGES = 10

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def get_by_id(self, image_id: UUID) -> FarmImageInDB | None:
        """Get a farm image by ID.

        Args:
            image_id: Image UUID.

        Returns:
            FarmImageInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(image_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmImageInDB(**response.data[0])
        return None

    def get_by_farmer_id(self, farmer_id: UUID) -> list[FarmImageInDB]:
        """Get all images for a farmer, ordered by display_order.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            List of FarmImageInDB instances.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("farmer_id", str(farmer_id))
            .order("display_order")
            .execute()
        )

        return [FarmImageInDB(**img) for img in response.data] if response.data else []

    def count_by_farmer_id(self, farmer_id: UUID) -> int:
        """Count images for a farmer.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Number of images.
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
        image_url: str,
        caption: str | None = None,
        alt_text: str | None = None,
        is_primary: bool = False,
    ) -> FarmImageInDB:
        """Create a new farm image.

        Args:
            farmer_id: Farmer's UUID.
            image_url: URL to the image.
            caption: Image caption.
            alt_text: Alt text for accessibility.
            is_primary: Whether this is the primary image.

        Returns:
            Created FarmImageInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # Get next display order
        existing = self.get_by_farmer_id(farmer_id)
        next_order = len(existing)

        # If this is primary, unset other primaries
        if is_primary and existing:
            self._unset_all_primary(farmer_id)

        image_data = {
            "farmer_id": str(farmer_id),
            "image_url": image_url,
            "caption": caption,
            "alt_text": alt_text,
            "display_order": next_order,
            "is_primary": is_primary or next_order == 0,  # First image is primary
        }

        response = self.db.table(self.TABLE_NAME).insert(image_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create farm image")

        return FarmImageInDB(**response.data[0])

    def update(
        self,
        image_id: UUID,
        caption: str | None = None,
        alt_text: str | None = None,
        is_primary: bool | None = None,
    ) -> FarmImageInDB | None:
        """Update a farm image.

        Args:
            image_id: Image UUID.
            caption: Image caption.
            alt_text: Alt text for accessibility.
            is_primary: Whether this is the primary image.

        Returns:
            Updated FarmImageInDB if successful, None otherwise.
        """
        data: dict = {}

        if caption is not None:
            data["caption"] = caption
        if alt_text is not None:
            data["alt_text"] = alt_text
        if is_primary is not None:
            data["is_primary"] = is_primary
            if is_primary:
                # Get the image to find farmer_id
                image = self.get_by_id(image_id)
                if image:
                    self._unset_all_primary(image.farmer_id)

        if not data:
            return self.get_by_id(image_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(data)
            .eq("id", str(image_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmImageInDB(**response.data[0])
        return None

    def update_order(self, farmer_id: UUID, image_ids: list[UUID]) -> bool:
        """Update display order for multiple images.

        Args:
            farmer_id: Farmer's UUID.
            image_ids: List of image IDs in desired order.

        Returns:
            True if successful.
        """
        for order, image_id in enumerate(image_ids):
            self.db.table(self.TABLE_NAME).update({"display_order": order}).eq(
                "id", str(image_id)
            ).eq("farmer_id", str(farmer_id)).execute()

        return True

    def delete(self, image_id: UUID) -> bool:
        """Delete a farm image.

        Args:
            image_id: Image UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .delete()
            .eq("id", str(image_id))
            .execute()
        )

        return len(response.data) > 0 if response.data else False

    def _unset_all_primary(self, farmer_id: UUID) -> None:
        """Unset all primary flags for a farmer's images.

        Args:
            farmer_id: Farmer's UUID.
        """
        self.db.table(self.TABLE_NAME).update({"is_primary": False}).eq(
            "farmer_id", str(farmer_id)
        ).execute()
