"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import PasswordValidator
from app.db.supabase import get_supabase_client
from app.models.farmer import FarmerCreate, FarmerRegistrationResponse
from app.models.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    TokenRefreshRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from app.repositories.farm_image import FarmImageRepository
from app.repositories.farm_video import FarmVideoRepository
from app.repositories.farmer import FarmerRepository
from app.repositories.farmer_bank_account import FarmerBankAccountRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.email import get_email_service
from app.services.farmer import FarmerService

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
    settings = get_settings()
    base_url = f"http://{settings.host}:{settings.port}"
    email_service = get_email_service(base_url)
    return AuthService(user_repo, email_service)


def get_farmer_service() -> FarmerService:
    """Dependency to get the farmer service."""
    db_client = get_supabase_client()
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
    "/farmer/register",
    response_model=FarmerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        409: {"model": ErrorResponse, "description": "Email already exists"},
    },
    summary="Register a new farmer",
    description="Register a new farmer account. A verification email will be sent. Farmer must be 18+.",
)
def register_farmer(
    farmer_data: FarmerCreate,
    farmer_service: FarmerService = Depends(get_farmer_service),
) -> FarmerRegistrationResponse:
    """Register a new farmer account.

    Creates a new farmer account with both user and farmer profile.
    Sends a verification email.

    Args:
        farmer_data: Farmer registration data including personal info and farm name.
        farmer_service: Injected farmer service.

    Returns:
        FarmerRegistrationResponse with success message and IDs.

    Raises:
        HTTPException: If registration fails due to validation or duplicate email.
    """
    result = farmer_service.register_farmer(farmer_data)

    if not result.success:
        if "already exists" in (result.error or ""):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result.error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return FarmerRegistrationResponse(
        message="Farmer registration successful. Please check your email to verify your account.",
        user_id=result.user_id,  # type: ignore
        farmer_id=result.farmer_id,  # type: ignore
        email=result.email,  # type: ignore
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


class LoginResponse(BaseModel):
    """Response model for successful login."""

    message: str
    user: UserResponse
    token: Token


class MessageResponse(BaseModel):
    """Response model for simple message responses."""

    message: str


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Email not verified"},
        423: {"model": ErrorResponse, "description": "Account locked"},
    },
    summary="Login user",
    description="Authenticate user with email and password, returns JWT tokens.",
)
def login(
    login_data: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate user and return tokens.

    Args:
        login_data: User login credentials (email and password).
        response: FastAPI response object for setting cookies.
        auth_service: Injected auth service.

    Returns:
        LoginResponse with user data and tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    result = auth_service.login_user(login_data)

    if not result.success:
        error_msg = result.error or "Login failed"

        if "locked" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=error_msg,
            )
        elif "verify" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    # Set access token as HTTP-only cookie for web page authentication
    response.set_cookie(
        key="access_token",
        value=result.token.access_token,  # type: ignore
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600,  # 1 hour
        path="/",
    )

    return LoginResponse(
        message="Login successful",
        user=result.user,  # type: ignore
        token=result.token,  # type: ignore
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Clear authentication cookies and logout user.",
)
def logout(response: Response) -> MessageResponse:
    """Logout user by clearing authentication cookies.

    Args:
        response: FastAPI response object for clearing cookies.

    Returns:
        MessageResponse confirming logout.
    """
    response.delete_cookie(key="access_token", path="/")
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/refresh-token",
    response_model=Token,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
)
def refresh_token(
    request_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Refresh access token.

    Args:
        request_data: Request containing the refresh token.
        auth_service: Injected auth service.

    Returns:
        New Token with access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    result = auth_service.refresh_access_token(request_data.refresh_token)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Invalid refresh token",
        )

    return result.token  # type: ignore


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Request a password reset email. Always returns success to prevent email enumeration.",
)
def forgot_password(
    request_data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Request password reset email.

    Args:
        request_data: Request containing the email address.
        auth_service: Injected auth service.

    Returns:
        MessageResponse with success message.
    """
    result = auth_service.request_password_reset(request_data.email)
    return MessageResponse(message=result.message)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
    summary="Reset password",
    description="Reset password using the token from the reset email.",
)
def reset_password(
    request_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Reset user password.

    Args:
        request_data: Request containing reset token and new password.
        auth_service: Injected auth service.

    Returns:
        MessageResponse with success or error message.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    result = auth_service.reset_password(request_data.token, request_data.new_password)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return MessageResponse(message=result.message)
