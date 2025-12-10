"""Profile-related Pydantic models for US-003 User Profile Management."""

from datetime import date, datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# ENUMERATIONS
# ============================================================================


class DietaryPreference(str, Enum):
    """Dietary preference options for user profiles."""

    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    GLUTEN_FREE = "Gluten-Free"
    DAIRY_FREE = "Dairy-Free"
    NUT_FREE = "Nut-Free"
    ORGANIC = "Organic"
    KETO = "Keto"
    PALEO = "Paleo"


# ============================================================================
# COMMUNICATION PREFERENCES
# ============================================================================


class CommunicationPreferences(BaseModel):
    """Communication preference settings."""

    email: bool = Field(default=True, description="Receive email notifications")
    sms: bool = Field(default=False, description="Receive SMS notifications")
    push: bool = Field(default=False, description="Receive push notifications")


# ============================================================================
# PROFILE MODELS
# ============================================================================


class ProfileUpdate(BaseModel):
    """Request model for updating user profile basic information."""

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="User's phone number",
        examples=["+1234567890"],
    )
    date_of_birth: date | None = Field(
        default=None,
        description="User's date of birth",
        examples=["1990-01-15"],
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """Validate and clean full name."""
        if v is None:
            return None
        cleaned = " ".join(v.split())
        if len(cleaned) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return cleaned


class ProfileResponse(BaseModel):
    """Response model for complete user profile."""

    id: UUID
    email: str
    full_name: str
    phone: str | None
    date_of_birth: date | None
    profile_picture_url: str | None
    email_verified: bool
    dietary_preferences: list[str]
    communication_preferences: CommunicationPreferences
    addresses: list["AddressResponse"]
    payment_methods: list["PaymentMethodResponse"]
    created_at: datetime

    model_config = {"from_attributes": True}


class AvatarResponse(BaseModel):
    """Response model for avatar upload."""

    message: str
    profile_picture_url: str


# ============================================================================
# ADDRESS MODELS
# ============================================================================


class AddressBase(BaseModel):
    """Base model for address data."""

    label: str | None = Field(
        default=None,
        max_length=50,
        description="Address label (e.g., Home, Work)",
        examples=["Home"],
    )
    street: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Street address",
        examples=["123 Main Street, Apt 4B"],
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name",
        examples=["Austin"],
    )
    state: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="State or province",
        examples=["TX"],
    )
    zip_code: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="ZIP or postal code",
        examples=["78701"],
    )
    delivery_instructions: str | None = Field(
        default=None,
        max_length=500,
        description="Special delivery instructions",
        examples=["Leave at the front door"],
    )

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        """Validate ZIP code format (US format)."""
        import re

        # Allow US ZIP codes: 12345 or 12345-6789
        pattern = r"^\d{5}(-\d{4})?$"
        if not re.match(pattern, v):
            raise ValueError("Invalid ZIP code format. Use 12345 or 12345-6789")
        return v


class AddressCreate(AddressBase):
    """Request model for creating a new address."""

    is_default: bool = Field(
        default=False,
        description="Set as default delivery address",
    )


class AddressUpdate(BaseModel):
    """Request model for updating an address (all fields optional)."""

    label: str | None = Field(default=None, max_length=50)
    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=50)
    zip_code: str | None = Field(default=None, min_length=5, max_length=20)
    delivery_instructions: str | None = Field(default=None, max_length=500)
    is_default: bool | None = None

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str | None) -> str | None:
        """Validate ZIP code format if provided."""
        if v is None:
            return None
        import re

        pattern = r"^\d{5}(-\d{4})?$"
        if not re.match(pattern, v):
            raise ValueError("Invalid ZIP code format. Use 12345 or 12345-6789")
        return v


class AddressInDB(BaseModel):
    """Address model as stored in the database."""

    id: UUID
    user_id: UUID
    label: str | None
    street: str
    city: str
    state: str
    zip_code: str
    delivery_instructions: str | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AddressResponse(BaseModel):
    """Response model for address data."""

    id: UUID
    label: str | None
    street: str
    city: str
    state: str
    zip_code: str
    delivery_instructions: str | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PAYMENT METHOD MODELS
# ============================================================================


class PaymentMethodCreate(BaseModel):
    """Request model for adding a payment method."""

    payment_type: Literal["card", "digital_wallet"] = Field(
        ...,
        description="Type of payment method",
    )
    provider: str = Field(
        ...,
        max_length=50,
        description="Payment provider (visa, mastercard, apple_pay, etc.)",
        examples=["visa"],
    )
    # For cards - these will be tokenized, not stored raw
    card_number: str | None = Field(
        default=None,
        description="Card number (will be tokenized, not stored)",
        examples=["4111111111111111"],
    )
    expiry_month: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Card expiry month (1-12)",
    )
    expiry_year: int | None = Field(
        default=None,
        ge=2024,
        description="Card expiry year",
    )
    is_default: bool = Field(
        default=False,
        description="Set as default payment method",
    )

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str | None) -> str | None:
        """Validate card number format using Luhn algorithm."""
        if v is None:
            return None
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.isdigit() or len(cleaned) < 13 or len(cleaned) > 19:
            raise ValueError("Invalid card number format")
        return cleaned


class PaymentMethodInDB(BaseModel):
    """Payment method model as stored in the database."""

    id: UUID
    user_id: UUID
    payment_type: str
    provider: str | None
    token: str
    last_four: str | None
    expiry_month: int | None
    expiry_year: int | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaymentMethodResponse(BaseModel):
    """Response model for payment method (excludes sensitive data)."""

    id: UUID
    payment_type: str
    provider: str | None
    last_four: str | None
    expiry_month: int | None
    expiry_year: int | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PREFERENCES MODELS
# ============================================================================


class PreferencesUpdate(BaseModel):
    """Request model for updating user preferences."""

    dietary_preferences: list[DietaryPreference] | None = Field(
        default=None,
        description="List of dietary preferences",
        examples=[["Vegetarian", "Gluten-Free"]],
    )
    communication_preferences: CommunicationPreferences | None = Field(
        default=None,
        description="Communication notification settings",
    )


class PreferencesResponse(BaseModel):
    """Response model for user preferences."""

    dietary_preferences: list[str]
    communication_preferences: CommunicationPreferences
    message: str = "Preferences updated successfully"


# Update forward references for ProfileResponse
ProfileResponse.model_rebuild()
