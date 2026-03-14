"""
Server Configuration - Environment-based settings validation.

Uses pydantic-settings for type-safe environment variable loading.
Fails fast if required configuration is missing.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class ServerConfig(BaseSettings):
    """
    Server configuration loaded from .env file.

    All required fields MUST be present or server will fail to start (fail-fast).
    Optional fields degrade gracefully (e.g., embedding endpoint unavailable).
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # PostgreSQL
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    db_name: str = Field(description="PostgreSQL database name")
    db_user: str = Field(description="PostgreSQL user")
    db_password: str = Field(description="PostgreSQL password")

    # Project paths
    project_root: Path = Field(description="Repository root directory")
    artifacts_dir: Path = Field(default=Path(".ai/artifacts"), description="Artifacts directory (relative to project_root)")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Optional: Embedding endpoint (OpenAI-compatible API)
    embedding_base_url: str | None = Field(default=None, description="OpenAI-compatible endpoint URL")
    embedding_api_key: str | None = Field(default=None, description="API key (or 'lm-studio' for local)")
    embedding_model: str | None = Field(default=None, description="Model name")

    @property
    def db_url(self) -> str:
        """PostgreSQL async connection URL (asyncpg driver)."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def artifacts_path(self) -> Path:
        """Absolute path to artifacts directory."""
        return self.project_root / self.artifacts_dir

    @property
    def embedding_enabled(self) -> bool:
        """Whether embedding endpoint is configured."""
        return self.embedding_base_url is not None
