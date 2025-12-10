"""Public product catalog API endpoints for consumers (US-011)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.db.supabase import get_supabase_client
from app.models.product import (
    ProductCategory,
    ProductListResponse,
    ProductResponse,
)
from app.repositories.product import ProductRepository
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Product Catalog"])


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str


class CategoriesListResponse(BaseModel):
    """Response model for categories list."""

    categories: list[dict]


class FeaturedProductsResponse(BaseModel):
    """Response model for featured products."""

    products: list[ProductResponse]


def get_product_service() -> ProductService:
    """Dependency to get the product service."""
    db_client = get_supabase_client()
    product_repo = ProductRepository(db_client)
    return ProductService(product_repo)


@router.get(
    "",
    response_model=ProductListResponse,
    summary="Browse products",
    description="Get paginated product catalog for browsing. Only active, in-stock products are shown.",
)
async def browse_products(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    category: str | None = Query(default=None, description="Filter by category"),
    search: str | None = Query(default=None, description="Search term"),
    product_service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    """Browse the public product catalog.

    Returns paginated list of active, in-stock products.
    Supports filtering by category and search.
    """
    result = product_service.get_public_catalog(
        page=page,
        page_size=page_size,
        category=category,
        search=search,
    )

    return ProductListResponse(
        products=result.products or [],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get(
    "/featured",
    response_model=FeaturedProductsResponse,
    summary="Get featured products",
    description="Get featured/seasonal products for homepage display.",
)
async def get_featured_products(
    limit: int = Query(default=10, ge=1, le=50, description="Number of products"),
    product_service: ProductService = Depends(get_product_service),
) -> FeaturedProductsResponse:
    """Get featured products for homepage."""
    products = product_service.get_featured_products(limit=limit)
    return FeaturedProductsResponse(products=products)


@router.get(
    "/categories",
    response_model=CategoriesListResponse,
    summary="Get categories",
    description="Get all available product categories.",
)
async def get_categories() -> CategoriesListResponse:
    """Get all product categories."""
    categories = [
        {"value": cat.value, "label": cat.value}
        for cat in ProductCategory
    ]
    return CategoriesListResponse(categories=categories)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
    summary="Get product details",
    description="Get detailed information about a specific product.",
)
async def get_product_detail(
    product_id: UUID,
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Get product details for the product detail page."""
    result = product_service.get_public_product(product_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error or "Product not found",
        )

    return result.product  # type: ignore
