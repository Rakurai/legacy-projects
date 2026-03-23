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
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

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

    # Embedding provider selection (required — server fails fast without it)
    embedding_provider: Literal["local", "hosted"] = Field(
        description="Embedding provider: 'local' (bundled ONNX) or 'hosted' (OpenAI-compatible)",
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

    # Local symbol embedding model (code-aware, for symbol view)
    embedding_local_symbol_model: str = Field(
        default="jinaai/jina-embeddings-v2-base-code",
        description="FastEmbed model name for symbol view (local provider only)",
    )

    # Cross-encoder reranker
    cross_encoder_model: str = Field(
        default="Xenova/ms-marco-MiniLM-L-12-v2",
        description="fastembed cross-encoder model name for reranking",
    )

    # Per-signal floor thresholds (FR-043)
    floor_doc_semantic: float = Field(default=0.3, ge=0, description="Floor threshold for doc semantic signal")
    floor_symbol_semantic: float = Field(default=0.3, ge=0, description="Floor threshold for symbol semantic signal")
    floor_doc_keyword_shaped: float = Field(default=0.05, ge=0, description="Floor threshold for shaped doc keyword")
    floor_symbol_keyword_shaped: float = Field(
        default=0.05, ge=0, description="Floor threshold for shaped symbol keyword"
    )
    floor_trigram: float = Field(default=0.2, ge=0, description="Floor threshold for trigram similarity")

    @property
    def db_url(self) -> str:
        """PostgreSQL async connection URL (asyncpg driver)."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def artifacts_path(self) -> Path:
        """Absolute path to artifacts directory."""
        return self.project_root / self.artifacts_dir

    @property
    def embedding_model_slug(self) -> str:
        """Normalized model slug for doc embedding cache file naming.

        Replaces '/' with '-' to make filesystem-safe.
        Example: BAAI/bge-base-en-v1.5 → BAAI-bge-base-en-v1-5
        """
        if self.embedding_provider == "local":
            return self.embedding_local_model.replace("/", "-")
        # hosted — embedding_model is validated as required in create_provider
        return self.embedding_model.replace("/", "-") if self.embedding_model else "unknown"

    @property
    def embedding_symbol_model_slug(self) -> str:
        """Normalized model slug for symbol embedding cache file naming.

        For local provider, uses the dedicated symbol model.
        For hosted provider, falls back to the same model as doc.
        """
        if self.embedding_provider == "local":
            return self.embedding_local_symbol_model.replace("/", "-")
        return self.embedding_model_slug

    @property
    def embed_cache_filename(self) -> str:
        """Artifact filename keyed by model name and dimension.

        Uses the active model name (local or hosted) with '/' replaced by '-'.
        Example: embed_cache_BAAI-bge-base-en-v1.5_768.pkl
        """
        return f"embed_cache_{self.embedding_model_slug}_{self.embedding_dimension}.pkl"
