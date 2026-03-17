# Feature Specification: MCP Doc Server V2 — Hierarchical System Documentation

**Feature Branch**: `002-mcp-doc-server-v2`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "V2 of .ai/mcp/doc_server — add hierarchical system documentation layer on top of V1 entity-level services, referencing DESIGN.md §18 for intended shape and scope"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subsystem Browsing and Lookup (Priority: P1) MVP

An AI assistant needs to understand the high-level architectural organization of the Legacy MUD codebase. The assistant can list all subsystems (e.g., Combat System, Affect System, Object System), browse the hierarchy (parent/child relationships), and retrieve a full subsystem profile including its overview narrative, responsibilities, component breakdown, implementation details, and dependency relationships. The subsystem data is drawn from 23 curated component documents (~4,500 lines of narrative prose) that capture knowledge per-entity documentation cannot compose — such as "the combat system resolves attacks in a per-round cycle: hit check → damage calc → defensive rolls → elemental cascading → death processing with corpse creation."

**Why this priority**: Subsystem lookup is the foundational V2 capability. Without the ability to browse and retrieve system-level documentation, none of the cross-referencing (entity↔subsystem links, unified search, context assembly) is useful. This is the MVP that makes the architectural narrative layer accessible.

**Independent Test**: Can be fully tested by querying known subsystems (e.g., "Combat System", "Affect System", "Networking") and verifying that returned documentation matches the corresponding component markdown files in `.ai/docs/components/`. Success means an assistant can navigate the codebase at the architectural level using curated prose rather than aggregating function-level docs.

**Acceptance Scenarios**:

1. **Given** no parameters, **When** assistant lists subsystems, **Then** receive all subsystems with names, hierarchy (parent/child), entity counts, doc section counts, and dependency summaries
2. **Given** a subsystem name, **When** assistant requests full subsystem detail, **Then** receive overview section first, followed by other sections ordered by section kind priority (overview → responsibilities → key_components → implementation → dependencies → behaviors → future)
3. **Given** a subsystem with child subsystems (e.g., Object System containing Dynamic Loot Generation), **When** assistant requests subsystem detail, **Then** child subsystems are listed with summaries and navigation IDs
4. **Given** a subsystem name, **When** assistant requests subsystem dependencies, **Then** receive upstream ("depends on") and downstream ("depended on by") subsystem lists with relationship types

---

### User Story 2 - Entity-to-Subsystem Context Assembly (Priority: P2)

An AI assistant is analyzing a specific function (e.g., `damage()`) and needs to understand what larger system narrative explains its role. The assistant requests subsystem context for the entity and receives: which subsystem(s) the entity belongs to with its role (core, entry_point, supporting, utility, integration), the relevant overview prose from those subsystems, doc sections that mention the entity or closely related functions, and capability framing. This bridges V1 entity-level facts with V2 system-level narratives.

**Why this priority**: Entity↔subsystem linking is what makes V2 more than a separate documentation browser — it connects per-function facts to architectural narratives. Without this, an assistant would need to manually search subsystem docs for entity mentions. This is the core cross-referencing capability that justifies V2.

**Independent Test**: Can be tested by requesting subsystem context for well-known entities (e.g., `damage()` should link to Combat System as `core`, `act()` should link to multiple subsystems as `utility`). Verify that returned subsystem sections are relevant and properly reranked (overview first, then sections mentioning the entity). Success means an assistant can pivot from "what does this function do?" to "what architectural context explains it?" in a single tool call.

**Acceptance Scenarios**:

1. **Given** an entity that belongs to one subsystem, **When** assistant requests subsystem context, **Then** receive the entity's subsystem membership with role, overview section, and relevant doc sections with inclusion reasons
2. **Given** an entity that spans multiple subsystems (e.g., `act()` participating in many systems), **When** assistant requests subsystem context, **Then** receive all linked subsystems with distinct roles per subsystem and relevant sections from each
3. **Given** a subsystem context result, **When** reviewing returned doc sections, **Then** each section includes an inclusion_reason field (overview_section, mentions_entity, same_capability, linked_subsystem, matches_behavior_terms)
4. **Given** an entity with no subsystem links, **When** assistant requests subsystem context, **Then** receive a response indicating no links exist, with the entity's capability group as fallback context
5. **Given** a subsystem context request, **When** many doc sections are candidates, **Then** sections are reranked by relevance (overview first, then entity mentions, then capability alignment) rather than returned as an unordered dump

---

### User Story 3 - Unified Search Across Entities and System Documentation (Priority: P3)

An AI assistant searching for "poison spreading between characters" can now discover not only the relevant code entities (from V1) but also the narrative documentation sections that explain the poison mechanics at a system level. The `search` tool's existing `source` parameter (V2-reserved in V1) becomes functional, allowing scoped searches across entity docs only, subsystem docs only, or both. Results use the existing `SearchResult` envelope with the `result_type` discriminator distinguishing entity results from subsystem doc results.

**Why this priority**: Unified search is what transforms V2 from a browsing tool into a discovery tool. Without it, assistants must know which subsystem to look in. This enables open-ended exploratory queries that surface both code-level and narrative-level knowledge. It builds directly on V1's hybrid search infrastructure, extending it to subsystem doc embeddings.

**Independent Test**: Can be tested by issuing queries with `source=all` and verifying that results include both entity matches and subsystem doc section matches with correct `result_type` discriminators. Test with `source=subsystem_doc` to confirm scoped filtering. Verify score normalization produces reasonable interleaving of entity and doc results. Success means an assistant can discover relevant knowledge regardless of whether it lives in per-entity docs or system-level prose.

**Acceptance Scenarios**:

1. **Given** a search query with `source=all`, **When** assistant searches, **Then** receive mixed results containing both entity matches (`result_type=entity`) and subsystem doc section matches (`result_type=subsystem_doc`) ranked by unified score
2. **Given** a search query with `source=subsystem_doc`, **When** assistant searches, **Then** receive only subsystem doc section matches using `SubsystemDocSummary` shape
3. **Given** a search query with `source=entity` (default), **When** assistant searches, **Then** behavior is identical to V1 — only entity matches returned
4. **Given** subsystem doc sections have embeddings, **When** hybrid search runs, **Then** semantic similarity and full-text search combine for doc sections the same way they do for entities
5. **Given** embedding service is unavailable, **When** searching subsystem docs, **Then** keyword-only fallback applies to doc section search with explicit `search_mode: "keyword_fallback"` reporting

---

### User Story 4 - Subsystem Documentation Section Search (Priority: P4)

An AI assistant needs to find specific documentation sections across the subsystem prose — for example, searching for "death processing" to find the combat system's section on corpse creation and loot dropping, or "memory pooling" to find the memory management component's allocation strategy. A dedicated subsystem doc search tool provides focused retrieval with section-level granularity, returning section paths, headings, excerpt text, and subsystem context without mixing in code entities.

**Why this priority**: While unified search (P3) enables broad discovery, focused doc search is essential for assistants that know they need architectural prose rather than code. It provides tighter result relevance and avoids entity noise when exploring the narrative layer specifically. This is especially valuable for migration planning workflows.

**Independent Test**: Can be tested by querying for known topics covered in the component docs (e.g., "attack resolution", "object prototypes", "MobProg triggers") and verifying that returned sections come from the correct component documents with accurate section paths and excerpts. Success means an assistant can efficiently locate specific architectural knowledge within the narrative corpus.

**Acceptance Scenarios**:

1. **Given** a text query, **When** assistant searches subsystem docs, **Then** receive ranked list of doc sections as `SubsystemDocSummary` objects with subsystem_id, section_path, heading, section_kind, excerpt, and score
2. **Given** a query matching a specific section heading, **When** search runs, **Then** exact heading matches receive a score boost
3. **Given** a subsystem filter, **When** assistant searches docs scoped to one subsystem, **Then** only sections from that subsystem are returned
4. **Given** a section_kind filter (e.g., "implementation"), **When** assistant searches, **Then** only sections classified as that kind are returned

---

### User Story 5 - Subsystem Dependency Graph Navigation (Priority: P5)

An AI assistant planning changes to the Affect System needs to understand which other subsystems depend on it and which subsystems it depends on. The assistant can navigate the system-level dependency graph parsed from `subsystems.md` dependency declarations, discovering upstream and downstream relationships. This provides architectural impact analysis at a higher level than entity-level call graphs — answering "if I change the Affect System, which other systems are at risk?" rather than "which functions call affect_to_char()?"

**Why this priority**: System-level dependency navigation is the final layer that enables architectural reasoning. While entity-level graph tools (V1) show function-to-function relationships, this shows system-to-system relationships — essential for planning large changes or understanding cross-cutting concerns. It has lower priority because it requires all subsystems to be indexed first.

**Independent Test**: Can be tested by querying known dependency relationships from `subsystems.md` (e.g., Combat System depends on Affect System, Character Progression). Verify bidirectional traversal works and relationship types are preserved. Success means an assistant can reason about architectural impact at the system level.

**Acceptance Scenarios**:

1. **Given** a subsystem name, **When** assistant requests dependencies, **Then** receive lists of upstream (depends_on) and downstream (depended_on_by) subsystems with relationship types
2. **Given** a subsystem with bidirectional dependencies, **When** assistant views dependencies, **Then** bidirectional relationships are explicitly labeled
3. **Given** a subsystem at the root of a dependency chain, **When** assistant requests full dependency tree, **Then** receive transitive dependencies (systems that indirectly depend on this one)

---

### Edge Cases

- **Entity belongs to no subsystem**: System returns entity documentation and capability group as fallback context; response explicitly indicates no subsystem links exist rather than returning empty results silently
- **Entity linked to 10+ subsystems**: Results are ordered by role priority (core → entry_point → supporting → integration → utility); all links returned, no truncation unless exceeding response limits
- **Subsystem has no entity links (curation gap)**: System returns subsystem documentation (overview, sections, dependencies) without entity cross-references; a warning field indicates curation may be incomplete
- **Subsystem doc section has no embedding** (embedding generation failed): Section is still searchable via keyword/full-text; excluded from semantic search results; search_mode indicates partial coverage
- **Circular subsystem dependencies**: Dependency graph traversal uses visited set to prevent infinite loops; cycles are reported as-is without error
- **Component markdown file deleted or renamed after build**: Subsystem data remains in database from last build; `source_file` field may point to nonexistent file; doc sections are still served from stored body text
- **Curation artifact references nonexistent entity_id**: Validation rules catch this before DB ingestion; link is rejected with clear error; build continues with remaining links
- **Subsystem doc section body is empty**: Section is stored with empty body; excluded from search results; included in subsystem detail view with note
- **Search query matches both entity docs and subsystem docs with similar scores**: Unified search interleaves results by score; `result_type` discriminator allows consumers to separate or filter
- **V1 tools called after V2 tables are populated**: V1 tools continue to function identically; V2 tables are additive and do not affect V1 behavior
- **`include_subsystems=true` passed to V1 EntitySummary-returning tools**: EntitySummary gains optional `subsystems` field populated from entity_subsystem_links join table; field is absent when parameter is false or omitted

## Requirements *(mandatory)*

### Functional Requirements

#### Subsystem Data Ingestion & Build Pipeline

- **FR-001**: Build pipeline MUST parse the 23 subsystem component documents from `.ai/docs/components/*.md` and the subsystem index from `.ai/docs/subsystems.md` into structured subsystem records
- **FR-002**: Build pipeline MUST chunk component documents by heading boundaries (`##`/`###`) producing one doc section record per heading, preserving heading hierarchy as `section_path` (e.g., "Core Components > Attack Resolution")
- **FR-003**: Build pipeline MUST classify each doc section's `section_kind` mechanically from heading text using a closed enumeration: overview, responsibilities, key_components, implementation, dependencies, behaviors, future
- **FR-004**: Build pipeline MUST identify and flag exactly one `is_overview` section per subsystem (the canonical overview paragraph)
- **FR-005**: Build pipeline MUST parse dependency declarations ("Depends on" / "Depended on by") from `subsystems.md` into subsystem-to-subsystem edges with typed relationships (depends_on, bidirectional)
- **FR-006**: Build pipeline MUST generate embeddings for each doc section body text and store as vector data alongside the section record
- **FR-007**: Build pipeline MUST generate weighted full-text search vectors for each doc section, weighting heading text higher than body text
- **FR-008**: Build pipeline MUST support subsystem hierarchy (parent/child nesting) so that a subsystem like "Dynamic Loot Generation" can be a child of "Object System"

#### Entity-Subsystem Link Curation

- **FR-009**: Build pipeline MUST ingest entity↔subsystem links from a curated intermediate artifact file, not from mechanical keyword matching
- **FR-010**: Each entity↔subsystem link MUST carry a `role` from a closed enumeration: core, entry_point, supporting, utility, integration
- **FR-011**: Each entity↔subsystem link MUST carry `link_source` (curated, inferred, imported) and `confidence` (high, medium, low) as independent fields
- **FR-012**: Each entity↔subsystem link MUST carry structured `evidence` recording provenance — which doc sections, capabilities, entry points, or files motivated the link
- **FR-013**: Entity↔subsystem relationships MUST be many-to-many — a single entity can belong to multiple subsystems with different roles (e.g., `damage()` is `core` to Combat and `supporting` to Magic)
- **FR-014**: Entity↔subsystem links MUST NOT alter V1's `entities` table — the mapping is maintained as a separate join table

#### Curation Artifact Validation

- **FR-015**: Build pipeline MUST validate that every subsystem has at least one `is_overview` doc chunk before DB ingestion
- **FR-016**: Build pipeline MUST validate that every `entity_id` in link artifacts references an existing entity in the V1 `entities` table
- **FR-017**: Build pipeline MUST validate that every `subsystem_id` in link and doc artifacts references a subsystem in the subsystem seed artifact
- **FR-018**: Build pipeline MUST validate that `entry_point` role links target only function-kind entities
- **FR-019**: Build pipeline MUST warn (non-blocking) when more than 30% of a subsystem's entity links use the `utility` role
- **FR-020**: Build pipeline MUST produce informational reports for orphan entities (no subsystem link) and orphan subsystems (no entity links)

#### Subsystem Lookup Tools

- **FR-021**: System MUST provide a `list_subsystems` tool returning all subsystems with hierarchy, entity counts, doc section counts, and dependency summaries, using the `SubsystemSummary` response shape
- **FR-022**: System MUST provide a `get_subsystem` tool returning full subsystem detail: overview section first (via `is_overview`), then other sections ordered by `section_kind` priority, curated entity links, and dependency edges
- **FR-023**: System MUST provide a `get_subsystem_dependencies` tool returning upstream and downstream subsystem lists with relationship types for a given subsystem

#### Entity-Subsystem Context Assembly

- **FR-024**: System MUST provide a `get_subsystem_context` tool that, given an entity, returns a `ContextBundle` containing: the entity's subsystem memberships with roles, relevant doc sections reranked by relevance, capability framing, and related entities
- **FR-025**: `get_subsystem_context` MUST rerank doc sections by relevance rather than returning unordered results, using the following priority: (1) subsystem overview section, (2) sections mentioning the entity or close neighbors, (3) sections aligned with the entity's capability group, (4) general subsystem membership sections
- **FR-026**: `get_subsystem_context` MUST include an `inclusion_reason` field on each returned doc section: overview_section, mentions_entity, same_capability, linked_subsystem, or matches_behavior_terms
- **FR-027**: When an entity has no subsystem links, `get_subsystem_context` MUST return a response indicating no links with the entity's capability group as fallback context rather than an error

#### Unified and Scoped Search

- **FR-028**: The existing `search` tool's V2-reserved `source` parameter MUST become functional, accepting: `entity` (V1 behavior), `subsystem_doc` (subsystem sections only), or `all` (unified cross-type search)
- **FR-029**: Unified search (`source=all`) MUST interleave entity and subsystem doc results by unified score, using the `SearchResult` envelope with `result_type` discriminator (`entity` or `subsystem_doc`)
- **FR-030**: Subsystem doc search results MUST use the `SubsystemDocSummary` response shape, returning subsystem_id, subsystem_name, section_path, heading, section_kind, source_file, excerpt, and score
- **FR-031**: System MUST provide a `search_subsystem_docs` tool for focused retrieval scoped exclusively to subsystem prose, supporting filtering by subsystem and section_kind

#### V1 Tool Enhancements (Backward-Compatible)

- **FR-032**: All V1 tools returning `EntitySummary` MUST support an optional `include_subsystems` parameter (default: false) that, when true, populates a `subsystems` field listing `{id, name, role}` from the entity↔subsystem join table
- **FR-033**: V1 tools MUST continue to function identically when `include_subsystems` is false or omitted — V2 tables are purely additive
- **FR-034**: V2 response shapes (`SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) pre-defined in V1's model layer MUST be used as-is without modification to their existing field structure

#### Curation Intermediate Artifacts

- **FR-035**: The curation agent MUST produce versioned intermediate artifact files (stored in `.ai/artifacts/v2/`) rather than writing directly to the database
- **FR-036**: Curation artifacts MUST include: `subsystems_seed.json`, `subsystem_doc_chunks.jsonl`, `entity_subsystem_links.jsonl`, `subsystem_edges.json`, and `curation_flags.jsonl`
- **FR-037**: Curation artifacts MUST be human-reviewable, re-ingestable without rerunning the curation agent, and correctable by manual editing

#### Build Script

- **FR-038**: A `build_v2_db.py` script MUST read all V2 curation artifacts, embed doc chunks, and populate V2 database tables
- **FR-039**: The V2 build script MUST be idempotent — re-running from the same artifacts produces identical database state
- **FR-040**: The V2 build script MUST NOT modify any V1 tables or data; V2 tables are additive only
- **FR-041**: The V2 build script MUST run validation rules (FR-015 through FR-020) before populating database tables, failing on blocking errors and logging warnings for non-blocking issues

### Key Entities

- **Subsystem**: An architectural component of the game (e.g., "Combat System", "Affect System", "Networking"). Contains identity (id, name), hierarchy (parent subsystem reference), description (overview paragraph), source document reference, and dependency declarations (upstream/downstream subsystem lists). Supports nesting so child subsystems can exist within parent systems.

- **Subsystem Doc Section**: A chunked section of subsystem narrative documentation, produced by splitting component markdown files at heading boundaries. Contains section path (hierarchical heading trail), heading text, section kind (overview, responsibilities, key_components, implementation, dependencies, behaviors, future), body text (markdown content), source file reference, line range, embedding vector, and full-text search vector. Exactly one section per subsystem is flagged as the canonical overview.

- **Entity-Subsystem Link**: A curated many-to-many relationship connecting a code entity to a subsystem with a specific role. Contains entity reference, subsystem reference, role (core, entry_point, supporting, utility, integration), provenance metadata (link_source: curated/inferred/imported, confidence: high/medium/low), explanatory notes, and structured evidence recording what motivated the link. A single entity can participate in multiple subsystems with different roles.

- **Subsystem Edge**: A directed relationship between two subsystems representing architectural dependency. Contains source subsystem, target subsystem, and relationship type (depends_on, bidirectional). Parsed from dependency declarations in subsystem index documentation.

- **Curation Flag**: An unresolved case, gap, or review marker produced by the curation agent during entity↔subsystem link creation. Stored in curation artifacts for human review before re-ingestion. Covers ambiguous classifications, low-confidence links, and orphan detection.

- **ContextBundle**: A structured response assembling mixed entity/system context for a given focus entity or subsystem. Contains the focus object, related entities, related subsystems, relevant doc sections (reranked with inclusion reasons), capability framing, confidence notes, and truncation metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistants can retrieve any subsystem's full documentation profile (overview, sections, dependencies, entity links) in a single tool call
- **SC-002**: Subsystem doc section search returns relevant narrative sections for natural language queries, with relevant results appearing in the top 5 for known topics (e.g., "attack resolution" returns combat system sections)
- **SC-003**: Entity-to-subsystem context assembly returns relevant system-level narrative for known entities — `damage()` links to Combat System, `affect_to_char()` links to Affect System — with correct role assignments
- **SC-004**: Unified search (`source=all`) produces mixed entity + doc results correctly ranked, with `result_type` discriminator allowing consumers to filter by type
- **SC-005**: All 23 subsystem component documents are ingested, producing at least one overview section per subsystem and correctly chunked doc sections with section_kind classifications
- **SC-006**: Entity↔subsystem links cover at minimum the core and entry_point entities for each subsystem, with high-confidence curated links for primary functions referenced in component documentation
- **SC-007**: V1 tools continue to function identically after V2 tables are populated — no regressions in entity lookup, search, graph traversal, behavior analysis, or capability tools
- **SC-008**: Curation validation rules catch 100% of referential integrity errors (invalid entity_ids, invalid subsystem_ids) before database ingestion
- **SC-009**: Subsystem dependency graph correctly represents all dependency relationships declared in `subsystems.md`, with accurate upstream/downstream traversal
- **SC-010**: The V2 build script completes processing of all artifacts (23 subsystems, ~200 doc sections, curation links, dependency edges) and database population in under 10 minutes
- **SC-011**: When an entity has no subsystem links, context assembly tools return a meaningful response (capability fallback) rather than an error or empty result
- **SC-012**: Curation artifacts in `.ai/artifacts/v2/` are human-reviewable and can be re-ingested without rerunning the curation agent, producing identical database state

### Assumptions

- **A-001**: V1 of the MCP Documentation Server (spec 001-mcp-doc-server) is complete and operational before V2 work begins — V1 tables, tools, and response shapes are available and stable
- **A-002**: The 23 subsystem component documents in `.ai/docs/components/` and the subsystem index in `.ai/docs/subsystems.md` are complete and accurate at build time
- **A-003**: Entity↔subsystem links require agent-assisted curation — mechanical keyword matching is insufficient for accurate mappings; the curation agent uses V1's tools (search, behavior slices, capability detail) to make informed decisions
- **A-004**: The curation agent produces intermediate artifact files rather than writing directly to the database, enabling human review and correction before ingestion
- **A-005**: Subsystem hierarchy (parent/child nesting) is flat or shallow (1-2 levels maximum) based on the current 23 component documents
- **A-006**: The `section_kind` enumeration (overview, responsibilities, key_components, implementation, dependencies, behaviors, future) covers the heading patterns in existing component docs; new kinds may need to be added if document structure evolves
- **A-007**: Embedding generation for ~200 doc section chunks is feasible using the same embedding endpoint configured for V1 entity embeddings
- **A-008**: V2-reserved response shapes defined in V1's model layer (`SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) are used as-is — significant shape changes would require coordinated updates
- **A-009**: The `role` enumeration (core, entry_point, supporting, utility, integration) provides sufficient granularity for entity↔subsystem classification without needing custom per-subsystem roles
- **A-010**: The curation process is a one-time effort with incremental updates — not a continuous pipeline. Rebuilds happen when component docs or entity docs change significantly

## Dependency on V1

This specification is additive to spec `001-mcp-doc-server` (V1). The following V1 deliverables are prerequisites:

- V1 database schema (entities, edges, capabilities tables) — V2 adds tables, does not modify V1 tables
- V1 entity resolution pipeline — V2 tools use entity_id references from V1
- V1 hybrid search infrastructure — V2 extends it to subsystem doc embeddings
- V1 response shapes (EntitySummary, SearchResult envelope) — V2 extends them
- V1 model layer containing pre-defined V2-reserved shapes (SubsystemSummary, SubsystemDocSummary, ContextBundle)
- V1 MCP server framework and configuration — V2 tools register into the same server
