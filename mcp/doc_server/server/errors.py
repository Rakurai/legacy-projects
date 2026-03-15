"""
Structured Error Handling - Per-spec error classes and response builders.

Per spec FR-046/FR-047, entity-not-found returns a successful MCP response
with resolution_status="not_found" (not an MCP error). Hard failures
(invalid params, DB errors) remain MCP errors.
"""

from __future__ import annotations

from typing import Any


class EntityNotFoundError(Exception):
    """
    Raised when a tool cannot find the requested entity.

    Caught by server.py wrappers and converted to a successful response
    with resolution_status="not_found" per FR-047.
    """

    def __init__(self, identifier: str, kind: str = "entity"):
        self.identifier = identifier
        self.kind = kind
        super().__init__(f"{kind} not found: {identifier}")


class CapabilityNotFoundError(Exception):
    """Raised when a capability name doesn't exist."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Capability not found: {name}")


def not_found_response(
    identifier: str,
    kind: str = "entity",
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Build a structured not-found response per spec FR-047.

    The spec requires: "Unknown entity name: System returns successful MCP
    response with not_found status and nearest matches (not an MCP error)."

    Args:
        identifier: The query/id that was not found
        kind: What was being looked up (entity, capability, file, etc.)
        candidates: Optional nearest-match candidates

    Returns:
        Dict suitable for returning directly from an MCP tool
    """
    return {
        "resolution_status": "not_found",
        "message": f"{kind.capitalize()} not found: {identifier}",
        "query": identifier,
        "candidates": candidates or [],
    }
