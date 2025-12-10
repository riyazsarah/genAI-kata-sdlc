"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.farmer_pages import router as farmer_pages_router
from app.api.v1.router import api_router
from app.api.v1.shop_pages import router as shop_pages_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    yield
    # Shutdown


def create_application() -> FastAPI:
    """Application factory for creating FastAPI instance."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Mount static files
    application.mount(
        "/static",
        StaticFiles(directory=settings.templates_dir.parent / "static"),
        name="static",
    )

    # Include API routers
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    # Include farmer page routes (HTMX-powered)
    application.include_router(farmer_pages_router)

    # Include shop page routes (consumer product browsing)
    application.include_router(shop_pages_router)

    return application


app = create_application()
templates = Jinja2Templates(directory=settings.templates_dir)


@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home(request: Request) -> HTMLResponse:
    """Render the home page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/register", response_class=HTMLResponse, tags=["Pages"])
async def register_page(request: Request) -> HTMLResponse:
    """Render the registration page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/signup", response_class=HTMLResponse, tags=["Pages"])
async def signup_redirect(request: Request) -> HTMLResponse:
    """Redirect signup to register page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/login", response_class=HTMLResponse, tags=["Pages"])
async def login_page(request: Request) -> HTMLResponse:
    """Render the login page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/forgot-password", response_class=HTMLResponse, tags=["Pages"])
async def forgot_password_page(request: Request) -> HTMLResponse:
    """Render the forgot password page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/forgot-password.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/reset-password", response_class=HTMLResponse, tags=["Pages"])
async def reset_password_page(request: Request) -> HTMLResponse:
    """Render the reset password page."""
    return templates.TemplateResponse(
        request=request,
        name="auth/reset-password.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/dashboard", response_class=HTMLResponse, tags=["Pages"])
async def dashboard_page(request: Request) -> HTMLResponse:
    """Render the consumer dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/register/farmer", response_class=HTMLResponse, tags=["Pages"])
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


@app.get("/admin/dashboard", response_class=HTMLResponse, tags=["Pages"])
async def admin_dashboard_page(request: Request) -> HTMLResponse:
    """Render the admin dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/cart", response_class=HTMLResponse, tags=["Pages"])
async def cart_page(request: Request) -> HTMLResponse:
    """Render the shopping cart page."""
    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
        },
    )
