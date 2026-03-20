"""Tests for entity_processor source extraction with fail-fast validation."""

from pathlib import Path

import pytest
from loguru import logger

from unittest.mock import MagicMock

from build_helpers.entity_processor import BuildError, MergedEntity, extract_source_code, merge_entities
from legacy_common.doxygen_parse import DoxygenEntity, DoxygenLocation, EntityID


def _make_merged(
    name: str,
    body_fn: str | None = None,
    body_line: int | None = None,
    body_end_line: int | None = None,
    decl_fn: str | None = None,
    decl_line: int | None = None,
) -> MergedEntity:
    """Build a MergedEntity with optional body/decl locations."""
    body = DoxygenLocation(fn=body_fn, line=body_line, end_line=body_end_line, type="body") if body_fn else None
    decl = DoxygenLocation(fn=decl_fn, line=decl_line, type="decl") if decl_fn else None
    entity = DoxygenEntity(
        id=EntityID(compound=f"{name}_compound"),
        kind="function",
        name=name,
        body=body,
        decl=decl,
    )
    merged = MergedEntity(entity=entity, doc=None, sig_key=(f"{name}_compound", f"{name}_compound"))
    merged._deterministic_id = f"fn:test_{name}"
    return merged


def _write_source(tmp_path: Path, rel_path: str, content: str) -> None:
    """Write a source file into the tmp project root."""
    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)


class TestExtractSourceCodeHappyPath:
    """T006: Valid project_root with source files → extraction succeeds."""

    def test_body_and_definition_populated(self, tmp_path: Path) -> None:
        source = "line1\nvoid fight() {\n  return;\n}\nline5\n"
        _write_source(tmp_path, "src/fight.cc", source)

        merged = _make_merged(
            "fight",
            body_fn="src/fight.cc",
            body_line=2,
            body_end_line=4,
            decl_fn="src/fight.cc",
            decl_line=2,
        )
        extract_source_code([merged], tmp_path)

        assert merged.source_text == "void fight() {\n  return;\n}\n"
        assert merged.definition_text == "void fight() {"

    def test_multiple_entities(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "src/a.cc", "a_line1\na_line2\na_line3\n")
        _write_source(tmp_path, "src/b.cc", "b_line1\nb_line2\nb_line3\n")

        entities = [
            _make_merged("a", body_fn="src/a.cc", body_line=1, body_end_line=2),
            _make_merged("b", body_fn="src/b.cc", body_line=2, body_end_line=3),
        ]
        extract_source_code(entities, tmp_path)

        assert entities[0].source_text == "a_line1\na_line2\n"
        assert entities[1].source_text == "b_line2\nb_line3\n"


class TestExtractSourceCodeZeroExtractionRaises:
    """T007: Empty source tree → raises BuildError."""

    def test_raises_build_error_on_zero_extraction(self, tmp_path: Path) -> None:
        merged = _make_merged("fight", body_fn="src/fight.cc", body_line=1, body_end_line=5)
        with pytest.raises(BuildError, match="Zero source files extracted"):
            extract_source_code([merged], tmp_path)

    def test_error_includes_project_root(self, tmp_path: Path) -> None:
        merged = _make_merged("fight", body_fn="src/fight.cc", body_line=1, body_end_line=5)
        with pytest.raises(BuildError, match=str(tmp_path)):
            extract_source_code([merged], tmp_path)

    def test_no_error_when_no_body_located(self, tmp_path: Path) -> None:
        merged = _make_merged("fight")  # no body location
        extract_source_code([merged], tmp_path)
        assert merged.source_text is None


class TestExtractSourceCodePartialExtractionWarns:
    """T008: Some files present, some missing → warnings logged, build continues."""

    def test_partial_extraction_succeeds(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "src/a.cc", "a_line1\na_line2\n")
        # src/b.cc does NOT exist

        entities = [
            _make_merged("a", body_fn="src/a.cc", body_line=1, body_end_line=2),
            _make_merged("b", body_fn="src/b.cc", body_line=1, body_end_line=5),
        ]
        extract_source_code(entities, tmp_path)

        assert entities[0].source_text == "a_line1\na_line2\n"
        assert entities[1].source_text is None

    def test_partial_extraction_logs_warning(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "src/a.cc", "a_line1\na_line2\n")

        entities = [
            _make_merged("a", body_fn="src/a.cc", body_line=1, body_end_line=2),
            _make_merged("b", body_fn="src/missing.cc", body_line=1, body_end_line=5),
        ]

        warnings: list[str] = []
        sink_id = logger.add(lambda msg: warnings.append(str(msg)), level="WARNING", format="{message} {extra}")
        try:
            extract_source_code(entities, tmp_path)
        finally:
            logger.remove(sink_id)

        assert any("missing.cc" in w for w in warnings)


def _make_entity(
    name: str,
    compound_id: str,
    decl_fn: str,
    file_fn: str | None = None,
    kind: str = "function",
    member_hash: str | None = None,
    has_body: bool = False,
) -> DoxygenEntity:
    """Build a DoxygenEntity with a declaration location and optional file/body locations."""
    decl = DoxygenLocation(fn=decl_fn, line=1, type="decl")
    file_loc = DoxygenLocation(fn=file_fn, line=1, type="file") if file_fn else None
    body_loc = DoxygenLocation(fn=file_fn or decl_fn, line=1, type="body") if has_body else None
    return DoxygenEntity(
        id=EntityID(compound=compound_id, member=member_hash),
        kind=kind,
        name=name,
        decl=decl,
        file=file_loc,
        body=body_loc,
    )


class TestMergeEntitiesDedup:
    """Tests for declaration/definition split deduplication in merge_entities()."""

    def test_split_pair_produces_one_entity_with_surviving_doc(self) -> None:
        """Split pair: definition (with body) in graph with its own doc → one MergedEntity."""
        shared_member = "stc_member_hash"
        decl_entity = _make_entity("stc", "stc_decl", "include/stc.hh", member_hash=shared_member, has_body=False)
        def_entity = _make_entity(
            "stc", "stc_def", "include/stc.hh", file_fn="src/stc.cc", member_hash=shared_member, has_body=True
        )
        mock_doc = MagicMock()

        entity_db = MagicMock()
        entity_db.entities.values.return_value = [decl_entity, def_entity]
        doc_db = MagicMock()
        doc_db.get_doc.side_effect = lambda cid, sig: mock_doc if cid == "stc_def" else None

        result = merge_entities(entity_db, doc_db, frozenset({shared_member}))

        assert len(result) == 1
        assert result[0].entity.id.compound == "stc_def"
        assert result[0].doc is mock_doc

    def test_split_pair_copies_doc_from_sibling(self) -> None:
        """Survivor (definition with body) has no doc → doc is copied from the sibling fragment."""
        shared_member = "stc_member_hash"
        decl_entity = _make_entity("stc", "stc_decl", "include/stc.hh", member_hash=shared_member, has_body=False)
        def_entity = _make_entity(
            "stc", "stc_def", "include/stc.hh", file_fn="src/stc.cc", member_hash=shared_member, has_body=True
        )
        mock_doc = MagicMock()

        entity_db = MagicMock()
        entity_db.entities.values.return_value = [decl_entity, def_entity]
        doc_db = MagicMock()
        # Doc is on the declaration side; definition (survivor) has none
        doc_db.get_doc.side_effect = lambda cid, sig: mock_doc if cid == "stc_decl" else None

        result = merge_entities(entity_db, doc_db, frozenset({shared_member}))

        assert len(result) == 1
        assert result[0].entity.id.compound == "stc_def"
        assert result[0].doc is mock_doc  # copied from sibling

    def test_neither_compound_in_graph_raises(self) -> None:
        """Split pair with neither compound in code_graph.gml → BuildError."""
        shared_member = "damage_member_hash"
        decl_entity = _make_entity(
            "damage", "damage_decl", "include/damage.hh", member_hash=shared_member, has_body=False
        )
        def_entity = _make_entity(
            "damage",
            "damage_def",
            "include/damage.hh",
            file_fn="src/damage.cc",
            member_hash=shared_member,
            has_body=True,
        )

        entity_db = MagicMock()
        entity_db.entities.values.return_value = [decl_entity, def_entity]
        doc_db = MagicMock()
        doc_db.get_doc.return_value = None

        with pytest.raises(BuildError, match="damage"):
            merge_entities(entity_db, doc_db, frozenset())

    def test_single_entity_unchanged(self) -> None:
        """Single entity (no split) passes through without modification."""
        entity = _make_entity("solo", "solo_compound", "include/solo.hh")
        mock_doc = MagicMock()

        entity_db = MagicMock()
        entity_db.entities.values.return_value = [entity]
        doc_db = MagicMock()
        doc_db.get_doc.return_value = mock_doc

        result = merge_entities(entity_db, doc_db, frozenset({"solo_compound"}))

        assert len(result) == 1
        assert result[0].entity is entity
        assert result[0].doc is mock_doc
