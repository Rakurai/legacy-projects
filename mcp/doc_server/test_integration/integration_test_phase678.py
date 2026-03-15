"""
Integration tests for Phase 6-8 tools against the live database.

Tests behavioral analysis, capability system, resources, and prompts.
Run with: uv run python integration_test_phase678.py
"""

import asyncio
import sys
import json

# Test counter
_passed = 0
_failed = 0
_errors = []


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, msg: str):
    global _failed
    _failed += 1
    _errors.append(f"{name}: {msg}")
    print(f"  ❌ {name}: {msg}")


async def run_tests():
    from server.config import ServerConfig
    from server.db import DatabaseManager
    from server.graph import load_graph

    config = ServerConfig()
    db = DatabaseManager(config)

    # Load graph
    async with db.session() as session:
        graph = await load_graph(session)

    print(f"\nGraph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    # ----------------------------------------------------------------
    # Phase 6: Behavioral Analysis
    # ----------------------------------------------------------------
    print("\n== Phase 6: Behavioral Analysis ==")

    # T068/T069: get_behavior_slice
    print("\n--- get_behavior_slice ---")
    from server.tools.behavior import (
        GetBehaviorSliceParams, GetStateTouchesParams, GetHotspotsParams,
        get_behavior_slice_tool, get_state_touches_tool, get_hotspots_tool,
    )

    try:
        async with db.session() as session:
            # Find an entry point entity to test with
            from sqlmodel import select
            from server.db_models import Entity
            result = await session.execute(
                select(Entity)
                .where(Entity.is_entry_point == True)
                .where(Entity.name.like("do_%"))
                .limit(1)
            )
            ep = result.scalar_one_or_none()

            if ep:
                params = GetBehaviorSliceParams(entity_id=ep.entity_id, max_depth=3, max_cone_size=50)
                resp = await get_behavior_slice_tool(session, params, graph)
                b = resp.behavior

                assert b.entry_point.entity_id == ep.entity_id
                assert isinstance(b.direct_callees, list)
                assert isinstance(b.transitive_cone, list)
                assert isinstance(b.capabilities_touched, dict)
                assert isinstance(b.globals_used, list)
                assert isinstance(b.side_effects, dict)
                ok(f"get_behavior_slice for {ep.name}: {len(b.direct_callees)} direct, {len(b.transitive_cone)} transitive, {len(b.capabilities_touched)} caps")
            else:
                fail("get_behavior_slice", "No entry point found")
    except Exception as e:
        fail("get_behavior_slice", str(e))

    # T070/T071: get_state_touches
    print("\n--- get_state_touches ---")
    try:
        async with db.session() as session:
            if ep:
                params = GetStateTouchesParams(entity_id=ep.entity_id)
                resp = await get_state_touches_tool(session, params, graph)

                assert resp.entity_id == ep.entity_id
                assert isinstance(resp.direct_uses, list)
                assert isinstance(resp.transitive_uses, list)
                assert isinstance(resp.direct_side_effects, list)
                assert isinstance(resp.transitive_side_effects, list)
                ok(f"get_state_touches for {ep.name}: {len(resp.direct_uses)} direct, {len(resp.transitive_uses)} transitive uses")
    except Exception as e:
        fail("get_state_touches", str(e))

    # T075: get_hotspots
    print("\n--- get_hotspots ---")
    for metric in ["fan_in", "fan_out", "bridge", "underdocumented"]:
        try:
            async with db.session() as session:
                params = GetHotspotsParams(metric=metric, limit=5)
                resp = await get_hotspots_tool(session, params)

                assert resp.metric == metric
                assert isinstance(resp.hotspots, list)
                ok(f"get_hotspots metric={metric}: {len(resp.hotspots)} results")
        except Exception as e:
            fail(f"get_hotspots metric={metric}", str(e))

    # ----------------------------------------------------------------
    # Phase 7: Capability System
    # ----------------------------------------------------------------
    print("\n== Phase 7: Capability System ==")

    from server.tools.capability import (
        ListCapabilitiesParams, GetCapabilityDetailParams,
        CompareCapabilitiesParams, ListEntryPointsParams,
        GetEntryPointInfoParams,
        list_capabilities_tool, get_capability_detail_tool,
        compare_capabilities_tool, list_entry_points_tool,
        get_entry_point_info_tool,
    )

    # T080: list_capabilities
    print("\n--- list_capabilities ---")
    cap_names = []
    try:
        async with db.session() as session:
            params = ListCapabilitiesParams()
            resp = await list_capabilities_tool(session, params)

            assert isinstance(resp.capabilities, list)
            assert len(resp.capabilities) > 0
            cap_names = [c.name for c in resp.capabilities]
            ok(f"list_capabilities: {len(resp.capabilities)} capabilities")
    except Exception as e:
        fail("list_capabilities", str(e))

    # T081: get_capability_detail
    print("\n--- get_capability_detail ---")
    if cap_names:
        test_cap = cap_names[0]
        try:
            async with db.session() as session:
                params = GetCapabilityDetailParams(capability=test_cap, include_functions=False)
                resp = await get_capability_detail_tool(session, params)

                assert resp.detail.name == test_cap
                assert isinstance(resp.detail.dependencies, list)
                assert isinstance(resp.detail.entry_points, list)
                ok(f"get_capability_detail for {test_cap}: {resp.detail.function_count} functions, {len(resp.detail.dependencies)} deps")
        except Exception as e:
            fail(f"get_capability_detail for {test_cap}", str(e))

        # Also test with include_functions=True
        try:
            async with db.session() as session:
                params = GetCapabilityDetailParams(capability=test_cap, include_functions=True)
                resp = await get_capability_detail_tool(session, params)
                assert resp.detail.functions is not None
                ok(f"get_capability_detail with functions: {len(resp.detail.functions)} functions")
        except Exception as e:
            fail("get_capability_detail with functions", str(e))

    # T082: compare_capabilities
    print("\n--- compare_capabilities ---")
    if len(cap_names) >= 2:
        try:
            async with db.session() as session:
                params = CompareCapabilitiesParams(capabilities=cap_names[:2], limit=10)
                resp = await compare_capabilities_tool(session, params, graph)

                assert resp.capabilities == cap_names[:2]
                assert isinstance(resp.shared_dependencies, list)
                assert isinstance(resp.unique_dependencies, dict)
                assert isinstance(resp.bridge_entities, list)
                ok(f"compare_capabilities {cap_names[:2]}: {len(resp.shared_dependencies)} shared, {len(resp.bridge_entities)} bridges")
        except Exception as e:
            fail(f"compare_capabilities", str(e))

    # T083: list_entry_points
    print("\n--- list_entry_points ---")
    try:
        async with db.session() as session:
            params = ListEntryPointsParams(limit=10)
            resp = await list_entry_points_tool(session, params)

            assert isinstance(resp.entry_points, list)
            assert len(resp.entry_points) > 0
            ok(f"list_entry_points: {len(resp.entry_points)} entry points")
    except Exception as e:
        fail("list_entry_points", str(e))

    # With capability filter
    if cap_names:
        try:
            async with db.session() as session:
                params = ListEntryPointsParams(capability=cap_names[0], limit=10)
                resp = await list_entry_points_tool(session, params)
                ok(f"list_entry_points cap={cap_names[0]}: {len(resp.entry_points)} entry points")
        except Exception as e:
            fail(f"list_entry_points with capability filter", str(e))

    # With name pattern
    try:
        async with db.session() as session:
            params = ListEntryPointsParams(name_pattern="do_%", limit=10)
            resp = await list_entry_points_tool(session, params)
            ok(f"list_entry_points pattern=do_%: {len(resp.entry_points)} entry points")
    except Exception as e:
        fail("list_entry_points with name pattern", str(e))

    # T084: get_entry_point_info
    print("\n--- get_entry_point_info ---")
    if ep:
        try:
            async with db.session() as session:
                params = GetEntryPointInfoParams(entity_id=ep.entity_id)
                resp = await get_entry_point_info_tool(session, params, graph)

                assert resp.entry_point.entity_id == ep.entity_id
                assert isinstance(resp.capabilities_exercised, dict)
                ok(f"get_entry_point_info for {ep.name}: {len(resp.capabilities_exercised)} capabilities exercised")
        except Exception as e:
            fail("get_entry_point_info", str(e))

    # ----------------------------------------------------------------
    # Phase 8: Resources
    # ----------------------------------------------------------------
    print("\n== Phase 8: Resources ==")

    from server.resources import (
        get_capabilities_resource, get_capability_detail_resource,
        get_entity_resource, get_file_entities_resource, get_stats_resource,
    )

    # T087: capabilities resource
    print("\n--- legacy://capabilities ---")
    try:
        async with db.session() as session:
            data = await get_capabilities_resource(session)
            assert "capabilities" in data
            assert isinstance(data["capabilities"], list)
            assert len(data["capabilities"]) > 0
            ok(f"capabilities resource: {len(data['capabilities'])} capabilities")
    except Exception as e:
        fail("capabilities resource", str(e))

    # T088: capability detail resource
    print("\n--- legacy://capability/{name} ---")
    if cap_names:
        try:
            async with db.session() as session:
                data = await get_capability_detail_resource(session, cap_names[0])
                assert data["name"] == cap_names[0]
                assert "dependencies" in data
                assert "entry_points" in data
                ok(f"capability detail resource for {cap_names[0]}")
        except Exception as e:
            fail("capability detail resource", str(e))

    # T089: entity resource
    print("\n--- legacy://entity/{entity_id} ---")
    if ep:
        try:
            async with db.session() as session:
                data = await get_entity_resource(session, ep.entity_id)
                assert data["entity_id"] == ep.entity_id
                assert data["name"] == ep.name
                ok(f"entity resource for {ep.name}")
        except Exception as e:
            fail("entity resource", str(e))

    # T090: file entities resource
    print("\n--- legacy://file/{path} ---")
    try:
        async with db.session() as session:
            data = await get_file_entities_resource(session, "src/fight.cc")
            assert data["file_path"] == "src/fight.cc"
            assert "entities" in data
            ok(f"file entities resource: {data['entity_count']} entities in src/fight.cc")
    except Exception as e:
        fail("file entities resource", str(e))

    # T091: stats resource
    print("\n--- legacy://stats ---")
    try:
        async with db.session() as session:
            data = await get_stats_resource(session, graph=graph, embedding_available=True)
            assert "entity_stats" in data
            assert "graph_stats" in data
            assert "capability_stats" in data
            assert "server_info" in data
            assert data["server_info"]["version"] == "1.0.0"
            ok(f"stats resource: {data['entity_stats']['total_entities']} entities, {data['graph_stats']['total_nodes']} graph nodes")
    except Exception as e:
        fail("stats resource", str(e))

    # ----------------------------------------------------------------
    # Phase 8: Prompts
    # ----------------------------------------------------------------
    print("\n== Phase 8: Prompts ==")

    from server.prompts import (
        explain_entity_prompt, analyze_behavior_prompt,
        compare_entry_points_prompt, explore_capability_prompt,
    )

    # T093: explain_entity
    try:
        msgs = explain_entity_prompt("damage")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        assert "damage" in msgs[0]["content"]
        ok("explain_entity prompt")
    except Exception as e:
        fail("explain_entity prompt", str(e))

    # T094: analyze_behavior
    try:
        msgs = analyze_behavior_prompt("do_kill", max_depth=5)
        assert len(msgs) == 2
        assert "do_kill" in msgs[0]["content"]
        ok("analyze_behavior prompt")
    except Exception as e:
        fail("analyze_behavior prompt", str(e))

    # T095: compare_entry_points
    try:
        msgs = compare_entry_points_prompt(["do_look", "do_examine"])
        assert len(msgs) == 2
        assert "do_look" in msgs[0]["content"]
        ok("compare_entry_points prompt")
    except Exception as e:
        fail("compare_entry_points prompt", str(e))

    # T096: explore_capability
    try:
        msgs = explore_capability_prompt("combat")
        assert len(msgs) == 2
        assert "combat" in msgs[0]["content"]
        ok("explore_capability prompt")
    except Exception as e:
        fail("explore_capability prompt", str(e))

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    await db.dispose()

    print(f"\n{'='*60}")
    print(f"Results: {_passed} passed, {_failed} failed")
    if _errors:
        print(f"\nFailures:")
        for e in _errors:
            print(f"  - {e}")
    print(f"{'='*60}")

    return _failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
