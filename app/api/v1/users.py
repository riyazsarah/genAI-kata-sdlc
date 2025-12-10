"""User profile management API endpoints for US-003."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from supabase import Client

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.profile import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    AvatarResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PreferencesResponse,
    PreferencesUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.models.user import UserInDB
from app.repositories.address import AddressRepository
from app.repositories.payment_method import PaymentMethodRepository
from app.repositories.profile import ProfileRepository
from app.repositories.user import UserRepository
from app.services.profile import ProfileService

router = APIRouter(prefix="/users", tags=["User Profile"])


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_profile_service(
    db_client: Client = Depends(get_supabase_client),
) -> ProfileService:
    """Get a ProfileService instance with all dependencies.

    Args:
        db_client: Supabase client from dependency injection.

    Returns:
        ProfileService instance.
    """
    return ProfileService(
        user_repository=UserRepository(db_client),
        profile_repository=ProfileRepository(db_client),
        address_repository=AddressRepository(db_client),
        payment_repository=PaymentMethodRepository(db_client),
    )


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get user profile",
    description="Get the complete profile for the authenticated user, including addresses and payment methods.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
    },
)
def get_profile(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Get the current user's complete profile."""
    result = service.get_profile(current_user)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to retrieve profile",
        )

    return result.data


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Update user profile",
    description="Update the authenticated user's basic profile information (name, phone, date of birth).",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        422: {"description": "Validation error"},
    },
)
def update_profile(
    data: ProfileUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Update the current user's profile information."""
    result = service.update_profile(current_user, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to update profile",
        )

    return result.data


@router.post(
    "/profile/avatar",
    response_model=AvatarResponse,
    summary="Upload profile picture",
    description="Upload a new profile picture. Accepts JPG, PNG, or WebP images up to 5MB.",
    responses={
        200: {"description": "Avatar uploaded successfully"},
        400: {"description": "Invalid file type or size"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
    },
)
def upload_avatar(
    file: UploadFile = File(..., description="Profile picture file"),
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
    db_client: Client = Depends(get_supabase_client),
) -> AvatarResponse:
    """Upload a new profile picture for the current user."""
    result = service.upload_avatar(current_user, file, db_client.storage)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to upload avatar",
        )

    return AvatarResponse(
        message=result.data["message"],
        profile_picture_url=result.data["url"],
    )


# ============================================================================
# ADDRESS ENDPOINTS
# ============================================================================


@router.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add delivery address",
    description="Add a new delivery address for the authenticated user.",
    responses={
        201: {"description": "Address created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        422: {"description": "Validation error"},
    },
)
def add_address(
    data: AddressCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> AddressResponse:
    """Add a new delivery address."""
    result = service.add_address(current_user, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to create address",
        )

    return result.data


@router.put(
    "/addresses/{address_id}",
    response_model=AddressResponse,
    summary="Update delivery address",
    description="Update an existing delivery address.",
    responses={
        200: {"description": "Address updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        404: {"description": "Address not found"},
        422: {"description": "Validation error"},
    },
)
def update_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> AddressResponse:
    """Update an existing delivery address."""
    result = service.update_address(current_user, address_id, data)

    if not result.success:
        if "not found" in (result.error or "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to update address",
        )

    return result.data


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete delivery address",
    description="Delete a delivery address.",
    responses={
        204: {"description": "Address deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        404: {"description": "Address not found"},
    },
)
def delete_address(
    address_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    """Delete a delivery address."""
    result = service.delete_address(current_user, address_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )


# ============================================================================
# PAYMENT METHOD ENDPOINTS
# ============================================================================


@router.post(
    "/payment-methods",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add payment method",
    description="Add a new payment method. Card numbers are tokenized and not stored directly.",
    responses={
        201: {"description": "Payment method added successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        422: {"description": "Validation error"},
    },
)
def add_payment_method(
    data: PaymentMethodCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> PaymentMethodResponse:
    """Add a new payment method."""
    result = service.add_payment_method(current_user, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to add payment method",
        )

    return result.data


@router.delete(
    "/payment-methods/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove payment method",
    description="Remove a payment method.",
    responses={
        204: {"description": "Payment method removed successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        404: {"description": "Payment method not found"},
    },
)
def delete_payment_method(
    payment_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    """Remove a payment method."""
    result = service.delete_payment_method(current_user, payment_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )


# ============================================================================
# PREFERENCES ENDPOINTS
# ============================================================================


@router.put(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Update preferences",
    description="Update dietary and/or communication preferences.",
    responses={
        200: {"description": "Preferences updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Email not verified"},
        422: {"description": "Validation error"},
    },
)
def update_preferences(
    data: PreferencesUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    service: ProfileService = Depends(get_profile_service),
) -> PreferencesResponse:
    """Update user preferences (dietary and communication)."""
    result = service.update_preferences(current_user, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to update preferences",
        )

    return PreferencesResponse(
        dietary_preferences=result.data["dietary_preferences"],
        communication_preferences=result.data["communication_preferences"],
        message=result.data["message"],
    )
