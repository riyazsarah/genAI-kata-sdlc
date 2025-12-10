"""Farmer-related Pydantic models for US-004 and US-005."""

import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import PasswordValidator

# ============================================================================
# ENUMERATIONS
# ============================================================================


class UserRole(str, Enum):
    """User role types in the system."""

    CONSUMER = "consumer"
    FARMER = "farmer"


class FarmingPractice(str, Enum):
    """Farming practice types."""

    ORGANIC = "Organic"
    SUSTAINABLE = "Sustainable"
    CONVENTIONAL = "Conventional"
    BIODYNAMIC = "Biodynamic"
    REGENERATIVE = "Regenerative"


class VideoPlatform(str, Enum):
    """Supported video platforms."""

    YOUTUBE = "youtube"
    VIMEO = "vimeo"


class BankAccountType(str, Enum):
    """Bank account types."""

    CHECKING = "checking"
    SAVINGS = "savings"


# ============================================================================
# FARMER REGISTRATION MODELS (US-004)
# ============================================================================


class FarmerCreate(BaseModel):
    """Request model for farmer registration."""

    # User fields
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Farmer's full name",
        examples=["John Smith"],
    )
    email: EmailStr = Field(
        ...,
        description="Farmer's email address",
        examples=["john.farmer@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password",
        examples=["SecurePass123!"],
    )
    phone: str = Field(
        ...,
        max_length=20,
        description="Farmer's phone number (required for farmers)",
        examples=["+1234567890"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth (must be 18+)",
        examples=["1985-06-15"],
    )

    # Farm basic info
    farm_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the farm",
        examples=["Green Valley Farm"],
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

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Validate farmer is at least 18 years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Farmer must be at least 18 years old")
        return v


class FarmerRegistrationResponse(BaseModel):
    """Response model for successful farmer registration."""

    message: str
    user_id: UUID
    farmer_id: UUID
    email: str


# ============================================================================
# FARMER PROFILE MODELS (US-005)
# ============================================================================


class FarmerInDB(BaseModel):
    """Farmer model as stored in the database."""

    id: UUID
    user_id: UUID
    farm_name: str | None
    farm_description: str | None
    farm_street: str | None
    farm_city: str | None
    farm_state: str | None
    farm_zip_code: str | None
    farm_latitude: Decimal | None
    farm_longitude: Decimal | None
    farming_practices: list[str]
    profile_completed: bool
    profile_completion_step: int
    created_at: datetime
    updated_at: datetime


class FarmDetailsUpdate(BaseModel):
    """Request model for updating farm details."""

    farm_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
        description="Name of the farm",
        examples=["Green Valley Farm"],
    )
    farm_description: str | None = Field(
        default=None,
        max_length=2000,
        description="Description of the farm",
        examples=["A family-owned organic farm since 1990..."],
    )
    farm_street: str | None = Field(
        default=None,
        max_length=255,
        description="Farm street address",
        examples=["1234 Farm Road"],
    )
    farm_city: str | None = Field(
        default=None,
        max_length=100,
        description="Farm city",
        examples=["Austin"],
    )
    farm_state: str | None = Field(
        default=None,
        max_length=50,
        description="Farm state",
        examples=["TX"],
    )
    farm_zip_code: str | None = Field(
        default=None,
        max_length=20,
        description="Farm ZIP code",
        examples=["78701"],
    )
    farming_practices: list[FarmingPractice] | None = Field(
        default=None,
        description="Farming practices used",
        examples=[["Organic", "Sustainable"]],
    )

    @field_validator("farm_zip_code")
    @classmethod
    def validate_zip_code(cls, v: str | None) -> str | None:
        """Validate ZIP code format if provided."""
        if v is None:
            return None
        pattern = r"^\d{5}(-\d{4})?$"
        if not re.match(pattern, v):
            raise ValueError("Invalid ZIP code format. Use 12345 or 12345-6789")
        return v


class FarmerProfileResponse(BaseModel):
    """Response model for farmer profile."""

    # User info
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    phone: str | None
    date_of_birth: date | None
    profile_picture_url: str | None

    # Farm info
    farm_name: str | None
    farm_description: str | None
    farm_street: str | None
    farm_city: str | None
    farm_state: str | None
    farm_zip_code: str | None
    farming_practices: list[str]

    # Media
    farm_images: list["FarmImageResponse"]
    farm_videos: list["FarmVideoResponse"]

    # Bank account (only shows if exists, never shows full numbers)
    has_bank_account: bool
    bank_account_last_four: str | None

    # Status
    profile_completed: bool
    profile_completion_step: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# FARM IMAGE MODELS
# ============================================================================


class FarmImageCreate(BaseModel):
    """Request model for adding a farm image."""

    image_url: str = Field(
        ...,
        max_length=500,
        description="URL to the image in storage",
    )
    caption: str | None = Field(
        default=None,
        max_length=200,
        description="Image caption",
        examples=["Our beautiful sunflower field"],
    )
    alt_text: str | None = Field(
        default=None,
        max_length=200,
        description="Alt text for accessibility",
        examples=["Rows of sunflowers in bloom"],
    )
    is_primary: bool = Field(
        default=False,
        description="Set as primary/featured image",
    )


class FarmImageInDB(BaseModel):
    """Farm image model as stored in the database."""

    id: UUID
    farmer_id: UUID
    image_url: str
    caption: str | None
    alt_text: str | None
    display_order: int
    is_primary: bool
    created_at: datetime


class FarmImageResponse(BaseModel):
    """Response model for farm image."""

    id: UUID
    image_url: str
    caption: str | None
    alt_text: str | None
    display_order: int
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmImagesReorderRequest(BaseModel):
    """Request model for reordering farm images."""

    image_ids: list[UUID] = Field(
        ...,
        description="List of image IDs in desired order",
    )


# ============================================================================
# FARM VIDEO MODELS
# ============================================================================


class FarmVideoCreate(BaseModel):
    """Request model for adding a farm video."""

    video_url: str = Field(
        ...,
        max_length=500,
        description="YouTube or Vimeo video URL",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Video title",
        examples=["Tour of our organic farm"],
    )

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, v: str) -> str:
        """Validate that URL is from YouTube or Vimeo."""
        youtube_patterns = [
            r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+",
            r"^https?://(www\.)?youtu\.be/[\w-]+",
        ]
        vimeo_patterns = [
            r"^https?://(www\.)?vimeo\.com/\d+",
        ]

        is_youtube = any(re.match(p, v) for p in youtube_patterns)
        is_vimeo = any(re.match(p, v) for p in vimeo_patterns)

        if not is_youtube and not is_vimeo:
            raise ValueError("URL must be a valid YouTube or Vimeo video URL")
        return v


class FarmVideoInDB(BaseModel):
    """Farm video model as stored in the database."""

    id: UUID
    farmer_id: UUID
    video_url: str
    video_platform: str
    video_id: str
    title: str | None
    display_order: int
    created_at: datetime


class FarmVideoResponse(BaseModel):
    """Response model for farm video."""

    id: UUID
    video_url: str
    video_platform: str
    video_id: str
    title: str | None
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# BANK ACCOUNT MODELS
# ============================================================================


class BankAccountCreate(BaseModel):
    """Request model for adding/updating bank account."""

    account_holder_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name on the bank account",
        examples=["John Smith"],
    )
    account_number: str = Field(
        ...,
        min_length=4,
        max_length=17,
        description="Bank account number",
        examples=["123456789012"],
    )
    routing_number: str = Field(
        ...,
        min_length=9,
        max_length=9,
        description="Bank routing number (9 digits)",
        examples=["021000021"],
    )
    bank_name: str | None = Field(
        default=None,
        max_length=100,
        description="Name of the bank",
        examples=["Chase Bank"],
    )
    account_type: BankAccountType = Field(
        default=BankAccountType.CHECKING,
        description="Type of account",
    )

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Validate account number is numeric."""
        if not v.isdigit():
            raise ValueError("Account number must contain only digits")
        return v

    @field_validator("routing_number")
    @classmethod
    def validate_routing_number(cls, v: str) -> str:
        """Validate routing number format."""
        if not v.isdigit() or len(v) != 9:
            raise ValueError("Routing number must be exactly 9 digits")
        return v


class BankAccountInDB(BaseModel):
    """Bank account model as stored in the database."""

    id: UUID
    farmer_id: UUID
    account_holder_name: str
    account_number_encrypted: str
    routing_number_encrypted: str
    account_last_four: str
    bank_name: str | None
    account_type: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class BankAccountResponse(BaseModel):
    """Response model for bank account (excludes sensitive data)."""

    id: UUID
    account_holder_name: str
    account_last_four: str
    bank_name: str | None
    account_type: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PROFILE COMPLETION MODELS
# ============================================================================


class ProfileCompletionStatus(BaseModel):
    """Response model for profile completion status."""

    profile_completed: bool
    current_step: int
    steps: dict[str, bool] = Field(
        description="Completion status of each step",
        examples=[
            {
                "basic_info": True,
                "farm_details": True,
                "farm_media": False,
                "bank_account": False,
            }
        ],
    )


# Update forward references
FarmerProfileResponse.model_rebuild()
