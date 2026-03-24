"""
Tests for MCP server registration.

Verifies that the FastMCP server object:
- Imports without errors
- Has all expected tools, resources, templates, and prompts registered

Uses the public FastMCP async API (list_tools, list_resources, etc.)
— no internal/private attribute access.
"""

import pytest

from server.server import mcp


EXPECTED_TOOLS = {
    "get_entity",
    "get_source_code",
    "search",
    "get_callers",
    "get_callees",
    "get_dependencies",
    "get_class_hierarchy",
    "get_related_entities",
    "get_behavior_slice",
    "get_state_touches",
    "list_capabilities",
    "get_capability_detail",
    "compare_capabilities",
    "list_entry_points",
    "get_entry_point_info",
    "explain_interface",
}

EXPECTED_RESOURCES = {
    "legacy://capabilities",
    "legacy://components",
    "legacy://stats",
}

EXPECTED_TEMPLATES = {
    "legacy://capability/{name}",
    "legacy://component/{component_id}",
    "legacy://entity/{entity_id}",
    "legacy://file/{path}",
}

EXPECTED_PROMPTS = {
    "explain_entity",
    "analyze_behavior",
    "compare_entry_points",
    "explore_capability",
    "research_feature",
}


@pytest.mark.asyncio
async def test_all_tools_registered():
    """All expected tools are registered on the server."""
    tools = await mcp.list_tools()
    registered = {t.name for t in tools}

    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Tools not registered: {missing}"


@pytest.mark.asyncio
async def test_no_unexpected_tools():
    """No extra tools registered beyond the expected set."""
    tools = await mcp.list_tools()
    registered = {t.name for t in tools}

    unexpected = registered - EXPECTED_TOOLS
    assert not unexpected, f"Unexpected tools registered: {unexpected}"


@pytest.mark.asyncio
async def test_all_resources_registered():
    """All expected static resources are registered."""
    resources = await mcp.list_resources()
    registered = {str(r.uri) for r in resources}

    missing = EXPECTED_RESOURCES - registered
    assert not missing, f"Resources not registered: {missing}"


@pytest.mark.asyncio
async def test_all_templates_registered():
    """All expected resource templates are registered."""
    templates = await mcp.list_resource_templates()
    registered = {str(t.uri_template) for t in templates}

    missing = EXPECTED_TEMPLATES - registered
    assert not missing, f"Templates not registered: {missing}"


@pytest.mark.asyncio
async def test_all_prompts_registered():
    """All expected prompts are registered."""
    prompts = await mcp.list_prompts()
    registered = {p.name for p in prompts}

    missing = EXPECTED_PROMPTS - registered
    assert not missing, f"Prompts not registered: {missing}"
