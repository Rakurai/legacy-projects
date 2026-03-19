# MCP Documentation Server — Final Form Design

## 1. Starting Point: What Agents Actually Do

The consensus documents define three agent roles with distinct workflows. The server must support all three without any of them needing to fall back to raw source code reading for answerable questions.

### Planning Agent Workflow

The planning agent consumes the chunk registry and produces a refined migration manifest. Its workflow:

1. Understand the full system inventory — what exists, at what layer, how big
2. Traverse the dependency graph — what blocks what, where are the critical paths
3. Assess complexity per system — entity count, doc quality, edge-case density
4. Identify integration surfaces — what does each system expose to others
5. Validate the chunk registry's dependency edges against actual code evidence
6. Produce ordering, grouping, and parallelization decisions

**What it queries:** System-level structure, dependency graphs, complexity metrics, integration surfaces. Rarely touches individual entity docs or source code. Needs to move fast across the whole codebase at a high altitude.

### Spec-Creating Agent Workflow

The spec agent receives a chunk assignment and produces a dossier following the §11 template. Its workflow for a given chunk (e.g., "hit resolution"):

1. **Orient** — What entities belong to this chunk? What entry points does it cover? What subsystems does it touch?
2. **Read the code** — Source for the key functions, call graph for dependencies, behavior slice for side effects
3. **Extract data contracts** — What formulas? What constants from data tables? What stacking/ordering rules?
4. **Extract output contracts** — What does the player see? What are the exact `act()` format strings? What does the help system say?
5. **Understand configuration** — What builder's guide rules govern this feature? What area file values parameterize it?
6. **Map the integration boundary** — What contracts does this chunk consume from infrastructure? What interfaces does it expose to adjacent chunks?
7. **Identify edge cases** — Boundary conditions, unusual interactions, known quirks
8. **Write the spec** — Formulas, constants, output templates, state transitions, test cases

**What it queries:** Everything. Entity docs, source code, call graphs, behavior slices, subsystem narratives, help entries, builder's guide sections, data table values, `act()` format strings. It moves from high-level orientation to deep code-level detail within a single session. The most demanding consumer of the server.

### Auditor Agent Workflow

The auditor receives a completed spec and checks it against the evidence. Its workflow:

1. **Completeness** — Does the spec cover all entry points the chunk enables? Are there entities in the chunk's scope that the spec doesn't mention?
2. **Formula verification** — Do the spec's formulas match the source code? Are constants correct against the data tables?
3. **Output verification** — Do the spec's message templates match the actual `act()` calls in the source?
4. **Contract consistency** — Do the spec's interface assumptions match the cited contract versions?
5. **Fidelity check** — Does the spec capture the legacy behavior, or does it inadvertently simplify/change it?

**What it queries:** The same data as the spec agent, but in verification mode — it's cross-referencing spec claims against server evidence rather than discovering new information. It needs efficient ways to ask "does the code actually do what the spec says it does?"

---

## 2. Information Layers (Reorganized by Purpose)

Instead of V1-V4 implementation phases, organize by what question the data answers:

### Layer A: Code Structure

*What is this code object and how does it work?*

This is the existing code graph, entity docs, and source code access. Already built (the current V1 surface). The data:

- ~5,300 entities parsed from Doxygen XML
- ~25,000 dependency edges (calls, uses, inherits, includes, contained_by)
- LLM-generated documentation per entity (briefs, parameters, rationale)
- Source code with configurable context lines
- 30 capability group definitions with membership and dependency edges
- Signature map for stable entity IDs

### Layer B: System Narrative

*What larger system does this belong to, and how do the pieces fit together?*

The 29 curated component markdown files with tagged headings, grounding signals, and entity↔subsystem links. Stage 0 (document rewrite) is complete; ingestion pipeline remains.

### Layer C: Player-Facing Contracts

*What does the user see and expect?*

Two sub-layers:

**C1: Help entries** — In-game help text that players read. Describes commands, spells, skills, game concepts from the player's perspective. This is the authoritative source for "what does the player expect?" questions.

**C2: Output templates** — The actual `act()` format strings extracted from C++ source code. These are the exact messages the player sees during gameplay: combat output, spell effects, skill use, movement, object interaction. Not what the help system *describes* — what the code *produces*.

C2 is the layer that didn't exist in the original V1-V4 roadmap but that Round 1 analysis identified as critical. The spec agent writing the combat dossier needs to know that the player sees `"Your slash hits $N."` — not a paraphrase, the actual format string. This is mechanically extractable from the source.

### Layer D: Configuration and Data Contracts

*What are the data-level rules and constants?*

Two sub-layers:

**D1: Static tables** — Structured data from `const.cc`, `tables.cc`, `merc.hh`: race definitions, class definitions, skill/spell table entries (level requirements, mana costs, target types, damage nouns), attack types, item types, weapon types, flag definitions, loot tables. These are the constants that parameterize everything.

**D2: Builder's guide** — External documentation describing area file formats, value field meanings, flag semantics, reset instruction syntax, mob/object prototype configuration. The rules for how content is authored.

### Layer E: Migration-Specific Artifacts

*What does this evidence mean for the migration?*

This layer doesn't exist yet and is new. It contains pre-computed artifacts that support planning and spec agents specifically:

**E1: Spell/behavior clusters** — Pre-computed groupings of spells (and potentially spec_fun behaviors) by behavioral similarity, using call-graph shape analysis from behavior slices. The spec agent writing the spell framework dossier needs to know which spells follow which pattern *before* starting.

**E2: `act()` message catalog** — A structured index of every `act()` call in the codebase, organized by source function, with format string, audience mode, and context entities. The auditor checking a spec's output templates can look up "what are all the `act()` calls in `one_hit()`?" and compare them to the spec.

**E3: Integration surface summaries** — Pre-computed per-subsystem: entry points exposed, functions called by other systems, shared data structures, user-visible surfaces. The planning agent's "what does this system expose?" question answered without manual graph traversal.

**E4: Data table extracts** — Structured, queryable versions of the C arrays from `const.cc`/`tables.cc`. Not just "here's the source code for the race table" but "here is the race `elf`: STR max 16, DEX max 23, size small, vulnerabilities: [iron], resistances: [charm]."

---

## 3. Tool Surface (Final Form)

Organized by workflow, not implementation phase. Every tool is available from day one.

### 3.1 Entity Lookup and Code Access

These are the "show me the code" tools. Unchanged from the current V1 surface except for the addition of `explore_entity`.

| Tool | Purpose |
|------|---------|
| `search` | Hybrid semantic + keyword search across all layers (entities, subsystem docs, help entries, builder guide, output templates). Filterable by source layer. |
| `explore_entity` | **Composite.** Orientation entry point: full entity doc, direct call-graph neighbors with briefs, state touches, and related-concepts suggestions from all layers. The default first call for any spec agent research. |
| `get_entity` | Full entity record by ID with optional source code and graph neighbors |
| `get_source_code` | Source code with context lines, plus called functions and referenced globals with briefs |
| `list_file_entities` | All entities in a source file, filterable by kind |
| `get_file_summary` | File-level statistics: entity counts, capability distribution, top entities |

### 3.2 Graph Navigation

Unchanged from current V1. These are fine as-is — they're primitive building blocks that the composite tools and prompts orchestrate.

| Tool | Purpose |
|------|---------|
| `get_callers` | Backward call graph, depth 1–3 |
| `get_callees` | Forward call graph, depth 1–3 |
| `get_dependencies` | Filtered dependencies by relationship type and direction |
| `get_class_hierarchy` | Inheritance tree |
| `get_related_entities` | All direct neighbors grouped by relationship type |
| `get_related_files` | Related files via include relationships |

### 3.3 Behavioral Analysis

Mostly unchanged, but with one significant addition: output template extraction.

| Tool | Purpose |
|------|---------|
| `get_behavior_slice` | Transitive call cone with capabilities touched, globals used, side effects categorized |
| `get_state_touches` | Direct + transitive global variable usage and side effects |
| `get_hotspots` | Entities ranked by fan-in, fan-out, bridge score, or doc gaps |
| `get_output_templates` | **New.** For a given function, return all `act()` calls within its call cone: format strings, audience modes, and context entity roles. This is the "what does the player see?" tool at the code level. |

### 3.4 Capability and System Navigation

Enhanced with integration surface and complexity tools for the planning agent.

| Tool | Purpose |
|------|---------|
| `list_capabilities` | All 30 capability groups with type, description, function count, stability |
| `get_capability_detail` | Group definition, dependencies, entry points, function list |
| `compare_capabilities` | Shared/unique dependencies and bridge entities between capabilities |
| `list_entry_points` | `do_*`, `spell_*`, `spec_*` functions with capability/name filter |
| `get_entry_point_info` | Which capabilities an entry point exercises |
| `list_subsystems` | All subsystems with hierarchy and summary metrics |
| `get_subsystem` | Full subsystem detail with narrative sections, grounding-aware |
| `get_subsystem_context` | Given an entity, assemble relevant narrative via reranking |
| `get_subsystem_dependencies` | System-level dependency graph traversal |
| `search_subsystem_docs` | Semantic + keyword search scoped to subsystem prose |
| `get_integration_surface` | **New.** Per subsystem: exposed entry points, functions called by external systems, shared state, user-visible surfaces, weak-doc areas. The "minimum contract to plan around this system" view. |
| `estimate_complexity` | **New.** Per subsystem: entity count, entry point count, fan-in/fan-out distribution, doc quality distribution, inter-system dependency count. Raw signals for scope and risk assessment. |

### 3.5 Player-Facing Contracts

All new. This is the layer that didn't exist and that every Round 1 response flagged as critical.

| Tool | Purpose |
|------|---------|
| `search_help` | Semantic + keyword search over in-game help entries |
| `get_help_topic` | Full text of a help entry plus related topics |
| `list_related_help` | Given an entity or concept, return help topics with high similarity |
| `get_output_templates` | (Listed above in §3.3 — serves both behavioral analysis and output contract extraction) |
| `search_output_templates` | **New.** Search the `act()` message catalog by keyword, function, or capability. "Show me all combat messages containing 'slash'" or "all messages produced by `spell_fireball`." |

### 3.6 Configuration and Data Tables

All new. The highest-value addition for spec agents after the output template tools.

| Tool | Purpose |
|------|---------|
| `get_table_entry` | **New.** Structured query: `get_table_entry("skill", "fireball")` → returns level requirements per class, mana cost, target type, damage noun, spell group, function pointer name. Works for: skill_table, race_table, class_table, attack_table, item_type_table, weapon_table, flag_defs. |
| `list_table_entries` | **New.** List all entries in a table, with optional filters. `list_table_entries("skill", spell_group="offensive")` → all offensive spells with their metadata. |
| `search_builder_guide` | Semantic + keyword search over builder's guide sections |
| `get_builder_guide_section` | Full text of a builder guide section plus related sections |
| `list_related_builder_sections` | Given an entity or concept, return builder guide sections with high similarity |

### 3.7 Migration Support

New tools that leverage pre-computed migration artifacts.

| Tool | Purpose |
|------|---------|
| `get_spell_cluster` | **New.** For a spell, return its behavioral cluster (damage/affect/heal/transport/detect/bespoke), the cluster's common call-graph pattern, and how this specific spell deviates from the pattern. For a cluster name, return all member spells. Supports the framework + catalog approach. |
| `list_spell_clusters` | **New.** All behavioral clusters with member counts and pattern descriptions. |
| `get_chunk_evidence` | **New.** For a chunk from the registry, return: all entry points it enables, all entities in its scope, all subsystems it touches, relevant data table entries, relevant help topics, relevant builder guide sections. The "everything the spec agent needs to start" package. |

---

## 4. Resources (Static Data Exposed via MCP)

Resources are static or slowly-changing data that agents can read without parameters.

| Resource | Content |
|----------|---------|
| `system_inventory` | All subsystems with kind, layer, summary, entity count, doc quality distribution |
| `dependency_graph` | Full system-level dependency DAG as structured data |
| `capability_definitions` | All 30 capability groups with types, dependencies, function counts |
| `chunk_registry` | The migration chunk registry with phases, modes, dependencies, entry-point enablement |
| `contract_index` | Index of all infrastructure contracts with versions and status |

---

## 5. Prompts (Workflow Recipes)

Prompts guide agents through multi-step workflows. They don't call tools — they describe which tools to call, in what order, with what depth constraints.

### 5.1 `research_feature` (Spec-Creating Agent)

*"I need to write a spec for [feature]. Walk me through the research."*

1. Call `get_chunk_evidence(chunk_id)` for initial scope
2. For each key entry point: call `explore_entity` for orientation
3. For high-complexity entities: call `get_source_code` + `get_behavior_slice`
4. Call `get_output_templates` for each entry point to extract player-visible messages
5. Call `get_table_entry` for each skill/spell/data-driven value referenced
6. Call `get_subsystem_context` for the primary entity to understand architectural context
7. Call `search_help` + `list_related_help` for player-facing documentation
8. Call `search_builder_guide` if the feature touches authored content
9. Check `get_spell_cluster` if the feature involves spells
10. Synthesize: behavioral contract, integration interfaces, data contracts, output templates, edge cases

Depth rule: stop at depth 2 for call-graph exploration unless a callee is undocumented. Don't explore adjacent systems beyond their interface.

### 5.2 `plan_system` (Planning Agent)

*"I need to assess [system] for migration planning."*

1. Call `get_subsystem(system_id)` for overview
2. Call `get_subsystem_dependencies` for upstream/downstream
3. Call `get_integration_surface` for the system's external API
4. Call `estimate_complexity` for scope signals
5. Call `list_entry_points(capability=...)` for the system's capabilities
6. Note weak-doc sections from the subsystem detail
7. Cross-reference against the chunk registry to validate chunk boundaries

### 5.3 `audit_spec` (Auditor Agent)

*"I need to verify [spec] against legacy evidence."*

1. For each formula in the spec: call `get_source_code` for the implementing function and verify the formula matches
2. For each constant in the spec: call `get_table_entry` and verify the value matches
3. For each output template in the spec: call `get_output_templates` for the relevant function and verify the format strings match
4. For each integration contract cited: check the contract registry resource and verify the spec's assumptions align with the contract version
5. For each entry point the chunk enables: verify the spec mentions it (call `get_chunk_evidence` for the entry-point list)
6. Flag: any spec claim not traceable to a server evidence source

### 5.4 `trace_behavior` (Spec-Creating Agent, Focused)

*"What exactly happens when [entry_point] runs, focused on [concern]?"*

Concerns: "messaging" → extract all `act()` calls; "state mutation" → extract all globals written; "damage" → trace the damage pipeline; "affect interaction" → trace affect queries and modifications.

1. Call `get_behavior_slice` for the entry point
2. Filter the call cone to entities relevant to the concern
3. For messaging concern: call `get_output_templates` for the entry point
4. For state concern: call `get_state_touches`
5. For each relevant entity in the filtered cone: call `get_entity` for its documentation
6. Synthesize the behavioral contract for this specific concern

### 5.5 `cluster_spells` (Spec-Creating Agent, Spell Framework)

*"I need to understand the spell patterns for the framework spec."*

1. Call `list_spell_clusters` for the full clustering
2. For each major cluster: call `get_spell_cluster(cluster_name)` for members and pattern
3. Pick one representative spell per cluster and call `get_source_code` + `get_behavior_slice` to verify the pattern
4. Identify outliers within each cluster (spells with deviation notes) — these are candidates for bespoke treatment
5. For the bespoke cluster: examine each member to determine if sub-patterns exist

---

## 6. Required Pre-Computation and Curation Work

This is the work that must happen before the server is complete. Organized by effort type.

### 6.1 Automated / Computed (No Human Input)

These are mechanical extraction and computation tasks.

| Task | Input | Output | Method |
|------|-------|--------|--------|
| **`act()` format string extraction** | C++ source files | Structured catalog: {function, format_string, audience, context_roles} | Parse `act()` call sites from source. The pattern is consistent: `act("format", ch, obj, vict, TO_*)`. Regex or AST-based extraction. Expect ~500-800 call sites. |
| **Data table structuring** | `const.cc`, `tables.cc`, `merc.hh` source | Structured JSON per table: race_table, class_table, skill_table, attack_table, item_type_table, weapon_table, flag_defs | Parse C array initializers. The table formats are regular (structs with known fields). Semi-automated: write a parser per table type, hand-verify edge cases. |
| **Spell behavior clustering** | Behavior slices for all `spell_*` entry points | Cluster assignments: {spell_name, cluster, common_pattern, deviations} | Compute behavior slice for each spell, extract call-graph signature (the set of key functions called: damage(), affect_to_char(), char_from_room(), etc.), cluster by signature similarity. |
| **Integration surface computation** | Code graph + subsystem membership | Per-subsystem: {exposed_entry_points, externally_called_functions, shared_state, user_visible_surfaces} | Graph analysis: for each subsystem, find functions called by entities in *other* subsystems. Find globals read/written by external callers. Find entry points (do_*, spell_*, spec_*) within the subsystem. |
| **Complexity estimation** | Code graph + entity docs + subsystem membership | Per-subsystem: {entity_count, entry_point_count, fan_in_distribution, fan_out_distribution, doc_quality_distribution, inter_system_dependency_count} | Aggregation over existing metrics. Straightforward. |
| **Chunk evidence assembly** | Chunk registry + code graph + all layers | Per-chunk: {entry_points, entities, subsystems, data_table_entries, help_topics, builder_guide_sections} | Cross-reference chunk membership against all data layers. Join on entity names, capability groups, and semantic search for concepts. |

### 6.2 LLM-Assisted (Agentic Curation)

These tasks benefit from LLM judgment but don't require deep domain expertise.

| Task | Input | Output | Method |
|------|-------|--------|--------|
| **Subsystem doc ingestion (V2 completion)** | 29 component markdown files with tagged headings | Chunked sections in DB with embeddings, grounding status, narrative role, entity links | Mechanical chunking by heading tags → embedding generation → entity linking via name matching + semantic similarity. The 29 source docs already have YAML frontmatter and section tags (Stage 0 is complete). The remaining work is: chunk, embed, link to entities, and validate grounding signals. |
| **Help file ingestion** | In-game help file corpus | Structured entries: {topic, body, see_also, linked_entities, linked_subsystems} | Parse help files into topic/body pairs. Link to code entities by name matching (automated) + semantic similarity for concept-level links. An LLM pass can generate brief summaries and identify which entities/commands each help entry describes. |
| **Builder's guide ingestion** | Web-based builder's guide HTML | Chunked sections with embeddings and entity links | Scrape HTML, section by heading, embed, link to code entities by matching area file field names and object/mob prototype attributes. LLM pass to summarize each section and tag it with the game concepts it governs. |
| **Spell cluster validation** | Automated cluster assignments | Validated clusters with human-readable pattern descriptions and confirmed outlier flags | LLM reviews each cluster: does the grouping make sense? Are the "deviations" real or artifacts of the call-graph analysis? Produces a natural-language description of each cluster's common pattern. |
| **Cross-layer entity linking** | All layers | Many-to-many links: {entity ↔ help_topic, entity ↔ builder_section, entity ↔ subsystem_doc, help_topic ↔ builder_section} | Automated name matching produces a first pass. LLM-assisted pass resolves ambiguities (e.g., "cure light" in help refers to `spell_cure_light` in code, but name matching alone might miss it). |

### 6.3 Human Curation Required

These tasks need domain expertise that neither automation nor LLM inference can reliably provide.

| Task | Input | Output | Why Human |
|------|-------|--------|-----------|
| **Grounding validation for subsystem docs** | Subsystem doc sections with auto-assigned grounding status | Validated grounding: grounded / mixed / weak / rejected | The grounding signal says "can we trust this narrative?" An LLM can *guess* based on whether code evidence supports the claims, but only a domain expert can confirm whether a "mixed" section is reliable enough for spec-writing or whether it needs source-level verification. This is ~200-300 sections across 29 docs. |
| **Help file completeness assessment** | Help corpus + system inventory | Gap analysis: which systems have no help coverage? Which help entries are stale? | Someone who knows the game needs to assess whether the help corpus is comprehensive enough to serve as a player-visible contract source, or whether significant gaps exist that would leave spec agents without output references. |
| **Data table verification** | Parsed table data + source code | Confirmed table values | The automated parser will get most values right, but C array initializers with macros, conditional compilation, and implicit defaults need human spot-checking. This is especially important for the skill_table (200+ entries) where a misparse could propagate incorrect mana costs or level requirements into every spell spec. |
| **Chunk registry → evidence mapping review** | Auto-generated chunk evidence packages | Confirmed scope per chunk: are the right entities assigned to each chunk? | The automated assembly will join on capability groups and name matching, but some entities are ambiguous (a utility function used by multiple chunks, an entity whose name doesn't match any chunk's capability group). Human review ensures each chunk's evidence package is complete and correctly scoped. |

---

## 7. What the Server Does NOT Do

Maintaining boundary discipline from the original design:

- **No migration prescriptions.** The server doesn't suggest Evennia implementations, target architectures, or migration ordering. It provides facts about the legacy system.
- **No LLM inference at runtime.** All data is pre-computed and deterministic. Search uses embeddings but no generative inference.
- **No session state.** Each tool call is independent. Agents are responsible for query sequencing.
- **No contract registry hosting.** The contract registry is a migration-repo artifact, not a server feature. The server provides evidence; the contracts directory consumes that evidence.

---

## 8. Sizing and Feasibility

Rough estimates for the pre-computation work:

| Work Item | Estimated Effort | Confidence |
|-----------|-----------------|------------|
| `act()` extraction | 2-3 days (parser + validation) | High — the call pattern is regular |
| Data table structuring | 3-5 days (parser per table type + spot-checking) | Medium — macro expansion and edge cases |
| Spell clustering | 1-2 days (automated) + 1 day (LLM validation) | High — behavior slices already exist |
| Integration surface computation | 1 day (graph queries) | High — straightforward aggregation |
| Complexity estimation | 0.5 days | High — aggregation of existing metrics |
| Chunk evidence assembly | 1-2 days | Medium — depends on cross-layer link quality |
| Subsystem doc ingestion | 3-5 days (chunking + embedding + linking) | Medium — Stage 0 done, pipeline TBD |
| Help file ingestion | 2-4 days (depends on format) | Low — format not yet determined |
| Builder's guide ingestion | 3-5 days (scraping + chunking + linking) | Medium — depends on HTML structure |
| Cross-layer entity linking | 2-3 days (automated + LLM review) | Medium |
| Human grounding validation | 3-5 days of domain expert time | Medium |
| Data table verification | 1-2 days of domain expert time | High |
| Chunk evidence review | 1-2 days of domain expert time | High |

**Total estimate:** ~25-40 days of work, with ~5-10 days requiring domain expert input and the rest being engineering/curation tasks. The server tooling (new endpoints, search integration) is additional on top of data preparation.

---

## 9. Priority Order for Curation Work

Not all layers are equally blocking. If we sequence the curation work:

**Tier 1 — Blocks all spec work:**
1. Subsystem doc ingestion (Layer B) — planning agent can't navigate architecture without it
2. Data table structuring (Layer D1) — every spec references constants
3. `act()` format string extraction (Layer C2) — every spec needs output templates
4. Integration surface computation (Layer E3) — planning agent needs this for manifest

**Tier 2 — Blocks specific spec domains:**
5. Spell clustering (Layer E1) — blocks the magic framework dossier
6. Help file ingestion (Layer C1) — needed for player-facing contract verification
7. Chunk evidence assembly (Layer E4) — needed before spec agents start per-chunk work

**Tier 3 — Improves quality but not strictly blocking:**
8. Builder's guide ingestion (Layer D2) — most valuable for area reset, NPC config, loot specs
9. Cross-layer entity linking — makes search more effective but agents can work around gaps
10. Grounding validation — improves trust signals but agents can use "trust but verify" approach