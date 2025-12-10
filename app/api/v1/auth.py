"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.security import PasswordValidator
from app.db.supabase import get_supabase_client
from app.models.user import UserCreate, UserResponse, VerifyEmailRequest
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.email import MockEmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegistrationResponse(BaseModel):
    """Response model for successful registration."""

    message: str
    user: UserResponse


class EmailVerificationResponse(BaseModel):
    """Response model for email verification."""

    message: str
    verified: bool


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str


def get_auth_service() -> AuthService:
    """Dependency to get the auth service."""
    db_client = get_supabase_client()
    user_repo = UserRepository(db_client)
    email_service = MockEmailService()
    return AuthService(user_repo, email_service)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
    },
    summary="Register a new user",
    description="Register a new user account. A verification email will be sent.",
)
def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegistrationResponse:
    """Register a new user account.

    Creates a new user account and sends a verification email.

    Args:
        user_data: User registration data including email, password, name, and phone.
        auth_service: Injected auth service.

    Returns:
        RegistrationResponse with success message and user data.

    Raises:
        HTTPException: If registration fails due to validation or duplicate email.
    """
    result = auth_service.register_user(user_data)

    if not result.success:
        # Determine appropriate status code based on error
        if "already exists" in (result.error or ""):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result.error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return RegistrationResponse(
        message="Registration successful. Please check your email to verify your account.",
        user=result.user,  # type: ignore
    )


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
    summary="Verify email address",
    description="Verify a user's email address using the token sent via email.",
)
def verify_email(
    request_data: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> EmailVerificationResponse:
    """Verify a user's email address.

    Args:
        request_data: Request containing the verification token.
        auth_service: Injected auth service.

    Returns:
        EmailVerificationResponse with verification status.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    result = auth_service.verify_email(request_data.token)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return EmailVerificationResponse(
        message=result.message,
        verified=True,
    )


@router.get(
    "/verify-email",
    response_model=EmailVerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
    summary="Verify email address (GET)",
    description="Verify email via link click. Redirects to success/error page.",
)
def verify_email_get(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
) -> EmailVerificationResponse:
    """Verify email address via GET request (for email link clicks).

    Args:
        token: Verification token from the email link.
        auth_service: Injected auth service.

    Returns:
        EmailVerificationResponse with verification status.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    result = auth_service.verify_email(token)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return EmailVerificationResponse(
        message=result.message,
        verified=True,
    )


@router.get(
    "/password-requirements",
    summary="Get password requirements",
    description="Get the password requirements for registration.",
)
def get_password_requirements() -> dict:
    """Get password requirements for registration.

    Returns:
        Dictionary with password requirements.
    """
    return {
        "min_length": PasswordValidator.MIN_LENGTH,
        "requirements": [desc for _, desc in PasswordValidator.REQUIREMENTS],
        "message": PasswordValidator.get_requirements_message(),
    }
