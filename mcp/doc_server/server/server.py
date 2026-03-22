"""
MCP Documentation Server - FastMCP Server Entry Point.

Slim entry point: imports the shared mcp app, imports tool/resource/prompt
registration modules (which register themselves on `mcp`), and provides main().
"""

import json
from urllib.parse import unquote

from fastmcp import Context

# ---- Import tool modules (side-effect: registers @mcp.tool decorators) ----
import server.tools.behavior
import server.tools.capability
import server.tools.entity
import server.tools.explain
import server.tools.graph
import server.tools.search  # noqa: F401
from server.app import get_ctx, mcp

# ---- Resources ----
from server.resources import (
    get_capabilities_resource,
    get_capability_detail_resource,
    get_entity_resource,
    get_file_entities_resource,
    get_stats_resource,
)


@mcp.resource("legacy://capabilities")
async def capabilities_resource(ctx: Context) -> str:
    """List all capability groups with metadata."""
    lc = get_ctx(ctx)
    async with lc["db_manager"].session() as session:
        data = await get_capabilities_resource(session)
    return json.dumps(data, default=str)


@mcp.resource("legacy://capability/{name}")
async def capability_detail_resource(name: str, ctx: Context) -> str:
    """Get detailed capability information."""
    lc = get_ctx(ctx)
    async with lc["db_manager"].session() as session:
        data = await get_capability_detail_resource(session, name)
    return json.dumps(data, default=str)


@mcp.resource("legacy://entity/{entity_id}")
async def entity_resource(entity_id: str, ctx: Context) -> str:
    """Get full entity details by entity_id."""
    lc = get_ctx(ctx)
    async with lc["db_manager"].session() as session:
        data = await get_entity_resource(session, entity_id)
    return json.dumps(data, default=str)


@mcp.resource("legacy://file/{path}")
async def file_entities_resource(path: str, ctx: Context) -> str:
    """List all entities defined in a source file."""
    file_path = unquote(path)
    lc = get_ctx(ctx)
    async with lc["db_manager"].session() as session:
        data = await get_file_entities_resource(session, file_path)
    return json.dumps(data, default=str)


@mcp.resource("legacy://stats")
async def stats_resource(ctx: Context) -> str:
    """Get aggregate server statistics."""
    lc = get_ctx(ctx)
    async with lc["db_manager"].session() as session:
        data = await get_stats_resource(
            session,
            graph=lc["graph"],
        )
    return json.dumps(data, default=str)


# ---- Prompts ----

from server.prompts import (  # noqa: E402
    analyze_behavior_prompt,
    compare_entry_points_prompt,
    explain_entity_prompt,
    explore_capability_prompt,
)


@mcp.prompt()
def explain_entity(entity_name: str) -> list[dict[str, str]]:
    """Comprehensive entity explanation workflow."""
    return explain_entity_prompt(entity_name)


@mcp.prompt()
def analyze_behavior(entity_name: str, max_depth: int = 5) -> list[dict[str, str]]:
    """Behavioral analysis workflow for a function."""
    return analyze_behavior_prompt(entity_name, max_depth)


@mcp.prompt()
def compare_entry_points(entry_point_names: list[str]) -> list[dict[str, str]]:
    """Entry point comparison workflow."""
    return compare_entry_points_prompt(entry_point_names)


@mcp.prompt()
def explore_capability(capability_name: str) -> list[dict[str, str]]:
    """Capability exploration workflow."""
    return explore_capability_prompt(capability_name)


# ---- Entry Point ----


def main() -> None:
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
