"""Security utilities for password hashing and token generation."""

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a new JWT access token.

    Args:
        subject: The subject of the token (usually user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a new JWT refresh token.

    Args:
        subject: The subject of the token (usually user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        Decoded payload dict if valid, None otherwise.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except jwt.PyJWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hashed password.

    Returns:
        True if password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def generate_verification_token() -> str:
    """Generate a unique email verification token.

    Returns:
        UUID string for email verification.
    """
    return str(uuid.uuid4())


def get_verification_expiry(hours: int = 24) -> datetime:
    """Get the expiration datetime for email verification token.

    Args:
        hours: Number of hours until expiration. Defaults to 24.

    Returns:
        Datetime when the token expires.
    """
    return datetime.now(UTC) + timedelta(hours=hours)


def is_token_expired(expiry_time: datetime | None) -> bool:
    """Check if a verification token has expired.

    Args:
        expiry_time: The expiration datetime of the token.

    Returns:
        True if expired or None, False otherwise.
    """
    if expiry_time is None:
        return True
    now = datetime.now(UTC)
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=UTC)
    return now > expiry_time


class PasswordValidator:
    """Validates password strength according to security requirements."""

    MIN_LENGTH = 8
    REQUIREMENTS = [
        (r"[A-Z]", "at least one uppercase letter"),
        (r"[a-z]", "at least one lowercase letter"),
        (r"[0-9]", "at least one digit"),
        (r"[!@#$%^&*(),.?\":{}|<>]", "at least one special character"),
    ]

    @classmethod
    def validate(cls, password: str) -> tuple[bool, list[str]]:
        """Validate password strength.

        Args:
            password: Password to validate.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors: list[str] = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        for pattern, description in cls.REQUIREMENTS:
            if not re.search(pattern, password):
                errors.append(f"Password must contain {description}")

        return len(errors) == 0, errors

    @classmethod
    def get_requirements_message(cls) -> str:
        """Get a human-readable message describing password requirements.

        Returns:
            String describing all password requirements.
        """
        reqs = [f"at least {cls.MIN_LENGTH} characters"]
        reqs.extend(desc for _, desc in cls.REQUIREMENTS)
        return "Password must contain: " + ", ".join(reqs)
