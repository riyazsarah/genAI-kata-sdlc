"""Tests for authentication service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.user import UserCreate, UserInDB
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.email import MockEmailService


@pytest.fixture
def mock_user_repo():
    """Create a mock user repository."""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_email_service():
    """Create a mock email service."""
    return MockEmailService()


@pytest.fixture
def auth_service(mock_user_repo, mock_email_service):
    """Create an auth service with mocked dependencies."""
    return AuthService(mock_user_repo, mock_email_service)


@pytest.fixture
def sample_user_create():
    """Create a sample user registration request."""
    return UserCreate(
        full_name="John Doe",
        email="john.doe@example.com",
        password="SecurePass123!",
        phone="+1234567890",
    )


@pytest.fixture
def sample_user_in_db():
    """Create a sample user as stored in database."""
    return UserInDB(
        id=uuid4(),
        email="john.doe@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="John Doe",
        phone="+1234567890",
        email_verified=False,
        email_verification_token=uuid4(),
        email_verification_expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestRegistration:
    """Tests for user registration."""

    def test_successful_registration(
        self, auth_service, mock_user_repo, sample_user_create, sample_user_in_db
    ):
        """Successful registration should return user data."""
        # Setup
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.create.return_value = sample_user_in_db

        # Execute
        result = auth_service.register_user(sample_user_create)

        # Verify
        assert result.success is True
        assert result.user is not None
        assert result.user.email == sample_user_create.email
        assert result.user.full_name == sample_user_create.full_name
        assert result.error is None

    def test_registration_sends_verification_email(
        self, auth_service, mock_user_repo, mock_email_service, sample_user_create, sample_user_in_db
    ):
        """Registration should send verification email."""
        # Setup
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.create.return_value = sample_user_in_db

        # Execute
        auth_service.register_user(sample_user_create)

        # Verify email was "sent"
        assert len(mock_email_service.sent_emails) == 1
        email = mock_email_service.sent_emails[0]
        assert email["to"] == sample_user_in_db.email

    def test_registration_fails_for_duplicate_email(
        self, auth_service, mock_user_repo, sample_user_create
    ):
        """Registration should fail if email already exists."""
        # Setup
        mock_user_repo.email_exists.return_value = True

        # Execute
        result = auth_service.register_user(sample_user_create)

        # Verify
        assert result.success is False
        assert result.user is None
        assert "already exists" in result.error

    def test_registration_fails_on_db_error(
        self, auth_service, mock_user_repo, sample_user_create
    ):
        """Registration should fail gracefully on database error."""
        # Setup
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.create.side_effect = Exception("Database connection failed")

        # Execute
        result = auth_service.register_user(sample_user_create)

        # Verify
        assert result.success is False
        assert "Failed to create user" in result.error

    def test_registration_hashes_password(
        self, auth_service, mock_user_repo, sample_user_create, sample_user_in_db
    ):
        """Registration should hash the password before storing."""
        # Setup
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.create.return_value = sample_user_in_db

        # Execute
        auth_service.register_user(sample_user_create)

        # Verify password is hashed in the call to create
        call_args = mock_user_repo.create.call_args
        password_hash = call_args.kwargs.get("password_hash") or call_args[1].get("password_hash")

        # The password hash should not be the plain password
        assert password_hash != sample_user_create.password
        # It should be a bcrypt hash
        assert password_hash.startswith("$2")


class TestEmailVerification:
    """Tests for email verification."""

    def test_successful_verification(
        self, auth_service, mock_user_repo, sample_user_in_db
    ):
        """Valid token should verify email successfully."""
        # Setup
        token = str(sample_user_in_db.email_verification_token)
        mock_user_repo.get_by_verification_token.return_value = sample_user_in_db
        mock_user_repo.verify_email.return_value = sample_user_in_db

        # Execute
        result = auth_service.verify_email(token)

        # Verify
        assert result.success is True
        assert "verified successfully" in result.message.lower() or "verified" in result.message.lower()

    def test_verification_fails_for_invalid_token(
        self, auth_service, mock_user_repo
    ):
        """Invalid token should fail verification."""
        # Setup
        mock_user_repo.get_by_verification_token.return_value = None

        # Execute
        result = auth_service.verify_email("invalid-token")

        # Verify
        assert result.success is False
        assert "invalid" in result.message.lower()

    def test_verification_fails_for_expired_token(
        self, auth_service, mock_user_repo
    ):
        """Expired token should fail verification."""
        # Setup - create user with expired token
        expired_user = UserInDB(
            id=uuid4(),
            email="expired@example.com",
            password_hash="hashed",
            full_name="Expired User",
            phone=None,
            email_verified=False,
            email_verification_token=uuid4(),
            email_verification_expires_at=datetime.now(UTC) - timedelta(hours=1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_repo.get_by_verification_token.return_value = expired_user

        # Execute
        result = auth_service.verify_email(str(expired_user.email_verification_token))

        # Verify
        assert result.success is False
        assert "expired" in result.message.lower()

    def test_already_verified_returns_success(
        self, auth_service, mock_user_repo
    ):
        """Already verified email should return success."""
        # Setup - create user with already verified email
        verified_user = UserInDB(
            id=uuid4(),
            email="verified@example.com",
            password_hash="hashed",
            full_name="Verified User",
            phone=None,
            email_verified=True,  # Already verified
            email_verification_token=None,
            email_verification_expires_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_repo.get_by_verification_token.return_value = verified_user

        # Execute
        result = auth_service.verify_email("some-token")

        # Verify
        assert result.success is True
        assert "already verified" in result.message.lower()

    def test_verification_handles_db_error(
        self, auth_service, mock_user_repo, sample_user_in_db
    ):
        """Verification should handle database update failure."""
        # Setup
        mock_user_repo.get_by_verification_token.return_value = sample_user_in_db
        mock_user_repo.verify_email.return_value = None  # Simulate failure

        # Execute
        result = auth_service.verify_email(str(sample_user_in_db.email_verification_token))

        # Verify
        assert result.success is False
        assert "failed" in result.message.lower() or "try again" in result.message.lower()
