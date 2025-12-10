"""Data models for the application."""

from app.models.product import (
    CategoriesResponse,
    ImageUploadResponse,
    ProductCategory,
    ProductCreate,
    ProductInDB,
    ProductListResponse,
    ProductResponse,
    ProductStatus,
    ProductUnit,
    ProductUpdate,
    Seasonality,
)
from app.models.profile import (
    AddressCreate,
    AddressInDB,
    AddressResponse,
    AddressUpdate,
    AvatarResponse,
    CommunicationPreferences,
    DietaryPreference,
    PaymentMethodCreate,
    PaymentMethodInDB,
    PaymentMethodResponse,
    PreferencesResponse,
    PreferencesUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.models.user import (
    UserCreate,
    UserInDB,
    UserResponse,
    VerifyEmailRequest,
)

__all__ = [
    # User models
    "UserCreate",
    "UserInDB",
    "UserResponse",
    "VerifyEmailRequest",
    # Profile models
    "AddressCreate",
    "AddressInDB",
    "AddressResponse",
    "AddressUpdate",
    "AvatarResponse",
    "CommunicationPreferences",
    "DietaryPreference",
    "PaymentMethodCreate",
    "PaymentMethodInDB",
    "PaymentMethodResponse",
    "PreferencesResponse",
    "PreferencesUpdate",
    "ProfileResponse",
    "ProfileUpdate",
    # Product models
    "CategoriesResponse",
    "ImageUploadResponse",
    "ProductCategory",
    "ProductCreate",
    "ProductInDB",
    "ProductListResponse",
    "ProductResponse",
    "ProductStatus",
    "ProductUnit",
    "ProductUpdate",
    "Seasonality",
]
