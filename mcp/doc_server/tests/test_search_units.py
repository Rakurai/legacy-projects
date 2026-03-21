"""
Unit tests for search pipeline internals and utility error paths.

Tests pure-Python functions that don't need a database.
"""

import math

import pytest
from pydantic import ValidationError

from server.models import EntitySummary
from server.search import Candidate, _shape_tsrank

# ---------- _shape_tsrank ----------


class TestShapeTsrank:
    """Tests for corpus-calibrated ts_rank shaping."""

    def test_zero_raw_returns_zero(self):
        assert _shape_tsrank(0.0, ceiling=1.0) == 0.0

    def test_zero_ceiling_returns_zero(self):
        assert _shape_tsrank(0.5, ceiling=0.0) == 0.0

    def test_negative_ceiling_returns_zero(self):
        assert _shape_tsrank(0.5, ceiling=-1.0) == 0.0

    def test_raw_equals_ceiling_returns_one(self):
        result = _shape_tsrank(2.0, ceiling=2.0)
        assert abs(result - 1.0) < 1e-9

    def test_raw_below_ceiling(self):
        result = _shape_tsrank(0.5, ceiling=2.0)
        expected = math.log1p(0.5) / math.log1p(2.0)
        assert abs(result - expected) < 1e-9

    def test_raw_above_ceiling_exceeds_one(self):
        result = _shape_tsrank(5.0, ceiling=2.0)
        assert result > 1.0


# ---------- Candidate ----------


class TestCandidate:
    """Tests for the Candidate dataclass defaults."""

    def test_defaults(self):
        c = Candidate(entity_id="test")
        assert c.doc_semantic == 0.0
        assert c.symbol_semantic == 0.0
        assert c.doc_keyword == 0.0
        assert c.symbol_keyword == 0.0
        assert c.trigram == 0.0
        assert c.name_exact is False
        assert c.signature_exact is False
        assert c.ce_doc == 0.0
        assert c.ce_symbol == 0.0

    def test_signal_accumulation(self):
        c = Candidate(entity_id="x", doc_semantic=0.8, trigram=0.5, name_exact=True)
        assert c.doc_semantic == 0.8
        assert c.trigram == 0.5
        assert c.name_exact is True


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
                fan_in=0,
                fan_out=0,
            )

    def test_whitespace_stripped(self):
        summary = EntitySummary(
            entity_id="x",
            signature="  void test()  ",
            name="  test  ",
            kind="function",
            fan_in=0,
            fan_out=0,
        )
        assert summary.name == "test"
        assert summary.signature == "void test()"
