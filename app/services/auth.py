"""Authentication service for user registration and verification."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_verification_token,
    get_verification_expiry,
    hash_password,
    is_token_expired,
    verify_password,
    verify_token,
)
from app.models.user import Token, UserCreate, UserInDB, UserLogin, UserResponse
from app.repositories.user import UserRepository
from app.services.email import EmailServiceBase

# Constants for login security
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


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


@dataclass
class LoginResult:
    """Result of a login attempt."""

    success: bool
    token: Token | None = None
    user: UserResponse | None = None
    error: str | None = None


@dataclass
class PasswordResetResult:
    """Result of a password reset request."""

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
            role=user.role,
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

    def login_user(self, login_data: UserLogin) -> LoginResult:
        """Authenticate a user and return tokens.

        Args:
            login_data: User login credentials.

        Returns:
            LoginResult with tokens or error.
        """
        # Find user by email
        user = self.user_repo.get_by_email(login_data.email)

        if not user:
            # Don't reveal if user exists
            return LoginResult(success=False, error="Invalid email or password")

        # Check if account is locked
        if user.locked_until and not is_token_expired(user.locked_until):
            return LoginResult(
                success=False,
                error="Account is temporarily locked. Please try again later.",
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            self._handle_failed_login(user)
            return LoginResult(success=False, error="Invalid email or password")

        # Check if email is verified
        if not user.email_verified:
            return LoginResult(
                success=False,
                error="Please verify your email before logging in",
            )

        # Success - reset failed attempts and generate tokens
        self.user_repo.reset_login_attempts(user.id)
        token = self._generate_tokens(user.id)

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            email_verified=user.email_verified,
            role=user.role,
            created_at=user.created_at,
        )

        return LoginResult(success=True, token=token, user=user_response)

    def _handle_failed_login(self, user: UserInDB) -> None:
        """Handle failed login attempt - increment counter, possibly lock account.

        Args:
            user: The user who failed to login.
        """
        new_failed_attempts = (user.failed_login_attempts or 0) + 1
        locked_until = None

        if new_failed_attempts >= MAX_FAILED_ATTEMPTS:
            locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

        self.user_repo.update_login_stats(
            user.id,
            failed_attempts=new_failed_attempts,
            locked_until=locked_until,
        )

    def _generate_tokens(self, user_id) -> Token:
        """Generate access and refresh tokens for a user.

        Args:
            user_id: The user's ID.

        Returns:
            Token object with access and refresh tokens.
        """
        settings = get_settings()
        access_token = create_access_token(str(user_id))
        refresh_token = create_refresh_token(str(user_id))

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def refresh_access_token(self, refresh_token_str: str) -> LoginResult:
        """Refresh access token using a valid refresh token.

        Args:
            refresh_token_str: The refresh token string.

        Returns:
            LoginResult with new tokens or error.
        """
        payload = verify_token(refresh_token_str)

        if not payload or payload.get("type") != "refresh":
            return LoginResult(success=False, error="Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            return LoginResult(success=False, error="Invalid token payload")

        # Verify user still exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return LoginResult(success=False, error="User not found")

        # Check if account is locked
        if user.locked_until and not is_token_expired(user.locked_until):
            return LoginResult(success=False, error="Account is locked")

        token = self._generate_tokens(user.id)
        return LoginResult(success=True, token=token)

    def request_password_reset(self, email: str) -> PasswordResetResult:
        """Request a password reset email.

        Args:
            email: User's email address.

        Returns:
            PasswordResetResult with success status.
        """
        user = self.user_repo.get_by_email(email)

        # Always return success to prevent email enumeration
        if not user:
            return PasswordResetResult(
                success=True,
                message="If an account with that email exists, a password reset link has been sent.",
            )

        # Generate reset token
        reset_token = generate_verification_token()
        reset_expires = get_verification_expiry(hours=1)  # 1 hour expiry for reset

        # Save token to database
        self.user_repo.set_password_reset_token(user.id, reset_token, reset_expires)

        # Send reset email
        self.email_service.send_password_reset_email(
            to_email=user.email,
            full_name=user.full_name,
            reset_token=reset_token,
        )

        return PasswordResetResult(
            success=True,
            message="If an account with that email exists, a password reset link has been sent.",
        )

    def reset_password(self, token: str, new_password: str) -> PasswordResetResult:
        """Reset a user's password using a valid reset token.

        Args:
            token: Password reset token.
            new_password: New password to set.

        Returns:
            PasswordResetResult with success status.
        """
        user = self.user_repo.get_by_password_reset_token(token)

        if not user:
            return PasswordResetResult(
                success=False,
                message="Invalid or expired password reset token",
            )

        # Check if token is expired
        if is_token_expired(user.password_reset_expires_at):
            return PasswordResetResult(
                success=False,
                message="Password reset token has expired. Please request a new one.",
            )

        # Hash new password and update
        password_hash = hash_password(new_password)
        updated_user = self.user_repo.update_password(user.id, password_hash)

        if not updated_user:
            return PasswordResetResult(
                success=False,
                message="Failed to update password. Please try again.",
            )

        return PasswordResetResult(
            success=True,
            message="Password has been reset successfully. You can now log in.",
        )

