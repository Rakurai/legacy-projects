"""
Unit tests for ServerConfig computed properties.
"""

from pathlib import Path

from server.config import ServerConfig


def _make_config(**overrides) -> ServerConfig:
    """Create a ServerConfig with test defaults."""
    defaults = dict(
        db_name="testdb",
        db_user="user",
        db_password="pass",
        db_host="myhost",
        db_port=5433,
        project_root="/tmp/repo",
        artifacts_dir="artifacts",
    )
    defaults.update(overrides)
    return ServerConfig(**defaults)


def test_db_url():
    """db_url property builds correct asyncpg connection URL."""
    cfg = _make_config()
    assert cfg.db_url == "postgresql+asyncpg://user:pass@myhost:5433/testdb"


def test_artifacts_path():
    """artifacts_path joins project_root with artifacts_dir."""
    cfg = _make_config(project_root="/tmp/repo", artifacts_dir="artifacts")
    assert cfg.artifacts_path == Path("/tmp/repo/artifacts")


def test_embed_cache_filename_local():
    """embed_cache_filename uses local model slug and dimension."""
    cfg = _make_config(
        embedding_provider="local",
        embedding_local_model="BAAI/bge-base-en-v1.5",
        embedding_dimension=768,
    )
    assert cfg.embed_cache_filename == "embed_cache_BAAI-bge-base-en-v1.5_768.pkl"


def test_embed_cache_filename_hosted():
    """embed_cache_filename uses hosted model slug and dimension."""
    cfg = _make_config(
        embedding_provider="hosted",
        embedding_model="text-embedding-3-large",
        embedding_dimension=4096,
        embedding_base_url="http://localhost:4000/v1",
    )
    assert cfg.embed_cache_filename == "embed_cache_text-embedding-3-large_4096.pkl"
