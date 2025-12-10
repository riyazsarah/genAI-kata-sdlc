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
        # Validate token is a valid UUID format before querying
        try:
            UUID(token)
        except (ValueError, TypeError):
            return None

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
        role: str = "consumer",
        date_of_birth: datetime | None = None,
    ) -> UserInDB:
        """Create a new user in the database.

        Args:
            email: User's email address.
            password_hash: Bcrypt hashed password.
            full_name: User's full name.
            phone: User's phone number (optional).
            verification_token: Email verification token.
            verification_expires_at: Token expiration datetime.
            role: User role (consumer or farmer).
            date_of_birth: User's date of birth (required for farmers).

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
            "role": role,
        }

        if date_of_birth is not None:
            user_data["date_of_birth"] = date_of_birth.isoformat()

        response = self.db.table(self.TABLE_NAME).insert(user_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create user")

        return UserInDB(**response.data[0])

    def update_role(self, user_id: UUID, role: str) -> UserInDB | None:
        """Update user's role.

        Args:
            user_id: User's UUID.
            role: New role (consumer or farmer).

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"role": role})
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

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

    def update_login_stats(
        self,
        user_id: UUID,
        failed_attempts: int,
        locked_until: datetime | None = None,
    ) -> None:
        """Update user login statistics (failed attempts and lockout).

        Args:
            user_id: User's UUID.
            failed_attempts: New count of failed attempts.
            locked_until: Timestamp until which account is locked (optional).
        """
        data = {
            "failed_login_attempts": failed_attempts,
            "locked_until": locked_until.isoformat() if locked_until else None,
        }
        self.db.table(self.TABLE_NAME).update(data).eq("id", str(user_id)).execute()

    def reset_login_attempts(self, user_id: UUID) -> None:
        """Reset failed login attempts after successful login.

        Args:
            user_id: User's UUID.
        """
        self.db.table(self.TABLE_NAME).update(
            {"failed_login_attempts": 0, "locked_until": None}
        ).eq("id", str(user_id)).execute()

    def get_by_password_reset_token(self, token: str) -> UserInDB | None:
        """Get a user by password reset token.

        Args:
            token: Password reset token.

        Returns:
            UserInDB if found, None otherwise.
        """
        try:
            UUID(token)
        except (ValueError, TypeError):
            return None

        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("password_reset_token", token)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None

    def set_password_reset_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> None:
        """Set password reset token for a user.

        Args:
            user_id: User's UUID.
            token: Password reset token.
            expires_at: Token expiration datetime.
        """
        self.db.table(self.TABLE_NAME).update(
            {
                "password_reset_token": token,
                "password_reset_expires_at": expires_at.isoformat(),
            }
        ).eq("id", str(user_id)).execute()

    def update_password(self, user_id: UUID, password_hash: str) -> UserInDB | None:
        """Update user's password and clear reset token.

        Args:
            user_id: User's UUID.
            password_hash: New bcrypt hashed password.

        Returns:
            Updated UserInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update(
                {
                    "password_hash": password_hash,
                    "password_reset_token": None,
                    "password_reset_expires_at": None,
                    "failed_login_attempts": 0,
                    "locked_until": None,
                }
            )
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return UserInDB(**response.data[0])
        return None
