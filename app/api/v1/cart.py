"""Cart API endpoints for shopping cart management (US-013)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.cart import (
    AddToCartRequest,
    CartItemAddedResponse,
    CartOperationResponse,
    CartResponse,
    EmptyCartResponse,
    UpdateCartItemRequest,
)
from app.models.user import UserInDB
from app.repositories.cart import CartRepository
from app.repositories.farmer import FarmerRepository
from app.repositories.product import ProductRepository
from app.services.cart import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_service(
    db_client: Client = Depends(get_supabase_client),
) -> CartService:
    """Get CartService instance.

    Args:
        db_client: Supabase client from dependency injection.

    Returns:
        CartService instance.
    """
    cart_repo = CartRepository(db_client)
    product_repo = ProductRepository(db_client)
    farmer_repo = FarmerRepository(db_client)
    return CartService(cart_repo, product_repo, farmer_repo)


# ============================================================================
# Cart Endpoints
# ============================================================================


@router.get(
    "",
    response_model=CartResponse | EmptyCartResponse,
    summary="Get shopping cart",
    description="Get the current user's shopping cart with all items and summary.",
)
async def get_cart(
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> CartResponse | EmptyCartResponse:
    """Get the current user's shopping cart."""
    return cart_service.get_cart(current_user.id)


@router.post(
    "/items",
    response_model=CartItemAddedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product to the shopping cart. If product already in cart, quantity is updated.",
)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> CartItemAddedResponse:
    """Add an item to the shopping cart."""
    result = cart_service.add_to_cart(current_user.id, request)

    if isinstance(result, CartOperationResponse) and not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return result


@router.put(
    "/items/{item_id}",
    response_model=CartOperationResponse,
    summary="Update cart item quantity",
    description="Update the quantity of an item in the cart.",
)
async def update_cart_item(
    item_id: UUID,
    request: UpdateCartItemRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> CartOperationResponse:
    """Update a cart item's quantity."""
    result = cart_service.update_cart_item(current_user.id, item_id, request)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return result


@router.delete(
    "/items/{item_id}",
    response_model=CartOperationResponse,
    summary="Remove item from cart",
    description="Remove an item from the shopping cart.",
)
async def remove_from_cart(
    item_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> CartOperationResponse:
    """Remove an item from the cart."""
    result = cart_service.remove_from_cart(current_user.id, item_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return result


@router.delete(
    "",
    response_model=CartOperationResponse,
    summary="Clear cart",
    description="Remove all items from the shopping cart.",
)
async def clear_cart(
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> CartOperationResponse:
    """Clear all items from the cart."""
    return cart_service.clear_cart(current_user.id)


@router.get(
    "/count",
    summary="Get cart item count",
    description="Get the total number of items in the cart.",
)
async def get_cart_count(
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> dict:
    """Get the total number of items in cart."""
    count = cart_service.get_cart_count(current_user.id)
    return {"count": count}


@router.get(
    "/validate",
    summary="Validate cart stock",
    description="Check all cart items against current stock levels. Useful before checkout.",
)
async def validate_cart(
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> dict:
    """Validate cart items against current stock."""
    issues = cart_service.validate_cart_stock(current_user.id)
    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


@router.post(
    "/checkout",
    summary="Checkout cart",
    description="Process checkout - convert cart items to an order.",
)
async def checkout_cart(
    current_user: UserInDB = Depends(get_current_active_user),
    cart_service: CartService = Depends(get_cart_service),
) -> dict:
    """Process checkout and create an order from cart items."""
    result = cart_service.checkout(current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Checkout failed"),
        )

    return result
