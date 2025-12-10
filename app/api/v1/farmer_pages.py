"""Farmer page routes with HTMX support for product management."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.dependencies import require_auth_cookie
from app.db.supabase import get_supabase_client
from app.models.product import (
    ProductCategory,
    ProductCreate,
    ProductStatus,
    ProductUnit,
    ProductUpdate,
    Seasonality,
)
from app.models.user import UserInDB
from app.repositories.product import ProductRepository
from app.services.product import ProductService

settings = get_settings()
templates = Jinja2Templates(directory=settings.templates_dir)

router = APIRouter(prefix="/farmer", tags=["Farmer Pages"])


# =============================================================================
# US-004 & US-005: Farmer Registration & Dashboard Pages
# =============================================================================


@router.get("/register", response_class=HTMLResponse)
async def farmer_register_page(request: Request) -> HTMLResponse:
    """Render the farmer registration page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/farmer-register.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def farmer_dashboard_page(request: Request) -> HTMLResponse:
    """Render the farmer dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="farmer/dashboard.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


def get_product_service() -> ProductService:
    """Dependency to get the product service."""
    db_client = get_supabase_client()
    product_repo = ProductRepository(db_client)
    return ProductService(product_repo)


@router.get("/products", response_class=HTMLResponse)
async def farmer_products_page(
    request: Request,
    current_user: UserInDB = Depends(require_auth_cookie),
) -> HTMLResponse:
    """Render the farmer's products list page."""
    return templates.TemplateResponse(
        request=request,
        name="farmer/products.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "user": current_user,
        },
    )


@router.get("/products/new", response_class=HTMLResponse)
async def farmer_product_new_page(
    request: Request,
    current_user: UserInDB = Depends(require_auth_cookie),
) -> HTMLResponse:
    """Render the new product creation page."""
    return templates.TemplateResponse(
        request=request,
        name="farmer/product_new.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "user": current_user,
            "categories": [c.value for c in ProductCategory],
            "units": [u.value for u in ProductUnit],
            "seasons": [s.value for s in Seasonality],
        },
    )


@router.post("/products", response_class=HTMLResponse)
async def farmer_product_create(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    quantity: int = Form(...),
    seasonality: list[str] = Form(default=[]),
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Handle product creation via HTMX form submission."""
    # Convert form data to ProductCreate
    product_data = ProductCreate(
        name=name,
        category=ProductCategory(category),
        description=description,
        price=Decimal(str(price)),
        unit=ProductUnit(unit),
        quantity=quantity,
        seasonality=[Seasonality(s) for s in seasonality] if seasonality else [Seasonality.YEAR_ROUND],
    )

    result = product_service.create_product(
        farmer_id=current_user.id,
        product_data=product_data,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div id="form-result" class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    # Return success message with redirect script
    return HTMLResponse(
        content=f'''<div id="form-result" class="alert alert-success">
            Product created successfully! Redirecting...
            <script>setTimeout(function() {{ window.location.href = "/farmer/products"; }}, 1500);</script>
        </div>''',
    )


@router.get("/products/list", response_class=HTMLResponse)
async def farmer_products_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    status: str | None = Query(default=None),
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Render the products list partial for HTMX."""
    status_filter = ProductStatus(status) if status else None

    result = product_service.get_farmer_products(
        farmer_id=current_user.id,
        page=page,
        page_size=12,
        status=status_filter,
    )

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/product_list.html",
        context={
            "products": result.products or [],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "status": status or "",
        },
    )


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def farmer_product_edit_page(
    request: Request,
    product_id: UUID,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Render the product edit page."""
    result = product_service.get_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        return templates.TemplateResponse(
            request=request,
            name="farmer/product_edit.html",
            context={
                "app_name": settings.app_name,
                "version": settings.app_version,
                "error": result.error,
                "product": None,
                "categories": [],
                "units": [],
                "seasons": [],
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="farmer/product_edit.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "product": result.product,
            "categories": [c.value for c in ProductCategory],
            "units": [u.value for u in ProductUnit],
            "seasons": [s.value for s in Seasonality],
        },
    )


@router.put("/products/{product_id}", response_class=HTMLResponse)
async def farmer_product_update(
    request: Request,
    product_id: UUID,
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    quantity: int = Form(...),
    status: str = Form(...),
    version: int = Form(...),
    seasonality: list[str] = Form(default=[]),
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Handle product update via HTMX form submission."""
    # Convert form data to ProductUpdate
    update_data = ProductUpdate(
        name=name,
        category=ProductCategory(category),
        description=description,
        price=Decimal(str(price)),
        unit=ProductUnit(unit),
        quantity=quantity,
        status=ProductStatus(status),
        version=version,
        seasonality=[Seasonality(s) for s in seasonality] if seasonality else None,
    )

    result = product_service.update_product(
        farmer_id=current_user.id,
        product_id=product_id,
        update_data=update_data,
    )

    if not result.success:
        error_class = "alert-error"
        if "version conflict" in (result.error or "").lower():
            error_class = "alert-error"
        return HTMLResponse(
            content=f'<div id="form-result" class="alert {error_class}">{result.error}</div>',
            status_code=409 if "version conflict" in (result.error or "").lower() else 400,
        )

    # Return success message with updated version
    return HTMLResponse(
        content=f'''<div id="form-result" class="alert alert-success">
            Product updated successfully!
            <script>document.getElementById("product-version").value = "{result.product.version}";</script>
        </div>''',
    )


@router.delete("/products/{product_id}/images", response_class=HTMLResponse)
async def farmer_product_remove_image(
    request: Request,
    product_id: UUID,
    image_url: str = Query(...),
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Handle image removal via HTMX."""
    result = product_service.remove_product_image(
        farmer_id=current_user.id,
        product_id=product_id,
        image_url=image_url,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    # Return empty response to remove the image element
    return HTMLResponse(content="")


# =============================================================================
# US-009: Low Stock Products Page
# =============================================================================


@router.get("/products/low-stock", response_class=HTMLResponse)
async def farmer_low_stock_page(
    request: Request,
    current_user: UserInDB = Depends(require_auth_cookie),
) -> HTMLResponse:
    """Render the low-stock products page."""
    return templates.TemplateResponse(
        request=request,
        name="farmer/low_stock.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "user": current_user,
        },
    )


@router.get("/products/low-stock/list", response_class=HTMLResponse)
async def farmer_low_stock_list(
    request: Request,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Render the low-stock products list partial for HTMX."""
    result = product_service.get_low_stock_products(farmer_id=current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/low_stock_list.html",
        context={
            "products": result.products or [],
        },
    )


# =============================================================================
# US-008 & US-009: HTMX API Endpoints for Product Cards
# =============================================================================


@router.put("/products/{product_id}/archive", response_class=HTMLResponse)
async def farmer_archive_product(
    request: Request,
    product_id: UUID,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Archive a product and return updated product card HTML."""
    result = product_service.archive_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/product_card.html",
        context={"product": result.product},
    )


@router.put("/products/{product_id}/reactivate", response_class=HTMLResponse)
async def farmer_reactivate_product(
    request: Request,
    product_id: UUID,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Reactivate a product and return updated product card HTML."""
    result = product_service.reactivate_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/product_card.html",
        context={"product": result.product},
    )


@router.delete("/products/{product_id}", response_class=HTMLResponse)
async def farmer_delete_product(
    request: Request,
    product_id: UUID,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Delete a product and return empty response to remove from DOM."""
    result = product_service.delete_product(
        farmer_id=current_user.id,
        product_id=product_id,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    # Return empty content to remove the card from the DOM
    return HTMLResponse(content="")


@router.put("/products/{product_id}/inventory", response_class=HTMLResponse)
async def farmer_update_inventory(
    request: Request,
    product_id: UUID,
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Update product inventory and return updated product card HTML."""
    # Parse JSON body
    body = await request.json()
    quantity = body.get("quantity", 0)

    result = product_service.update_inventory(
        farmer_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
    )

    if not result.success:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/product_card.html",
        context={"product": result.product},
    )


@router.put("/products/{product_id}/availability", response_class=HTMLResponse)
async def farmer_set_availability(
    request: Request,
    product_id: UUID,
    in_stock: bool = Query(...),
    quantity: int = Query(default=1, ge=1),
    current_user: UserInDB = Depends(require_auth_cookie),
    product_service: ProductService = Depends(get_product_service),
) -> HTMLResponse:
    """Set product availability and return updated card HTML."""
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
        return HTMLResponse(
            content=f'<div class="alert alert-error">{result.error}</div>',
            status_code=400,
        )

    # Check if this is from the low-stock page
    referer = request.headers.get("referer", "")
    if "low-stock" in referer:
        return templates.TemplateResponse(
            request=request,
            name="farmer/partials/low_stock_list.html",
            context={"products": [result.product]},
        )

    return templates.TemplateResponse(
        request=request,
        name="farmer/partials/product_card.html",
        context={"product": result.product},
    )
