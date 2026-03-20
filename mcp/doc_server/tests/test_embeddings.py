"""Tests for minimal embedding text generation and doc-less entity coverage."""

import pickle
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from build_helpers.embeddings_loader import (
    build_minimal_embed_text,
    generate_embeddings,
    load_embedding_cache,
    save_embedding_cache,
)
from build_helpers.entity_processor import MergedEntity
from legacy_common.doxygen_parse import DoxygenEntity, DoxygenLocation, EntityID


def _make_merged(
    name: str,
    kind: str = "function",
    doc: MagicMock | None = None,
    body_fn: str | None = None,
    decl_fn: str | None = None,
) -> MergedEntity:
    """Build a MergedEntity for embedding tests."""
    body = DoxygenLocation(fn=body_fn, line=1, end_line=10, type="body") if body_fn else None
    decl = DoxygenLocation(fn=decl_fn, line=1, type="decl") if decl_fn else None
    entity = DoxygenEntity(
        id=EntityID(compound=f"{name}_compound"),
        kind=kind,
        name=name,
        body=body,
        decl=decl,
    )
    merged = MergedEntity(entity=entity, doc=doc, sig_key=(f"{name}_compound", f"{name}_compound"))
    merged._deterministic_id = f"fn:test_{name}"
    return merged


class TestBuildMinimalEmbedTextFunction:
    """T012: Function entity → @fn tag + signature output."""

    def test_function_entity_produces_fn_tag(self) -> None:
        merged = _make_merged("damage", kind="function", body_fn="src/fight.cc")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@fn" in result
        assert "damage" in result

    def test_function_entity_includes_file_path(self) -> None:
        merged = _make_merged("damage", kind="function", body_fn="src/fight.cc")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@file src/fight.cc" in result

    def test_variable_entity_produces_var_tag(self) -> None:
        merged = _make_merged("player_list", kind="variable", body_fn="src/db.cc")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@var" in result
        assert "player_list" in result

    def test_class_entity_produces_class_tag(self) -> None:
        merged = _make_merged("Character", kind="class", body_fn="src/character.cc")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@class" in result
        assert "Character" in result


class TestBuildMinimalEmbedTextFile:
    """T013: File compound → @file tag + path output."""

    def test_file_compound_produces_file_tag(self) -> None:
        merged = _make_merged("fight.cc", kind="file", body_fn="src/fight.cc")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@file" in result
        assert "fight.cc" in result

    def test_dir_compound_produces_dir_tag(self) -> None:
        merged = _make_merged("src", kind="dir")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@dir" in result
        assert "src" in result

    def test_namespace_produces_namespace_tag(self) -> None:
        merged = _make_merged("Logging", kind="namespace")
        result = build_minimal_embed_text(merged)

        assert result is not None
        assert "@namespace" in result
        assert "Logging" in result


class TestBuildMinimalEmbedTextEmptySkips:
    """T014: Entity with no name/sig/kind → returns None."""

    def test_empty_entity_returns_none(self) -> None:
        entity = DoxygenEntity(
            id=EntityID(compound="empty_compound"),
            kind="",
            name="",
        )
        merged = MergedEntity(entity=entity, doc=None, sig_key=("empty_compound", "empty_compound"))
        merged._deterministic_id = "fn:test_empty"
        result = build_minimal_embed_text(merged)

        assert result is None


class TestGenerateEmbeddingsIncludesDocLess:
    """T015: Mock provider verifying doc-less entities are in the embed batch."""

    def test_doc_less_entities_included_in_batch(self, tmp_path: Path) -> None:
        # Entity with doc
        mock_doc = MagicMock()
        mock_doc.to_doxygen.return_value = "/** @fn void fight() */"
        with_doc = _make_merged("fight", kind="function", doc=mock_doc, body_fn="src/fight.cc")
        with_doc.doc = mock_doc

        # Entity without doc
        without_doc = _make_merged("damage", kind="function", body_fn="src/fight.cc")
        without_doc.doc = None

        mock_provider = MagicMock()
        mock_provider.embed_documents_sync.return_value = [
            [0.1] * 768,  # fight (doc-rich)
            [0.2] * 768,  # damage (doc-less)
        ]

        mock_config = MagicMock()
        mock_config.embedding_model_slug = "test-model"
        mock_config.embedding_dimension = 768

        result = generate_embeddings(
            artifacts_dir=tmp_path,
            provider=mock_provider,
            config=mock_config,
            merged_entities=[with_doc, without_doc],
        )

        # Both entities should have embeddings
        assert with_doc.entity_id in result
        assert without_doc.entity_id in result

        # Provider should have been called with 2 texts (both doc-rich and doc-less)
        call_args = mock_provider.embed_documents_sync.call_args
        texts = call_args[0][0]
        assert len(texts) == 2

    def test_all_doc_less_entities_embedded(self, tmp_path: Path) -> None:
        entities = [_make_merged(f"fn_{i}", kind="function", body_fn=f"src/f{i}.cc") for i in range(5)]
        for e in entities:
            e.doc = None

        mock_provider = MagicMock()
        mock_provider.embed_documents_sync.return_value = [[0.1] * 768] * 5

        mock_config = MagicMock()
        mock_config.embedding_model_slug = "test-model"
        mock_config.embedding_dimension = 768

        result = generate_embeddings(
            artifacts_dir=tmp_path,
            provider=mock_provider,
            config=mock_config,
            merged_entities=entities,
        )

        assert len(result) == 5


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
