"""Health check endpoints for application monitoring."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Health status")
    timestamp: datetime = Field(description="Current server timestamp")
    environment: str = Field(description="Deployment environment")
    version: str = Field(description="Application version")


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool = Field(description="Application readiness status")
    checks: dict[str, bool] = Field(description="Individual component checks")


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Basic health check endpoint to verify the service is running.",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Return basic health status of the application."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        environment=settings.environment,
        version=settings.app_version,
    )


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Kubernetes liveness probe endpoint.",
)
async def liveness() -> dict[str, str]:
    """Return liveness status for Kubernetes probes."""
    return {"status": "alive"}


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Kubernetes readiness probe endpoint with component checks.",
)
async def readiness() -> ReadinessResponse:
    """Return readiness status with component health checks.

    Add additional checks here (database, cache, external services).
    """
    checks = {
        "api": True,
    }

    return ReadinessResponse(
        ready=all(checks.values()),
        checks=checks,
    )
