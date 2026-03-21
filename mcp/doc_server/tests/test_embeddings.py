"""Tests for schema-agnostic embedding cache operations."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from build_helpers.embeddings_loader import (
    load_embedding_cache,
    save_embedding_cache,
    sync_embeddings_cache,
)


class TestGeneralizedCacheWithCustomType:
    """T017: Save/load with custom type identifier."""

    def test_save_load_with_custom_type(self, tmp_path: Path) -> None:
        """Verify cache mechanism handles arbitrary type identifiers."""
        embeddings = {
            "subsystem:combat": [0.1, 0.2, 0.3],
            "subsystem:magic": [0.4, 0.5, 0.6],
        }

        save_embedding_cache(
            embeddings=embeddings,
            artifacts_path=tmp_path,
            model_slug="test-model",
            dimension=3,
            embedding_type="subsystem",
        )

        # Verify file created with correct name
        expected_file = tmp_path / "embed_cache_test-model_3_subsystem.pkl"
        assert expected_file.exists()

        # Load and verify data matches
        loaded = load_embedding_cache(
            artifacts_path=tmp_path,
            model_slug="test-model",
            dimension=3,
            embedding_type="subsystem",
        )

        assert loaded is not None
        assert loaded == embeddings


class TestMultipleTypesIndependent:
    """T018: Multiple types with independent invalidation."""

    def test_multiple_types_independent(self, tmp_path: Path) -> None:
        """Verify multiple types can coexist and be invalidated independently."""
        entity_embeddings = {"fn:abc": [0.1] * 768}
        usage_embeddings = {("fn:abc", "caller", "sig"): [0.2] * 768}
        subsystem_embeddings = {"subsystem:combat": [0.3] * 768}

        # Save three types
        save_embedding_cache(entity_embeddings, tmp_path, "model", 768, "entity")
        save_embedding_cache(usage_embeddings, tmp_path, "model", 768, "usages")
        save_embedding_cache(subsystem_embeddings, tmp_path, "model", 768, "subsystem")

        # Verify all three files exist
        assert (tmp_path / "embed_cache_model_768_entity.pkl").exists()
        assert (tmp_path / "embed_cache_model_768_usages.pkl").exists()
        assert (tmp_path / "embed_cache_model_768_subsystem.pkl").exists()

        # Delete one cache file
        (tmp_path / "embed_cache_model_768_usages.pkl").unlink()

        # Verify other two still loadable
        entity_loaded = load_embedding_cache(tmp_path, "model", 768, "entity")
        subsystem_loaded = load_embedding_cache(tmp_path, "model", 768, "subsystem")
        usage_loaded = load_embedding_cache(tmp_path, "model", 768, "usages")

        assert entity_loaded == entity_embeddings
        assert subsystem_loaded == subsystem_embeddings
        assert usage_loaded is None


class TestInvalidTypeIdentifierRaises:
    """T019: Invalid type identifiers raise ValueError."""

    def test_invalid_type_identifier_raises(self, tmp_path: Path) -> None:
        """Verify invalid type identifiers are rejected."""
        embeddings = {"test": [0.1, 0.2, 0.3]}

        # Test various invalid characters
        invalid_types = [
            "entity/usages",  # slash
            "type.invalid",  # dot
            "entity usages",  # space
            "type@special",  # @
            "",  # empty string
        ]

        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match="Invalid embedding_type"):
                save_embedding_cache(embeddings, tmp_path, "model", 3, invalid_type)

            with pytest.raises(ValueError, match="Invalid embedding_type"):
                load_embedding_cache(tmp_path, "model", 3, invalid_type)


class TestCorruptedCacheReturnsNone:
    """T020: Corrupted cache files return None with warning."""

    def test_corrupted_cache_returns_none(self, tmp_path: Path) -> None:
        """Verify corrupted pickle files return None and log warning."""
        cache_file = tmp_path / "embed_cache_model_768_entity.pkl"

        # Create a corrupted pickle file
        cache_file.write_bytes(b"not a valid pickle file")

        # Attempt to load should return None (not raise)
        result = load_embedding_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=768,
            embedding_type="entity",
        )

        assert result is None


class TestSyncEmbeddingsCacheStringKeys:
    """Test sync_embeddings_cache with string keys (entity-like)."""

    def test_cold_cache_generates_all_embeddings(self, tmp_path: Path) -> None:
        """No cache file → generates all embeddings."""
        mock_provider = MagicMock()
        mock_provider.embed_batch.return_value = [[0.1] * 3, [0.2] * 3]

        current_keys = ["key1", "key2"]
        texts_by_key = {"key1": "text1", "key2": "text2"}

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="test",
            current_keys=current_keys,
            texts_by_key=texts_by_key,
            provider=mock_provider,
        )

        assert len(result) == 2
        assert "key1" in result
        assert "key2" in result
        mock_provider.embed_batch.assert_called_once()

    def test_warm_cache_no_changes(self, tmp_path: Path) -> None:
        """Cache contains all keys → no generation, cache reused."""
        existing = {"key1": [0.1] * 3, "key2": [0.2] * 3}
        save_embedding_cache(existing, tmp_path, "model", 3, "test")

        mock_provider = MagicMock()

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="test",
            current_keys=["key1", "key2"],
            texts_by_key={"key1": "text1", "key2": "text2"},
            provider=mock_provider,
        )

        assert result == existing
        mock_provider.embed_batch.assert_not_called()

    def test_partial_cache_generates_missing_only(self, tmp_path: Path) -> None:
        """Cache has some keys → generates only missing keys."""
        existing = {"key1": [0.1] * 3}
        save_embedding_cache(existing, tmp_path, "model", 3, "test")

        mock_provider = MagicMock()
        mock_provider.embed_batch.return_value = [[0.2] * 3]

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="test",
            current_keys=["key1", "key2"],
            texts_by_key={"key1": "text1", "key2": "text2"},
            provider=mock_provider,
        )

        assert len(result) == 2
        assert result["key1"] == [0.1] * 3
        assert result["key2"] == [0.2] * 3
        mock_provider.embed_batch.assert_called_once_with(["text2"])

    def test_stale_keys_pruned(self, tmp_path: Path) -> None:
        """Cache has extra keys → prunes stale keys."""
        existing = {"key1": [0.1] * 3, "key2": [0.2] * 3, "key3": [0.3] * 3}
        save_embedding_cache(existing, tmp_path, "model", 3, "test")

        mock_provider = MagicMock()

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="test",
            current_keys=["key1", "key2"],
            texts_by_key={"key1": "text1", "key2": "text2"},
            provider=mock_provider,
        )

        assert len(result) == 2
        assert "key3" not in result
        mock_provider.embed_batch.assert_not_called()

    def test_missing_and_stale_keys(self, tmp_path: Path) -> None:
        """Cache has some stale, some missing → prunes stale, generates missing."""
        existing = {"key1": [0.1] * 3, "stale": [0.9] * 3}
        save_embedding_cache(existing, tmp_path, "model", 3, "test")

        mock_provider = MagicMock()
        mock_provider.embed_batch.return_value = [[0.2] * 3]

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="test",
            current_keys=["key1", "key2"],
            texts_by_key={"key1": "text1", "key2": "text2"},
            provider=mock_provider,
        )

        assert len(result) == 2
        assert result["key1"] == [0.1] * 3
        assert result["key2"] == [0.2] * 3
        assert "stale" not in result


class TestSyncEmbeddingsCacheTupleKeys:
    """Test sync_embeddings_cache with tuple keys (usage-like)."""

    def test_tuple_keys_work(self, tmp_path: Path) -> None:
        """Tuple keys (callee, caller, sig) work correctly."""
        mock_provider = MagicMock()
        mock_provider.embed_batch.return_value = [[0.1] * 3]

        key = ("fn:callee", "caller_compound", "caller_sig")
        texts_by_key = {key: "usage text"}

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="usages",
            current_keys=[key],
            texts_by_key=texts_by_key,
            provider=mock_provider,
        )

        assert len(result) == 1
        assert key in result

    def test_tuple_keys_partial_cache(self, tmp_path: Path) -> None:
        """Tuple keys with partial cache."""
        key1 = ("fn:a", "caller1", "sig1")
        key2 = ("fn:b", "caller2", "sig2")
        existing = {key1: [0.1] * 3}
        save_embedding_cache(existing, tmp_path, "model", 3, "usages")

        mock_provider = MagicMock()
        mock_provider.embed_batch.return_value = [[0.2] * 3]

        result = sync_embeddings_cache(
            artifacts_path=tmp_path,
            model_slug="model",
            dimension=3,
            embedding_type="usages",
            current_keys=[key1, key2],
            texts_by_key={key1: "text1", key2: "text2"},
            provider=mock_provider,
        )

        assert len(result) == 2
        assert result[key1] == [0.1] * 3
        assert result[key2] == [0.2] * 3
