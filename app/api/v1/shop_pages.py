"""Shop page routes with HTMX support for consumers (US-011)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.db.supabase import get_supabase_client
from app.models.product import ProductCategory
from app.repositories.farmer import FarmerRepository
from app.repositories.product import ProductRepository
from app.services.product import ProductService

settings = get_settings()
templates = Jinja2Templates(directory=settings.templates_dir)

router = APIRouter(prefix="/shop", tags=["Shop Pages"])


def get_product_service() -> ProductService:
    """Dependency to get the product service."""
    db_client = get_supabase_client()
    product_repo = ProductRepository(db_client)
    farmer_repo = FarmerRepository(db_client)
    return ProductService(product_repo, farmer_repo)


@router.get("", response_class=HTMLResponse)
async def shop_catalog_page(request: Request) -> HTMLResponse:
    """Render the shop catalog page."""
    categories = [
        {"value": cat.value, "label": cat.value}
        for cat in ProductCategory
    ]

    return templates.TemplateResponse(
        request=request,
        name="shop/catalog.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "categories": categories,
        },
    )


@router.get("/products", response_class=HTMLResponse)
async def shop_products_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Render the products grid partial for HTMX."""
    result = product_service.get_public_catalog(
        page=page,
        page_size=20,
        category=category,
        search=search,
    )

    # Convert to dicts for template - service already populates all pricing fields
    products = [p.model_dump() for p in result.products or []]

    return templates.TemplateResponse(
        request=request,
        name="shop/partials/product_grid.html",
        context={
            "products": products,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "category": category or "",
            "search": search or "",
        },
    )


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def shop_product_detail_page(
    request: Request,
    product_id: UUID,
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Render the product detail page."""
    result = product_service.get_public_product(product_id)

    if not result.success:
        return templates.TemplateResponse(
            request=request,
            name="shop/product_detail.html",
            context={
                "app_name": settings.app_name,
                "version": settings.app_version,
                "error": result.error,
                "product": None,
                "bulk_pricing": [],
            },
            status_code=404,
        )

    # Service already populates all pricing fields including discount info
    product_dict = result.product.model_dump()

    # Get bulk pricing tiers for display
    bulk_pricing = product_service.product_repo.get_bulk_pricing(product_id)

    return templates.TemplateResponse(
        request=request,
        name="shop/product_detail.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "product": product_dict,
            "bulk_pricing": bulk_pricing,
        },
    )
