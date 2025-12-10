"""User repository for database operations."""

from datetime import datetime
from uuid import UUID

from supabase import Client

from app.models.user import UserInDB


class UserRepository:
    """Repository for user-related database operations."""

    TABLE_NAME = "users"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def get_by_email(self, email: str) -> UserInDB | None:
        """Get a user by email address.

        Args:
            email: User's email address.

        Returns:
            UserInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("email", email.lower())
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def get_by_id(self, user_id: UUID) -> UserInDB | None:
        """Get a user by ID.

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

    def get_by_verification_token(self, token: str) -> UserInDB | None:
        """Get a user by email verification token.

        Args:
            token: Email verification token.

        Returns:
            UserInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("email_verification_token", token)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        phone: str | None,
        verification_token: str,
        verification_expires_at: datetime,
    ) -> UserInDB:
        """Create a new user in the database.

        Args:
            email: User's email address.
            password_hash: Bcrypt hashed password.
            full_name: User's full name.
            phone: User's phone number (optional).
            verification_token: Email verification token.
            verification_expires_at: Token expiration datetime.

        Returns:
            Created UserInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        user_data = {
            "email": email.lower(),
            "password_hash": password_hash,
            "full_name": full_name,
            "phone": phone,
            "email_verified": False,
            "email_verification_token": verification_token,
            "email_verification_expires_at": verification_expires_at.isoformat(),
        }

        response = self.db.table(self.TABLE_NAME).insert(user_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create user")

        return UserInDB(**response.data[0])

    def verify_email(self, user_id: UUID) -> UserInDB | None:
        """Mark a user's email as verified.

        Args:
            user_id: User's UUID.

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update(
                {
                    "email_verified": True,
                    "email_verification_token": None,
                    "email_verification_expires_at": None,
                }
            )
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def email_exists(self, email: str) -> bool:
        """Check if an email already exists in the database.

        Args:
            email: Email address to check.

        Returns:
            True if email exists, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("id")
            .eq("email", email.lower())
            .execute()
        )
        return len(response.data) > 0
