"""Address repository for database operations."""

from typing import Any
from uuid import UUID

from supabase import Client

from app.models.profile import AddressCreate, AddressInDB, AddressUpdate


class AddressRepository:
    """Repository for address-related database operations."""

    TABLE_NAME = "user_addresses"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def create(self, user_id: UUID, data: AddressCreate) -> AddressInDB:
        """Create a new address for a user.

        Args:
            user_id: User's UUID.
            data: Address creation data.

        Returns:
            Created AddressInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # If this address is set as default, unset other defaults first
        if data.is_default:
            self._unset_default_addresses(user_id)

        address_data = {
            "user_id": str(user_id),
            "label": data.label,
            "street": data.street,
            "city": data.city,
            "state": data.state,
            "zip_code": data.zip_code,
            "delivery_instructions": data.delivery_instructions,
            "is_default": data.is_default,
            "is_active": True,
        }

        response = self.db.table(self.TABLE_NAME).insert(address_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create address")

        return AddressInDB(**response.data[0])

    def get_by_id(self, address_id: UUID, user_id: UUID) -> AddressInDB | None:
        """Get an address by ID for a specific user.

        Args:
            address_id: Address UUID.
            user_id: User's UUID (for ownership verification).

        Returns:
            AddressInDB if found and owned by user, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return AddressInDB(**response.data[0])
        return None

    def get_all_for_user(self, user_id: UUID) -> list[AddressInDB]:
        """Get all active addresses for a user.

        Args:
            user_id: User's UUID.

        Returns:
            List of AddressInDB instances.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .order("is_default", desc=True)
            .order("created_at", desc=True)
            .execute()
        )

        return [AddressInDB(**row) for row in response.data]

    def update(
        self, address_id: UUID, user_id: UUID, data: AddressUpdate
    ) -> AddressInDB | None:
        """Update an address.

        Args:
            address_id: Address UUID.
            user_id: User's UUID (for ownership verification).
            data: Address update data.

        Returns:
            Updated AddressInDB if successful, None otherwise.
        """
        # Verify ownership first
        existing = self.get_by_id(address_id, user_id)
        if not existing:
            return None

        # If setting as default, unset other defaults first
        if data.is_default is True:
            self._unset_default_addresses(user_id)

        update_data: dict[str, Any] = {}

        if data.label is not None:
            update_data["label"] = data.label
        if data.street is not None:
            update_data["street"] = data.street
        if data.city is not None:
            update_data["city"] = data.city
        if data.state is not None:
            update_data["state"] = data.state
        if data.zip_code is not None:
            update_data["zip_code"] = data.zip_code
        if data.delivery_instructions is not None:
            update_data["delivery_instructions"] = data.delivery_instructions
        if data.is_default is not None:
            update_data["is_default"] = data.is_default

        if not update_data:
            return existing

        response = (
            self.db.table(self.TABLE_NAME)
            .update(update_data)
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return AddressInDB(**response.data[0])
        return None

    def delete(self, address_id: UUID, user_id: UUID) -> bool:
        """Soft delete an address.

        Args:
            address_id: Address UUID.
            user_id: User's UUID (for ownership verification).

        Returns:
            True if deleted, False if not found or not owned.
        """
        # Verify ownership first
        existing = self.get_by_id(address_id, user_id)
        if not existing:
            return False

        response = (
            self.db.table(self.TABLE_NAME)
            .update({"is_active": False})
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        return len(response.data) > 0

    def set_default(self, address_id: UUID, user_id: UUID) -> AddressInDB | None:
        """Set an address as the default for a user.

        Args:
            address_id: Address UUID.
            user_id: User's UUID.

        Returns:
            Updated AddressInDB if successful, None otherwise.
        """
        # Verify ownership first
        existing = self.get_by_id(address_id, user_id)
        if not existing:
            return None

        # Unset all other defaults
        self._unset_default_addresses(user_id)

        # Set new default
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"is_default": True})
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return AddressInDB(**response.data[0])
        return None

    def _unset_default_addresses(self, user_id: UUID) -> None:
        """Unset all default addresses for a user.

        Args:
            user_id: User's UUID.
        """
        self.db.table(self.TABLE_NAME).update({"is_default": False}).eq(
            "user_id", str(user_id)
        ).eq("is_default", True).execute()
