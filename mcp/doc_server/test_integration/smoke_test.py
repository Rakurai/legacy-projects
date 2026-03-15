"""
Smoke test for MCP Documentation Server.

Tests core functionality against the live database:
- Database connection
- Graph loading
- Entity resolution (all stages)
- Entity detail retrieval
- Search (keyword fallback)
- Graph navigation (callers, callees)
- File listing and summary

Run: uv run python smoke_test.py
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server.config import ServerConfig
from server.db import DatabaseManager
from server.graph import load_graph
from server.resolver import resolve_entity
from server.tools.entity import (
    resolve_entity_tool, ResolveEntityParams,
    get_entity_tool, GetEntityParams,
    get_source_code_tool, GetSourceCodeParams,
    list_file_entities_tool, ListFileEntitiesParams,
    get_file_summary_tool, GetFileSummaryParams,
)
from server.tools.search import search_tool, SearchParams
from server.tools.graph import (
    get_callers_tool, GetCallersParams,
    get_callees_tool, GetCalleesParams,
    get_dependencies_tool, GetDependenciesParams,
    get_class_hierarchy_tool, GetClassHierarchyParams,
    get_related_entities_tool, GetRelatedEntitiesParams,
    get_related_files_tool, GetRelatedFilesParams,
)
from server.logging_config import configure_logging, log


passed = 0
failed = 0
errors = []


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        errors.append((name, detail))
        print(f"  ❌ {name}: {detail}")


async def main():
    global passed, failed

    config = ServerConfig()
    configure_logging("WARNING")

    db = DatabaseManager(config)
    graph = None

    print("\n=== MCP Doc Server Smoke Tests ===\n")

    # --- 1. Database Connection ---
    print("[1] Database Connection")
    try:
        async with db.session() as session:
            from sqlalchemy import text
            row = await session.execute(text("SELECT COUNT(*) FROM entities"))
            count = row.scalar()
            report("connect_and_query", count > 0, f"entities={count}")
    except Exception as e:
        report("connect_and_query", False, str(e))

    # --- 2. Graph Loading ---
    print("[2] Graph Loading")
    try:
        async with db.session() as session:
            graph = await load_graph(session)
            report("load_graph", graph.number_of_nodes() > 0,
                   f"nodes={graph.number_of_nodes()}, edges={graph.number_of_edges()}")
    except Exception as e:
        report("load_graph", False, str(e))

    # --- 3. Entity Resolution ---
    print("[3] Entity Resolution")
    try:
        async with db.session() as session:
            # Exact name match
            r = await resolve_entity(session, "damage", embedding_client=None)
            report("resolve_name_exact", r.status in ("exact", "ambiguous") and len(r.candidates) >= 1,
                   f"status={r.status}, candidates={len(r.candidates)}")

            # Prefix match
            r = await resolve_entity(session, "do_k", embedding_client=None)
            report("resolve_prefix", r.status == "ambiguous" and r.match_type == "name_prefix",
                   f"status={r.status}, match={r.match_type}, candidates={len(r.candidates)}")

            # Not found
            r = await resolve_entity(session, "zzz_nonexistent_xyz_99", embedding_client=None)
            report("resolve_not_found", r.status == "not_found",
                   f"status={r.status}")

            # Kind filter
            r = await resolve_entity(session, "Character", kind="class", embedding_client=None)
            report("resolve_kind_filter", len(r.candidates) >= 1 and all(c.kind == "class" for c in r.candidates),
                   f"candidates={len(r.candidates)}")
    except Exception as e:
        report("resolve_entity", False, str(e))

    # --- 4. Entity Detail ---
    print("[4] Entity Detail")
    try:
        async with db.session() as session:
            # First resolve to get an entity_id
            r = await resolve_entity(session, "damage", kind="function", embedding_client=None)
            if r.candidates:
                eid = r.candidates[0].entity_id
                detail = await get_entity_tool(session, GetEntityParams(entity_id=eid, include_code=True))
                report("get_entity_with_code", detail.source_text is not None and len(detail.source_text) > 0,
                       f"source_len={len(detail.source_text) if detail.source_text else 0}")
                report("get_entity_fields", detail.kind == "function" and detail.entity_id is not None,
                       f"kind={detail.kind}, brief={'yes' if detail.brief else 'no'}, quality={detail.doc_quality}")
            else:
                report("get_entity_with_code", False, "no candidates found")
                report("get_entity_fields", False, "no candidates found")
    except Exception as e:
        report("get_entity", False, str(e))

    # --- 5. Source Code Retrieval ---
    print("[5] Source Code Retrieval")
    try:
        async with db.session() as session:
            r = await resolve_entity(session, "damage", kind="function", embedding_client=None)
            if r.candidates:
                eid = r.candidates[0].entity_id
                src = await get_source_code_tool(session, GetSourceCodeParams(entity_id=eid))
                report("get_source_code", src.get("source_text") is not None,
                       f"file={src.get('file_path')}")
            else:
                report("get_source_code", False, "no entity")
    except Exception as e:
        report("get_source_code", False, str(e))

    # --- 6. Search ---
    print("[6] Search (keyword fallback)")
    try:
        async with db.session() as session:
            result = await search_tool(session, SearchParams(query="damage", limit=10), embedding_client=None)
            report("search_keyword", result.search_mode == "keyword_fallback" and result.result_count > 0,
                   f"mode={result.search_mode}, results={result.result_count}")

            # With filters
            result = await search_tool(session, SearchParams(query="damage", kind="function", capability="combat", limit=10), embedding_client=None)
            report("search_filtered", result.result_count >= 0,
                   f"results={result.result_count}")

            # Empty results
            result = await search_tool(session, SearchParams(query="zzz_nothing_xyz", limit=10), embedding_client=None)
            report("search_empty", result.result_count == 0,
                   f"results={result.result_count}")
    except Exception as e:
        report("search", False, str(e))

    # --- 7. Graph Navigation ---
    print("[7] Graph Navigation")
    if graph is None:
        report("graph_not_loaded", False, "graph failed to load")
    else:
        try:
            async with db.session() as session:
                # Find an entity with known callers/callees
                r = await resolve_entity(session, "damage", kind="function", embedding_client=None)
                if r.candidates:
                    eid = r.candidates[0].entity_id

                    # Callers
                    callers = await get_callers_tool(session, GetCallersParams(entity_id=eid, depth=1), graph=graph)
                    total_callers = sum(len(v) for v in callers.callers_by_depth.values())
                    report("get_callers", total_callers > 0,
                           f"callers={total_callers}")

                    # Callees
                    callees = await get_callees_tool(session, GetCalleesParams(entity_id=eid, depth=1), graph=graph)
                    total_callees = sum(len(v) for v in callees.callees_by_depth.values())
                    report("get_callees", total_callees >= 0,
                           f"callees={total_callees}")

                    # Dependencies
                    deps = await get_dependencies_tool(session, GetDependenciesParams(entity_id=eid, direction="both"), graph=graph)
                    report("get_dependencies", len(deps.dependencies) > 0,
                           f"deps={len(deps.dependencies)}")

                    # Related entities
                    related = await get_related_entities_tool(session, GetRelatedEntitiesParams(entity_id=eid), graph=graph)
                    total_neighbors = sum(len(v) for v in related.neighbors_by_relationship.values())
                    report("get_related_entities", total_neighbors > 0,
                           f"neighbors={total_neighbors}")

                else:
                    report("graph_navigation", False, "no entity to test")
        except Exception as e:
            report("graph_navigation", False, str(e))

    # --- 8. Class Hierarchy ---
    print("[8] Class Hierarchy")
    if graph:
        try:
            async with db.session() as session:
                r = await resolve_entity(session, "Character", kind="class", embedding_client=None)
                if r.candidates:
                    eid = r.candidates[0].entity_id
                    hier = await get_class_hierarchy_tool(session, GetClassHierarchyParams(entity_id=eid), graph=graph)
                    report("class_hierarchy", True,
                           f"base={len(hier.base_classes)}, derived={len(hier.derived_classes)}")
                else:
                    report("class_hierarchy", False, "no class entity")
        except Exception as e:
            report("class_hierarchy", False, str(e))

    # --- 9. File Operations ---
    print("[9] File Operations")
    try:
        async with db.session() as session:
            result = await list_file_entities_tool(session, ListFileEntitiesParams(file_path="src/fight.cc"))
            entities_list = result.get("entities", [])
            report("list_file_entities", len(entities_list) > 0,
                   f"entities={len(entities_list)}")

            summary = await get_file_summary_tool(session, GetFileSummaryParams(file_path="src/fight.cc"))
            report("get_file_summary", summary.entity_count > 0,
                   f"count={summary.entity_count}, kinds={summary.entity_count_by_kind}")
    except Exception as e:
        report("file_operations", False, str(e))

    # --- 10. Related Files ---
    print("[10] Related Files")
    if graph:
        try:
            async with db.session() as session:
                result = await get_related_files_tool(session, GetRelatedFilesParams(file_path="src/fight.cc"), graph=graph)
                report("get_related_files", True,
                       f"related={len(result.related_files)}")
        except Exception as e:
            report("get_related_files", False, str(e))

    # --- 11. MCP Server Import ---
    print("[11] Server Import")
    try:
        from server.server import mcp
        report("server_import", mcp is not None, f"name={mcp.name}")
    except Exception as e:
        report("server_import", False, str(e))

    # --- Summary ---
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if errors:
        print(f"\nFailures:")
        for name, detail in errors:
            print(f"  ❌ {name}: {detail}")
    print()

    await db.dispose()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
