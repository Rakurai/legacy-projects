# MCP Documentation Server — What It Provides

> **Purpose:** Seed discussion on migration agent strategies and surface gaps in
> the tool surface before V2–V4 implementation proceeds. This is a disposable
> working document, not a permanent specification.
>
> **References:** [V1 Spec](specs/v1/spec.md) ·
> [V1 Data Model](specs/v1/MODEL.md) ·
> [V1 Search Validation](specs/v1/search_performance.md) ·
> [V2 Design](specs/v2/DESIGN_v2.md) ·
> [Agent Requirements](../../docs/migration/speculative_agent_reqs.md)

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
analysis, and capability groupings through 16 tools, 5 resources, and 4 prompts.

### Data

| Artifact | Content |
|----------|---------|
| `code_graph.json` | ~5,300 entities parsed from Doxygen XML (functions, classes, structs, files, variables) |
| `code_graph.gml` | Directed multigraph with ~25,000 dependency edges (calls, uses, inherits, includes, contained_by) |
| `generated_docs/*.json` | LLM-generated documentation per source file — briefs, parameter descriptions, rationale, usage examples |
| `capability_defs.json` | 30 capability group definitions with type, stability, and function membership |
| `capability_graph.json` | Inter-capability dependency edges, member-to-capability mapping (~848 assignments) |

The signature map is computed on-the-fly at build time from `EntityDatabase` +
`DocumentDB` — no separate artifact file is required.

### Entity Identity

Entity IDs are deterministic: `{prefix}:{sha256(canonical_key)[:7]}` where the
canonical key is the signature map tuple `(compound_id, signature_or_name)`.
Prefixes: `fn` (function/define), `var` (variable), `cls` (class/struct), `file`
(file), `sym` (other). IDs are stable across rebuilds from identical artifacts.

The `search` tool is the sole path from human-readable text to entity IDs — no
other tool performs name-to-ID resolution.

### Tools

#### Entity Lookup

| Tool | Purpose |
|------|---------|
| `get_entity` | Full entity record by ID — docs, source location, metrics, optional source code and graph neighbors |
| `get_source_code` | Source code with configurable context lines |

#### Search

| Tool | Purpose |
|------|---------|
| `search` | Multi-view hybrid search with cross-encoder reranking (see below) |

Search uses a 5-channel retrieval pipeline:

1. **Doc semantic** — pgvector cosine similarity on `doc_embedding` (BAAI/bge-base-en-v1.5)
2. **Symbol semantic** — pgvector cosine similarity on `symbol_embedding` (jinaai/jina-embeddings-v2-base-code)
3. **Doc keyword** — `ts_rank` on `doc_search_vector` (english dictionary, stemming)
4. **Symbol keyword** — `ts_rank` on `symbol_search_vector` (simple dictionary, no stemming)
5. **Trigram** — `pg_trgm` similarity on `symbol_searchable`

All candidates are reranked by a cross-encoder (Xenova/ms-marco-MiniLM-L-12-v2).
Per-candidate score = max cross-encoder score across doc and symbol views, with
query-shape-aware view selection for symbol-like queries. No per-query
normalization. Embedding and cross-encoder are **required** infrastructure — there
is no keyword-only degraded mode.

Results include multi-view metadata: `winning_view`, `winning_score`,
`losing_score`.

#### Graph Navigation

| Tool | Purpose |
|------|---------|
| `get_callers` | Backward call graph traversal, depth 1–3 |
| `get_callees` | Forward call graph traversal, depth 1–3 |
| `get_dependencies` | Filtered dependencies by relationship type and direction |
| `get_class_hierarchy` | Base classes and derived classes for a class entity |
| `get_related_entities` | All direct neighbors grouped by relationship type |

#### Behavioral Analysis

| Tool | Purpose |
|------|---------|
| `get_behavior_slice` | Transitive call cone with capabilities touched, globals used, and categorized side effects |
| `get_state_touches` | Direct + transitive global variable usage and side effects |

#### Capabilities

| Tool | Purpose |
|------|---------|
| `list_capabilities` | All 30 capability groups with type, description, function count, stability |
| `get_capability_detail` | Group definition, typed dependency edges, entry points, optional function list |
| `compare_capabilities` | Shared/unique dependencies and bridge entities between 2+ capabilities |
| `list_entry_points` | `do_*`, `spell_*`, `spec_*` functions with optional capability/name filter |
| `get_entry_point_info` | Which capabilities an entry point exercises, with direct/transitive counts |

#### Interface Analysis

| Tool | Purpose |
|------|---------|
| `explain_interface` | Contract-focused view of a function: parameters, return value, preconditions, side effects, state assumptions |

### What This Enables

A spec-creating agent can research a feature end-to-end at the code level:
search for the entity → read its documentation and source → trace its call graph →
inspect its behavioral footprint (side effects, globals, capabilities touched) →
understand where it sits in the capability map → get a contract-focused interface
view. This is sufficient for features that are self-contained within a single
subsystem, but it gives the agent no narrative context about the system the feature
belongs to, no understanding of what the user expects to see, and no knowledge of
content authoring constraints.

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
| `get_entity` | New `include_subsystems` flag adds subsystem links to entity responses |

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

## 8. MCP Prompts — Agent Workflow Scaffolds

MCP prompts are role-specific workflow scaffolds that guide agents through the
right tools in the right order, with explicit depth budgets and stop conditions.
They are not generic "analyze X" prose — they are retrieval recipes designed to
prevent the primary failure mode: agents over-pulling graph/search context and
sifting through noise.

### Design principles

Every prompt encodes:

1. **Starting tool** — where to begin
2. **Depth budgets** — default graph depth, when to stop, when deeper traversal
   is justified
3. **Layer ordering** — which layer is authoritative for which question:
   implementation (how it works), conceptual (why it exists), help (what users
   expect), builder guide (data/config rules)
4. **Escalation rules** — only escalate summary → full record → source code when
   doc quality is low, result is central to the contract, evidence conflicts,
   or grounding is weak
5. **Structured synthesis target** — what the agent should produce at the end

Prompts should **not** start with transitive graph traversal, merge all layers
by default, or encourage "search everything about X" patterns.

### Prompt inventory

Eight prompts are planned, phased by tool availability. Prompts 1–4 use V1 tools
and can ship now. Prompts 5–6 require V2 subsystem tools. Prompts 7–8 require
V3/V4 ingestion.

#### V1-ready (spec-creating agent)

| Prompt | Purpose | Key tools |
|--------|---------|-----------|
| `research_feature_for_spec` | Full feature research: implementation → interface → behavior → conceptual context | `search` → `get_entity` → `get_source_code` → `get_state_touches` → `get_behavior_slice` → `explain_interface` → `get_subsystem_context`* |
| `trace_feature_concern` | Answer one narrow behavioral question (messaging, state mutation, persistence, scheduling) | `get_behavior_slice` → filter by concern → `get_entity`/`get_source_code` for relevant entities only |
| `explain_entity_in_context` | Lightweight orientation on a single entity | `get_entity(include_neighbors=true)` → `get_behavior_slice(max_depth=1)` → `get_subsystem_context`* |
| `map_interface_contract` | Extract the contract another system must rely on | `get_entity` → `explain_interface` → `get_state_touches` → optionally one layer of callees |

\* `get_subsystem_context` is a V2 tool; V1 versions of these prompts skip the
conceptual layer step and note the gap.

#### V2-ready (system planning agent)

| Prompt | Purpose | Key tools (V2) |
|--------|---------|----------------|
| `orient_to_system` | Understand one subsystem at the conceptual/dependency level | `list_subsystems` → `get_subsystem` → `get_subsystem_dependencies` → entity inspection only if docs are weak or complexity is high |
| `compare_systems_for_sequencing` | Migration sequencing analysis for a set of systems | `get_subsystem_dependencies` for each → `compare_capabilities` → `list_entry_points` → synthesize blockers, coupling, independent work |

#### V3/V4-ready (cross-layer)

| Prompt | Purpose | Key tools (V3/V4) |
|--------|---------|-------------------|
| `collect_user_visible_contract` | What does the player see and expect? | `search_help_docs` → `get_help_topic` → cross-check with `get_behavior_slice` |
| `collect_data_and_configuration_rules` | What are the content authoring constraints? | `search_builder_guide` → `get_builder_guide_section` → cross-check with `get_state_touches` |

### Primary prompt detail: `research_feature_for_spec`

This is the most important prompt — the primary workflow for the spec-creating
agent. The workflow walks implementation → interface → behavior → context:

1. **Resolve**: `search(feature_name)` → get entity ID
2. **Orient**: `get_entity(entity_id, include_code=false, include_neighbors=true)`
3. **Read code**: `get_source_code(entity_id)` — primary entity only
4. **Inspect callees**: Review direct neighbors from step 2. Follow a callee
   deeper only if: it appears in side effects/state touches, it defines an
   interface contract the feature depends on, or its brief is absent/unclear
5. **Behavioral footprint**: `get_state_touches(entity_id)` +
   `get_behavior_slice(entity_id, max_depth=2)`
6. **Interface contracts**: `explain_interface(entity_id)` for the primary entity
   and any dependency that looks like an external contract boundary
7. **Conceptual context** (V2): `get_subsystem_context(entity_id)` — skip in V1
8. **User-facing behavior** (V3): `search_help_docs` — skip until V3
9. **Config constraints** (V4): `search_builder_guide` — skip until V4
10. **Synthesize**: purpose, entry conditions, side effects, user-visible behavior,
    external contracts, config/data constraints, open uncertainties

**Stop rules**: Do not chase transitive callees unless they expose or constrain
the feature's interface. Prefer summaries/briefs before full records.

### Tool surface gaps for prompts

Several prompt patterns assume tool capabilities that do not yet exist:

| Gap | Impact | Where needed |
|-----|--------|-------------|
| No `exclude_ids` parameter on any tool | Agents cannot avoid re-fetching already-seen entities across sequential calls | All prompts (anti-bloat mechanism) |
| No file-level tools (`list_file_entities`, `get_file_summary`) | Cannot orient on "what else is in this file?" without manual search | `research_feature_for_spec` step 4 |
| No `get_hotspots` | Cannot quickly find high-fan-in or bridge entities for a capability | `orient_to_system`, `compare_systems_for_sequencing` |
| V2 subsystem tools not yet implemented | Planning agent prompts are blocked; spec agent prompts lose conceptual layer step | Prompts 5–6 blocked; prompts 1, 3 degraded |
| V3/V4 tools not yet designed | User-facing and builder constraint prompts are blocked | Prompts 7–8 blocked |

The `exclude_ids` gap is the most impactful — it is the primary anti-bloat
mechanism for iterative multi-call workflows and is referenced by every prompt.
Adding it as an optional parameter to `search`, `get_callers`, `get_callees`,
`get_related_entities`, and `get_behavior_slice` would be a small change with
high prompt-design payoff.

---

## 9. Discussion Questions

1. **`exclude_ids` priority** — The prompt designs all assume an `exclude_ids`
   parameter for iterative de-duplication. This is a small tool-surface change
   with high impact on every multi-call workflow. Should this be the next V1
   enhancement before V2 work begins?

2. **V1 behavioral tools in practice** — Are `get_behavior_slice` and
   `get_state_touches` producing shapes that agents actually find useful? Or do
   agents need different aggregations — e.g., "show me all messaging side effects
   for this entry point as output strings" rather than categorized function lists?

3. **V2 grounding granularity** — The four-level grounding model
   (grounded/mixed/weak/rejected) was designed so agents can calibrate trust. Is
   this the right granularity? Would a binary signal (verified/unverified) be
   simpler and equally effective?

4. **Cross-layer search timing** — Should unified cross-layer search (`source=all`
   spanning entities, subsystem docs, help entries, and builder guide sections)
   exist as early as V3, or are per-layer search tools sufficient until all layers
   are populated?

5. **`explore_entity` vs. prompts** — The speculative agent requirements propose
   `explore_entity` as a composite orientation tool. With `explain_entity_in_context`
   as a prompt (guiding the agent through existing primitive tools in the right
   order), is a dedicated tool still needed? Prompts avoid response-size problems
   by letting the agent decide what to fetch next.

6. **Help entry linking** — Automatic linking of help entries to code entities (by
   name matching) will produce noisy results. Manual curation is expensive. What
   is the right balance?

7. **Builder's guide scope** — How much of the builder's guide is relevant to
   migration? Some sections describe how to *use* the online building commands
   (which are being reimplemented from scratch) while others describe data formats
   and conventions (which constrain the reimplementation). Should V4 include both,
   or scope to data-level documentation only?

8. **Missing file-level tools** — V1 currently lacks `list_file_entities`,
   `get_file_summary`, `get_hotspots`, and `get_related_files` (described in the
   agent requirements but not implemented). Are these needed for the spec-creating
   agent workflow, or do `search` and graph tools provide sufficient coverage?

9. **Prompt shipping strategy** — Should V1-ready prompts (1–4) ship as MCP
   prompts immediately, with degraded notes where V2 steps are skipped? Or wait
   until V2 tools exist so the prompts are complete on first release?
