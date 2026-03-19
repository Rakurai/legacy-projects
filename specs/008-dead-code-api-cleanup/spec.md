# Feature Specification: Dead Code Purge & API Cleanup

**Feature Branch**: `008-dead-code-api-cleanup`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Dead code purge and API cleanup: remove doc_quality/doc_state, side_effect_markers, provenance, compound_id/member_id dead fields; remove low-value tools; fix entry point capability semantics; align tool parameters with contracts"

## User Scenarios & Testing *(mandatory)*

<!--
  The "users" of this MCP server are AI agents (e.g., coding assistants)
  that call tools to explore and understand the legacy C++ codebase.
  User stories are written from the agent's perspective.
-->

### User Story 1 — Smaller, Accurate Tool Responses (Priority: P1)

An AI agent calls entity-related tools (`get_entity`, `search`, `get_behavior_slice`, etc.) and receives responses containing only fields that carry meaningful, accurate information. No response includes vestigial fields (`doc_quality`, `doc_state`, `provenance`, `side_effect_markers`, `compound_id`, `member_id`) that are either always null, never acted upon, or derived from unvalidated data.

**Why this priority**: Dead fields bloat every response, waste context window tokens, and risk misleading agents into treating null/placeholder values as signals. Removing them is the highest-impact change — it touches every tool response and enables the other cleanup stories.

**Independent Test**: Invoke every entity-returning tool and verify no response contains any of the six removed field families. Rebuild the database from artifacts and confirm it loads without schema errors.

**Acceptance Scenarios**:

1. **Given** a freshly built database, **When** an agent calls `get_entity` for any entity, **Then** the response contains no `doc_quality`, `doc_state`, `provenance`, `side_effect_markers`, `compound_id`, or `member_id` fields
2. **Given** a freshly built database, **When** an agent calls `search` with any query, **Then** each result contains no `provenance` or `doc_quality` fields
3. **Given** the server is running, **When** an agent calls `get_behavior_slice` for any entity, **Then** the response contains no `side_effects` dict and no `provenance` field
4. **Given** the build pipeline has run, **When** inspecting all entities in the database, **Then** no columns exist for `doc_state`, `doc_quality`, `side_effect_markers`, `compound_id`, or `member_id`

---

### User Story 2 — Reduced Tool Surface (Priority: P2)

An AI agent discovers the available tools via tool listing and sees a focused set of 15 tools (down from 19). The four removed tools (`get_hotspots`, `get_related_files`, `get_file_summary`, `list_file_entities`) are no longer advertised or callable. Agents that previously used these tools can achieve equivalent results via the remaining tools (primarily `search` with appropriate filters and sorting).

**Why this priority**: Fewer tools reduce agent decision overhead and eliminate tools whose primary features depend on removed fields (`get_hotspots` depends on `doc_quality`) or serve file-centric workflows that don't match how agents actually navigate the codebase (entity-first, not file-first).

**Independent Test**: List all registered tools and verify exactly 15 are present. Attempt to call each removed tool name and verify a clear "tool not found" error.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** an agent lists available tools, **Then** exactly 15 tools are returned and none of `get_hotspots`, `get_related_files`, `get_file_summary`, `list_file_entities` appear
2. **Given** the server is running, **When** an agent attempts to call any of the four removed tool names, **Then** the server returns a standard "unknown tool" error

---

### User Story 3 — Correct Entry Point / Capability Semantics (Priority: P2)

An AI agent exploring how capabilities connect to user-facing commands uses `list_entry_points` and `get_capability_detail`. These tools correctly reflect the architectural reality that entry points (`do_*`, `spell_*`, `spec_*`) are routing dispatchers — they have no direct capability assignment, but they *route into* capabilities via their call graphs.

- `get_capability_detail` returns the entry points that route into a given capability (derived from precomputed capability graph data)
- `list_entry_points` no longer accepts a `capability` filter (agents use `get_capability_detail` to discover which entry points route into a capability)

**Why this priority**: Misunderstanding entry point / capability semantics is a recurring confusion in specs and TODOs. Correcting the contract and documentation prevents agents from misinterpreting null capability fields as missing data.

**Independent Test**: Call `get_capability_detail` for a known capability and verify the `entry_points` list contains routing functions that dispatch into that capability. Call `list_entry_points` without a capability filter and verify all returned entities have `capability=NULL`.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** an agent calls `get_capability_detail` for "combat", **Then** the `entry_points` field lists `do_*` functions that route into the combat capability
2. **Given** the server is running, **When** an agent calls `list_entry_points`, **Then** the tool does not accept a `capability` parameter, all returned entities have null capability, and this is documented as correct behavior
3. **Given** the server documentation, **When** a developer reads the tool contracts, **Then** the entry point / capability relationship is clearly explained as dispatch-vs-implementation

---

### User Story 4 — Tool Parameters Match Contracts (Priority: P3)

An AI agent calling tools uses the parameter names and defaults specified in the tool contracts. Every parameter name, default value, and accepted value set in the implementation matches the published contract.

**Why this priority**: Parameter mismatches between contract and implementation cause silent failures or unexpected behavior. Fixing these ensures agents can rely on the documented API.

**Independent Test**: For each tool with a known contract divergence, call the tool using the contract-specified parameter name and verify correct behavior.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** an agent calls `search` with `top_k=5`, **Then** exactly 5 results are returned (parameter previously named `limit`)
2. **Given** the server is running, **When** an agent calls `get_class_hierarchy` with `direction="ancestors"`, **Then** only base classes are returned (previously always returned both)
3. **Given** the server is running, **When** an agent calls `get_dependencies` with no `direction` parameter, **Then** results default to `"outgoing"` only (previously defaulted to `"both"`)
4. **Given** the server is running, **When** an agent calls `get_related_entities` with `limit_per_type=10`, **Then** each relationship group contains at most 10 entries (previously a single global `limit`)

---

### Edge Cases

- What happens when an agent references a removed tool by name? The server returns a standard "unknown tool" error.
- What happens when a database was built before this cleanup and still contains the removed columns? The server ignores unknown columns on read; a full rebuild is required for a clean schema.
- What happens when `get_class_hierarchy` is called with `direction="both"` (the explicit value)? Both base and derived classes are returned, same as the old behavior.
- What happens when `get_related_entities` returns fewer entries than `limit_per_type` for a relationship type? The response includes only the available entries with no padding.

## Clarifications

### Session 2026-03-19

- Q: Should the `Confidence` enum be removed (FR-006) given that `GlobalTouch.confidence` and `get_state_touches` actively use it? → A: Preserve `Confidence` — it is used by retained features. **UPDATE (research phase)**: Investigation found `Confidence` is used ONLY by `SideEffectMarker`, NOT by `GlobalTouch`. Since `SideEffectMarker` is removed, `Confidence` CAN be removed. FR-006 updated to include `Confidence` in the removal list.
- Q: User Story 2 acceptance scenarios claimed `search` with `file_path` filter / `fan_in` sort could replace removed tools, but `search` lacks those parameters. Keep them? → A: Remove those scenarios — tools are simply dropped with no replacement pathway promised
- Q: `search` rename `limit` → `top_k`: contract says default 10, implementation uses 20. Which default? → A: Use contract default `top_k=10`

## Requirements *(mandatory)*

### Functional Requirements

**Dead Field Removal**

- **FR-001**: The system MUST NOT include `doc_quality` or `doc_state` fields on any entity in the database schema or API responses *(already satisfied — fields absent from codebase)*
- **FR-002**: The system MUST NOT include `doc_quality_dist` on any capability in the database schema or API responses *(already satisfied — field absent from codebase)*
- **FR-003**: The system MUST NOT include `side_effect_markers` on any entity in the database schema or API responses
- **FR-004**: The system MUST NOT include `provenance` on any model in API responses
- **FR-005**: The system MUST NOT include `compound_id` or `member_id` on any entity in the database schema or API responses *(already satisfied — fields absent from codebase)*
- **FR-006**: The system MUST NOT define the `DocState`, `DocQuality`, `SideEffectCategory`, `Confidence`, or `Provenance` enumerations *(partially satisfied — `DocState` and `DocQuality` already absent; `SideEffectCategory`, `Confidence`, `Provenance` still present)*
- **FR-007**: The build pipeline MUST NOT compute or persist any of the removed fields
- **FR-008**: Entity sort ordering (when resolving ambiguous IDs) MUST use `fan_in` descending as the tiebreaker instead of the removed `doc_quality` sort key *(already satisfied — resolver already uses `fan_in`)*

**Tool Removal**

- **FR-009**: The system MUST NOT register or expose the `get_hotspots` tool
- **FR-010**: The system MUST NOT register or expose the `get_related_files` tool
- **FR-011**: The system MUST NOT register or expose the `get_file_summary` tool
- **FR-012**: The system MUST NOT register or expose the `list_file_entities` tool
- **FR-013**: The system MUST NOT define response models associated only with removed tools (`HotspotsResponse`, `FileSummaryResponse`, `ListFileEntitiesResponse`, and similar)

**Entry Point / Capability Semantics**

- **FR-014**: `get_capability_detail` MUST return `entry_points` as the list of entry points that route into the capability, sourced from precomputed capability graph data
- **FR-015**: `list_entry_points` MUST NOT accept a `capability` filter parameter; it returns all entry point entities, optionally filtered by name pattern
- **FR-015a**: Agents MUST use `get_capability_detail` to discover which entry points route into a given capability
- **FR-016**: Documentation (tool contracts, model docs) MUST state that entry points have `capability=NULL` by design because they are routing dispatchers, not capability implementations

**Contract Alignment**

- **FR-017**: The `search` tool MUST accept `top_k` as the parameter name for result count (not `limit`), with a default value of 10
- **FR-018**: The `get_class_hierarchy` tool MUST accept a `direction` parameter with values `"ancestors"`, `"descendants"`, or `"both"` (default `"both"`) and filter results accordingly
- **FR-019**: The `get_dependencies` tool MUST default the `direction` parameter to `"outgoing"` (not `"both"`)
- **FR-020**: The `get_related_entities` tool MUST accept `limit_per_type` (default 20) to cap results per relationship group, replacing any single global `limit`

### Key Entities

- **Entity**: A code element (function, class, struct, variable, macro, etc.) in the legacy C++ codebase. After this cleanup, entities shed 1 DB field (`side_effect_markers`); 4 others (`doc_quality`, `doc_state`, `compound_id`, `member_id`) were already removed in prior work and are listed here only for completeness
- **Capability**: A functional grouping of entities (e.g., "combat", "magic", "persistence"). After this cleanup, capabilities shed the `doc_quality_dist` summary field
- **Entry Point**: A special subset of entities (`do_*`, `spell_*`, `spec_*` functions) that serve as dispatch routers. They have `capability=NULL` by design and connect to capabilities via their call graphs

### Assumptions

- The `Confidence` enum is used ONLY by `SideEffectMarker` (being removed), NOT by `GlobalTouch`. It MUST be removed along with `SideEffectMarker`
- The `AccessType` enum is used by `GlobalTouch` (not being removed) and is preserved
- `get_capability_detail.entry_points` requires enriching each `EntryPoint`'s `capabilities` JSONB at build time with transitive capability data derived from call-cone computation (`capability_graph.json`'s `entry_points_using` is an integer count, not a list — the build pipeline must resolve the actual capability names)
- Agents do not depend on any removed tool or field — no downstream breakage is expected since these fields carried no actionable signal

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total registered tool count is exactly 15 (down from 19)
- **SC-002**: Entity API responses contain zero instances of removed field names across all tool calls
- **SC-003**: Full database rebuild from artifacts completes without schema errors
- **SC-004**: All existing tests pass after updating fixtures to remove dead fields (no net increase in test failures)
- **SC-005**: Every tool parameter name and default value matches the published contract in `contracts/tools.md`
- **SC-006**: `get_capability_detail` returns non-empty `entry_points` for capabilities that have known command dispatchers
- **SC-007**: Codebase contains zero references to `DocQuality`, `DocState`, `SideEffectCategory`, `Provenance`, `compute_doc_quality`, `compute_side_effect_markers`, `doc_quality_sort_key`, or `_provenance_for`
