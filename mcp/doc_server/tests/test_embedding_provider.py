"""
Tests for server/embedding.py — EmbeddingProvider protocol, factory, and LocalEmbeddingProvider.

Note: LocalEmbeddingProvider tests require the fastembed model to be downloaded (~130 MB).
      These tests are marked with `slow` and can be skipped in CI if needed.
      HostedEmbeddingProvider tests are omitted (require running endpoint).
"""

import pytest
from unittest.mock import patch, MagicMock

from server.config import ServerConfig
from server.embedding import (
    EmbeddingProvider,
    LocalEmbeddingProvider,
    HostedEmbeddingProvider,
    create_provider,
)


# ---------------------------------------------------------------------------
# Factory tests (no model download needed — mock providers)
# ---------------------------------------------------------------------------


class TestCreateProvider:
    """Tests for the create_provider factory function."""

    def test_none_provider_returns_none(self):
        config = _mock_config(embedding_provider=None)
        result = create_provider(config)
        assert result is None

    def test_local_provider_creates_local_instance(self):
        with patch("server.embedding.LocalEmbeddingProvider") as MockLocal:
            mock_instance = MagicMock()
            mock_instance.dimension = 768
            MockLocal.return_value = mock_instance

            config = _mock_config(
                embedding_provider="local",
                embedding_local_model="BAAI/bge-base-en-v1.5",
                embedding_dimension=768,
            )
            result = create_provider(config)

            assert result is mock_instance
            MockLocal.assert_called_once_with(model_name="BAAI/bge-base-en-v1.5")

    def test_hosted_provider_creates_hosted_instance(self):
        with patch("server.embedding.HostedEmbeddingProvider") as MockHosted:
            mock_instance = MagicMock()
            mock_instance.dimension = 4096
            MockHosted.return_value = mock_instance

            config = _mock_config(
                embedding_provider="hosted",
                embedding_base_url="http://localhost:4000/v1",
                embedding_api_key="lm-studio",
                embedding_model="text-embedding-3-large",
                embedding_dimension=4096,
            )
            result = create_provider(config)

            assert result is mock_instance

    def test_hosted_missing_base_url_raises(self):
        config = _mock_config(
            embedding_provider="hosted",
            embedding_base_url=None,
            embedding_model="some-model",
        )
        with pytest.raises(ValueError, match="EMBEDDING_BASE_URL"):
            create_provider(config)

    def test_hosted_missing_model_raises(self):
        config = _mock_config(
            embedding_provider="hosted",
            embedding_base_url="http://localhost:4000/v1",
            embedding_model=None,
        )
        with pytest.raises(ValueError, match="EMBEDDING_MODEL"):
            create_provider(config)

    def test_dimension_mismatch_raises(self):
        with patch("server.embedding.LocalEmbeddingProvider") as MockLocal:
            mock_instance = MagicMock()
            mock_instance.dimension = 384  # model outputs 384
            MockLocal.return_value = mock_instance

            config = _mock_config(
                embedding_provider="local",
                embedding_local_model="BAAI/bge-small-en-v1.5",
                embedding_dimension=768,  # config says 768
            )
            with pytest.raises(ValueError, match="Embedding dimension mismatch"):
                create_provider(config)

    def test_unknown_provider_raises(self):
        config = _mock_config(embedding_provider="unknown")
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_provider(config)


# ---------------------------------------------------------------------------
# LocalEmbeddingProvider integration tests (require model download)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestLocalEmbeddingProviderIntegration:
    """Integration tests that actually load the ONNX model.

    These download ~130 MB on first run. Mark with `slow` for CI gating.
    """

    @pytest.fixture(scope="class")
    def provider(self):
        return LocalEmbeddingProvider(model_name="BAAI/bge-base-en-v1.5")

    def test_dimension_is_768(self, provider):
        assert provider.dimension == 768

    def test_embed_query_sync_returns_correct_length(self, provider):
        vec = provider.embed_query_sync("test query")
        assert isinstance(vec, list)
        assert len(vec) == 768
        # All elements should be floats
        assert all(isinstance(x, float) for x in vec)

    def test_embed_documents_sync_batch(self, provider):
        texts = ["hello world", "combat damage calculation"]
        vecs = provider.embed_documents_sync(texts)
        assert len(vecs) == 2
        assert all(len(v) == 768 for v in vecs)

    @pytest.mark.asyncio
    async def test_embed_query_async(self, provider):
        vec = await provider.embed_query("async test")
        assert len(vec) == 768

    @pytest.mark.asyncio
    async def test_embed_documents_async(self, provider):
        vecs = await provider.embed_documents(["a", "b", "c"])
        assert len(vecs) == 3
        assert all(len(v) == 768 for v in vecs)


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    """Verify implementations match the EmbeddingProvider protocol."""

    def test_local_provider_has_required_attributes(self):
        # Verify LocalEmbeddingProvider has all protocol methods/properties
        assert hasattr(LocalEmbeddingProvider, "dimension")
        assert hasattr(LocalEmbeddingProvider, "embed_query")
        assert hasattr(LocalEmbeddingProvider, "embed_documents")
        assert hasattr(LocalEmbeddingProvider, "embed_query_sync")
        assert hasattr(LocalEmbeddingProvider, "embed_documents_sync")

    def test_hosted_provider_has_required_attributes(self):
        assert hasattr(HostedEmbeddingProvider, "dimension")
        assert hasattr(HostedEmbeddingProvider, "embed_query")
        assert hasattr(HostedEmbeddingProvider, "embed_documents")
        assert hasattr(HostedEmbeddingProvider, "embed_query_sync")
        assert hasattr(HostedEmbeddingProvider, "embed_documents_sync")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_config(**overrides) -> MagicMock:
    """Create a mock ServerConfig with sensible defaults."""
    defaults = {
        "embedding_provider": None,
        "embedding_local_model": "BAAI/bge-base-en-v1.5",
        "embedding_dimension": 768,
        "embedding_base_url": None,
        "embedding_api_key": None,
        "embedding_model": None,
    }
    defaults.update(overrides)
    config = MagicMock(spec=ServerConfig)
    for k, v in defaults.items():
        setattr(config, k, v)
    return config
