"""Profile page routes for consumer dashboard features."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

settings = get_settings()
templates = Jinja2Templates(directory=settings.templates_dir)

router = APIRouter(prefix="/profile", tags=["Profile Pages"])


@router.get("/edit", response_class=HTMLResponse)
async def edit_profile_page(request: Request) -> HTMLResponse:
    """Render the edit profile page."""
    return templates.TemplateResponse(
        request=request,
        name="profile/edit.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@router.get("/addresses", response_class=HTMLResponse)
async def addresses_page(request: Request) -> HTMLResponse:
    """Render the address management page."""
    return templates.TemplateResponse(
        request=request,
        name="profile/addresses.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@router.get("/preferences", response_class=HTMLResponse)
async def preferences_page(request: Request) -> HTMLResponse:
    """Render the preferences page."""
    return templates.TemplateResponse(
        request=request,
        name="profile/preferences.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request) -> HTMLResponse:
    """Render the orders page."""
    return templates.TemplateResponse(
        request=request,
        name="profile/orders.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@router.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request) -> HTMLResponse:
    """Render the favorites page."""
    return templates.TemplateResponse(
        request=request,
        name="profile/favorites.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )
