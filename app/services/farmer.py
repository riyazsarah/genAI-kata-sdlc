"""Farmer service for farmer registration and profile management."""

from dataclasses import dataclass
from uuid import UUID

from app.core.security import (
    generate_verification_token,
    get_verification_expiry,
    hash_password,
)
from app.models.farmer import (
    BankAccountCreate,
    BankAccountResponse,
    FarmDetailsUpdate,
    FarmerCreate,
    FarmerInDB,
    FarmerProfileResponse,
    FarmImageCreate,
    FarmImageResponse,
    FarmVideoCreate,
    FarmVideoResponse,
)
from app.models.user import UserInDB
from app.repositories.farm_image import FarmImageRepository
from app.repositories.farm_video import FarmVideoRepository
from app.repositories.farmer import FarmerRepository
from app.repositories.farmer_bank_account import FarmerBankAccountRepository
from app.repositories.user import UserRepository
from app.services.email import EmailServiceBase


@dataclass
class FarmerRegistrationResult:
    """Result of a farmer registration attempt."""

    success: bool
    user_id: UUID | None = None
    farmer_id: UUID | None = None
    email: str | None = None
    error: str | None = None


@dataclass
class ProfileUpdateResult:
    """Result of a profile update attempt."""

    success: bool
    error: str | None = None


class FarmerService:
    """Service for farmer-related operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        farmer_repository: FarmerRepository,
        farm_image_repository: FarmImageRepository,
        farm_video_repository: FarmVideoRepository,
        bank_account_repository: FarmerBankAccountRepository,
        email_service: EmailServiceBase,
    ) -> None:
        """Initialize the farmer service.

        Args:
            user_repository: Repository for user database operations.
            farmer_repository: Repository for farmer database operations.
            farm_image_repository: Repository for farm image operations.
            farm_video_repository: Repository for farm video operations.
            bank_account_repository: Repository for bank account operations.
            email_service: Service for sending emails.
        """
        self.user_repo = user_repository
        self.farmer_repo = farmer_repository
        self.image_repo = farm_image_repository
        self.video_repo = farm_video_repository
        self.bank_repo = bank_account_repository
        self.email_service = email_service

    def register_farmer(self, farmer_data: FarmerCreate) -> FarmerRegistrationResult:
        """Register a new farmer.

        Args:
            farmer_data: Farmer registration data.

        Returns:
            FarmerRegistrationResult with success status and IDs or error.
        """
        # Check if email already exists
        if self.user_repo.email_exists(farmer_data.email):
            return FarmerRegistrationResult(
                success=False,
                error="An account with this email already exists",
            )

        # Hash password
        password_hash = hash_password(farmer_data.password)

        # Generate verification token
        verification_token = generate_verification_token()
        verification_expires = get_verification_expiry(hours=24)

        # Create user in database with farmer role
        try:
            user = self.user_repo.create(
                email=farmer_data.email,
                password_hash=password_hash,
                full_name=farmer_data.full_name,
                phone=farmer_data.phone,
                verification_token=verification_token,
                verification_expires_at=verification_expires,
                role="farmer",
                date_of_birth=farmer_data.date_of_birth,
            )
        except Exception as e:
            return FarmerRegistrationResult(
                success=False,
                error=f"Failed to create user: {str(e)}",
            )

        # Create farmer profile
        try:
            farmer = self.farmer_repo.create(
                user_id=user.id,
                farm_name=farmer_data.farm_name,
            )
        except Exception as e:
            # Rollback would be needed here in production
            return FarmerRegistrationResult(
                success=False,
                error=f"Failed to create farmer profile: {str(e)}",
            )

        # Send verification email
        self.email_service.send_verification_email(
            to_email=user.email,
            full_name=user.full_name,
            verification_token=verification_token,
        )

        return FarmerRegistrationResult(
            success=True,
            user_id=user.id,
            farmer_id=farmer.id,
            email=user.email,
        )

    def get_farmer_by_user_id(self, user_id: UUID) -> FarmerInDB | None:
        """Get a farmer by user ID.

        Args:
            user_id: User's UUID.

        Returns:
            FarmerInDB if found, None otherwise.
        """
        return self.farmer_repo.get_by_user_id(user_id)

    def get_farmer_profile(
        self, user: UserInDB, farmer: FarmerInDB
    ) -> FarmerProfileResponse:
        """Get complete farmer profile with media and bank account status.

        Args:
            user: User database model.
            farmer: Farmer database model.

        Returns:
            Complete FarmerProfileResponse.
        """
        # Get farm images
        images = self.image_repo.get_by_farmer_id(farmer.id)
        image_responses = [
            FarmImageResponse(
                id=img.id,
                image_url=img.image_url,
                caption=img.caption,
                alt_text=img.alt_text,
                display_order=img.display_order,
                is_primary=img.is_primary,
                created_at=img.created_at,
            )
            for img in images
        ]

        # Get farm videos
        videos = self.video_repo.get_by_farmer_id(farmer.id)
        video_responses = [
            FarmVideoResponse(
                id=vid.id,
                video_url=vid.video_url,
                video_platform=vid.video_platform,
                video_id=vid.video_id,
                title=vid.title,
                display_order=vid.display_order,
                created_at=vid.created_at,
            )
            for vid in videos
        ]

        # Get bank account status
        bank_account = self.bank_repo.get_by_farmer_id(farmer.id)

        return FarmerProfileResponse(
            id=farmer.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            date_of_birth=user.date_of_birth,
            profile_picture_url=user.profile_picture_url,
            farm_name=farmer.farm_name,
            farm_description=farmer.farm_description,
            farm_street=farmer.farm_street,
            farm_city=farmer.farm_city,
            farm_state=farmer.farm_state,
            farm_zip_code=farmer.farm_zip_code,
            farming_practices=farmer.farming_practices,
            farm_images=image_responses,
            farm_videos=video_responses,
            has_bank_account=bank_account is not None,
            bank_account_last_four=bank_account.account_last_four
            if bank_account
            else None,
            profile_completed=farmer.profile_completed,
            profile_completion_step=farmer.profile_completion_step,
            created_at=farmer.created_at,
        )

    def update_farm_details(
        self, farmer_id: UUID, update_data: FarmDetailsUpdate
    ) -> ProfileUpdateResult:
        """Update farm details.

        Args:
            farmer_id: Farmer's UUID.
            update_data: Farm update data.

        Returns:
            ProfileUpdateResult with success status.
        """
        # Convert farming practices to strings if provided
        practices = None
        if update_data.farming_practices is not None:
            practices = [p.value for p in update_data.farming_practices]

        result = self.farmer_repo.update_farm_details(
            farmer_id=farmer_id,
            farm_name=update_data.farm_name,
            farm_description=update_data.farm_description,
            farm_street=update_data.farm_street,
            farm_city=update_data.farm_city,
            farm_state=update_data.farm_state,
            farm_zip_code=update_data.farm_zip_code,
            farming_practices=practices,
        )

        if result is None:
            return ProfileUpdateResult(success=False, error="Failed to update farm details")

        # Update profile completion step if at step 1
        if result.profile_completion_step < 2:
            self._update_completion_step(farmer_id, 2)

        return ProfileUpdateResult(success=True)

    # =========================================================================
    # Farm Images
    # =========================================================================

    def add_farm_image(
        self, farmer_id: UUID, image_data: FarmImageCreate
    ) -> FarmImageResponse | str:
        """Add a farm image.

        Args:
            farmer_id: Farmer's UUID.
            image_data: Image data.

        Returns:
            FarmImageResponse if successful, error string otherwise.
        """
        # Check image limit
        count = self.image_repo.count_by_farmer_id(farmer_id)
        if count >= self.image_repo.MAX_IMAGES:
            return f"Maximum of {self.image_repo.MAX_IMAGES} images allowed"

        try:
            image = self.image_repo.create(
                farmer_id=farmer_id,
                image_url=image_data.image_url,
                caption=image_data.caption,
                alt_text=image_data.alt_text,
                is_primary=image_data.is_primary,
            )

            return FarmImageResponse(
                id=image.id,
                image_url=image.image_url,
                caption=image.caption,
                alt_text=image.alt_text,
                display_order=image.display_order,
                is_primary=image.is_primary,
                created_at=image.created_at,
            )
        except Exception as e:
            return f"Failed to add image: {str(e)}"

    def delete_farm_image(self, farmer_id: UUID, image_id: UUID) -> ProfileUpdateResult:
        """Delete a farm image.

        Args:
            farmer_id: Farmer's UUID.
            image_id: Image UUID.

        Returns:
            ProfileUpdateResult with success status.
        """
        # Verify image belongs to farmer
        image = self.image_repo.get_by_id(image_id)
        if image is None or image.farmer_id != farmer_id:
            return ProfileUpdateResult(success=False, error="Image not found")

        if not self.image_repo.delete(image_id):
            return ProfileUpdateResult(success=False, error="Failed to delete image")

        return ProfileUpdateResult(success=True)

    def reorder_farm_images(
        self, farmer_id: UUID, image_ids: list[UUID]
    ) -> ProfileUpdateResult:
        """Reorder farm images.

        Args:
            farmer_id: Farmer's UUID.
            image_ids: List of image IDs in desired order.

        Returns:
            ProfileUpdateResult with success status.
        """
        self.image_repo.update_order(farmer_id, image_ids)
        return ProfileUpdateResult(success=True)

    # =========================================================================
    # Farm Videos
    # =========================================================================

    def add_farm_video(
        self, farmer_id: UUID, video_data: FarmVideoCreate
    ) -> FarmVideoResponse | str:
        """Add a farm video.

        Args:
            farmer_id: Farmer's UUID.
            video_data: Video data.

        Returns:
            FarmVideoResponse if successful, error string otherwise.
        """
        # Check video limit
        count = self.video_repo.count_by_farmer_id(farmer_id)
        if count >= self.video_repo.MAX_VIDEOS:
            return f"Maximum of {self.video_repo.MAX_VIDEOS} videos allowed"

        try:
            video = self.video_repo.create(
                farmer_id=farmer_id,
                video_url=video_data.video_url,
                title=video_data.title,
            )

            return FarmVideoResponse(
                id=video.id,
                video_url=video.video_url,
                video_platform=video.video_platform,
                video_id=video.video_id,
                title=video.title,
                display_order=video.display_order,
                created_at=video.created_at,
            )
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Failed to add video: {str(e)}"

    def delete_farm_video(self, farmer_id: UUID, video_id: UUID) -> ProfileUpdateResult:
        """Delete a farm video.

        Args:
            farmer_id: Farmer's UUID.
            video_id: Video UUID.

        Returns:
            ProfileUpdateResult with success status.
        """
        # Verify video belongs to farmer
        video = self.video_repo.get_by_id(video_id)
        if video is None or video.farmer_id != farmer_id:
            return ProfileUpdateResult(success=False, error="Video not found")

        if not self.video_repo.delete(video_id):
            return ProfileUpdateResult(success=False, error="Failed to delete video")

        return ProfileUpdateResult(success=True)

    # =========================================================================
    # Bank Account
    # =========================================================================

    def add_or_update_bank_account(
        self, farmer_id: UUID, account_data: BankAccountCreate
    ) -> BankAccountResponse | str:
        """Add or update bank account.

        Args:
            farmer_id: Farmer's UUID.
            account_data: Bank account data.

        Returns:
            BankAccountResponse if successful, error string otherwise.
        """
        existing = self.bank_repo.get_by_farmer_id(farmer_id)

        try:
            if existing:
                # Update existing account
                account = self.bank_repo.update(
                    farmer_id=farmer_id,
                    account_holder_name=account_data.account_holder_name,
                    account_number=account_data.account_number,
                    routing_number=account_data.routing_number,
                    bank_name=account_data.bank_name,
                    account_type=account_data.account_type.value,
                )
            else:
                # Create new account
                account = self.bank_repo.create(
                    farmer_id=farmer_id,
                    account_holder_name=account_data.account_holder_name,
                    account_number=account_data.account_number,
                    routing_number=account_data.routing_number,
                    bank_name=account_data.bank_name,
                    account_type=account_data.account_type.value,
                )

            if account is None:
                return "Failed to save bank account"

            # Update profile completion step if at step 3
            farmer = self.farmer_repo.get_by_id(farmer_id)
            if farmer and farmer.profile_completion_step < 4:
                self._update_completion_step(farmer_id, 4)
                # Mark profile as complete
                self.farmer_repo.update_profile_completion(farmer_id, 4, completed=True)

            return BankAccountResponse(
                id=account.id,
                account_holder_name=account.account_holder_name,
                account_last_four=account.account_last_four,
                bank_name=account.bank_name,
                account_type=account.account_type,
                is_verified=account.is_verified,
                created_at=account.created_at,
            )
        except Exception as e:
            return f"Failed to save bank account: {str(e)}"

    def get_bank_account(self, farmer_id: UUID) -> BankAccountResponse | None:
        """Get bank account for a farmer.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            BankAccountResponse if found, None otherwise.
        """
        account = self.bank_repo.get_by_farmer_id(farmer_id)
        if account is None:
            return None

        return BankAccountResponse(
            id=account.id,
            account_holder_name=account.account_holder_name,
            account_last_four=account.account_last_four,
            bank_name=account.bank_name,
            account_type=account.account_type,
            is_verified=account.is_verified,
            created_at=account.created_at,
        )

    # =========================================================================
    # Profile Completion
    # =========================================================================

    def _update_completion_step(self, farmer_id: UUID, step: int) -> None:
        """Update profile completion step.

        Args:
            farmer_id: Farmer's UUID.
            step: New completion step.
        """
        farmer = self.farmer_repo.get_by_id(farmer_id)
        if farmer and farmer.profile_completion_step < step:
            self.farmer_repo.update_profile_completion(
                farmer_id, step, completed=(step >= 4)
            )

    def get_completion_status(self, farmer_id: UUID) -> dict:
        """Get profile completion status.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            Dictionary with completion status.
        """
        farmer = self.farmer_repo.get_by_id(farmer_id)
        if farmer is None:
            return {"profile_completed": False, "current_step": 0, "steps": {}}

        has_images = self.image_repo.count_by_farmer_id(farmer_id) > 0
        has_bank = self.bank_repo.get_by_farmer_id(farmer_id) is not None

        return {
            "profile_completed": farmer.profile_completed,
            "current_step": farmer.profile_completion_step,
            "steps": {
                "basic_info": True,  # Always true after registration
                "farm_details": bool(farmer.farm_description),
                "farm_media": has_images,
                "bank_account": has_bank,
            },
        }
