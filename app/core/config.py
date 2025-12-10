"""Application configuration module.

Uses pydantic-settings for type-safe configuration management
with automatic .env file loading.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="FastAPI App", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode flag")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    @property
    def base_dir(self) -> Path:
        """Return the base directory of the application."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def templates_dir(self) -> Path:
        """Return the templates directory path."""
        return Path(__file__).resolve().parent.parent / "templates"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
