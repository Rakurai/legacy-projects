"""Tests for entity_processor source extraction with fail-fast validation."""

from pathlib import Path

import pytest
from loguru import logger

from build_helpers.entity_processor import BuildError, MergedEntity, extract_source_code
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
