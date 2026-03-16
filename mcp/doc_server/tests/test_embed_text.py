"""
Tests for build_helpers/embed_text.py — Doxygen-formatted docstring construction.

build_embed_text takes a raw doc_db.json dict and always returns text (never None).
"""

import pytest

from build_helpers.embed_text import build_embed_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(**overrides) -> dict:
    """Create a minimal doc dict with sensible defaults."""
    defaults = {"kind": "function", "name": "do_look", "mid": "test_id"}
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Tests: always produces text (never None)
# ---------------------------------------------------------------------------

class TestAlwaysProducesText:
    """Every doc entry produces text, matching original to_doxygen() behavior."""

    def test_minimal_doc_produces_text(self):
        doc = _make_doc()
        result = build_embed_text(doc)
        assert result.startswith("/**")
        assert result.endswith(" */")
        assert "@fn do_look" in result

    def test_empty_fields_still_produces_text(self):
        doc = _make_doc(brief=None, details=None)
        result = build_embed_text(doc)
        assert "/**" in result
        assert "@fn" in result

    def test_group_with_no_brief(self):
        doc = _make_doc(kind="group", name="MobProgTypes")
        result = build_embed_text(doc)
        assert "@defgroup MobProgTypes" in result


# ---------------------------------------------------------------------------
# Tests: full function entity
# ---------------------------------------------------------------------------

class TestFunctionEntity:
    """Function entity with full documentation."""

    def test_full_doc_produces_doxygen_format(self):
        doc = _make_doc(
            kind="function",
            name="do_look",
            brief="Handles the look command.",
            details="Shows room description and contents to the character.",
            params={"ch": "The character looking", "argument": "Optional target"},
            returns="void",
            notes="Called frequently during gameplay.",
            rationale="Core user interaction for spatial awareness.",
            definition="void do_look",
            argsstring="(Character *ch, String argument)",
        )
        result = build_embed_text(doc)

        assert result.startswith("/**")
        assert result.endswith(" */")
        assert "@fn void do_look(Character *ch, String argument)" in result
        assert "@brief Handles the look command." in result
        assert "@details Shows room description and contents to the character." in result
        assert "@note Called frequently during gameplay." in result
        assert "@rationale Core user interaction for spatial awareness." in result
        assert "@param ch The character looking" in result
        assert "@param argument Optional target" in result
        assert "@return void" in result

    def test_function_without_definition_uses_name(self):
        doc = _make_doc(kind="function", name="do_look", brief="A brief summary.")
        result = build_embed_text(doc)
        assert "@fn do_look" in result


# ---------------------------------------------------------------------------
# Tests: non-function entity kinds
# ---------------------------------------------------------------------------

class TestEntityKinds:
    """Different entity kinds produce correct Doxygen tags."""

    @pytest.mark.parametrize("kind,expected_tag", [
        ("variable", "@var"),
        ("class", "@class"),
        ("struct", "@struct"),
        ("enum", "@enum"),
        ("define", "@def"),
        ("namespace", "@namespace"),
        ("group", "@defgroup"),
    ])
    def test_kind_tag_mapping(self, kind, expected_tag):
        doc = _make_doc(kind=kind, name="test_entity", brief="Some brief.")
        result = build_embed_text(doc)
        assert f"{expected_tag} test_entity" in result

    def test_unknown_kind_defaults_to_fn_tag(self):
        doc = _make_doc(kind="typedef", name="my_type", brief="Some brief.")
        result = build_embed_text(doc)
        assert "@fn my_type" in result


# ---------------------------------------------------------------------------
# Tests: partial documentation fields
# ---------------------------------------------------------------------------

class TestPartialDocs:
    """Entities with partial documentation."""

    def test_only_brief(self):
        doc = _make_doc(brief="Just a brief.")
        result = build_embed_text(doc)
        assert "@brief Just a brief." in result
        assert "@details" not in result
        assert "@note" not in result

    def test_only_params(self):
        doc = _make_doc(params={"ch": "Character pointer"})
        result = build_embed_text(doc)
        assert "@param ch Character pointer" in result

    def test_only_returns(self):
        doc = _make_doc(returns="bool")
        result = build_embed_text(doc)
        assert "@return bool" in result
