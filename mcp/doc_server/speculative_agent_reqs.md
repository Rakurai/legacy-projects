# MCP Legacy Documentation Server — Agent Requirements

This document describes the requirements for the MCP server from the perspective of
the agents that will consume it. It is intended to guide tool design, response shape
design, and prompt design for both the current V1/V2 implementation and future
extensions (in-game help system, builder's guide).

---

## 1. What the MCP Server Is and Is Not

The MCP server is a **read-only reference layer over the legacy C++ MUD codebase**.
Its job is to answer questions about what the legacy system is, how it works, and
how its pieces relate to each other.

**It is:**
- A structured, queryable knowledge store over legacy code, documentation, system
  narratives, user-facing help, and builder specifications
- A navigation aid that helps agents move between levels of abstraction
- A source of factual, structural, and behavioral information grounded in actual code

**It is not:**
- A migration planner — it does not prescribe target architectures, migration waves,
  or implementation ordering
- An intelligent router — it does not try to predict what an agent needs or make
  LLM calls internally to decide what to return
- Stateful — each tool call is independent; the server has no session or conversation
  memory

The server exposes **tools** (active queries returning structured data) and **prompts**
(canned analysis recipes guiding how to explore topics). The agents are responsible
for query sequencing and synthesis.

---

## 2. Information Layers

The server draws from four layers of information about the legacy system. These are
not separate tool families — they are different perspectives on the same concepts,
and a single agent query may need to draw from multiple layers. The layers are:

### 2.1 Implementation Layer
The actual C++ code: functions, variables, files, call graphs, data structures,
source locations, side effects. Answers: *"Here is exactly how this is implemented."*

Sources: `code_graph.json`, `code_graph.gml`, source code extracted at build time,
LLM-generated entity documentation (`doc_db`).

### 2.2 Conceptual Layer
System-level narratives describing how larger game systems work, their
responsibilities, their dependencies, and their internal components. Answers:
*"Here is what this system is supposed to do and how its pieces fit together."*

Sources: `components/*.md` documents chunked into `subsystem_docs` (V2), capability
group definitions.

### 2.3 User-Facing Layer
In-game help documentation describing game systems and how players, builders, and
administrators interact with them. Answers: *"Here is what a user of this system
sees and expects."*

Sources: In-game help file system (planned).

### 2.4 Specification/Design Layer
Builder's guide and area file documentation describing rules, constraints, and
conventions for how game content is configured. Answers: *"Here are the rules and
constraints that govern how things work at the data and configuration level."*

Sources: External builder's guide (web-based, planned).

---

## 3. Agent Types and Their Needs

Two distinct agent types consume this server. Their information needs and query
patterns are different.

### 3.1 Specification-Creating Agent

**Task:** Given a feature from the legacy system (e.g., the Fireball spell), produce
a specification and data contract for implementing that feature in the target system.
The spec must capture: what the feature does, how it behaves, what the user sees,
what contracts it must honor, and how it integrates with adjacent systems — with
enough fidelity that an implementing agent can work from the spec alone without
needing access to the legacy codebase.

**What it already has:**
- Knowledge of the target system architecture and substrate
- Context about which migration work has already been done (adjacent systems that
  are already implemented)
- A bounded scope: it does not need to fully understand every system the feature
  touches, only the interfaces between this feature and those systems

**What it needs from the MCP server:**

1. **Entity identity and documentation** — What is this thing? What does it do?
   What does the LLM-generated documentation say about its purpose, parameters,
   return value, side effects, and rationale?

2. **Source code** — What does the actual implementation look like? What functions
   does it call? What globals does it reference? What are the code-level details
   that documentation might not capture?

3. **Call graph context** — What are the direct callees with their brief descriptions?
   (Not the full transitive cone — just enough to understand the immediate
   dependencies and decide whether any of them need deeper investigation.)

4. **State and side effects** — What global state does this feature read and write?
   What are its observable side effects (messaging, persistence, state mutation,
   scheduling, combat)?

5. **User-facing behavior** — What do players see? What are the output strings? What
   are the user-visible contracts? (Help system layer.)

6. **Configuration constraints** — Are there area file or builder-level configurations
   that affect this feature? What are the rules and constraints? (Builder's guide layer.)

7. **System narrative context** — How does this feature fit into the conceptual
   narrative of the systems it belongs to? (Conceptual layer — subsystem docs.)

8. **Related concepts** — Are there other entities, help topics, or builder guide
   sections with high semantic similarity that might be relevant? (Similarity
   suggestions, not forced — the agent decides whether to follow them.)

**Query pattern:** Iterative and surgical. The agent starts with a specific entity,
gets a structured response, decides which aspects need deeper investigation, and
makes additional targeted calls. It does not need everything at once. Tool calls
are cheap and chaining is expected.

**Depth constraint:** The agent only needs to understand adjacent systems at the
interface level — what they expose and what contracts they require. It does not
need to understand the full implementation of adjacent systems if those are already
specified or implemented.

---

### 3.2 System Planning Agent

**Task:** Understand the legacy system at a high level to plan the migration: what
systems exist, what depends on what, what the critical paths are, which systems are
independent, and what scope each system represents.

**What it already has:**
- General knowledge of the migration approach and target architecture
- High-level understanding of what a MUD is and its common patterns

**What it needs from the MCP server:**

1. **System inventory** — What systems exist? What are they called, what layer are
   they at (infrastructure/data_model/game_mechanic/etc.), what kind are they
   (system/feature/support)?

2. **Dependency graph** — What depends on what? Which systems are foundational (must
   be implemented first)? Which systems are leaf nodes (can be implemented last)?
   What are the critical paths?

3. **Integration surfaces** — For each system, what does it expose to other systems?
   What entry points does it have? What interfaces do dependent systems rely on?

4. **Complexity signals** — What is the scope of each system? How many entities,
   entry points, and dependencies does it have? How well-documented is it? Are
   there known edge cases or architectural complexity?

5. **System narrative** — What does each system do, conceptually, and why does it
   exist?

6. **Comparative analysis** — How do systems relate to each other? Do any share
   dependencies, overlap in responsibilities, or have bidirectional coupling?

**Query pattern:** Broad and exploratory. The planning agent navigates the system
graph, starting from the full inventory and drilling into specific systems as needed.
It works primarily at the conceptual layer and rarely needs implementation details.
When it does need implementation details, it's usually to assess feasibility or
complexity, not to understand mechanics.

---

## 4. Core Response Design Principles

Regardless of which agent is calling, all tool responses follow these principles:

### 4.1 Return the thing requested plus navigation metadata

Every response contains:
1. The primary requested content (entity docs, source code, system narrative, etc.)
2. Brief descriptions of directly related items that the agent may want to query next
3. Similarity-based suggestions (labeled by source layer) for items with high
   semantic relevance, if any exist

The agent is not force-fed the related content — it receives enough to decide
whether to request more. The brief descriptions are summaries, not full records.

**Example:** A `get_source_code` call returns the source text plus a list of called
functions each with their brief documentation summary. The agent can decide "I
already know what `damage()` does, but I should look up `check_line_of_sight`."

### 4.2 Include IDs in every returned item

Every item returned in a response (entities, help topics, builder guide sections,
subsystem docs) includes its ID. The agent accumulates these IDs and can pass them
as an `exclude` parameter on subsequent calls to avoid receiving already-seen items.
This is the mechanism for de-duplication without server-side state.

### 4.3 Provenance and confidence on derived data

Any data that was derived (graph traversal, side-effect detection, similarity
matching) includes:
- `provenance`: how it was obtained (`graph_calls`, `graph_transitive`,
  `side_effect_marker`, `semantic_similarity`, `capability_map`, etc.)
- `confidence`: `direct`, `heuristic`, or `transitive`

This lets the agent calibrate how much to trust each piece of data.

### 4.4 Doc quality signals

Every entity returned includes a `doc_quality` field (`high`, `medium`, `low`)
so the agent can decide whether to trust the documentation or fetch and read the
source code directly.

### 4.5 Truncation metadata on all list results

All list-returning calls include: `truncated` (bool), `node_count` (returned),
`total_available` (if known), and `truncation_reason`. The agent is never left
assuming a list is complete when it is not.

### 4.6 Stateless, standalone responses

The server has no session memory. Each response must be self-contained and
meaningful in isolation. Tools do not assume the agent has seen previous results.

---

## 5. Tool Inventory

### 5.1 Entity Resolution and Lookup (V1 — Implemented)

**`resolve_entity(query, kind?, limit, verbose)`**
Find entities by name, signature fragment, or natural language. Returns ranked
candidates with match type and score. Use first, then follow with `get_entity`.

**`get_entity(entity_id, include_code, include_neighbors)`**
Full entity record: all documentation fields, source location, definition,
`doc_quality`, metrics (fan_in, fan_out, is_bridge), side_effect_markers.
Optionally includes source code and direct graph neighbors as EntitySummary list.

**`get_source_code(entity_name, context_lines?)`**
Source code for an entity plus: list of called functions with brief descriptions,
list of referenced globals with brief descriptions, file path, line range.
This is the primary "show me the implementation" tool.

**`list_file_entities(file_path, kind?)`**
All entities in a source file as EntitySummary list with line ranges and doc quality.

**`get_file_summary(file_path)`**
Entity counts by kind, capabilities present, doc quality distribution, key entities
by fan_in, includes/included_by.

---

### 5.2 Search (V1 — Implemented)

**`search(query, top_k, kind?, capability?, min_quality?, source?)`**
Hybrid pgvector + full-text search. Returns SearchResult envelope with result_type,
score, search_mode (hybrid/semantic_only/keyword_fallback), provenance, and
EntitySummary or SubsystemDocSummary. The `source` parameter filters to `entity`,
`subsystem_doc`, or `all` (V2). Degrades gracefully to keyword_fallback if embedding
endpoint is unavailable.

---

### 5.3 Graph Exploration (V1 — Implemented)

**`get_callers(entity, max_depth, limit)`**
Who calls this entity, up to max_depth hops. Includes truncation metadata.

**`get_callees(entity, max_depth, limit)`**
What this entity calls. Includes truncation metadata.

**`get_dependencies(entity, relationship?, max_depth)`**
Broader dependency traversal across CALLS, USES, INHERITS, INCLUDES edge types.

**`get_class_hierarchy(entity)`**
Inheritance tree up (base classes) and down (derived classes).

**`get_related_entities(entity, relationships?, limit)`**
Unified neighbor view grouped by relationship type and direction
(incoming/outgoing). Covers all edge types.

**`get_related_files(file_path, relationship?)`**
Related files via INCLUDES edges, shared entities, or co-occurrence in call chains.

---

### 5.4 Behavior Analysis (V1 — Implemented)

**`get_behavior_slice(entity, max_depth, max_cone_size)`**
Entry point behavioral footprint: direct_callees, transitive_call_cone,
capabilities_touched (with direct/transitive counts), globals_used,
side_effect_markers categorized, confidence. Pure graph traversal — no LLM calls.

**`get_state_touches(entity)`**
What state this entity reads/writes: direct_uses, direct_side_effects,
transitive_uses (2 hops), transitive_side_effects. Provenance labeled.

**`get_hotspots(metric, kind?, capability?, limit)`**
Entities ranked by fan_in, fan_out, bridge (cross-capability), or underdocumented.
Uses precomputed columns — fast.

---

### 5.5 Capabilities (V1 — Implemented)

**`list_capabilities()`**
All 30 capability groups with type, description, function_count, stability,
doc_quality_distribution.

**`get_capability_detail(capability, include_functions, include_dependencies)`**
Group definition, typed dependency edges, entry points, optionally full function
list as EntitySummary.

**`list_entry_points(capability?, pattern?, limit)`**
do_*, spell_*, spec_* functions with capabilities_touched.

**`compare_capabilities(capabilities[])`**
Side-by-side with shared/unique dependencies and bridge entities.

**`get_entry_point_info(entry_point)`**
Which capabilities this entry point exercises (direct/transitive counts), key
direct callees, call cone summary.

---

### 5.6 System Navigation (V2 — Planned)

**`list_subsystems(kind?, layer?, parent_id?)`**
All subsystems with hierarchy and summary metrics as SubsystemSummary list.
Supports filtering by kind (system/feature/support), layer, or parent.

**`get_subsystem(subsystem_id, include_sections, include_entities, include_dependencies, min_grounding?)`**
Full subsystem detail. Sections ordered overview-first by narrative_role
(overview → mechanism → dependency → edge_case → admin → history).
Optionally includes linked entities and dependency edges. `rejected` sections
excluded by default; `weak` sections flagged.

**`get_subsystem_context(entity, max_sections, min_grounding?)`**
Given an entity, assemble relevant system narrative. Reranking strategy: overview
sections of linked subsystems first, then sections with evidence matching the entity,
then sections mentioning the entity name, then capability-aligned sections. Each
returned section carries `inclusion_reason` and `narrative_role`.

**`get_subsystem_dependencies(subsystem_id)`**
System-level dependency graph navigation for a given subsystem.

**`search_subsystem_docs(query, subsystem_id?, min_grounding?)`**
Semantic + keyword search scoped to subsystem narrative prose.

---

### 5.7 Entity Exploration (Proposed — Bridges Implementation and Context Layers)

**`explore_entity(entity_name_or_signature, exclude_ids?)`**
High-level orientation entry point. Returns: full entity doc, direct call graph
neighbors with briefs, direct state touches, and a "related concepts" section
(similarity-based suggestions from all layers: entities, help topics, builder guide
sections, subsystem docs). Labeled by source so the agent understands what kind of
follow-up each suggestion would require. Designed as the natural first call when
starting to research a feature.

**`explain_interface(entity_name, exclude_ids?)`**
Contract-focused view of a function: parameters and their meanings (from doc params),
return value, preconditions (inferred from documentation), side effects from
side_effect_markers, what state it assumes exists. The "what do I need to provide
and what can I rely on?" view. Useful for the spec-creating agent establishing
integration contracts.

---

### 5.8 Help System Tools (Planned — User-Facing Layer)

**`search_help_docs(query, limit?, exclude_ids?)`**
Semantic + keyword search over in-game help entries. Returns help topic summaries
with excerpts and relevance scores. The entry point for help system exploration.

**`get_help_topic(topic_name, exclude_ids?)`**
Full text of a specific help entry plus related topics (by similarity or explicit
cross-references in the help text).

**`list_related_help_topics(entity_name_or_concept, exclude_ids?)`**
Given an entity name or concept, return help topics with high similarity. Returns
topic names, brief excerpts, and relevance scores — not full text. Designed for
the "is there user-facing documentation about this?" discovery query.

---

### 5.9 Builder's Guide Tools (Planned — Specification/Design Layer)

**`search_builder_guide(query, limit?, exclude_ids?)`**
Semantic + keyword search over builder's guide sections. Returns section summaries
with excerpts. Entry point for builder guide exploration.

**`get_builder_guide_section(section_id, exclude_ids?)`**
Full text of a builder guide section plus related sections and related entities.

**`list_related_builder_sections(entity_name_or_concept, exclude_ids?)`**
Given an entity or concept, return builder guide sections with high similarity.
Returns headings and excerpts — not full text.

---

### 5.10 System Planning Tools (Proposed — For System Planning Agent)

**`get_system_dependency_graph(system_ids?)`**
Full or focused system-level dependency DAG. Returns nodes (subsystems with kind,
layer, entity_count) and typed edges (depends_on, bidirectional). Supports passing
specific system IDs to get a focused subgraph.

**`list_systems_by_layer(layer?)`**
Groups systems by abstraction layer. Useful for understanding: what needs to exist
before what (foundational layers first)?

**`get_integration_surface(system_id)`**
For a system, return: entry points it exposes, functions other systems call on it,
data structures external systems need to know about. The "minimum contract to plan
around this system" view.

**`compare_systems(system_ids[])`**
Side-by-side comparison: shared dependencies, mutual coupling, entity overlap,
capability groups spanned. Answers "are these systems independent or tightly
coupled?"

**`find_system_by_concern(concept)`**
Semantic search at the system level: "what system handles inventory?" Returns
relevant systems with brief explanations of why they matched.

**`estimate_complexity(system_id)`**
Complexity signals for a system: entity count, avg doc quality, entry point count,
fan-in/fan-out distribution, inter-system dependency count, presence of weak/
rejected doc sections. Raw material for the planning agent to reason about scope
and risk. Not a migration prescription — factual signals only.

---

## 6. MCP Prompts

Prompts are canned analysis recipes that guide the agent on how to explore a
topic with the server. They define a workflow — which tools to call, in what order,
with what depth constraints, and what questions to ask at each step. The agent uses
these as starting points, not rigid scripts.

### 6.1 Feature Research Prompt (For Spec-Creating Agent)

**`research_feature(feature_name)`**

Guides the agent through:
1. Resolve the feature entity and fetch its documentation and source code
2. Examine direct callees with briefs — identify any that need deeper investigation
3. Get state touches — understand what global state is read/written
4. Get behavior slice at depth=2 — understand direct and near-transitive behavior
5. Search for related help topics — understand user-facing contracts
6. Search for related builder guide sections — understand configuration constraints
7. Get subsystem context — understand how this fits in the system narrative
8. Synthesize: what is the behavioral contract? What are the integration interfaces?
   What edge cases exist? What is the user-visible behavior?

Constraints: Stop at depth=2 for call graph exploration unless a callee is
undocumented or has low doc_quality. Do not explore adjacent systems deeply —
only their interfaces.

### 6.2 System Orientation Prompt (For System Planning Agent)

**`orient_to_system(system_id)`**

Guides the agent through:
1. Get system overview — what is this system, what layer, what kind?
2. Get dependency edges — what does it depend on, what depends on it?
3. Get integration surface — what does it expose?
4. Get entity counts and doc quality distribution — what is the scope?
5. Identify entry points — what are the externally-callable functions?
6. Note any weak/rejected doc sections — where is documentation unreliable?

### 6.3 Dependency Mapping Prompt (For System Planning Agent)

**`map_dependencies(system_ids?)`**

Guides the agent through:
1. Get the full system dependency graph (or a focused subgraph)
2. Identify leaf nodes (no upstream dependencies) — these can be implemented first
3. Identify critical path systems (high in-degree) — these are blockers
4. Identify bidirectionally coupled systems — these may need to be tackled together
5. Group by layer — infrastructure before data_model before game_mechanic, etc.

### 6.4 Explain Entity Prompt (General)

**`explain_entity(entity_name)`**

Guides the agent through:
1. Resolve entity
2. Fetch full entity with source code and neighbors
3. Get behavior slice
4. Get subsystem context
5. Search for related help topics and builder guide sections
6. Present: what is it, what does it do, how is it used, where does it fit?

### 6.5 Trace Behavior Prompt (For Spec-Creating Agent)

**`trace_behavior(entry_point, concern)`**

Given an entry point and a specific concern (e.g., "what messages does the player
see?" or "what state is mutated?"), guides the agent through:
1. Get behavior slice for the entry point
2. Filter the cone to entities relevant to the concern (messaging side effects,
   state mutation markers, etc.)
3. For each relevant entity, fetch its documentation
4. Synthesize: what is the behavioral contract for this concern?

---

## 7. Summary Table: Agent × Information Need × Tool

| Agent | Information Need | Primary Tools |
|-------|-----------------|---------------|
| Spec-Creating | What is this entity? | `resolve_entity`, `get_entity` |
| Spec-Creating | What does the code do? | `get_source_code` |
| Spec-Creating | What does it call? | `get_source_code` (called_functions in response), `get_callees` |
| Spec-Creating | What state does it touch? | `get_state_touches`, `get_behavior_slice` |
| Spec-Creating | What does the user see? | `list_related_help_topics`, `get_help_topic` |
| Spec-Creating | What are the config rules? | `list_related_builder_sections`, `get_builder_guide_section` |
| Spec-Creating | How does it fit architecturally? | `get_subsystem_context`, `get_subsystem` |
| Spec-Creating | What else is related? | `search`, `explore_entity` (similarity suggestions) |
| Spec-Creating | What is the integration contract? | `explain_interface` |
| System Planning | What systems exist? | `list_subsystems`, `list_systems_by_layer` |
| System Planning | What depends on what? | `get_system_dependency_graph` |
| System Planning | What does a system expose? | `get_integration_surface` |
| System Planning | How big/complex is a system? | `estimate_complexity`, `get_subsystem` |
| System Planning | Are these systems coupled? | `compare_systems` |
| System Planning | What system handles X? | `find_system_by_concern` |
| Both | Find entities by concept | `search` |
| Both | Entry points for a capability | `list_entry_points`, `get_entry_point_info` |
| Both | Understand capability relationships | `list_capabilities`, `compare_capabilities` |

---

## 8. Open Design Questions

These are areas where the design is not yet fully resolved and will need to be
addressed as implementation proceeds:

1. **Help system ingestion** — What is the format of the in-game help files? How
   are they chunked? Are they already structured (topic/body) or free-form text?
   How are they linked to entity names and system concepts?

2. **Builder's guide ingestion** — The guide is web-based. What is the ingestion
   strategy? HTML scrape + chunking? How are sections linked to area file concepts
   and entity names? What's the embedding model — same as entity docs?

3. **Cross-layer similarity** — When returning similarity suggestions across layers
   (entity docs, help topics, builder guide, subsystem narrative), how is relevance
   scored across heterogeneous sources? Is it a unified embedding space or separate
   searches merged by score?

4. **`explore_entity` response size** — The proposed `explore_entity` tool returns
   a lot: full doc, direct neighbors with briefs, state touches, and similarity
   suggestions. Is this too large? Should it be split into a lightweight orientation
   call and a separate similarity suggestion call?

5. **`exclude_ids` scope** — The exclude_ids parameter prevents already-seen items
   from being returned. Should this apply globally (exclude from all result lists)
   or per-list (exclude from a specific result category)?

6. **Grounding trust in spec creation** — When the spec-creating agent reads subsystem
   narrative sections with `grounding_status: weak`, how should it be guided to handle
   that? Should the prompt explicitly instruct it to verify weak claims against source
   code before including them in a spec?
