"""FastAPI dependencies for authentication and authorization."""

from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from supabase import Client

from app.core.security import verify_token
from app.db.supabase import get_supabase_client
from app.models.user import UserInDB
from app.repositories.user import UserRepository

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_repository(
    db_client: Client = Depends(get_supabase_client),
) -> UserRepository:
    """Get a UserRepository instance.

    Args:
        db_client: Supabase client from dependency injection.

    Returns:
        UserRepository instance.
    """
    return UserRepository(db_client)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserInDB:
    """Get the current authenticated user from JWT token.

    This dependency extracts the JWT token from the Authorization header,
    validates it, and returns the corresponding user from the database.

    Args:
        token: JWT access token from Authorization header.
        user_repo: UserRepository for database access.

    Returns:
        UserInDB: The authenticated user.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError as e:
        raise credentials_exception from e

    # Get user from database
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before accessing this resource.",
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Get the current active user (not locked).

    Args:
        current_user: User from get_current_user dependency.

    Returns:
        UserInDB: The authenticated and active user.

    Raises:
        HTTPException: 423 if user account is locked.
    """
    from datetime import UTC, datetime

    if current_user.locked_until and current_user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked. Please try again later.",
        )

    return current_user


# =============================================================================
# Cookie-based authentication for web pages
# =============================================================================


async def get_current_user_from_cookie(
    request: Request,
    access_token: str | None = Cookie(default=None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserInDB | None:
    """Get the current user from cookie-based authentication.

    Returns None if not authenticated (allows page to render with login redirect).

    Args:
        request: FastAPI request object.
        access_token: JWT access token from cookie.
        user_repo: UserRepository for database access.

    Returns:
        UserInDB if authenticated, None otherwise.
    """
    if not access_token:
        return None

    # Verify the token
    payload = verify_token(access_token)
    if payload is None:
        return None

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        return None

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    # Get user from database
    user = user_repo.get_by_id(user_id)
    return user


class AuthRedirectException(Exception):
    """Exception to signal a redirect to login page."""

    def __init__(self, redirect_url: str = "/login"):
        self.redirect_url = redirect_url


async def require_auth_cookie(
    request: Request,
    current_user: UserInDB | None = Depends(get_current_user_from_cookie),
) -> UserInDB:
    """Require cookie-based authentication, redirect to login if not authenticated.

    Args:
        request: FastAPI request object.
        current_user: User from cookie auth or None.

    Returns:
        UserInDB if authenticated.

    Raises:
        AuthRedirectException: Redirect to login page if not authenticated.
        HTTPException: For HTMX requests or other auth errors.
    """
    if current_user is None:
        # For HTMX requests, return 401 so client can handle redirect
        if request.headers.get("HX-Request"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"HX-Redirect": "/login"},
            )
        # For regular browser requests, raise redirect exception
        raise AuthRedirectException("/login")

    # Check if email is verified
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    # Check if account is locked
    from datetime import UTC, datetime

    if current_user.locked_until and current_user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked",
        )

    return current_user
