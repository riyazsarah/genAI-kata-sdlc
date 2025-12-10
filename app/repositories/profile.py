"""Profile repository for user profile database operations."""

from datetime import date
from typing import Any
from uuid import UUID

from supabase import Client

from app.models.user import UserInDB


class ProfileRepository:
    """Repository for profile-related database operations."""

    TABLE_NAME = "users"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def update_profile(
        self,
        user_id: UUID,
        full_name: str | None = None,
        phone: str | None = None,
        date_of_birth: date | None = None,
    ) -> UserInDB | None:
        """Update user profile basic information.

        Args:
            user_id: User's UUID.
            full_name: User's full name (optional).
            phone: User's phone number (optional).
            date_of_birth: User's date of birth (optional).

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        data: dict[str, Any] = {}

        if full_name is not None:
            data["full_name"] = full_name
        if phone is not None:
            data["phone"] = phone
        if date_of_birth is not None:
            data["date_of_birth"] = date_of_birth.isoformat()

        if not data:
            # No updates provided, return current user
            return self._get_user_by_id(user_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(data)
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def update_avatar_url(self, user_id: UUID, url: str) -> UserInDB | None:
        """Update user's profile picture URL.

        Args:
            user_id: User's UUID.
            url: URL of the uploaded profile picture.

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"profile_picture_url": url})
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def update_dietary_preferences(
        self, user_id: UUID, preferences: list[str]
    ) -> UserInDB | None:
        """Update user's dietary preferences.

        Args:
            user_id: User's UUID.
            preferences: List of dietary preference strings.

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"dietary_preferences": preferences})
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def update_communication_preferences(
        self, user_id: UUID, preferences: dict[str, bool]
    ) -> UserInDB | None:
        """Update user's communication preferences.

        Args:
            user_id: User's UUID.
            preferences: Dict with email, sms, push boolean values.

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"communication_preferences": preferences})
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def update_preferences(
        self,
        user_id: UUID,
        dietary_preferences: list[str] | None = None,
        communication_preferences: dict[str, bool] | None = None,
    ) -> UserInDB | None:
        """Update user's preferences (dietary and/or communication).

        Args:
            user_id: User's UUID.
            dietary_preferences: List of dietary preference strings (optional).
            communication_preferences: Dict with notification settings (optional).

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        data: dict[str, Any] = {}

        if dietary_preferences is not None:
            data["dietary_preferences"] = dietary_preferences
        if communication_preferences is not None:
            data["communication_preferences"] = communication_preferences

        if not data:
            return self._get_user_by_id(user_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(data)
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def _get_user_by_id(self, user_id: UUID) -> UserInDB | None:
        """Get a user by ID (internal helper).

        Args:
            user_id: User's UUID.

        Returns:
            UserInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None
