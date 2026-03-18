# MCP Documentation Server — What It Provides

> **Purpose:** Seed discussion on migration agent strategies and surface gaps in
> the tool surface before V2–V4 implementation proceeds. This is a disposable
> working document, not a permanent specification.
>
> **References:** [V1 Spec](../../mcp/doc_server/specs/v1/spec.md) ·
> [V2 Design](../../mcp/doc_server/specs/v2/DESIGN_v2.md) ·
> [Agent Requirements](speculative_agent_reqs.md)

---

## 1. Context

Two kinds of agent consume this server:

- **Specification-creating agents** research individual legacy features (e.g. the
  Fireball spell) and produce specs detailed enough that an implementing agent can
  work from them alone, without access to the legacy codebase.
- **System planning agents** navigate the codebase at the architectural level —
  system inventory, dependency graph, complexity signals — to plan migration waves
  and sequencing.

Both agents need factual, structural, and behavioral information about the legacy
C++ MUD codebase (~90 KLOC). The MCP server is the read-only reference layer that
provides it. It makes no migration prescriptions and performs no LLM inference at
runtime — all data is pre-computed and deterministic.

The server's information surface grows across four versions, each adding a new
perspective on the same codebase.

---

## 2. Information Layers

| Layer | Version | Question Answered | Data Sources |
|-------|---------|-------------------|--------------|
| **Implementation** | V1 (live) | *What is this code object and how does it work?* | Code graph (~5,300 entities, ~25K edges), LLM-generated entity docs, source code, 30 capability group definitions |
| **Conceptual** | V2 (designed) | *What larger system narrative helps interpret it?* | 29 curated component docs with tagged headings, entity↔subsystem links, system dependency graph |
| **User-Facing** | V3 (intent) | *What does the user see and expect?* | In-game help file system (format TBD) |
| **Specification / Design** | V4 (intent) | *What are the content authoring rules and constraints?* | External builder's guide (ingestion strategy TBD) |

Each layer is additive. V2 does not change V1 tools or tables. V3 and V4 follow
the same principle.

---

## 3. V1 — Implementation Layer (Live)

V1 exposes entity-level documentation, source code, dependency graphs, behavioral
analysis, and capability groupings through 19 tools, 5 resources, and 4 prompts.

### Data

| Artifact | Content |
|----------|---------|
| `code_graph.json` | ~5,300 entities parsed from Doxygen XML (functions, classes, structs, files, variables) |
| `code_graph.gml` | Directed multigraph with ~25,000 dependency edges (calls, uses, inherits, includes, contained_by) |
| `generated_docs/*.json` | LLM-generated documentation per source file — briefs, parameter descriptions, rationale, usage examples |
| `signature_map.json` | Deterministic entity ID bridge (`{prefix}:{7hex}`) between code graph and doc DB |
| `capability_defs.json` | 30 capability group definitions with type, stability, and function membership |
| `capability_graph.json` | Inter-capability dependency edges |

### Tools

#### Entity Lookup

| Tool | Purpose |
|------|---------|
| `get_entity` | Full entity record by ID — docs, source location, metrics, optional source code and graph neighbors |
| `get_source_code` | Source code with configurable context lines |
| `list_file_entities` | All entities in a source file, filterable by kind |
| `get_file_summary` | File-level statistics — entity counts by kind, capability distribution, top entities by fan-in |

#### Search

| Tool | Purpose |
|------|---------|
| `search` | Hybrid semantic (pgvector) + keyword (tsvector) search with exact-match boost; degrades to keyword-only when embeddings are unavailable |

#### Graph Navigation

| Tool | Purpose |
|------|---------|
| `get_callers` | Backward call graph traversal, depth 1–3 |
| `get_callees` | Forward call graph traversal, depth 1–3 |
| `get_dependencies` | Filtered dependencies by relationship type and direction |
| `get_class_hierarchy` | Base classes and derived classes for a class entity |
| `get_related_entities` | All direct neighbors grouped by relationship type |
| `get_related_files` | Related files via include relationships |

#### Behavioral Analysis

| Tool | Purpose |
|------|---------|
| `get_behavior_slice` | Transitive call cone with capabilities touched, globals used, and categorized side effects |
| `get_state_touches` | Direct + transitive global variable usage and side effects |
| `get_hotspots` | Entities ranked by fan-in, fan-out, bridge score, or documentation gaps |

#### Capabilities

| Tool | Purpose |
|------|---------|
| `list_capabilities` | All 30 capability groups with type, description, function count, stability |
| `get_capability_detail` | Group definition, typed dependency edges, entry points, optional function list |
| `compare_capabilities` | Shared/unique dependencies and bridge entities between 2+ capabilities |
| `list_entry_points` | `do_*`, `spell_*`, `spec_*` functions with optional capability/name filter |
| `get_entry_point_info` | Which capabilities an entry point exercises, with direct/transitive counts |

### What This Enables

A spec-creating agent can research a feature end-to-end at the code level:
resolve the entity → read its documentation and source → trace its call graph →
inspect its behavioral footprint (side effects, globals, capabilities touched) →
understand where it sits in the capability map. This is sufficient for features
that are self-contained within a single subsystem, but it gives the agent no
narrative context about the system the feature belongs to, no understanding of
what the user expects to see, and no knowledge of content authoring constraints.

---

## 4. V2 — Conceptual Layer (Designed, Stage 0 Complete)

V2 adds curated system-level narratives: 19 systems + 3 support entries, chunked
for semantic search, with grounding trust signals and entity↔subsystem links. V1
tools and tables are unchanged.

**Status:** Stage 0 (document rewrite) is complete — 29 component markdown files
exist in `artifacts/components/` with YAML frontmatter and inline section tags.
Stages 1–4 (mechanical chunking → curation → validation → ingestion) remain.

### Data

| Artifact | Content |
|----------|---------|
| `artifacts/components/*.md` | 29 curated system docs with YAML frontmatter (`id`, `kind`, `layer`, `depends_on`, etc.) and tagged `##` headings encoding section kind, grounding status, and narrative role |
| `subsystem_docs` table | Chunks with embeddings, grounding status (`grounded` / `mixed` / `weak` / `rejected`), narrative role (`overview` / `mechanism` / `dependency` / `edge_case` / `admin` / `history`) |
| `entity_subsystem_links` table | Many-to-many join with role, provenance, and confidence |
| `subsystem_edges` table | System-level dependency edges |

### New Tools

| Tool | Purpose |
|------|---------|
| `list_subsystems` | All subsystems with hierarchy and summary metrics; filter by kind, layer, or parent |
| `get_subsystem` | Full subsystem detail with sections ordered overview-first by narrative role; grounding-aware filtering |
| `get_subsystem_context` | Given an entity, assemble relevant system narrative via reranking (overview → evidence match → mentions → capability alignment) |
| `get_subsystem_dependencies` | System-level dependency graph traversal, depth 1–3 |
| `search_subsystem_docs` | Semantic + keyword search scoped to subsystem narrative prose |

### Enhanced V1 Tools

| Tool | Enhancement |
|------|-------------|
| `search` | New `source` parameter (`entity` / `subsystem_doc` / `all`); grounding-aware ranking for subsystem doc results |
| `get_entity` / `list_file_entities` | New `include_subsystems` flag adds subsystem links to entity responses |

### What This Enables

The system planning agent can now work at the architectural level: list all systems
by layer, traverse the system dependency graph, and assess complexity without
reading individual entities. The spec-creating agent gains narrative context — after
getting the code-level view of a feature via V1 tools, it can call
`get_subsystem_context` to understand how that feature fits into the broader system
and what architectural patterns surround it. Grounding signals let agents calibrate
trust: `grounded` sections are verified against code; `weak` sections warrant
source-level verification before relying on them in a spec.

---

## 5. V3 — User-Facing Layer (Intent)

V3 adds in-game help entries: the text players, builders, and administrators see
when they type `help <topic>` in the running MUD. This layer answers a question
no amount of source code analysis can: *what does the user expect to happen?*

Help entries describe game systems from the player's point of view — combat
mechanics as the player experiences them, spell effects as the player reads about
them, command syntax as the player learns it. For a spec-creating agent producing
a migration spec, this is the primary source for user-visible contracts: output
messages, syntax expectations, behavioral guarantees that the reimplementation must
preserve.

### Data source

The in-game help file system. Format, chunking strategy, and entity-linking
approach are not yet determined.

### Open questions

- What format are the help files? Structured (topic + body + see-also) or
  free-form text?
- How should help entries link to code entities and system concepts — automatic
  name matching, manual curation, or both?
- Should help entries carry their own grounding/trust signals, or is the source
  (official in-game help) sufficient to assume accuracy?
- How do overlapping help entries (e.g. `help cast` vs. `help fireball` vs.
  `help magic`) relate to each other and to the magic subsystem narrative?

---

## 6. V4 — Specification / Design Layer (Intent)

V4 adds builder's guide sections: external documentation describing how game
content is authored. Area file formats, value field meanings, flag definitions,
reset instruction syntax, mob/object prototype configuration — the rules and
constraints that govern the data layer of the game.

For a spec-creating agent, this is essential context for any feature that touches
authored content. A spell's damage dice, a mob's shop configuration, an area's
reset schedule — these are not implementation details discovered in source code,
they are configuration conventions documented in the builder's guide. Without this
layer, the agent must guess at data-level contracts or extract them from code that
was designed to be configured, not read.

### Data source

An external web-based builder's guide. Ingestion would involve HTML scraping and
section chunking.

### Open questions

- What is the scraping and chunking strategy? Does the guide have stable section
  structure, or is it free-form HTML?
- How should builder guide sections link to code entities — by area file field
  names, by object/mob prototype attributes, or by convention?
- Is a single unified embedding space across all four layers feasible, or do the
  different document types require separate search pipelines merged at query time?

---

## 7. Layered Lookup in Practice

To make the progression concrete, consider an agent researching `spell_fireball`:

**V1 (Implementation):** The agent searches for "fireball", gets the entity ID,
fetches documentation and source code from `magic.cc`. It traces the call graph:
`spell_fireball` calls `damage()`, which calls `update_pos()`. It gets a behavior
slice showing side effects (messaging to room, HP state mutation, potential death
processing) and capabilities touched (magic, combat). The agent now understands
*how fireball is implemented*.

**V2 (Conceptual):** The agent calls `get_subsystem_context` for the fireball
entity and receives the magic system's overview section, the "Spell Casting"
mechanism section explaining mana costs and interruption rules, and the
"Offensive Spells" section where fireball sits alongside other damage spells. It
also sees that the magic system depends on the affect system (for spell duration
effects) and the combat system (for damage delivery). The agent now understands
*how fireball fits into the architecture*.

**V3 (User-Facing):** The agent retrieves help entries for `cast`, `fireball`,
and `magic`. It learns that players see "You raise your hands and a ball of fire
erupts...", that the spell costs 15 mana at level 10, that it can be cast on a
target in the room or at self, and that the help text cross-references
`help saves` for damage reduction. The agent now understands *what the player
expects to see*.

**V4 (Specification):** The agent retrieves builder's guide sections on spell
configuration. It learns that fireball's damage dice are defined as object values
in the spell table, that the target type field controls valid targets, that the
minimum level per class is configured in the skill table, and that spell
availability can be modified by area-specific overrides. The agent now understands
*the data-level contract*.

With all four layers, the agent can produce a spec that captures implementation
mechanics, architectural context, user-visible behavior, and configuration rules —
enough for an implementing agent to reproduce the feature faithfully without
ever reading the legacy source.

---

## 8. Discussion Questions

1. **V1 behavioral tools in practice** — Are `get_behavior_slice`, `get_state_touches`,
   and `get_hotspots` producing shapes that agents actually find useful? Or do agents
   need different aggregations — e.g., "show me all messaging side effects for this
   entry point as output strings" rather than categorized function lists?

2. **V2 grounding granularity** — The four-level grounding model
   (grounded/mixed/weak/rejected) was designed so agents can calibrate trust. Is
   this the right granularity? Would a binary signal (verified/unverified) be
   simpler and equally effective?

3. **Cross-layer search timing** — Should unified cross-layer search (`source=all`
   spanning entities, subsystem docs, help entries, and builder guide sections)
   exist as early as V3, or are per-layer search tools sufficient until all layers
   are populated?

4. **Aggregation tools** — The speculative agent requirements propose
   `explore_entity` (orientation across all layers) and `explain_interface`
   (contract-focused view). Are these necessary, or do agents compose effectively
   from primitive tools?

5. **Help entry linking** — Automatic linking of help entries to code entities (by
   name matching) will produce noisy results. Manual curation is expensive. What
   is the right balance?

6. **Builder's guide scope** — How much of the builder's guide is relevant to
   migration? Some sections describe how to *use* the online building commands
   (which are being reimplemented from scratch) while others describe data formats
   and conventions (which constrain the reimplementation). Should V4 include both,
   or scope to data-level documentation only?
