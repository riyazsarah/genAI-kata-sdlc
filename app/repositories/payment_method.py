"""Payment method repository for database operations."""

from uuid import UUID

from supabase import Client

from app.models.profile import PaymentMethodInDB


class PaymentMethodRepository:
    """Repository for payment method database operations."""

    TABLE_NAME = "user_payment_methods"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def create(
        self,
        user_id: UUID,
        payment_type: str,
        provider: str,
        token: str,
        last_four: str | None = None,
        expiry_month: int | None = None,
        expiry_year: int | None = None,
        is_default: bool = False,
    ) -> PaymentMethodInDB:
        """Create a new payment method for a user.

        Args:
            user_id: User's UUID.
            payment_type: Type of payment (card, digital_wallet).
            provider: Payment provider (visa, mastercard, etc.).
            token: Tokenized payment reference.
            last_four: Last 4 digits of card (optional).
            expiry_month: Card expiry month (optional).
            expiry_year: Card expiry year (optional).
            is_default: Whether this is the default payment method.

        Returns:
            Created PaymentMethodInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # If this payment method is set as default, unset other defaults first
        if is_default:
            self._unset_default_payment_methods(user_id)

        payment_data = {
            "user_id": str(user_id),
            "payment_type": payment_type,
            "provider": provider,
            "token": token,
            "last_four": last_four,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "is_default": is_default,
            "is_active": True,
        }

        response = self.db.table(self.TABLE_NAME).insert(payment_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create payment method")

        return PaymentMethodInDB(**response.data[0])

    def get_by_id(
        self, payment_id: UUID, user_id: UUID
    ) -> PaymentMethodInDB | None:
        """Get a payment method by ID for a specific user.

        Args:
            payment_id: Payment method UUID.
            user_id: User's UUID (for ownership verification).

        Returns:
            PaymentMethodInDB if found and owned by user, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(payment_id))
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return PaymentMethodInDB(**response.data[0])
        return None

    def get_all_for_user(self, user_id: UUID) -> list[PaymentMethodInDB]:
        """Get all active payment methods for a user.

        Args:
            user_id: User's UUID.

        Returns:
            List of PaymentMethodInDB instances.
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

        return [PaymentMethodInDB(**row) for row in response.data]

    def delete(self, payment_id: UUID, user_id: UUID) -> bool:
        """Soft delete a payment method.

        Args:
            payment_id: Payment method UUID.
            user_id: User's UUID (for ownership verification).

        Returns:
            True if deleted, False if not found or not owned.
        """
        # Verify ownership first
        existing = self.get_by_id(payment_id, user_id)
        if not existing:
            return False

        response = (
            self.db.table(self.TABLE_NAME)
            .update({"is_active": False})
            .eq("id", str(payment_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        return len(response.data) > 0

    def set_default(
        self, payment_id: UUID, user_id: UUID
    ) -> PaymentMethodInDB | None:
        """Set a payment method as the default for a user.

        Args:
            payment_id: Payment method UUID.
            user_id: User's UUID.

        Returns:
            Updated PaymentMethodInDB if successful, None otherwise.
        """
        # Verify ownership first
        existing = self.get_by_id(payment_id, user_id)
        if not existing:
            return None

        # Unset all other defaults
        self._unset_default_payment_methods(user_id)

        # Set new default
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"is_default": True})
            .eq("id", str(payment_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return PaymentMethodInDB(**response.data[0])
        return None

    def _unset_default_payment_methods(self, user_id: UUID) -> None:
        """Unset all default payment methods for a user.

        Args:
            user_id: User's UUID.
        """
        self.db.table(self.TABLE_NAME).update({"is_default": False}).eq(
            "user_id", str(user_id)
        ).eq("is_default", True).execute()
