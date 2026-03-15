"""
MCP App Instance - Shared FastMCP application object.

This module exists to break circular imports between server.py (which imports
tool modules) and tool modules (which need the mcp instance to register on).
"""

from fastmcp import FastMCP, Context

from server.lifespan import lifespan, LifespanContext

# Create FastMCP app
mcp = FastMCP(
    "Legacy Documentation Server",
    lifespan=lifespan,
)


def get_ctx(ctx: Context) -> LifespanContext:
    """Extract typed lifespan context from FastMCP Context."""
    return ctx.lifespan_context  # type: ignore[return-value]
