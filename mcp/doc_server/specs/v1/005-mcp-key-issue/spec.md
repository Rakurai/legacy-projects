# Feature Specification: Deterministic Entity IDs & Documentation Merge Fix

**Feature Branch**: `005-mcp-key-issue`
**Created**: 2026-03-17
**Status**: Draft
**Input**: User description: "Implement changes to the mcp/doc_server according to design.005.md"
**Design Document**: `mcp/doc_server/specs/design.005.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Entity References Across Tool Calls (Priority: P1)

An AI assistant explores the Legacy codebase by searching for a concept, receiving entity IDs in the results, and passing those IDs into subsequent tool calls (`get_entity`, `get_callers`, `get_behavior_slice`, etc.). Today, entities carry opaque Doxygen-internal IDs that change between Doxygen runs, and 521 signatures map to multiple entities — causing silent wrong-entity bugs when an agent accumulates and forwards references. After this change, every entity has a short, deterministic, type-prefixed ID (e.g., `fn:a3f8c1d`) that is stable across rebuilds and unambiguous. The agent's workflow becomes: search → receive IDs → use IDs in all follow-up calls, with no possibility of ID collision or silent mismatch.

**Why this priority**: Without stable, unambiguous identity, every downstream tool call is unreliable. This is the single prerequisite for trustworthy agent interactions with the server.

**Independent Test**: Rebuild the database from the same source artifacts twice and confirm that every entity receives the same ID in both builds. Then issue a `search` call, take the returned `entity_id`, and pass it to `get_entity`, `get_callers`, and `get_behavior_slice` — all must return correct results for that entity.

**Acceptance Scenarios**:

1. **Given** the same source artifacts, **When** the build pipeline runs twice, **Then** every entity receives the same deterministic ID both times
2. **Given** a search result containing `entity_id: "fn:a3f8c1d"`, **When** the agent calls `get_entity(entity_id="fn:a3f8c1d")`, **Then** the server returns the correct entity's full documentation
3. **Given** an entity ID in `{prefix}:{7 hex}` format, **When** used across `get_entity`, `get_callers`, `get_callees`, `get_behavior_slice`, **Then** all tools accept it and return results for the same entity
4. **Given** ~5,300 entities in the database, **When** the build computes IDs, **Then** zero collisions occur (enforced by unique constraint; build halts on collision)
5. **Given** two entities that share the same bare name (e.g., two functions both named `save`), **When** each receives its deterministic ID, **Then** the IDs are different and each unambiguously identifies one entity

---

### User Story 2 - Complete Documentation After Build (Priority: P2)

An AI assistant queries an entity and expects to see its documented brief, details, parameters, and rationale. Today, only ~330 of ~5,293 documented entities retain their briefs after the build pipeline — 85% of documentation is silently lost because the build runs with a stale `signature_map.json` whose member hashes no longer match the current `code_graph.json`. The merge logic itself is correct, but stale signature_map entries cause most doc_db lookups to fail silently. After this change, the build pipeline regenerates `signature_map.json` from current artifacts before merging, and uses the signature_map key `(compound_id, signature)` as the deterministic identity.

**Why this priority**: The server's primary value proposition is exposing pre-computed documentation to AI agents. Losing 85% of that documentation negates the purpose of the system.

**Independent Test**: After a build, query a sample of 50 entities that have non-null briefs in `doc_db.json` and confirm that each entity's `brief` field in the database matches the artifact. Count total entities with non-null `brief` and compare against the artifact count (~5,293 with documentation).

**Acceptance Scenarios**:

1. **Given** `doc_db.json` contains ~5,293 entries with documentation, **When** the build pipeline completes, **Then** at least 95% of those entries have non-null `brief` fields in the database
2. **Given** an entity with full documentation (brief, details, params, returns, notes, rationale) in `doc_db.json`, **When** queried via `get_entity`, **Then** all documentation fields are present and match the artifact
3. **Given** an entity in `code_graph.json` without a matching `doc_db.json` entry, **When** the build completes, **Then** the entity exists in the database with null documentation fields (not lost entirely)
4. **Given** `signature_map.json` bridges Doxygen IDs to doc_db keys, **When** the build merges data, **Then** every bridge is used to carry documentation from doc_db into the entity record

---

### User Story 3 - Simplified Tool Interface (Priority: P3)

An AI assistant interacts with MCP tools using a streamlined two-step pattern: `search` to discover entities, then `get_entity` (or graph/behavior tools) with the returned `entity_id`. The `resolve_entity` tool is retired because `search` now subsumes its resolution pipeline. Tools that previously accepted both `entity_id` and `signature` now accept only `entity_id`. The `ResolutionEnvelope` wrapper is removed from all responses — every tool returns its domain-specific response directly.

**Why this priority**: Removing the signature-as-lookup-key path eliminates the 521-signature-collision class of bugs and simplifies the agent interaction model. Fewer tool parameters and response wrappers reduce agent confusion and context consumption.

**Independent Test**: Confirm that calling `get_entity` with a valid `entity_id` returns the entity, and calling it with a `signature` string is rejected. Confirm that `resolve_entity` is no longer listed in the tool catalog. Confirm that no response from any tool contains a `resolution` field.

**Acceptance Scenarios**:

1. **Given** the MCP tool catalog, **When** an agent lists available tools, **Then** `resolve_entity` is not present
2. **Given** a tool that previously accepted `entity_id` or `signature`, **When** called with only `entity_id`, **Then** it returns the correct result
3. **Given** any tool response, **When** inspecting the response shape, **Then** no `resolution` or `ResolutionEnvelope` field is present
4. **Given** an agent workflow using `search → get_entity → get_callers`, **When** the agent passes entity IDs forward, **Then** the entire chain completes without needing signature-based resolution

---

### Edge Cases

- **Hash collision during build**: If two different doc_db keys produce the same 7-hex-character hash, the build pipeline halts with a collision error rather than silently overwriting one entity
- **Entity in signature_map but not in code_graph**: Impossible by construction — `signature_map.json` is regenerated from `code_graph.json` + `doc_db.json`, so every signature_map entry has a code_graph entity
- **Entity in code_graph without a doc_db match**: ~12 entities have no documentation in doc_db. These get null documentation fields in the database — this is normal and expected
- **Stale entity_id from a previous build**: An agent using an ID from a prior build against a database with different source artifacts will get a "not found" error (expected and correct — IDs are deterministic per artifact set, not globally stable)
- **Empty search results**: `search` returns an empty array with `search_mode` indicating whether hybrid or keyword fallback was used — no change from V1 behavior

## Requirements *(mandatory)*

### Functional Requirements

#### Identity & Build Pipeline

- **FR-001**: Build pipeline MUST compute entity IDs as `{prefix}:{sha256(canonical_key)[:7]}` where the canonical key is the signature_map key tuple `(compound_id, second_element)` — this key exists for every entity in the system
- **FR-002**: Prefix MUST be determined by entity kind: `fn` for function/define, `var` for variable, `cls` for class/struct, `file` for file, `sym` for everything else
- **FR-003**: Build pipeline MUST load `signature_map.json` (pre-built from current `code_graph.json` + `doc_db.json`) and use it to join entities with documentation — `code_graph.json` (5,305 entities) is the canonical entity set, `doc_db.json` (~5,293 entries) provides documentation, and `signature_map.json` bridges them. All three are pre-built input artifacts; the build pipeline does not regenerate them.
- **FR-004**: Build pipeline MUST halt with a clear error on any ID collision (two different canonical keys producing the same prefixed hash)
- **FR-005**: Build pipeline MUST carry all documentation fields (brief, details, params, returns, notes, rationale, usages) from doc_db through the merge without loss
- **FR-006**: Build pipeline MUST replace the existing `entity_ids.py` Doxygen-format helpers (`split_entity_id`, `SignatureMap`) with the new deterministic ID generator — old helpers become dead code

#### Schema Changes

- **FR-007**: Schema MUST remove columns: `compound_id`, `member_id`, `doc_state`, `doc_quality` from the entities table
- **FR-008**: Schema MUST remove column: `doc_quality_dist` from the capabilities table
- **FR-009**: `entity_id` primary key values MUST follow the `{prefix}:{7 hex}` format
- **FR-010**: `signature` column MUST remain in the schema as a display-only field (no UNIQUE constraint — 521 signatures collide across compounds; no longer accepted as a lookup key)

#### Tool Interface Changes

- **FR-011**: `resolve_entity` tool MUST be removed from the MCP tool catalog
- **FR-012**: All tools that previously accepted `entity_id` and `signature` parameters MUST accept only `entity_id` as a required parameter
- **FR-013**: `ResolutionEnvelope` MUST be removed from all tool response shapes
- **FR-014**: `search` tool MUST remove the `min_doc_quality` parameter
- **FR-015**: `list_capabilities` and `get_capability_detail` responses MUST remove the `doc_quality_dist` field
- **FR-016**: All modules that import `DocQuality` or `DocState` MUST have those imports removed when the enums are deleted (including `behavior.py` which imports `DocQuality` for hotspot responses)
- **FR-017**: Prompt workflow descriptions referencing entity resolution MUST be updated to reflect the search → entity_id pattern

#### Model Changes

- **FR-018**: `EntitySummary` MUST remove `doc_state` and `doc_quality` fields
- **FR-019**: `EntityDetail` MUST remove `compound_id`, `member_id`, `doc_state`, and `doc_quality` fields
- **FR-020**: `search` is the sole path from human-readable text to entity IDs — no other tool performs name-to-ID resolution

#### Affected Tools (entity_id-only parameter)

The following tools MUST accept only `entity_id` (required) and MUST NOT accept `signature`:
- `get_entity`
- `get_source_code`
- `get_callers`
- `get_callees`
- `get_dependencies`
- `get_class_hierarchy`
- `get_related_entities`
- `get_behavior_slice`
- `get_state_touches`
- `get_entry_point_info`

### Key Entities

- **Entity**: A code element (function, class, variable, struct, etc.) extracted from the Legacy MUD codebase. Key attributes: deterministic ID (`{prefix}:{7 hex}`), signature (display-only), name, kind, file path, documentation fields (brief, details, params, returns, notes, rationale), graph metrics (fan_in, fan_out), capability membership, embedding vector.
- **Edge**: A directed relationship between two entities. Key attributes: source and target entity IDs, relationship type (CALLS, USES, INHERITS, INCLUDES, CONTAINED_BY). Source and target IDs change from Doxygen format to deterministic format.
- **Capability**: A functional grouping of entities (~30 groups). Key attributes: name, type, description, function count. `doc_quality_dist` is removed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a full build, at least 95% of the ~5,293 entities with documentation in `doc_db.json` have non-null `brief` fields in the database (up from ~6% today)
- **SC-002**: Two consecutive builds from the same artifacts produce identical entity ID sets (100% determinism)
- **SC-003**: All 20 existing contract tests pass after the tool interface changes (adjusted for removed `resolve_entity` and changed parameter signatures)
- **SC-004**: An agent can complete a full exploration workflow (search → get_entity → get_callers → get_behavior_slice) using only entity IDs, with zero signature-based lookups
- **SC-005**: No tool in the MCP catalog accepts a `signature` parameter for entity lookup

## Assumptions

- `code_graph.json` (5,305 entities), `doc_db.json` (~5,293 entries), and `signature_map.json` (5,305 entries) are all pre-built input artifacts, locked before the build pipeline runs. `code_graph.json` is the canonical entity set. `signature_map.json` maps every code_graph entity ID to its stable `(compound_id, signature)` doc_db key. There are never entities without a signature_map entry — this is guaranteed by construction of `signature_map.json`.
- The signature_map key `(compound_id, second_element)` is stable across Doxygen runs because compound_id derives from C++ qualified names and the second element is the entity's signature (functions) or name (other kinds).
- The `mid` field inside doc_db entries is irrelevant to the build pipeline — member ID values from doc_db are never used. Only the `(compound_id, signature)` key matters.

## Clarifications

### Session 2026-03-17

- Q: What canonical key is used for entities that exist only in code_graph.json (no doc_db match)? → A: signature_map.json is derived from code_graph.json + doc_db.json, so every code_graph entity has a signature_map entry. ~12 entities have no doc_db match and get null documentation — this is normal.
- Q: What about entities in signature_map that are not in code_graph? → A: Impossible by construction. signature_map is derived from code_graph. code_graph.json (5,305 entities) IS the entity set. The prior doc loss was caused by a stale signature_map, not a missing-entity problem.
- 7 hex characters (28 bits) provide negligible collision probability at the ~5,300 entity scale. Build-time collision detection is the safety net.
- Removing `doc_quality` and `doc_state` is acceptable because quality assessment belongs to artifact creation, not server/agent interaction. Agents use `brief is not null` as the practical quality signal.
- The multi-stage resolution pipeline (name_exact → prefix → keyword → semantic) currently in `resolve_entity` will be preserved internally as the implementation of `search`, not removed entirely.
- The `entry_points.capabilities` JSONB column already exists in the schema and is correctly populated during the build.
