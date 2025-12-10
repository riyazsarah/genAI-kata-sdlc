"""Authentication service for user registration and verification."""

from dataclasses import dataclass

from app.core.security import (
    generate_verification_token,
    get_verification_expiry,
    hash_password,
    is_token_expired,
)
from app.models.user import UserCreate, UserInDB, UserResponse
from app.repositories.user import UserRepository
from app.services.email import EmailServiceBase


@dataclass
class RegistrationResult:
    """Result of a registration attempt."""

    success: bool
    user: UserResponse | None = None
    error: str | None = None


@dataclass
class VerificationResult:
    """Result of an email verification attempt."""

    success: bool
    message: str


class AuthService:
    """Service for authentication-related operations."""

    def __init__(
        self, user_repository: UserRepository, email_service: EmailServiceBase
    ) -> None:
        """Initialize the auth service.

        Args:
            user_repository: Repository for user database operations.
            email_service: Service for sending emails.
        """
        self.user_repo = user_repository
        self.email_service = email_service

    def register_user(self, user_data: UserCreate) -> RegistrationResult:
        """Register a new user.

        Args:
            user_data: User registration data.

        Returns:
            RegistrationResult with success status and user or error.
        """
        # Check if email already exists
        if self.user_repo.email_exists(user_data.email):
            return RegistrationResult(
                success=False,
                error="An account with this email already exists",
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Generate verification token
        verification_token = generate_verification_token()
        verification_expires = get_verification_expiry(hours=24)

        # Create user in database
        try:
            user = self.user_repo.create(
                email=user_data.email,
                password_hash=password_hash,
                full_name=user_data.full_name,
                phone=user_data.phone,
                verification_token=verification_token,
                verification_expires_at=verification_expires,
            )
        except Exception as e:
            return RegistrationResult(
                success=False,
                error=f"Failed to create user: {str(e)}",
            )

        # Send verification email
        self.email_service.send_verification_email(
            to_email=user.email,
            full_name=user.full_name,
            verification_token=verification_token,
        )

        # Return success with user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )

        return RegistrationResult(success=True, user=user_response)

    def verify_email(self, token: str) -> VerificationResult:
        """Verify a user's email address.

        Args:
            token: Email verification token.

        Returns:
            VerificationResult with success status and message.
        """
        # Find user by verification token
        user = self.user_repo.get_by_verification_token(token)

        if user is None:
            return VerificationResult(
                success=False,
                message="Invalid verification token",
            )

        # Check if already verified
        if user.email_verified:
            return VerificationResult(
                success=True,
                message="Email is already verified",
            )

        # Check if token is expired
        if is_token_expired(user.email_verification_expires_at):
            return VerificationResult(
                success=False,
                message="Verification token has expired. Please request a new one.",
            )

        # Verify the email
        updated_user = self.user_repo.verify_email(user.id)

        if updated_user is None:
            return VerificationResult(
                success=False,
                message="Failed to verify email. Please try again.",
            )

        return VerificationResult(
            success=True,
            message="Email verified successfully. You can now log in.",
        )

    def get_user_by_email(self, email: str) -> UserInDB | None:
        """Get a user by email address.

        Args:
            email: User's email address.

        Returns:
            UserInDB if found, None otherwise.
        """
        return self.user_repo.get_by_email(email)
