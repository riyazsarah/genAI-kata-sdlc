"""Farmer bank account repository for database operations."""

from uuid import UUID

from supabase import Client

from app.core.encryption import decrypt_data, encrypt_data
from app.models.farmer import BankAccountInDB


class FarmerBankAccountRepository:
    """Repository for farmer bank account database operations."""

    TABLE_NAME = "farmer_bank_accounts"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def get_by_id(self, account_id: UUID) -> BankAccountInDB | None:
        """Get a bank account by ID.

        Args:
            account_id: Bank account UUID.

        Returns:
            BankAccountInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(account_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return BankAccountInDB(**response.data[0])
        return None

    def get_by_farmer_id(self, farmer_id: UUID) -> BankAccountInDB | None:
        """Get a bank account by farmer ID.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            BankAccountInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return BankAccountInDB(**response.data[0])
        return None

    def create(
        self,
        farmer_id: UUID,
        account_holder_name: str,
        account_number: str,
        routing_number: str,
        bank_name: str | None = None,
        account_type: str = "checking",
    ) -> BankAccountInDB:
        """Create a new bank account with encrypted sensitive data.

        Args:
            farmer_id: Farmer's UUID.
            account_holder_name: Name on the account.
            account_number: Bank account number (will be encrypted).
            routing_number: Bank routing number (will be encrypted).
            bank_name: Name of the bank.
            account_type: Type of account (checking/savings).

        Returns:
            Created BankAccountInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # Encrypt sensitive data
        account_number_encrypted = encrypt_data(account_number)
        routing_number_encrypted = encrypt_data(routing_number)

        # Extract last 4 digits for display
        account_last_four = account_number[-4:]

        account_data = {
            "farmer_id": str(farmer_id),
            "account_holder_name": account_holder_name,
            "account_number_encrypted": account_number_encrypted,
            "routing_number_encrypted": routing_number_encrypted,
            "account_last_four": account_last_four,
            "bank_name": bank_name,
            "account_type": account_type,
            "is_verified": False,
        }

        response = self.db.table(self.TABLE_NAME).insert(account_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create bank account")

        return BankAccountInDB(**response.data[0])

    def update(
        self,
        farmer_id: UUID,
        account_holder_name: str | None = None,
        account_number: str | None = None,
        routing_number: str | None = None,
        bank_name: str | None = None,
        account_type: str | None = None,
    ) -> BankAccountInDB | None:
        """Update a bank account.

        Args:
            farmer_id: Farmer's UUID.
            account_holder_name: Name on the account.
            account_number: Bank account number (will be encrypted).
            routing_number: Bank routing number (will be encrypted).
            bank_name: Name of the bank.
            account_type: Type of account.

        Returns:
            Updated BankAccountInDB if successful, None otherwise.
        """
        data: dict = {}

        if account_holder_name is not None:
            data["account_holder_name"] = account_holder_name
        if account_number is not None:
            data["account_number_encrypted"] = encrypt_data(account_number)
            data["account_last_four"] = account_number[-4:]
        if routing_number is not None:
            data["routing_number_encrypted"] = encrypt_data(routing_number)
        if bank_name is not None:
            data["bank_name"] = bank_name
        if account_type is not None:
            data["account_type"] = account_type

        # Reset verification when account details change
        if account_number or routing_number:
            data["is_verified"] = False

        if not data:
            return self.get_by_farmer_id(farmer_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(data)
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return BankAccountInDB(**response.data[0])
        return None

    def delete(self, farmer_id: UUID) -> bool:
        """Delete a bank account.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .delete()
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        return len(response.data) > 0 if response.data else False

    def get_decrypted_account_number(self, farmer_id: UUID) -> str | None:
        """Get decrypted account number for payout processing.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Decrypted account number if found, None otherwise.
        """
        account = self.get_by_farmer_id(farmer_id)
        if not account:
            return None

        return decrypt_data(account.account_number_encrypted)

    def get_decrypted_routing_number(self, farmer_id: UUID) -> str | None:
        """Get decrypted routing number for payout processing.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Decrypted routing number if found, None otherwise.
        """
        account = self.get_by_farmer_id(farmer_id)
        if not account:
            return None

        return decrypt_data(account.routing_number_encrypted)

    def mark_verified(self, farmer_id: UUID) -> BankAccountInDB | None:
        """Mark a bank account as verified.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Updated BankAccountInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"is_verified": True})
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return BankAccountInDB(**response.data[0])
        return None
