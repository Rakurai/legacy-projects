"""
Tests for error classes and response builders.

Covers:
- not_found_response builder
- EntityNotFoundError
- CapabilityNotFoundError
"""

import pytest

from server.errors import (
    EntityNotFoundError,
    CapabilityNotFoundError,
    not_found_response,
)


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

    def test_custom_kind(self):
        err = EntityNotFoundError("path/file.cc", kind="file")
        assert err.kind == "file"
        assert "path/file.cc" in str(err)
