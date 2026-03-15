"""
Unit tests for search score merging and utility error paths.

Tests pure-Python functions that don't need a database.
"""

import pytest
from pydantic import ValidationError

from server.search import _merge_scores, _provenance_for
from server.db_models import Entity
from server.models import EntitySummary


# ---------- _merge_scores ----------

class TestMergeScores:
    """Tests for the score merging logic."""

    def test_exact_only(self):
        """Exact match only gets the exact weight."""
        result = _merge_scores({"a"}, {}, {}, limit=10)
        assert len(result) == 1
        assert result[0] == ("a", 10.0)

    def test_keyword_only(self):
        """Keyword match only gets keyword weight."""
        result = _merge_scores(set(), {"a": 0.5}, {}, limit=10)
        assert len(result) == 1
        assert result[0][0] == "a"
        assert abs(result[0][1] - 0.5 * 0.4) < 1e-9

    def test_semantic_only(self):
        """Semantic match only gets semantic weight."""
        result = _merge_scores(set(), {}, {"a": 0.8}, limit=10)
        assert len(result) == 1
        assert result[0][0] == "a"
        assert abs(result[0][1] - 0.8 * 0.6) < 1e-9

    def test_all_three_combined(self):
        """Entity matching all three strategies gets combined score."""
        result = _merge_scores({"a"}, {"a": 0.5}, {"a": 0.8}, limit=10)
        expected = 10.0 + 0.8 * 0.6 + 0.5 * 0.4
        assert len(result) == 1
        assert abs(result[0][1] - expected) < 1e-9

    def test_sorting_descending(self):
        """Results are sorted by score descending."""
        result = _merge_scores(
            {"a"},
            {"b": 1.0, "c": 0.5},
            {},
            limit=10,
        )
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_limit_applied(self):
        """Only top N results are returned."""
        keyword_scores = {f"e{i}": float(i) / 10 for i in range(20)}
        result = _merge_scores(set(), keyword_scores, {}, limit=5)
        assert len(result) == 5

    def test_empty_inputs(self):
        """No matches returns empty list."""
        result = _merge_scores(set(), {}, {}, limit=10)
        assert result == []

    def test_mixed_sources(self):
        """Different entities from different sources are all included."""
        result = _merge_scores(
            {"exact_only"},
            {"keyword_only": 0.5},
            {"semantic_only": 0.7},
            limit=10,
        )
        ids = {eid for eid, _ in result}
        assert ids == {"exact_only", "keyword_only", "semantic_only"}


# ---------- _provenance_for ----------

class TestProvenanceFor:
    """Tests for provenance classification."""

    _BASE = dict(entity_id="x", compound_id="x", signature="x", name="x",
                 kind="function", entity_type="member")

    @pytest.mark.parametrize("doc_state,expected", [
        ("refined_summary", "llm_generated"),
        ("refined_usage", "llm_generated"),
        ("generated_summary", "llm_generated"),
        ("extracted_summary", "doxygen_extracted"),
        (None, "doxygen_extracted"),
    ], ids=["refined_summary", "refined_usage", "generated_summary", "extracted_summary", "none"])
    def test_provenance(self, doc_state, expected):
        entity = Entity(**self._BASE, doc_state=doc_state)
        assert _provenance_for(entity) == expected


# ---------- EntitySummary validator ----------

class TestEntitySummaryValidator:
    """Tests for EntitySummary field validators."""

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            EntitySummary(
                entity_id="x",
                signature="void test()",
                name="",
                kind="function",
                doc_state="extracted_summary",
                doc_quality="low",
                fan_in=0,
                fan_out=0,
            )

    def test_empty_signature_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            EntitySummary(
                entity_id="x",
                signature="   ",
                name="test",
                kind="function",
                doc_state="extracted_summary",
                doc_quality="low",
                fan_in=0,
                fan_out=0,
            )

    def test_whitespace_stripped(self):
        summary = EntitySummary(
            entity_id="x",
            signature="  void test()  ",
            name="  test  ",
            kind="function",
            doc_state="extracted_summary",
            doc_quality="low",
            fan_in=0,
            fan_out=0,
        )
        assert summary.name == "test"
        assert summary.signature == "void test()"
