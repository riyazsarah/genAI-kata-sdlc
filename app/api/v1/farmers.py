"""Farmer profile management API endpoints for US-005."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.farmer import (
    BankAccountCreate,
    BankAccountResponse,
    FarmDetailsUpdate,
    FarmerInDB,
    FarmerProfileResponse,
    FarmImageCreate,
    FarmImageResponse,
    FarmImagesReorderRequest,
    FarmVideoCreate,
    FarmVideoResponse,
    ProfileCompletionStatus,
)
from app.models.user import UserInDB
from app.repositories.farm_image import FarmImageRepository
from app.repositories.farm_video import FarmVideoRepository
from app.repositories.farmer import FarmerRepository
from app.repositories.farmer_bank_account import FarmerBankAccountRepository
from app.repositories.user import UserRepository
from app.services.email import get_email_service
from app.services.farmer import FarmerService

router = APIRouter(prefix="/farmers", tags=["Farmer Profile"])


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_farmer_service(
    db_client: Client = Depends(get_supabase_client),
) -> FarmerService:
    """Get a FarmerService instance with all dependencies.

    Args:
        db_client: Supabase client from dependency injection.

    Returns:
        FarmerService instance.
    """
    from app.core.config import get_settings

    settings = get_settings()
    base_url = f"http://{settings.host}:{settings.port}"

    return FarmerService(
        user_repository=UserRepository(db_client),
        farmer_repository=FarmerRepository(db_client),
        farm_image_repository=FarmImageRepository(db_client),
        farm_video_repository=FarmVideoRepository(db_client),
        bank_account_repository=FarmerBankAccountRepository(db_client),
        email_service=get_email_service(base_url),
    )


def get_farmer_repository(
    db_client: Client = Depends(get_supabase_client),
) -> FarmerRepository:
    """Get a FarmerRepository instance.

    Args:
        db_client: Supabase client from dependency injection.

    Returns:
        FarmerRepository instance.
    """
    return FarmerRepository(db_client)


async def get_current_farmer(
    current_user: UserInDB = Depends(get_current_active_user),
    farmer_repo: FarmerRepository = Depends(get_farmer_repository),
) -> tuple[UserInDB, FarmerInDB]:
    """Get the current authenticated farmer.

    This dependency ensures the user is a farmer and returns both user and farmer records.

    Args:
        current_user: Authenticated user from get_current_active_user.
        farmer_repo: FarmerRepository for database access.

    Returns:
        Tuple of (UserInDB, FarmerInDB).

    Raises:
        HTTPException: 403 if user is not a farmer.
    """
    if current_user.role != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to farmers",
        )

    farmer = farmer_repo.get_by_user_id(current_user.id)
    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found",
        )

    return current_user, farmer


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================


@router.get(
    "/profile",
    response_model=FarmerProfileResponse,
    summary="Get farmer profile",
    description="Get the complete farmer profile including farm details, media, and bank account status.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def get_farmer_profile(
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> FarmerProfileResponse:
    """Get the current farmer's complete profile."""
    user, farmer = current_farmer
    return service.get_farmer_profile(user, farmer)


@router.put(
    "/farm",
    response_model=dict,
    summary="Update farm details",
    description="Update farm information including name, description, address, and farming practices.",
    responses={
        200: {"description": "Farm details updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
        422: {"description": "Validation error"},
    },
)
def update_farm_details(
    data: FarmDetailsUpdate,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> dict:
    """Update farm details."""
    _, farmer = current_farmer
    result = service.update_farm_details(farmer.id, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Failed to update farm details",
        )

    return {"message": "Farm details updated successfully"}


@router.get(
    "/completion-status",
    response_model=ProfileCompletionStatus,
    summary="Get profile completion status",
    description="Get the current profile completion status and which steps are done.",
    responses={
        200: {"description": "Status retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def get_completion_status(
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> ProfileCompletionStatus:
    """Get profile completion status."""
    _, farmer = current_farmer
    status_data = service.get_completion_status(farmer.id)

    return ProfileCompletionStatus(
        profile_completed=status_data["profile_completed"],
        current_step=status_data["current_step"],
        steps=status_data["steps"],
    )


# ============================================================================
# FARM IMAGES ENDPOINTS
# ============================================================================


@router.post(
    "/farm/images",
    response_model=FarmImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add farm image",
    description="Add a new farm image. Maximum 10 images per farm.",
    responses={
        201: {"description": "Image added successfully"},
        400: {"description": "Maximum images reached or upload failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def add_farm_image(
    data: FarmImageCreate,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> FarmImageResponse:
    """Add a new farm image."""
    _, farmer = current_farmer
    result = service.add_farm_image(farmer.id, data)

    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.delete(
    "/farm/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete farm image",
    description="Delete a farm image.",
    responses={
        204: {"description": "Image deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
        404: {"description": "Image not found"},
    },
)
def delete_farm_image(
    image_id: UUID,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> None:
    """Delete a farm image."""
    _, farmer = current_farmer
    result = service.delete_farm_image(farmer.id, image_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )


@router.put(
    "/farm/images/reorder",
    response_model=dict,
    summary="Reorder farm images",
    description="Reorder farm images by providing a list of image IDs in the desired order.",
    responses={
        200: {"description": "Images reordered successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def reorder_farm_images(
    data: FarmImagesReorderRequest,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> dict:
    """Reorder farm images."""
    _, farmer = current_farmer
    service.reorder_farm_images(farmer.id, data.image_ids)
    return {"message": "Images reordered successfully"}


# ============================================================================
# FARM VIDEOS ENDPOINTS
# ============================================================================


@router.post(
    "/farm/videos",
    response_model=FarmVideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add farm video",
    description="Add a YouTube or Vimeo video URL. Maximum 5 videos per farm.",
    responses={
        201: {"description": "Video added successfully"},
        400: {"description": "Maximum videos reached, invalid URL, or upload failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def add_farm_video(
    data: FarmVideoCreate,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> FarmVideoResponse:
    """Add a new farm video."""
    _, farmer = current_farmer
    result = service.add_farm_video(farmer.id, data)

    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.delete(
    "/farm/videos/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete farm video",
    description="Delete a farm video.",
    responses={
        204: {"description": "Video deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
        404: {"description": "Video not found"},
    },
)
def delete_farm_video(
    video_id: UUID,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> None:
    """Delete a farm video."""
    _, farmer = current_farmer
    result = service.delete_farm_video(farmer.id, video_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )


# ============================================================================
# BANK ACCOUNT ENDPOINTS
# ============================================================================


@router.post(
    "/bank-account",
    response_model=BankAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add/update bank account",
    description="Add or update bank account for payouts. Account numbers are encrypted.",
    responses={
        201: {"description": "Bank account saved successfully"},
        400: {"description": "Validation error or save failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def add_or_update_bank_account(
    data: BankAccountCreate,
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> BankAccountResponse:
    """Add or update bank account."""
    _, farmer = current_farmer
    result = service.add_or_update_bank_account(farmer.id, data)

    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


@router.get(
    "/bank-account",
    response_model=BankAccountResponse | None,
    summary="Get bank account",
    description="Get bank account details (masked).",
    responses={
        200: {"description": "Bank account retrieved successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not a farmer or email not verified"},
    },
)
def get_bank_account(
    current_farmer: tuple[UserInDB, FarmerInDB] = Depends(get_current_farmer),
    service: FarmerService = Depends(get_farmer_service),
) -> BankAccountResponse | None:
    """Get bank account details."""
    _, farmer = current_farmer
    return service.get_bank_account(farmer.id)
