# Feature Specification: MCP Documentation Server V2 — System-Level Documentation

> **Archived (2026-03-24):** This spec was not implemented. The V2 subsystem
> documentation layer was superseded by a simpler approach: component docs are
> served as MCP resources (`legacy://components`, `legacy://component/{id}`)
> with no new database tables, embeddings, or search pipelines. Retained for
> historical reference.

**Feature Branch**: `005-v2-subsystem-docs`
**Created**: 2026-03-24
**Status**: Archived (not implemented)
**Depends On**: V1 (live, `specs/v1/spec.md`)
**Input**: V2 indexing decisions (`v2_indexing.md`), agent requirements
(`docs/migration/speculative_agent_reqs.md`), prompt design (`ROADMAP.md §8`)

## Overview

V1 is entity-forward: every tool resolves, describes, and traverses individual
code entities. V2 adds a **system-level narrative layer**: curated prose
describing how larger game systems work, chunked for semantic search, with
entity↔subsystem links.

V1 answers: *"What is this code object and how does it work?"*
V2 answers: *"What larger system narrative helps interpret it?"*

V2 is purely additive. No V1 tables, tools, or response shapes change.

### What V2 provides

- **22 systems** organized in a shallow hierarchy with typed dependency edges
  (19 systems + 3 support entries from Stage 0 artifacts)
- **Curated narrative documentation** chunked at `##` heading boundaries
- **Many-to-many entity↔system links** with role, provenance, and confidence
- **System-level dependency graph** for cross-system navigation
- **Unified search** across entity docs (V1) and system narrative docs (V2)

### What V2 does NOT provide

Same principle as V1: no migration prescriptions, no architectural destination
guesses, no implementation ordering. Factual and structural information only.

### Stage 0 status

24 component markdown files exist in `artifacts/components/` with YAML
frontmatter and inline `<!-- section: ... -->` tags. 5 additional legacy files
exist without frontmatter (pre-rewrite). All 24 rewritten files have tagged
`##` sections (216 sections total, 100% tag coverage).

---

## User Scenarios & Testing

### User Story 1 — System Inventory and Navigation (Priority: P1)

A system planning agent needs to understand what systems exist, what depends on
what, and how they are organized. The agent lists all subsystems filtered by
layer, reads system-level dependency edges, and navigates from one system to its
upstream/downstream dependencies without inspecting individual code entities.

**Why this priority**: System inventory is the foundation for migration planning
— wave ordering, critical path identification, and scope estimation all start
from the system dependency graph.

**Independent Test**: List all subsystems, verify 22 entries with correct kind
and layer values matching frontmatter. Traverse dependency edges for `combat`
and verify upstream dependencies match `depends_on` from frontmatter. Verify
leaf systems (no upstream deps) and root systems (no downstream deps) are
consistent.

**Acceptance Scenarios**:

1. **Given** no parameters, **When** agent lists subsystems, **Then** receive
   all 22 entries with id, name, kind, layer, description, entity_count,
   doc_section_count, depends_on_count, depended_on_by_count
2. **Given** `layer=game_mechanic`, **When** agent lists subsystems, **Then**
   receive only game mechanic systems (combat, magic, affect_system,
   skills_progression, loot_generation)
3. **Given** `kind=support`, **When** agent lists subsystems, **Then** receive
   only support entries (utilities, memory_gc, event_dispatcher)
4. **Given** a subsystem id, **When** agent requests dependencies with
   `direction=upstream`, **Then** receive the systems this subsystem depends on

---

### User Story 2 — System-Level Documentation (Priority: P1)

A spec-creating agent researching a combat feature needs conceptual context
beyond what entity-level documentation provides. The agent fetches the combat
subsystem's documentation sections in narrative reading order (overview →
mechanism → dependency → edge case).

**Why this priority**: System narrative is the primary V2 value — without it,
agents have no architectural context for the features they're specifying.

**Independent Test**: Fetch `get_subsystem(combat)` and verify: overview section
is first, sections are ordered by narrative_role, body text is non-empty.

**Acceptance Scenarios**:

1. **Given** a subsystem id, **When** agent requests full detail, **Then**
   receive subsystem metadata plus doc sections ordered overview-first by
   narrative role priority
2. **Given** `include_entities=true`, **When** agent requests subsystem detail,
   **Then** receive linked entities as EntitySummary list with role and
   confidence from the join table

---

### User Story 3 — Entity-to-System Context Assembly (Priority: P1)

A spec-creating agent has identified entity `fn:51a4e7a` (`damage`) via V1
tools. It needs to understand how `damage` fits into the broader combat system
— not by reading all combat documentation, but by receiving the most relevant
sections ranked by evidence match, entity mention, and capability alignment.

**Why this priority**: This is the bridge between V1 (entity-level) and V2
(system-level). The `research_feature_for_spec` prompt calls this tool after
entity-level research to add architectural context.

**Independent Test**: Call `get_subsystem_context` for the `damage` entity.
Verify: combat overview section is included (linked subsystem), sections
mentioning `damage` or its direct neighbors are ranked higher, each returned
section has `inclusion_reason` and `narrative_role`, section count respects
`max_sections`.

**Acceptance Scenarios**:

1. **Given** an entity ID, **When** agent requests subsystem context, **Then**
   receive ranked doc sections from linked subsystems with inclusion_reason
   and narrative_role on each
2. **Given** an entity linked to multiple subsystems, **When** agent requests
   context, **Then** receive overview sections from each linked subsystem
3. **Given** `max_sections=5`, **When** agent requests context, **Then** receive
   at most 5 sections, prioritized by: overview → evidence match → entity
   mention → capability alignment

---

### User Story 4 — Subsystem Documentation Search (Priority: P2)

A planning agent needs to find which system handles "area resets" or "NPC
respawning" without knowing which subsystem owns that concept. The agent
searches subsystem documentation with a natural language query and receives
ranked prose sections.

**Why this priority**: Discovery is essential for agents that don't know the
system topology yet. This complements `list_subsystems` (structured browsing)
with semantic discovery.

**Acceptance Scenarios**:

1. **Given** a natural language query, **When** agent searches subsystem docs,
   **Then** receive ranked SubsystemDocSummary results with scores
2. **Given** `subsystem_id=combat`, **When** agent searches, **Then** results
   are scoped to combat system sections only

---

### User Story 5 — Unified Cross-Layer Search (Priority: P2)

A spec-creating agent searching for "death processing" should find both the
`raw_kill` entity (V1) and the "Death & Corpse Processing" system documentation
section (V2) in a single search call, each identified by `result_type`.

**Acceptance Scenarios**:

1. **Given** `source=all`, **When** agent searches, **Then** receive both
   entity and subsystem_doc results in a single ranked list, distinguished by
   `result_type`
2. **Given** `source=subsystem_doc`, **When** agent searches, **Then** receive
   only subsystem doc results
3. **Given** `source=entity` (default), **When** agent searches, **Then**
   V1 behavior is unchanged

---

### Edge Cases

- **Entity linked to zero subsystems**: `get_subsystem_context` returns empty
  sections list with a note, not an error
- **Subsystem with zero entity links**: `get_subsystem(include_entities=true)`
  returns empty entity list — valid for support entries
- **Subsystem doc section fails build validation**: Section is not ingested
  — build logs a warning
- **Orphan doc sections** (subsystem_id references nonexistent subsystem):
  Build validation rejects — FK constraint
- **Entity ID not found**: `get_subsystem_context` returns EntityNotFoundError
- **Search with `source=all` and no subsystem docs populated**: Returns only
  entity results (V1 behavior); no error

---

## Requirements

### Database Schema

#### Subsystems Table

- **FR-V2-001**: Schema MUST include a `subsystems` table with columns: `id`
  (TEXT PK), `name` (TEXT NOT NULL), `parent_id` (TEXT FK self-referencing,
  nullable), `kind` (TEXT NOT NULL), `layer` (TEXT), `description` (TEXT),
  `source_file` (TEXT), `depends_on` (JSONB), `depended_on_by` (JSONB)
- **FR-V2-002**: `kind` MUST be a closed enum: `system`, `feature`, `support`
- **FR-V2-003**: `layer` MUST be a closed enum: `infrastructure`, `data_model`,
  `game_mechanic`, `content_system`, `player_feature`, `operations`

#### Subsystem Docs Table

- **FR-V2-004**: Schema MUST include a `subsystem_docs` table with columns:
  `id` (SERIAL PK), `subsystem_id` (TEXT FK → subsystems), `section_path`
  (TEXT NOT NULL), `heading` (TEXT NOT NULL), `section_kind` (TEXT NOT NULL),
  `is_overview` (BOOLEAN DEFAULT FALSE), `narrative_role` (TEXT),
  `body` (TEXT NOT NULL), `source_file` (TEXT NOT NULL), `line_range` (INT4RANGE),
  `embedding` (VECTOR(N)), `search_vector` (TSVECTOR)
- **FR-V2-005**: `section_kind` MUST be a closed enum: `overview`,
  `responsibilities`, `key_components`, `implementation`, `dependencies`,
  `behaviors`, `future`
- **FR-V2-006**: *(removed)*
- **FR-V2-007**: `narrative_role` values MUST be: `overview`, `mechanism`,
  `dependency`, `edge_case`, `admin`, `history`
- **FR-V2-008**: Embedding column dimension MUST match V1's
  `EMBEDDING_DIMENSION` env var (default 768). Subsystem doc embeddings MUST
  use the same doc embedding model as V1 entity doc embeddings
  (BAAI/bge-base-en-v1.5)
- **FR-V2-009**: `search_vector` MUST be a weighted tsvector using english
  dictionary: `heading=A, body=B`
- **FR-V2-010**: Schema MUST include HNSW index on `embedding` column and GIN
  index on `search_vector`

#### Entity-Subsystem Links Table

- **FR-V2-011**: Schema MUST include an `entity_subsystem_links` table with
  columns: `entity_id` (TEXT FK → entities, PK), `subsystem_id` (TEXT FK →
  subsystems, PK), `role` (TEXT NOT NULL), `link_source` (TEXT NOT NULL DEFAULT
  'curated'), `confidence` (TEXT NOT NULL DEFAULT 'high'), `notes` (TEXT),
  `evidence` (JSONB)
- **FR-V2-012**: `role` MUST be a closed enum: `core`, `entry_point`,
  `supporting`, `utility`, `integration`
- **FR-V2-013**: `link_source` MUST be: `curated`, `inferred`, `imported`
- **FR-V2-014**: `confidence` MUST be: `high`, `medium`, `low`

#### Subsystem Edges Table

- **FR-V2-015**: Schema MUST include a `subsystem_edges` table with columns:
  `source_id` (TEXT FK → subsystems, PK), `target_id` (TEXT FK → subsystems,
  PK), `relationship` (TEXT NOT NULL)
- **FR-V2-016**: `relationship` MUST be: `depends_on`, `bidirectional`

### Tools

#### New V2 Tools

- **FR-V2-020**: System MUST provide `list_subsystems` tool accepting optional
  `kind`, `layer`, and `parent_id` filters, returning `SubsystemSummary[]`
- **FR-V2-021**: System MUST provide `get_subsystem` tool accepting
  `subsystem_id` (required), `include_sections` (bool, default true),
  `include_entities` (bool, default false), `include_dependencies` (bool,
  default true). Sections MUST be ordered by narrative_role priority:
  overview → mechanism → dependency → edge_case → admin → history.
- **FR-V2-022**: System MUST provide `get_subsystem_context` tool accepting
  `entity_id` (required) and `max_sections` (int, default 10). MUST return
  ranked doc sections with `inclusion_reason` and `narrative_role` on each.
  Retrieval priority:
  (1) overview sections of linked subsystems, (2) sections with evidence
  matching the entity or its direct neighbors, (3) sections mentioning the
  entity name, (4) capability-aligned sections, (5) dependency sections of
  linked subsystems
- **FR-V2-023**: System MUST provide `get_subsystem_dependencies` tool
  accepting `subsystem_id` (required), `direction` (`upstream`, `downstream`,
  `both`, default `both`), and `depth` (int, default 1, max 3). MUST return
  dependency tree with SubsystemSummary at each node
- **FR-V2-024**: System MUST provide `search_subsystem_docs` tool accepting
  `query` (required), `top_k` (int, default 10), and `subsystem_id` (optional
  scope filter). MUST return ranked
  SubsystemDocSummary results using hybrid search (pgvector cosine + tsvector
  ts_rank) with cross-encoder reranking

#### Enhanced V1 Tools

- **FR-V2-030**: `search` tool MUST accept a `source` parameter with values
  `entity` (default, unchanged V1 behavior), `subsystem_doc`, and `all`.
  When `source` includes subsystem docs, results MUST include
  `SubsystemDocSummary` entries in the `SearchResult` envelope with
  `result_type: "subsystem_doc"`
- **FR-V2-031**: When `source=all`, entity results and subsystem doc results
  MUST be ranked in a single list by cross-encoder score. Subsystem doc
  candidates MUST be reranked using the doc cross-encoder view only (no
  symbol view — subsystem docs are prose, not code identifiers)
- **FR-V2-033**: `get_entity` tool MUST accept an optional
  `include_subsystems` boolean parameter (default false). When true, the
  response MUST include a `subsystems` field: list of
  `{id, name, kind, role}` from the entity_subsystem_links table

### Response Shapes

- **FR-V2-040**: `SubsystemSummary` MUST include: `id`, `name`, `parent_id`,
  `kind`, `layer`, `description`, `source_file`, `entity_count`,
  `doc_section_count`, `depends_on_count`,
  `depended_on_by_count`
- **FR-V2-041**: `SubsystemDocSummary` MUST include: `id`, `subsystem_id`,
  `subsystem_name`, `section_path`, `heading`, `section_kind`,
  `narrative_role`, `source_file`, `line_range`, `excerpt`
- **FR-V2-042**: `SubsystemDocDetail` (full section in `get_subsystem`
  responses) MUST include all `SubsystemDocSummary` fields plus `body` (full
  markdown text)
- **FR-V2-043**: `ContextSection` (returned by `get_subsystem_context`) MUST
  include all `SubsystemDocSummary` fields plus `body` and `inclusion_reason`
- **FR-V2-044**: `inclusion_reason` MUST be one of: `overview_section`,
  `evidence_match`, `mentions_entity`, `same_capability`, `linked_subsystem`
- **FR-V2-045**: V1 `SearchResult` envelope MUST support `result_type:
  "subsystem_doc"` with `subsystem_doc_summary: SubsystemDocSummary` field
  (None when result_type is "entity")

### Build Pipeline

- **FR-V2-050**: Build MUST parse YAML frontmatter from each
  `artifacts/components/*.md` file to populate `subsystems` table rows
  (1:1 mapping)
- **FR-V2-051**: Build MUST split each file on `## ` headings, extract
  `<!-- section: ... -->` tags via regex, and produce one `subsystem_docs`
  row per section
- **FR-V2-052**: `narrative_role` MUST be derived from `section_kind` when
  not explicitly tagged: overview → overview, responsibilities → overview,
  key_components → mechanism, implementation → mechanism, behaviors →
  mechanism, dependencies → dependency, future → history
- **FR-V2-053**: Build MUST extract `depends_on` and `depended_on_by` from
  frontmatter and populate `subsystem_edges` table
- **FR-V2-054**: Build MUST generate embeddings for subsystem doc sections
  using the same doc embedding provider as V1 (BAAI/bge-base-en-v1.5, 768d).
  Embedding text MUST be `heading + body` concatenation
- **FR-V2-055**: Build MUST generate weighted tsvectors for subsystem doc
  sections: `setweight(to_tsvector('english', heading), 'A') ||
  setweight(to_tsvector('english', body), 'B')`
- **FR-V2-056**: Build MUST validate all foreign keys: `subsystem_docs.
  subsystem_id` → `subsystems.id`, entity_subsystem_links references valid
  entities in V1 `entities` table
- **FR-V2-057**: Build MUST validate that every subsystem has at least one
  `is_overview=true` doc section
- **FR-V2-058**: Build MUST run after V1 build and MUST NOT modify V1 tables
- **FR-V2-059**: Build MUST skip files without YAML frontmatter (legacy
  pre-rewrite files) with a warning log
- **FR-V2-060**: Build MUST be idempotent — repeated runs from same artifacts
  produce identical database state

### Curation

- **FR-V2-070**: Entity↔subsystem links MUST be curated using V1 tools to
  verify entity membership. `core` and `entry_point` roles require
  `confidence: high` and at least 2 populated evidence fields
- **FR-V2-071**: Grounding status on each section MUST be verified against
- **FR-V2-071**: *(removed)*
- **FR-V2-072**: Curation artifacts MUST be stored in `artifacts/v2/` as
  git-tracked intermediate files (JSONL/JSON), not written directly to DB
- **FR-V2-073**: Validation rules MUST run before ingestion: structural
  integrity (FK references, entry_point role targets functions only),
  quality checks (warn if system has <3 doc sections), canonical ownership
  conflict detection (flag high-similarity chunks under different owners)

### Retrieval

- **FR-V2-080**: *(removed)*
- **FR-V2-081**: `get_subsystem` MUST return sections in narrative_role
  priority order: overview → mechanism → dependency → edge_case → admin →
  history
- **FR-V2-082**: `get_subsystem_context` MUST perform reranked assembly, not
  dump all sections. Each section carries `inclusion_reason` for
  interpretability

---

## Success Criteria

### Measurable Outcomes

- **SC-V2-001**: After a full build, `subsystems` table contains all entries
  from frontmatter-bearing component docs (~22 rows)
- **SC-V2-002**: After a full build, `subsystem_docs` table contains one row
  per `##` section from rewritten docs (~216 rows)
- **SC-V2-003**: After a full build, `subsystem_edges` table contains edges
  matching the union of `depends_on` and `depended_on_by` from all frontmatter
- **SC-V2-004**: `list_subsystems` returns results in under 50ms
- **SC-V2-005**: `get_subsystem` returns full detail with sections in under
  100ms
- **SC-V2-006**: `get_subsystem_context` returns ranked sections in under
  500ms (includes entity lookup + section retrieval + ranking)
- **SC-V2-007**: `search_subsystem_docs` returns results in under 500ms
  including embedding query and cross-encoder reranking
- **SC-V2-008**: `search(source=all)` returns mixed entity + subsystem doc
  results ranked by cross-encoder score in under 500ms
- **SC-V2-009**: All subsystem doc sections have non-null embeddings after build
- **SC-V2-010**: V1 tools produce identical results with V2 tables present —
  no regressions
- **SC-V2-011**: Build pipeline completes V2 ingestion in under 2 minutes
  for ~22 subsystems and ~216 doc sections
- **SC-V2-012**: Searching for "area resets" or "NPC respawning" returns
  relevant world_system doc sections in top-5
- **SC-V2-013**: `get_subsystem_context` for entity `damage` returns combat
  system overview in the result set
- **SC-V2-014**: Two consecutive V2 builds from same artifacts produce
  identical subsystem_docs content (idempotent)

### Assumptions

- **A-V2-001**: Stage 0 artifacts (24 rewritten component docs with
  frontmatter and section tags) are complete and tagged consistently
- **A-V2-002**: V1 build has completed successfully before V2 build runs —
  V2 build validates FK references against V1 entities
- **A-V2-003**: The doc embedding model (BAAI/bge-base-en-v1.5) is suitable
  for subsystem narrative prose — these are technical descriptions of code
  systems, similar in domain to entity documentation
- **A-V2-004**: 216 subsystem doc sections is small enough that embedding
  generation and cross-encoder reranking add negligible overhead compared
  to V1's ~5,300 entities
- **A-V2-005**: Entity↔subsystem links will be curated in a separate step
  (Stage 2) and stored as intermediate artifacts before ingestion. This spec
  covers the schema and tools, not the curation workflow
- **A-V2-006**: The 5 legacy files without frontmatter in
  `artifacts/components/` are superseded by the 24 rewritten files and
  should be skipped by the build pipeline

---

## Implementation Phases

### Phase V2.1 — Schema + Build Pipeline

- Create V2 SQLModel table definitions (subsystems, subsystem_docs,
  entity_subsystem_links, subsystem_edges)
- Implement Stage 1 parser: frontmatter extraction, `##` splitting, tag
  parsing
- Implement `build_v2_db.py`: parse artifacts → embed sections → populate
  tables
- Implement validation rules (FK integrity, overview presence, quality
  warnings)
- Tests: build pipeline tests with fixture component docs

### Phase V2.2 — Core Tools

- `list_subsystems` with kind/layer/parent_id filters
- `get_subsystem` with section ordering, optional entities
  and dependencies
- `get_subsystem_dependencies` with direction and depth
- Tests: tool contract tests against fixture data

### Phase V2.3 — Search Integration

- `search_subsystem_docs` with hybrid search + cross-encoder reranking
- `search` enhancement: `source` parameter with `subsystem_doc` and `all`
  modes
- Tests: search quality tests for subsystem doc queries

### Phase V2.4 — Context Assembly + Entity Enhancement

- `get_subsystem_context` with reranked section assembly
- `get_entity` enhancement: `include_subsystems` flag
- Tests: context assembly tests verifying ranking priority and
  inclusion_reason

### Phase V2.5 — Curation

- Curation agent workflow using V1 tools to verify entity membership and
  create entity↔subsystem links
- Curation artifacts in `artifacts/v2/`
- Validation, flag resolution, final ingestion

---

## Design Decisions

### Why single embedding model for subsystem docs

Subsystem docs are narrative prose about code systems — they have no symbol
names, signatures, or C++ identifiers to embed separately. The dual-model
approach (doc + symbol) that V1 uses for entity search is unnecessary here.
Subsystem docs use only the doc embedding model (BAAI/bge-base-en-v1.5) and
a single tsvector (english dictionary).

### Why cross-encoder reranking for subsystem doc search

V1 demonstrated that cross-encoder reranking produces significantly better
result quality than raw embedding similarity scores. Subsystem doc search
uses the same cross-encoder (Xenova/ms-marco-MiniLM-L-12-v2) to maintain
consistent ranking quality across `source=all` queries that mix entity and
subsystem doc results.

### Why `get_subsystem_context` exists as a separate tool

The `research_feature_for_spec` prompt needs to add system-level context after
entity research. A dedicated tool (rather than requiring agents to manually
call `get_entity` → find linked subsystems → `get_subsystem` for each → filter
sections) reduces tool calls and enforces the reranked assembly pattern that
avoids context bloat.

### Why entity↔subsystem links are curated, not inferred

Automated inference (e.g., mapping entities to subsystems by capability group
or file path) produces noisy results. A function in `fight.cc` touches combat,
affects, objects, and character data — automatic assignment would link it to
all four subsystems with no role or confidence differentiation. Curation with
V1 tool verification produces higher-quality links with meaningful roles.

### Why 768-dim embeddings, not larger

V1 uses 768-dimensional embeddings (BAAI/bge-base-en-v1.5). Using a larger
model for subsystem docs would require either a separate vector column
dimension (complicating `source=all` search) or re-embedding all V1 entities.
Neither is justified for ~216 doc sections. The doc model is empirically
validated for technical prose.

### Why no `explore_entity` composite tool

The prompt design (`ROADMAP.md §8`) achieves the same outcome as a composite
`explore_entity` tool by guiding agents through existing primitive tools in
the right order. This avoids response-size problems (the composite tool would
return entity detail + neighbors + state touches + subsystem context in one
response) and lets agents decide what to fetch next based on what they see.

### Why per-layer search pipelines with late-stage merge

V1's `hybrid_search` is tightly coupled to the `Entity` model — 5-channel
retrieval, 8-signal candidate vector, dual cross-encoder views, and
query-shape-aware sort logic are all entity-specific. Rather than generalizing
this pipeline to handle arbitrary document types, V2 adds a separate
`search_subsystem_docs` pipeline function (analogous to `hybrid_search_usages`).

For `source=all` queries, the two pipelines run independently and their
results are merged into a single ranked list via cross-encoder score
comparison. This pattern scales cleanly to V3 (help docs) and V4 (builder
guide) — each layer adds its own pipeline function with retrieval logic
appropriate to its document shape, and the merge step combines results at
the end.

The alternative — a generic retrieval pipeline parameterized by document
type — would require abstracting away the very details that make each
pipeline effective (dual vs. single embeddings, symbol-vs-doc view
selection, query shape detection). The per-layer approach keeps each
pipeline simple and independently tunable.

### Why no trust or grounding signals on doc sections

Quality measures on narrative documentation are difficult to assign
reliably, and a "maybe trustworthy" signal is as useless to an agent as
no documentation at all. If a doc section is good enough to serve, serve
it. If it's not, don't ingest it.

Quality control happens at build time: the curation step (Phase V2.5)
verifies doc sections against code before ingestion. Sections that fail
curation are not ingested. Everything in the database is considered
authoritative for its layer.

### Why `SearchResult` uses optional typed fields

The `SearchResult` envelope uses `result_type` as a discriminator with
separate optional fields per type (`entity_summary`, `subsystem_doc_summary`,
etc.). By V4 this means four optional fields, one populated per result.

The alternative — a single polymorphic `content` field — is more compact
but less readable for LLM agents parsing tool responses. Named fields make
each result type's shape explicit in the schema. The tradeoff is acceptable
at four types; if the pattern extends further, revisit.
