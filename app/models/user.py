"""User-related Pydantic models."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import PasswordValidator


class UserCreate(BaseModel):
    """Request model for user registration."""

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password",
        examples=["SecurePass123!"],
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="User's phone number",
        examples=["+1234567890"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        is_valid, errors = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and clean full name."""
        cleaned = " ".join(v.split())
        if len(cleaned) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return cleaned


class UserInDB(BaseModel):
    """User model as stored in the database."""

    id: UUID
    email: str
    password_hash: str
    full_name: str
    phone: str | None
    email_verified: bool
    email_verification_token: UUID | None
    email_verification_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    password_reset_token: UUID | None = None
    password_reset_expires_at: datetime | None = None
    last_login_at: datetime | None = None
    # Profile fields (US-003)
    date_of_birth: date | None = None
    profile_picture_url: str | None = None
    dietary_preferences: list[str] = []
    communication_preferences: dict[str, Any] = {"email": True, "sms": False, "push": False}
    # Role field (US-004)
    role: str = "consumer"


class UserResponse(BaseModel):
    """Response model for user data (excludes sensitive fields)."""

    id: UUID
    email: str
    full_name: str
    phone: str | None
    email_verified: bool
    role: str = "consumer"
    created_at: datetime

    model_config = {"from_attributes": True}


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""

    token: str = Field(
        ...,
        description="Email verification token",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class RegistrationResponse(BaseModel):
    """Response model for successful registration."""

    message: str
    user: UserResponse


class EmailVerificationResponse(BaseModel):
    """Response model for email verification."""

    message: str
    verified: bool


class UserLogin(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class Token(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""

    email: EmailStr = Field(..., description="User's email address")


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        is_valid, errors = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v

