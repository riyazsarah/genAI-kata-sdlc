"""Profile service for user profile management business logic."""

import uuid
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import UploadFile

from app.models.profile import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    CommunicationPreferences,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PreferencesUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.models.user import UserInDB
from app.repositories.address import AddressRepository
from app.repositories.payment_method import PaymentMethodRepository
from app.repositories.profile import ProfileRepository
from app.repositories.user import UserRepository

# ============================================================================
# RESULT DATACLASSES
# ============================================================================


@dataclass
class ProfileResult:
    """Result of a profile operation."""

    success: bool
    data: Any = None
    error: str | None = None


# ============================================================================
# CONSTANTS
# ============================================================================

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


# ============================================================================
# PROFILE SERVICE
# ============================================================================


class ProfileService:
    """Service for profile management operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        address_repository: AddressRepository,
        payment_repository: PaymentMethodRepository,
    ) -> None:
        """Initialize the profile service.

        Args:
            user_repository: Repository for user operations.
            profile_repository: Repository for profile operations.
            address_repository: Repository for address operations.
            payment_repository: Repository for payment method operations.
        """
        self.user_repo = user_repository
        self.profile_repo = profile_repository
        self.address_repo = address_repository
        self.payment_repo = payment_repository

    # ========================================================================
    # PROFILE OPERATIONS
    # ========================================================================

    def get_profile(self, user: UserInDB) -> ProfileResult:
        """Get complete user profile with addresses and payment methods.

        Args:
            user: Current authenticated user.

        Returns:
            ProfileResult with ProfileResponse data.
        """
        # Get addresses
        addresses = self.address_repo.get_all_for_user(user.id)
        address_responses = [
            AddressResponse(
                id=addr.id,
                label=addr.label,
                street=addr.street,
                city=addr.city,
                state=addr.state,
                zip_code=addr.zip_code,
                delivery_instructions=addr.delivery_instructions,
                is_default=addr.is_default,
                created_at=addr.created_at,
            )
            for addr in addresses
        ]

        # Get payment methods
        payment_methods = self.payment_repo.get_all_for_user(user.id)
        payment_responses = [
            PaymentMethodResponse(
                id=pm.id,
                payment_type=pm.payment_type,
                provider=pm.provider,
                last_four=pm.last_four,
                expiry_month=pm.expiry_month,
                expiry_year=pm.expiry_year,
                is_default=pm.is_default,
                created_at=pm.created_at,
            )
            for pm in payment_methods
        ]

        # Build profile response
        profile = ProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            date_of_birth=user.date_of_birth,
            profile_picture_url=user.profile_picture_url,
            email_verified=user.email_verified,
            dietary_preferences=user.dietary_preferences,
            communication_preferences=CommunicationPreferences(
                **user.communication_preferences
            ),
            addresses=address_responses,
            payment_methods=payment_responses,
            created_at=user.created_at,
        )

        return ProfileResult(success=True, data=profile)

    def update_profile(self, user: UserInDB, data: ProfileUpdate) -> ProfileResult:
        """Update user profile basic information.

        Args:
            user: Current authenticated user.
            data: Profile update data.

        Returns:
            ProfileResult with updated profile.
        """
        updated_user = self.profile_repo.update_profile(
            user_id=user.id,
            full_name=data.full_name,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
        )

        if not updated_user:
            return ProfileResult(success=False, error="Failed to update profile")

        # Return full profile
        return self.get_profile(updated_user)

    def upload_avatar(
        self, user: UserInDB, file: UploadFile, storage_client: Any
    ) -> ProfileResult:
        """Upload and update user's profile picture.

        Args:
            user: Current authenticated user.
            file: Uploaded image file.
            storage_client: Supabase storage client.

        Returns:
            ProfileResult with avatar URL.
        """
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            return ProfileResult(
                success=False,
                error=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
            )

        # Read file content
        content = file.file.read()

        # Validate file size
        if len(content) > MAX_IMAGE_SIZE:
            return ProfileResult(
                success=False,
                error=f"File too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
            )

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
        filename = f"{user.id}/{uuid.uuid4()}.{file_ext}"

        try:
            # Upload to Supabase Storage
            bucket = storage_client.from_("avatars")

            # Delete old avatar if exists
            if user.profile_picture_url:
                old_path = user.profile_picture_url.split("/avatars/")[-1]
                try:
                    bucket.remove([old_path])
                except Exception:
                    pass  # Ignore errors deleting old file

            # Upload new avatar
            bucket.upload(filename, content, {"content-type": file.content_type})

            # Get public URL
            public_url = bucket.get_public_url(filename)

            # Update user profile
            updated_user = self.profile_repo.update_avatar_url(user.id, public_url)

            if not updated_user:
                return ProfileResult(success=False, error="Failed to update profile")

            return ProfileResult(
                success=True,
                data={"message": "Avatar uploaded successfully", "url": public_url},
            )

        except Exception as e:
            return ProfileResult(success=False, error=f"Upload failed: {str(e)}")

    # ========================================================================
    # ADDRESS OPERATIONS
    # ========================================================================

    def add_address(self, user: UserInDB, data: AddressCreate) -> ProfileResult:
        """Add a new address for the user.

        Args:
            user: Current authenticated user.
            data: Address creation data.

        Returns:
            ProfileResult with created address.
        """
        try:
            address = self.address_repo.create(user.id, data)
            response = AddressResponse(
                id=address.id,
                label=address.label,
                street=address.street,
                city=address.city,
                state=address.state,
                zip_code=address.zip_code,
                delivery_instructions=address.delivery_instructions,
                is_default=address.is_default,
                created_at=address.created_at,
            )
            return ProfileResult(success=True, data=response)
        except Exception as e:
            return ProfileResult(success=False, error=str(e))

    def update_address(
        self, user: UserInDB, address_id: UUID, data: AddressUpdate
    ) -> ProfileResult:
        """Update an existing address.

        Args:
            user: Current authenticated user.
            address_id: Address UUID.
            data: Address update data.

        Returns:
            ProfileResult with updated address.
        """
        address = self.address_repo.update(address_id, user.id, data)

        if not address:
            return ProfileResult(success=False, error="Address not found")

        response = AddressResponse(
            id=address.id,
            label=address.label,
            street=address.street,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
            delivery_instructions=address.delivery_instructions,
            is_default=address.is_default,
            created_at=address.created_at,
        )
        return ProfileResult(success=True, data=response)

    def delete_address(self, user: UserInDB, address_id: UUID) -> ProfileResult:
        """Delete an address.

        Args:
            user: Current authenticated user.
            address_id: Address UUID.

        Returns:
            ProfileResult indicating success or failure.
        """
        deleted = self.address_repo.delete(address_id, user.id)

        if not deleted:
            return ProfileResult(success=False, error="Address not found")

        return ProfileResult(success=True, data={"message": "Address deleted"})

    # ========================================================================
    # PAYMENT METHOD OPERATIONS
    # ========================================================================

    def add_payment_method(
        self, user: UserInDB, data: PaymentMethodCreate
    ) -> ProfileResult:
        """Add a new payment method for the user.

        Args:
            user: Current authenticated user.
            data: Payment method creation data.

        Returns:
            ProfileResult with created payment method.
        """
        try:
            # Tokenize card number (mock implementation)
            token = self._tokenize_card(data.card_number) if data.card_number else str(
                uuid.uuid4()
            )
            last_four = data.card_number[-4:] if data.card_number else None

            payment = self.payment_repo.create(
                user_id=user.id,
                payment_type=data.payment_type,
                provider=data.provider,
                token=token,
                last_four=last_four,
                expiry_month=data.expiry_month,
                expiry_year=data.expiry_year,
                is_default=data.is_default,
            )

            response = PaymentMethodResponse(
                id=payment.id,
                payment_type=payment.payment_type,
                provider=payment.provider,
                last_four=payment.last_four,
                expiry_month=payment.expiry_month,
                expiry_year=payment.expiry_year,
                is_default=payment.is_default,
                created_at=payment.created_at,
            )
            return ProfileResult(success=True, data=response)
        except Exception as e:
            return ProfileResult(success=False, error=str(e))

    def delete_payment_method(
        self, user: UserInDB, payment_id: UUID
    ) -> ProfileResult:
        """Delete a payment method.

        Args:
            user: Current authenticated user.
            payment_id: Payment method UUID.

        Returns:
            ProfileResult indicating success or failure.
        """
        deleted = self.payment_repo.delete(payment_id, user.id)

        if not deleted:
            return ProfileResult(success=False, error="Payment method not found")

        return ProfileResult(success=True, data={"message": "Payment method removed"})

    # ========================================================================
    # PREFERENCES OPERATIONS
    # ========================================================================

    def update_preferences(
        self, user: UserInDB, data: PreferencesUpdate
    ) -> ProfileResult:
        """Update user preferences.

        Args:
            user: Current authenticated user.
            data: Preferences update data.

        Returns:
            ProfileResult with updated preferences.
        """
        dietary = None
        communication = None

        if data.dietary_preferences is not None:
            dietary = [pref.value for pref in data.dietary_preferences]

        if data.communication_preferences is not None:
            communication = data.communication_preferences.model_dump()

        updated_user = self.profile_repo.update_preferences(
            user_id=user.id,
            dietary_preferences=dietary,
            communication_preferences=communication,
        )

        if not updated_user:
            return ProfileResult(success=False, error="Failed to update preferences")

        return ProfileResult(
            success=True,
            data={
                "dietary_preferences": updated_user.dietary_preferences,
                "communication_preferences": updated_user.communication_preferences,
                "message": "Preferences updated successfully",
            },
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _tokenize_card(self, card_number: str) -> str:
        """Mock tokenization for card numbers.

        In production, this would call a payment processor (Stripe, etc.)
        to tokenize the card and return a token.

        Args:
            card_number: Raw card number.

        Returns:
            Mock token string.
        """
        # This is a mock implementation for MVP
        # In production, integrate with Stripe/Braintree
        return f"tok_{uuid.uuid4().hex[:24]}"
