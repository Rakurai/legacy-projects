"""
Server Configuration - Environment-based settings validation.

Uses pydantic-settings for type-safe environment variable loading.
Fails fast if required configuration is missing.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    artifacts_dir: Path = Field(default=Path("artifacts"), description="Artifacts directory (relative to project_root)")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Embedding provider selection
    embedding_provider: Literal["local", "hosted"] | None = Field(
        default=None,
        description="Embedding provider: 'local' (bundled ONNX), 'hosted' (OpenAI-compatible), or None (keyword-only)",
    )

    # Local provider config
    embedding_local_model: str = Field(
        default="BAAI/bge-base-en-v1.5",
        description="FastEmbed model name for local provider",
    )
    embedding_onnx_provider: str = Field(
        default="CPUExecutionProvider",
        description="ONNX Runtime execution provider (e.g. CoreMLExecutionProvider, CUDAExecutionProvider)",
    )
    embedding_dimension: int = Field(
        default=768,
        ge=1,
        description="Vector dimension (must match provider output)",
    )

    # Hosted provider config (only when embedding_provider='hosted')
    embedding_base_url: str | None = Field(default=None, description="OpenAI-compatible endpoint URL")
    embedding_api_key: str | None = Field(default=None, description="API key (or 'lm-studio' for local)")
    embedding_model: str | None = Field(default=None, description="Hosted model name")

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
        """Whether an embedding provider is configured."""
        return self.embedding_provider is not None

    @property
    def embed_cache_filename(self) -> str:
        """Artifact filename keyed by model name and dimension.

        Uses the active model name (local or hosted) with '/' replaced by '-'.
        Example: embed_cache_BAAI-bge-base-en-v1.5_768.pkl
        """
        if self.embedding_provider == "local":
            model_slug = self.embedding_local_model.replace("/", "-")
        elif self.embedding_provider == "hosted" and self.embedding_model:
            model_slug = self.embedding_model.replace("/", "-")
        else:
            model_slug = "unknown"
        return f"embed_cache_{model_slug}_{self.embedding_dimension}.pkl"
