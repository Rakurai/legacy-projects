# MCP Documentation Server — Product Requirements Document

## 1. Overview

### 1.1 Product

An MCP (Model Context Protocol) server that exposes the Legacy MUD codebase (~90 KLOC C++) as a searchable, analysis-capable knowledge store for AI coding assistants.

### 1.2 Purpose

AI assistants working on the Legacy codebase need structured access to pre-computed documentation artifacts — entity-level documentation, dependency graphs, embeddings, capability classifications, and source code — without parsing raw JSON or loading large files into context. This server provides that access through a standardized MCP tool/resource/prompt interface.

### 1.3 Users

- **AI coding assistants** (Claude, Copilot, Cursor, etc.) operating in development sessions against the Legacy codebase
- **Migration agents** that need factual and structural understanding of the legacy code to inform rewrite decisions
- **Developers** using AI-assisted tooling for codebase exploration and understanding

### 1.4 Scope boundary

The server exposes **factual, structural, and behavioral** information about the legacy codebase. It does **not** prescribe migration strategy, target architecture, implementation ordering, or architectural destination guesses. Those are concerns of consuming agents.

---

## 2. Goals and Non-Goals

### 2.1 Goals

1. **Entity lookup** — resolve entity names to full documentation records with source code, supporting disambiguation of ambiguous bare names.
2. **Hybrid search** — combine keyword (full-text) and semantic (embedding-based) search across entity documentation and source code.
3. **Graph exploration** — expose the dependency graph (calls, uses, inherits, includes, containment) for traversal at configurable depth.
4. **Behavior analysis** — derive behavioral views from the graph: call cones, side-effect markers, state touches, hotspot detection.
5. **Capability browsing** — expose the 30 capability groups with their typed dependencies, entry point mappings, and function membership.
6. **Graceful degradation** — function correctly when no embedding provider is configured or when a configured provider encounters an error, falling back to keyword-only search with explicit mode reporting.
7. **Deterministic serving** — all data is pre-computed and loaded from a database. No LLM inference at runtime. Responses are reproducible.
8. **V2 readiness** — schema and response shapes are designed so that hierarchical system documentation (subsystem narratives, entity↔subsystem links) can be added without reworking V1 tables or tools.

### 2.2 Non-Goals

1. Migration prescriptions (target surfaces, migration modes, wave ordering, chunk sequencing).
2. Runtime LLM inference or dynamic documentation generation.
3. Write access — the server is read-only; data changes require re-running the offline build script.
4. Multi-codebase support — this server serves one codebase (Legacy MUD).
5. Authentication or multi-tenancy.

---

## 3. Acceptance Criteria

Implementation is phased; each phase builds on the prior phase's infrastructure.

### Phase 1 — Database + Core Lookup

- [ ] Build script populates all tables from artifacts without errors
- [ ] `search("damage")` returns ranked candidates including `void damage(Character *ch, ...)` from `src/fight.cc` <!-- spec 005: search replaces resolve_entity -->
- [ ] `get_entity` returns full record with all documentation fields, metrics, and optional source code
- [ ] `list_file_entities("src/fight.cc")` returns all entities in that file
- [ ] `get_file_summary("src/fight.cc")` returns entity counts and capability breakdown <!-- spec 005: doc_quality_distribution removed -->
- [ ] Resources (`legacy://entity/*`, `legacy://file/*`, `legacy://stats`) return correct data
- [ ] Entity IDs are deterministic `{prefix}:{7hex}` and stable across rebuilds <!-- spec 005 -->

### Phase 2 — Search

- [ ] `search("poison spreading between characters")` returns relevant entities ranked by combined score
- [ ] With no embedding provider configured, search returns results with `search_mode: "keyword_fallback"`
- [ ] Filtering by kind and capability works correctly <!-- spec 005: min_doc_quality filter removed -->

### Phase 3 — Graph Exploration

- [ ] `get_callers(entity_id, depth=2)` returns transitive callers with path information <!-- spec 005: entity_id only, not entity name -->
- [ ] `get_dependencies(entity_id, relationship="inherits")` returns class hierarchy
- [ ] All graph tools include truncation metadata when results are capped
- [ ] <!-- spec 005: resolution envelope removed from graph tools; tools accept only entity_id -->

### Phase 4 — Behavior Analysis

- [ ] `get_behavior_slice(entity_id, max_depth=5)` returns call cone with direct/transitive separation <!-- spec 005: entity_id only -->
- [ ] Side-effect markers correctly categorized (messaging, persistence, state_mutation, scheduling)
- [ ] `get_hotspots(metric="bridge")` returns cross-capability entities
- [ ] Provenance labels present on all derived data items

### Phase 5 — Capabilities + Prompts

- [ ] `list_capabilities` returns all 30 groups with correct types
- [ ] `compare_capabilities(["combat", "magic"])` shows shared/unique dependencies
- [ ] `list_entry_points(capability="combat")` returns filtered entry points
- [ ] All four canned prompts produce coherent analysis output

### Phase 6 — Deterministic IDs & Interface Simplification <!-- spec 005 -->

- [ ] Entity IDs follow `{prefix}:{7hex}` format, deterministic across rebuilds
- [ ] `resolve_entity` tool removed from catalog (19 tools)
- [ ] All tools accept only `entity_id` (no `signature` parameter)
- [ ] No `ResolutionEnvelope` in any response
- [ ] ≥95% of doc_db entries with briefs retain their brief in the database
- [ ] `doc_quality`, `doc_state`, `compound_id`, `member_id` columns removed

---

## 4. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| No embedding provider configured | Semantic search disabled; keyword-only mode | Explicit `keyword_fallback` mode; agents warned via `search_mode` field |
| Embedding provider error at query time | Single request degrades to keyword-only | Provider errors caught; request completes with keyword fallback and logs warning |
| Large call cones exceed response limits | Truncated behavior slices | `max_cone_size` parameter + truncation metadata in response |
| Entity resolution returns wrong entity | Agent proceeds with incorrect context | Deterministic entity IDs eliminate ID instability; search returns ranked results for disambiguation <!-- spec 005: deterministic IDs replace two-step resolve/get --> |
| Source code on disk out of sync with artifacts | Stale `source_text` in DB | Build script extracts source at build time; rebuild after code changes |
| Stale embedding artifact | Embeddings don't reflect documentation changes | Manual invalidation — developer deletes artifact file to trigger regeneration |
| First-run model download | Initial local embedding build requires internet | ONNX model cached locally (~130 MB); subsequent runs are fully offline |

---

## 5. Future (V2)

V2 adds hierarchical system documentation: subsystem narratives, entity↔subsystem mappings, and unified search across code entities and system-level prose. V2 is fully additive — no V1 tables or tools change.
