"""Farmer repository for database operations."""

from typing import Any
from uuid import UUID

from supabase import Client

from app.models.farmer import FarmerInDB


class FarmerRepository:
    """Repository for farmer-related database operations."""

    TABLE_NAME = "farmers"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def get_by_id(self, farmer_id: UUID) -> FarmerInDB | None:
        """Get a farmer by ID.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            FarmerInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmerInDB(**response.data[0])
        return None

    def get_by_user_id(self, user_id: UUID) -> FarmerInDB | None:
        """Get a farmer by user ID.

        Args:
            user_id: User's UUID (from users table).

        Returns:
            FarmerInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmerInDB(**response.data[0])
        return None

    def create(self, user_id: UUID, farm_name: str) -> FarmerInDB:
        """Create a new farmer profile.

        Args:
            user_id: User's UUID.
            farm_name: Name of the farm.

        Returns:
            Created FarmerInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        farmer_data = {
            "user_id": str(user_id),
            "farm_name": farm_name,
            "farming_practices": [],
            "profile_completed": False,
            "profile_completion_step": 0,
        }

        response = self.db.table(self.TABLE_NAME).insert(farmer_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create farmer profile")

        return FarmerInDB(**response.data[0])

    def update_farm_details(
        self,
        farmer_id: UUID,
        farm_name: str | None = None,
        farm_description: str | None = None,
        farm_street: str | None = None,
        farm_city: str | None = None,
        farm_state: str | None = None,
        farm_zip_code: str | None = None,
        farming_practices: list[str] | None = None,
    ) -> FarmerInDB | None:
        """Update farm details.

        Args:
            farmer_id: Farmer's UUID.
            farm_name: Name of the farm.
            farm_description: Description of the farm.
            farm_street: Farm street address.
            farm_city: Farm city.
            farm_state: Farm state.
            farm_zip_code: Farm ZIP code.
            farming_practices: List of farming practices.

        Returns:
            Updated FarmerInDB if successful, None otherwise.
        """
        data: dict[str, Any] = {}

        if farm_name is not None:
            data["farm_name"] = farm_name
        if farm_description is not None:
            data["farm_description"] = farm_description
        if farm_street is not None:
            data["farm_street"] = farm_street
        if farm_city is not None:
            data["farm_city"] = farm_city
        if farm_state is not None:
            data["farm_state"] = farm_state
        if farm_zip_code is not None:
            data["farm_zip_code"] = farm_zip_code
        if farming_practices is not None:
            data["farming_practices"] = farming_practices

        if not data:
            return self.get_by_id(farmer_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(data)
            .eq("id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmerInDB(**response.data[0])
        return None

    def update_profile_completion(
        self,
        farmer_id: UUID,
        step: int,
        completed: bool = False,
    ) -> FarmerInDB | None:
        """Update profile completion status.

        Args:
            farmer_id: Farmer's UUID.
            step: Current profile completion step.
            completed: Whether profile is fully completed.

        Returns:
            Updated FarmerInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update(
                {
                    "profile_completion_step": step,
                    "profile_completed": completed,
                }
            )
            .eq("id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FarmerInDB(**response.data[0])
        return None

    def delete(self, farmer_id: UUID) -> bool:
        """Delete a farmer profile.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .delete()
            .eq("id", str(farmer_id))
            .execute()
        )

        return len(response.data) > 0 if response.data else False
