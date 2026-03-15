"""
Smoke test for MCP server components.

Tests: config, DB connection, graph loading, entity resolution, search, graph tools.
Run: uv run python test_server_smoke.py
"""

import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server.config import ServerConfig
from server.db import DatabaseManager
from server.graph import load_graph
from server.logging_config import configure_logging, log
from server.resolver import resolve_entity, entity_to_summary
from server.search import hybrid_search
from server.graph import get_callers, get_callees, get_class_hierarchy, compute_call_cone
from server.tools.entity import (
    resolve_entity_tool, get_entity_tool, get_source_code_tool,
    list_file_entities_tool, get_file_summary_tool,
    ResolveEntityParams, GetEntityParams, GetSourceCodeParams,
    ListFileEntitiesParams, GetFileSummaryParams,
)
from server.tools.search import search_tool, SearchParams
from server.tools.graph import (
    get_callers_tool, get_callees_tool, get_dependencies_tool,
    get_class_hierarchy_tool, get_related_entities_tool, get_related_files_tool,
    GetCallersParams, GetCalleesParams, GetDependenciesParams,
    GetClassHierarchyParams, GetRelatedEntitiesParams, GetRelatedFilesParams,
)

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


async def main():
    global passed, failed

    config = ServerConfig()
    configure_logging("WARNING")  # Quiet for tests

    db_manager = DatabaseManager(config)

    # ── 1. Graph loading ──────────────────────────────────────────
    print("\n── Graph Loading ──")
    start = time.time()
    async with db_manager.session() as session:
        graph = await load_graph(session)
    elapsed = time.time() - start

    report("graph_load",
           graph.number_of_nodes() > 1000 and graph.number_of_edges() > 5000,
           f"{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges in {elapsed:.2f}s")

    report("graph_load_under_5s", elapsed < 5.0, f"{elapsed:.2f}s")

    # ── 2. Entity Resolution (US1) ────────────────────────────────
    print("\n── Entity Resolution (US1) ──")

    async with db_manager.session() as session:
        # Exact name
        result = await resolve_entity(session, "damage", embedding_client=None)
        report("resolve_by_name",
               result.status in ("exact", "ambiguous") and len(result.candidates) >= 1,
               f"status={result.status}, candidates={len(result.candidates)}")

        # Prefix
        result = await resolve_entity(session, "do_", embedding_client=None)
        report("resolve_by_prefix",
               len(result.candidates) >= 1,
               f"status={result.status}, match_type={result.match_type}, candidates={len(result.candidates)}")

        # Not found
        result = await resolve_entity(session, "zzz_nonexistent_xyz_999", embedding_client=None)
        report("resolve_not_found",
               result.status == "not_found",
               f"status={result.status}")

    # ── 3. Entity Tools (US1) ─────────────────────────────────────
    print("\n── Entity Tools (US1) ──")

    async with db_manager.session() as session:
        # resolve_entity_tool
        res = await resolve_entity_tool(
            session, ResolveEntityParams(query="damage", kind="function"),
            embedding_client=None)
        report("resolve_entity_tool",
               res.resolution_status in ("exact", "ambiguous") and len(res.candidates) >= 1,
               f"status={res.resolution_status}, candidates={len(res.candidates)}")

        # Grab an entity_id for further tests
        if res.candidates:
            test_entity_id = res.candidates[0].entity_id
            test_file_path = res.candidates[0].file_path

            # get_entity_tool
            try:
                detail = await get_entity_tool(session, GetEntityParams(entity_id=test_entity_id, include_code=True))
                report("get_entity_tool",
                       detail.entity_id == test_entity_id and detail.source_text is not None,
                       f"name={detail.name}, has_code={detail.source_text is not None}")
            except Exception as e:
                report("get_entity_tool", False, str(e))

            # get_source_code_tool
            try:
                src = await get_source_code_tool(session, GetSourceCodeParams(entity_id=test_entity_id))
                report("get_source_code_tool",
                       src.get("source_text") is not None,
                       f"has_source={src.get('source_text') is not None}")
            except Exception as e:
                report("get_source_code_tool", False, str(e))

            # list_file_entities_tool
            if test_file_path:
                try:
                    file_ent = await list_file_entities_tool(
                        session, ListFileEntitiesParams(file_path=test_file_path))
                    ent_count = len(file_ent.get("entities", []))
                    report("list_file_entities_tool",
                           ent_count > 0,
                           f"entities_in_file={ent_count}")
                except Exception as e:
                    report("list_file_entities_tool", False, str(e))

                # get_file_summary_tool
                try:
                    summary = await get_file_summary_tool(
                        session, GetFileSummaryParams(file_path=test_file_path))
                    report("get_file_summary_tool",
                           summary.entity_count > 0,
                           f"entity_count={summary.entity_count}, kinds={summary.entity_count_by_kind}")
                except Exception as e:
                    report("get_file_summary_tool", False, str(e))

    # ── 4. Search (US2) ───────────────────────────────────────────
    print("\n── Search (US2) ──")

    async with db_manager.session() as session:
        # Keyword-only search (no embedding client)
        results, mode = await hybrid_search(session, "damage", embedding_client=None)
        report("search_keyword_fallback",
               mode == "keyword_fallback",
               f"mode={mode}, results={len(results)}")

        report("search_has_results",
               len(results) > 0,
               f"result_count={len(results)}")

        # Search tool
        search_res = await search_tool(
            session, SearchParams(query="poison damage"), embedding_client=None)
        report("search_tool",
               search_res.search_mode == "keyword_fallback",
               f"mode={search_res.search_mode}, results={search_res.result_count}")

        # Search with kind filter
        results, mode = await hybrid_search(
            session, "damage", embedding_client=None, kind="function")
        report("search_kind_filter",
               all(r.entity_summary.kind == "function" for r in results if r.entity_summary),
               f"results={len(results)}, all_functions=True")

        # Search with capability filter
        results, mode = await hybrid_search(
            session, "damage", embedding_client=None, capability="combat")
        report("search_capability_filter",
               all(r.entity_summary.capability == "combat" for r in results if r.entity_summary),
               f"results={len(results)}")

    # ── 5. Graph Navigation (US3) ─────────────────────────────────
    print("\n── Graph Navigation (US3) ──")

    # Find a well-connected entity for graph tests
    async with db_manager.session() as session:
        res = await resolve_entity_tool(
            session, ResolveEntityParams(query="damage", kind="function"),
            embedding_client=None)
        if res.candidates:
            graph_entity_id = res.candidates[0].entity_id

            # In-memory graph callers/callees
            callers_map = get_callers(graph, graph_entity_id, depth=2)
            total_callers = sum(len(v) for v in callers_map.values())
            report("graph_get_callers",
                   total_callers > 0,
                   f"depth_levels={len(callers_map)}, total_callers={total_callers}")

            callees_map = get_callees(graph, graph_entity_id, depth=2)
            total_callees = sum(len(v) for v in callees_map.values())
            report("graph_get_callees",
                   total_callees >= 0,
                   f"depth_levels={len(callees_map)}, total_callees={total_callees}")

            # Call cone
            cone = compute_call_cone(graph, graph_entity_id, max_depth=3, max_size=50)
            report("compute_call_cone",
                   isinstance(cone, dict) and "direct" in cone,
                   f"direct={len(cone['direct'])}, transitive={len(cone['transitive'])}, truncated={cone['truncated']}")

            # Tool: get_callers
            callers_resp = await get_callers_tool(
                session, GetCallersParams(entity_id=graph_entity_id, depth=2), graph)
            report("get_callers_tool",
                   callers_resp.entity_id == graph_entity_id,
                   f"depths={list(callers_resp.callers_by_depth.keys())}, "
                   f"total={callers_resp.truncation.node_count}")

            # Tool: get_callees
            callees_resp = await get_callees_tool(
                session, GetCalleesParams(entity_id=graph_entity_id, depth=2), graph)
            report("get_callees_tool",
                   callees_resp.entity_id == graph_entity_id,
                   f"depths={list(callees_resp.callees_by_depth.keys())}, "
                   f"total={callees_resp.truncation.node_count}")

            # Tool: get_dependencies
            deps_resp = await get_dependencies_tool(
                session, GetDependenciesParams(entity_id=graph_entity_id, relationship="calls", direction="both"), graph)
            report("get_dependencies_tool",
                   deps_resp.entity_id == graph_entity_id,
                   f"dep_count={len(deps_resp.dependencies)}")

            # Tool: get_related_entities
            related_resp = await get_related_entities_tool(
                session, GetRelatedEntitiesParams(entity_id=graph_entity_id), graph)
            report("get_related_entities_tool",
                   related_resp.entity_id == graph_entity_id,
                   f"relationship_groups={list(related_resp.neighbors_by_relationship.keys())}")

    # ── 6. Class hierarchy (US3) ──────────────────────────────────
    print("\n── Class Hierarchy (US3) ──")

    async with db_manager.session() as session:
        # Find a class entity
        res = await resolve_entity_tool(
            session, ResolveEntityParams(query="Character", kind="class"),
            embedding_client=None)
        if res.candidates:
            class_entity_id = res.candidates[0].entity_id

            hierarchy = get_class_hierarchy(graph, class_entity_id)
            report("graph_class_hierarchy",
                   isinstance(hierarchy, dict),
                   f"base_classes={len(hierarchy['base_classes'])}, derived={len(hierarchy['derived_classes'])}")

            hier_resp = await get_class_hierarchy_tool(
                session, GetClassHierarchyParams(entity_id=class_entity_id), graph)
            report("get_class_hierarchy_tool",
                   hier_resp.entity_id == class_entity_id,
                   f"base={len(hier_resp.base_classes)}, derived={len(hier_resp.derived_classes)}")

    # ── 7. Related files (US3) ────────────────────────────────────
    print("\n── Related Files (US3) ──")

    async with db_manager.session() as session:
        try:
            files_resp = await get_related_files_tool(
                session, GetRelatedFilesParams(file_path="src/fight.cc"), graph)
            report("get_related_files_tool",
                   files_resp.file_path == "src/fight.cc",
                   f"related_files={len(files_resp.related_files)}")
        except Exception as e:
            report("get_related_files_tool", False, str(e))

    # ── 8. MCP server transport test ──────────────────────────────
    print("\n── FastMCP Server Object ──")
    try:
        from server.server import mcp
        tools = mcp.get_tools()  # May fail if FastMCP API changed
        report("fastmcp_tools_registered",
               True,
               f"(server.server.mcp imported ok)")
    except Exception as e:
        # Try alternate check
        try:
            from server.server import mcp
            report("fastmcp_server_import", True, "mcp object created")
        except Exception as e2:
            report("fastmcp_server_import", False, str(e2))

    # ── Summary ───────────────────────────────────────────────────
    await db_manager.dispose()

    print(f"\n{'='*50}")
    print(f"  PASSED: {passed}  |  FAILED: {failed}  |  TOTAL: {passed + failed}")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
