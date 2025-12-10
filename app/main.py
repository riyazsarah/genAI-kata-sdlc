"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.router import api_router
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
