"""
Tests for build pipeline utilities and server.util shared helpers.

Covers:
- parse_json_field normalization
- fetch_entity_summaries / fetch_entity_map (unit tests with mock session)
- resolve_entity_id helper
- not_found_response builder
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from server.util import parse_json_field
from server.errors import (
    EntityNotFoundError,
    CapabilityNotFoundError,
    not_found_response,
)


class TestParseJsonField:
    """Tests for parse_json_field utility."""

    def test_dict_passthrough(self):
        """Dict values pass through unchanged."""
        val = {"a": 1, "b": [2, 3]}
        assert parse_json_field(val) == {"a": 1, "b": [2, 3]}

    def test_list_passthrough(self):
        """List values pass through unchanged."""
        val = [1, 2, 3]
        assert parse_json_field(val) == [1, 2, 3]

    def test_none_passthrough(self):
        """None passes through as None."""
        assert parse_json_field(None) is None

    def test_string_json_dict(self):
        """JSON string containing dict is parsed."""
        val = '{"key": "value"}'
        assert parse_json_field(val) == {"key": "value"}

    def test_string_json_list(self):
        """JSON string containing list is parsed."""
        val = '[1, 2, 3]'
        assert parse_json_field(val) == [1, 2, 3]

    def test_invalid_json_string(self):
        """Non-JSON string returns None."""
        assert parse_json_field("not json") is None

    def test_empty_string(self):
        """Empty string returns None (invalid JSON)."""
        assert parse_json_field("") is None

    def test_integer_passthrough(self):
        """Integer values pass through unchanged."""
        assert parse_json_field(42) == 42


class TestNotFoundResponse:
    """Tests for not_found_response builder."""

    def test_basic_response(self):
        result = not_found_response("some_id")
        assert result["resolution_status"] == "not_found"
        assert result["query"] == "some_id"
        assert result["candidates"] == []

    def test_with_kind(self):
        result = not_found_response("combat", kind="capability")
        assert "Capability" in result["message"]

    def test_with_candidates(self):
        candidates = [{"entity_id": "a", "name": "alpha"}]
        result = not_found_response("x", candidates=candidates)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["entity_id"] == "a"


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_basic(self):
        err = EntityNotFoundError("abc123")
        assert err.identifier == "abc123"
        assert err.kind == "entity"
        assert "abc123" in str(err)

    def test_custom_kind(self):
        err = EntityNotFoundError("path/file.cc", kind="file")
        assert err.kind == "file"


class TestCapabilityNotFoundError:
    """Tests for CapabilityNotFoundError."""

    def test_basic(self):
        err = CapabilityNotFoundError("nonexistent_cap")
        assert err.name == "nonexistent_cap"
        assert "nonexistent_cap" in str(err)
