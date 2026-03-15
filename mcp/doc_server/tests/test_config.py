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
        artifacts_dir=".ai/artifacts",
    )
    defaults.update(overrides)
    return ServerConfig(**defaults)


def test_db_url():
    """db_url property builds correct asyncpg connection URL."""
    cfg = _make_config()
    assert cfg.db_url == "postgresql+asyncpg://user:pass@myhost:5433/testdb"


def test_artifacts_path():
    """artifacts_path joins project_root with artifacts_dir."""
    cfg = _make_config(project_root="/tmp/repo", artifacts_dir=".ai/artifacts")
    assert cfg.artifacts_path == Path("/tmp/repo/.ai/artifacts")


def test_embedding_enabled_true():
    """embedding_enabled is True when embedding_base_url is set."""
    cfg = _make_config(embedding_base_url="http://localhost:1234")
    assert cfg.embedding_enabled is True


def test_embedding_enabled_false():
    """embedding_enabled is False when embedding_base_url is None."""
    cfg = _make_config(embedding_base_url=None)
    assert cfg.embedding_enabled is False
