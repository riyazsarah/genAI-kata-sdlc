"""Wishlist API endpoints for favorites management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.user import UserInDB

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


class ProductInfo(BaseModel):
    """Product info for wishlist item."""

    id: UUID
    name: str
    category: str | None = None
    price: float
    unit: str | None = None
    images: list[str] = []


class WishlistItemResponse(BaseModel):
    """Wishlist item response model."""

    id: UUID
    user_id: UUID
    product_id: UUID
    product: ProductInfo | None = None
    created_at: str


class WishlistResponse(BaseModel):
    """Wishlist response model."""

    items: list[WishlistItemResponse]
    total: int


class AddToWishlistRequest(BaseModel):
    """Add to wishlist request model."""

    product_id: UUID


@router.get(
    "",
    response_model=WishlistResponse,
    summary="Get wishlist",
    description="Get all items in the user's wishlist.",
)
async def get_wishlist(
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> WishlistResponse:
    """Get all wishlist items for the current user."""
    result = (
        db_client.table("wishlists")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("created_at", desc=True)
        .execute()
    )

    items = []
    for item in result.data or []:
        # Get product info
        product_result = (
            db_client.table("products")
            .select("id, name, category, price, unit, images")
            .eq("id", item["product_id"])
            .single()
            .execute()
        )

        product = None
        if product_result.data:
            p = product_result.data
            product = ProductInfo(
                id=p["id"],
                name=p["name"],
                category=p.get("category"),
                price=float(p["price"]),
                unit=p.get("unit"),
                images=p.get("images", []),
            )

        items.append(
            WishlistItemResponse(
                id=item["id"],
                user_id=item["user_id"],
                product_id=item["product_id"],
                product=product,
                created_at=item["created_at"],
            )
        )

    return WishlistResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=WishlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add to wishlist",
    description="Add a product to the user's wishlist.",
)
async def add_to_wishlist(
    request: AddToWishlistRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> WishlistItemResponse:
    """Add a product to the wishlist."""
    # Check if product exists
    product_result = (
        db_client.table("products")
        .select("id, name, category, price, unit, images")
        .eq("id", str(request.product_id))
        .single()
        .execute()
    )

    if not product_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check if already in wishlist
    existing = (
        db_client.table("wishlists")
        .select("id")
        .eq("user_id", str(current_user.id))
        .eq("product_id", str(request.product_id))
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist",
        )

    # Add to wishlist
    result = (
        db_client.table("wishlists")
        .insert(
            {
                "user_id": str(current_user.id),
                "product_id": str(request.product_id),
            }
        )
        .execute()
    )

    item = result.data[0]
    p = product_result.data

    return WishlistItemResponse(
        id=item["id"],
        user_id=item["user_id"],
        product_id=item["product_id"],
        product=ProductInfo(
            id=p["id"],
            name=p["name"],
            category=p.get("category"),
            price=float(p["price"]),
            unit=p.get("unit"),
            images=p.get("images", []),
        ),
        created_at=item["created_at"],
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove from wishlist",
    description="Remove a product from the user's wishlist.",
)
async def remove_from_wishlist(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> None:
    """Remove a product from the wishlist."""
    result = (
        db_client.table("wishlists")
        .delete()
        .eq("user_id", str(current_user.id))
        .eq("product_id", str(product_id))
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in wishlist",
        )


@router.get(
    "/check/{product_id}",
    summary="Check if product is in wishlist",
    description="Check if a specific product is in the user's wishlist.",
)
async def check_wishlist(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> dict:
    """Check if a product is in the wishlist."""
    result = (
        db_client.table("wishlists")
        .select("id")
        .eq("user_id", str(current_user.id))
        .eq("product_id", str(product_id))
        .execute()
    )

    return {"in_wishlist": len(result.data or []) > 0}
