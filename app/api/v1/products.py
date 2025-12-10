"""Product management API endpoints for farmers."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.product import (
    InventoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductStatus,
    ProductUpdate,
    ThresholdUpdate,
)
from app.models.user import UserInDB
from app.repositories.product import ProductRepository
from app.services.product import ProductService

router = APIRouter(prefix="/farmers/products", tags=["Product Management"])


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str


class ProductUpdateResponse(BaseModel):
    """Response model for successful product update."""

    message: str
    product: ProductResponse


class ImageRemoveResponse(BaseModel):
    """Response model for image removal."""

    message: str
    product: ProductResponse


class DeleteResponse(BaseModel):
    """Response model for product deletion."""

    message: str


class LowStockListResponse(BaseModel):
    """Response model for low-stock products list."""

    products: list[ProductResponse]
    total: int


class ProductCreateResponse(BaseModel):
    """Response model for successful product creation."""

    message: str
    product: ProductResponse


def get_product_service() -> ProductService:
    """Dependency to get the product service."""
    db_client = get_supabase_client()
    product_repo = ProductRepository(db_client)
    return ProductService(product_repo)


# =============================================================================
# US-006: Add Product Listing
# =============================================================================


@router.post(
    "",
    response_model=ProductCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="Create new product",
    description="Create a new product listing for the authenticated farmer.",
)
async def create_product(
    product_data: ProductCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductCreateResponse:
    """Create a new product for the authenticated farmer.

    Args:
        product_data: ProductCreate with product details.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ProductCreateResponse with success message and created product.

    Raises:
        HTTPException: 400 for validation errors.
    """
    result = product_service.create_product(
        farmer_id=current_user.id,
        product_data=product_data,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return ProductCreateResponse(
        message="Product created successfully",
        product=result.product,  # type: ignore
    )


@router.get(
    "",
    response_model=ProductListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="List farmer's products",
    description="Get a paginated list of products belonging to the authenticated farmer.",
)
async def list_farmer_products(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: ProductStatus | None = Query(
        default=None, alias="status", description="Filter by status"
    ),
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    """Get all products for the authenticated farmer.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status_filter: Optional status filter.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ProductListResponse with paginated products.
    """
    result = product_service.get_farmer_products(
        farmer_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )

    return ProductListResponse(
        products=result.products or [],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Get product details",
    description="Get details of a specific product for editing. Only returns products owned by the farmer.",
)
async def get_product(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Get a product by ID for the authenticated farmer.

    Args:
        product_id: Product's UUID.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ProductResponse with product details.

    Raises:
        HTTPException: 404 if product not found or not owned by farmer.
    """
    result = product_service.get_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error,
        )

    return result.product  # type: ignore


@router.put(
    "/{product_id}",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or version conflict"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
        409: {"model": ErrorResponse, "description": "Version conflict"},
    },
    summary="Update product",
    description="Update an existing product. Requires version field for optimistic locking.",
)
async def update_product(
    product_id: UUID,
    update_data: ProductUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Update a product owned by the authenticated farmer.

    Uses optimistic locking to prevent concurrent edit conflicts.
    The version field must match the current product version.

    Args:
        product_id: Product's UUID.
        update_data: ProductUpdate with fields to update.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ProductUpdateResponse with success message and updated product.

    Raises:
        HTTPException: 400 for validation errors, 404 if not found, 409 for version conflict.
    """
    result = product_service.update_product(
        farmer_id=current_user.id,
        product_id=product_id,
        update_data=update_data,
    )

    if not result.success:
        # Determine appropriate status code
        error = result.error or "Unknown error"

        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        elif "version conflict" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

    return ProductUpdateResponse(
        message="Product updated successfully",
        product=result.product,  # type: ignore
    )


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=ImageRemoveResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product or image not found"},
    },
    summary="Remove product image",
    description="Remove a specific image from a product.",
)
async def remove_product_image(
    product_id: UUID,
    image_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ImageRemoveResponse:
    """Remove an image from a product by image ID.

    Args:
        product_id: Product's UUID.
        image_id: Image's UUID.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ImageRemoveResponse with success message and updated product.

    Raises:
        HTTPException: 404 if product or image not found.
    """
    result = product_service.remove_product_image_by_id(
        farmer_id=current_user.id,
        product_id=product_id,
        image_id=image_id,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error,
        )

    return ImageRemoveResponse(
        message="Image removed successfully",
        product=result.product,  # type: ignore
    )


@router.delete(
    "/{product_id}/images",
    response_model=ImageRemoveResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product or image not found"},
    },
    summary="Remove product image by URL",
    description="Remove a specific image from a product using the image URL.",
)
async def remove_product_image_by_url(
    product_id: UUID,
    image_url: str = Query(..., description="URL of the image to remove"),
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ImageRemoveResponse:
    """Remove an image from a product by image URL.

    Args:
        product_id: Product's UUID.
        image_url: Image URL to remove.
        current_user: Currently authenticated user.
        product_service: Injected product service.

    Returns:
        ImageRemoveResponse with success message and updated product.

    Raises:
        HTTPException: 404 if product or image not found.
    """
    result = product_service.remove_product_image(
        farmer_id=current_user.id,
        product_id=product_id,
        image_url=image_url,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error,
        )

    return ImageRemoveResponse(
        message="Image removed successfully",
        product=result.product,  # type: ignore
    )


# =============================================================================
# US-008: Remove/Archive Product Listing
# =============================================================================


@router.delete(
    "/{product_id}",
    response_model=DeleteResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Product has pending orders"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Delete product",
    description="Permanently delete a product. Cannot delete products with pending orders.",
)
async def delete_product(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> DeleteResponse:
    """Permanently delete a product."""
    result = product_service.delete_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return DeleteResponse(message="Product deleted successfully")


@router.put(
    "/{product_id}/archive",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Product already archived"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Archive product",
    description="Archive a product (soft delete). Archived products are hidden from consumers.",
)
async def archive_product(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Archive a product."""
    result = product_service.archive_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Product archived successfully",
        product=result.product,  # type: ignore
    )


@router.put(
    "/{product_id}/reactivate",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Product not archived"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Reactivate product",
    description="Reactivate an archived product.",
)
async def reactivate_product(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Reactivate an archived product."""
    result = product_service.reactivate_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Product reactivated successfully",
        product=result.product,  # type: ignore
    )


# =============================================================================
# US-009: Product Availability Management
# =============================================================================


@router.get(
    "/low-stock",
    response_model=LowStockListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="Get low-stock products",
    description="Get all products that are low on stock or out of stock.",
)
async def get_low_stock_products(
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> LowStockListResponse:
    """Get all low-stock products for the farmer."""
    result = product_service.get_low_stock_products(farmer_id=current_user.id)
    products = result.products or []
    return LowStockListResponse(products=products, total=len(products))


@router.put(
    "/{product_id}/inventory",
    response_model=ProductUpdateResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Update inventory",
    description="Update product inventory quantity.",
)
async def update_inventory(
    product_id: UUID,
    inventory_data: InventoryUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Update product inventory quantity."""
    result = product_service.update_inventory(
        farmer_id=current_user.id,
        product_id=product_id,
        quantity=inventory_data.quantity,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Inventory updated successfully",
        product=result.product,  # type: ignore
    )


@router.put(
    "/{product_id}/availability",
    response_model=ProductUpdateResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Set availability",
    description="Mark product as in-stock or out-of-stock.",
)
async def set_availability(
    product_id: UUID,
    in_stock: bool = Query(..., description="True for in-stock, False for out-of-stock"),
    quantity: int = Query(default=1, ge=1, description="Quantity if marking in-stock"),
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Set product availability status."""
    if in_stock:
        result = product_service.mark_in_stock(
            farmer_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
        )
    else:
        result = product_service.mark_out_of_stock(
            farmer_id=current_user.id,
            product_id=product_id,
        )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    status_msg = "in-stock" if in_stock else "out-of-stock"
    return ProductUpdateResponse(
        message=f"Product marked as {status_msg}",
        product=result.product,  # type: ignore
    )


@router.put(
    "/{product_id}/threshold",
    response_model=ProductUpdateResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Set low-stock threshold",
    description="Set the threshold for low-stock alerts.",
)
async def set_threshold(
    product_id: UUID,
    threshold_data: ThresholdUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Set product low-stock threshold."""
    result = product_service.update_threshold(
        farmer_id=current_user.id,
        product_id=product_id,
        threshold=threshold_data.low_stock_threshold,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Low-stock threshold updated successfully",
        product=result.product,  # type: ignore
    )


# =============================================================================
# US-010: Pricing Management
# =============================================================================


class PriceUpdateRequest(BaseModel):
    """Request model for price update."""

    price: float = Field(..., gt=0, description="New product price")


class DiscountRequest(BaseModel):
    """Request model for applying a discount."""

    discount_type: str = Field(..., description="Type: 'percentage' or 'fixed'")
    discount_value: float = Field(..., gt=0, description="Discount value")
    start_date: str | None = Field(default=None, description="Start date (ISO format)")
    end_date: str | None = Field(default=None, description="End date (ISO format)")


class BulkPricingTierRequest(BaseModel):
    """Request model for a bulk pricing tier."""

    min_quantity: int = Field(..., gt=0, description="Minimum quantity")
    price: float = Field(..., gt=0, description="Price per unit")


class BulkPricingRequest(BaseModel):
    """Request model for bulk pricing."""

    tiers: list[BulkPricingTierRequest] = Field(
        ..., min_length=1, description="Bulk pricing tiers"
    )


class PriceHistoryResponse(BaseModel):
    """Response model for price history."""

    entries: list[dict]
    total: int


class BulkPricingListResponse(BaseModel):
    """Response model for bulk pricing list."""

    tiers: list[dict]


@router.put(
    "/{product_id}/price",
    response_model=ProductUpdateResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Update product price",
    description="Update the base price of a product.",
)
async def update_price(
    product_id: UUID,
    price_data: PriceUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Update product price."""
    from decimal import Decimal

    result = product_service.update_price(
        farmer_id=current_user.id,
        product_id=product_id,
        price=Decimal(str(price_data.price)),
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Price updated successfully",
        product=result.product,  # type: ignore
    )


@router.post(
    "/{product_id}/discount",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid discount"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Apply discount",
    description="Apply a percentage or fixed discount to a product.",
)
async def apply_discount(
    product_id: UUID,
    discount_data: DiscountRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Apply discount to a product."""
    from decimal import Decimal

    result = product_service.apply_discount(
        farmer_id=current_user.id,
        product_id=product_id,
        discount_type=discount_data.discount_type,
        discount_value=Decimal(str(discount_data.discount_value)),
        start_date=discount_data.start_date,
        end_date=discount_data.end_date,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Discount applied successfully",
        product=result.product,  # type: ignore
    )


@router.delete(
    "/{product_id}/discount",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "No discount to remove"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Remove discount",
    description="Remove the active discount from a product.",
)
async def remove_discount(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Remove discount from a product."""
    result = product_service.remove_discount(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Discount removed successfully",
        product=result.product,  # type: ignore
    )


@router.put(
    "/{product_id}/bulk-pricing",
    response_model=ProductUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid bulk pricing"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Set bulk pricing",
    description="Set bulk pricing tiers for a product.",
)
async def set_bulk_pricing(
    product_id: UUID,
    pricing_data: BulkPricingRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductUpdateResponse:
    """Set bulk pricing tiers for a product."""
    tiers = [
        {"min_quantity": tier.min_quantity, "price": tier.price}
        for tier in pricing_data.tiers
    ]

    result = product_service.set_bulk_pricing(
        farmer_id=current_user.id,
        product_id=product_id,
        tiers=tiers,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return ProductUpdateResponse(
        message="Bulk pricing set successfully",
        product=result.product,  # type: ignore
    )


@router.get(
    "/{product_id}/bulk-pricing",
    response_model=BulkPricingListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Get bulk pricing",
    description="Get bulk pricing tiers for a product.",
)
async def get_bulk_pricing(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> BulkPricingListResponse:
    """Get bulk pricing tiers for a product."""
    tiers = product_service.get_bulk_pricing(
        farmer_id=current_user.id,
        product_id=product_id,
    )
    return BulkPricingListResponse(tiers=tiers)


@router.delete(
    "/{product_id}/bulk-pricing",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Delete bulk pricing",
    description="Remove all bulk pricing tiers from a product.",
)
async def delete_bulk_pricing(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> DeleteResponse:
    """Delete bulk pricing for a product."""
    result = product_service.delete_bulk_pricing(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        error = result.error or "Unknown error"
        if "not found" in error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return DeleteResponse(message="Bulk pricing deleted successfully")


@router.get(
    "/{product_id}/price-history",
    response_model=PriceHistoryResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Get price history",
    description="Get historical price changes for a product.",
)
async def get_price_history(
    product_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> PriceHistoryResponse:
    """Get price history for a product."""
    entries = product_service.get_price_history(
        farmer_id=current_user.id,
        product_id=product_id,
    )
    return PriceHistoryResponse(entries=entries, total=len(entries))
