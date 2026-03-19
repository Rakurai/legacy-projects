The final MCP server should be treated as a **compiled legacy knowledge base**, not just a code browser. Its job is to let three agent roles work from the same factual substrate:

* **planning agent**: system inventory, dependencies, integration surfaces, complexity
* **spec agent**: exact behavior, constants, output text, contracts, edge cases
* **auditor agent**: evidence-backed verification that a spec is complete, consistent, and faithful

That matches the server’s intended role as a **read-only, deterministic reference layer** rather than a migration planner or runtime inference system.  

## 1. What the final MCP server should contain

Forget V1/V2/V3/V4 as rollout stages. The completed server should expose **six information surfaces**.

### A. Code and graph surface

This is the current foundation:

* entities
* source code
* call/dependency graphs
* state touches
* behavioral slices
* file summaries
* capability maps

That remains necessary, but it is no longer sufficient by itself. The current docs already frame it as strong for code-level research but incomplete for user-visible and data-contract questions.  

### B. System narrative surface

Agents need subsystem overviews, dependency narratives, mechanism sections, and edge-case notes, all grounded and confidence-labeled. The roadmap and requirements both already define this conceptual layer and subsystem navigation need.  

### C. User-facing surface

This must include:

* help topics
* command syntax docs
* player-visible descriptions
* administrator/builder-facing help when relevant

This is not optional. The spec agent needs user-visible behavior, and the roadmap explicitly says this is the layer that answers “what does the user expect to happen?”  

### D. Data/configuration surface

This should not be limited to builder-guide prose. It must also expose **authoritative structured extracts from the legacy tables and content data**, including:

* skills/spells table rows
* races/classes
* attack types
* item/weapon/flag definitions
* area reset instructions
* prototype data
* room/object/mobile config semantics

This is one of the biggest gaps identified in Round 1: agents currently have to hunt through `const.cc`/`tables.cc` manually for values that are already tabular.  

### E. Runtime/ordering surface

The server must expose:

* tick phase ordering
* pulse multiples / timing constants
* runtime entry points
* which systems run in which phase
* ordering-sensitive interactions

This is another explicit current gap: behavior slices show local calls, but not the authoritative runtime ordering that shapes fidelity.  

### F. Verification/evidence surface

This is the part the earlier roadmap was missing most clearly. For the auditor agent especially, the server should provide:

* canonical message templates
* exact formulas/constants
* representative traces/scenarios
* provenance for all derived claims
* coverage/completeness signals

The consensus now requires specs to include exact formulas, timing constants, message templates, state reads/writes, ordering rules, and test cases. The MCP server should surface the legacy evidence that makes those claims verifiable. 

---

## 2. What tools the final MCP server needs

I would organize the final tool surface into **eight families**.

### 1. Entity and source tools

Keep the existing core:

* `resolve_entity`
* `get_entity`
* `get_source_code`
* `list_file_entities`
* `get_file_summary`
* `search`

These are already the base implementation layer. 

### 2. Behavior and dependency tools

Keep and extend:

* `get_behavior_slice`
* `get_state_touches`
* `get_callers`
* `get_callees`
* `get_dependencies`
* `get_related_entities`
* `get_hotspots`

But behavior slices should be enriched with **message literals, table dependencies, runtime roots, and ordering provenance** where known.

### 3. System tools

These are already well-motivated:

* `list_subsystems`
* `get_subsystem`
* `get_subsystem_context`
* `get_subsystem_dependencies`
* `search_subsystem_docs`
* `get_system_dependency_graph`
* `list_systems_by_layer`
* `get_integration_surface`
* `compare_systems`
* `find_system_by_concern`
* `estimate_complexity`

Planning agents need these directly; spec and auditor agents also need `get_integration_surface`. 

### 4. Composite feature-research tools

These should be first-class, not optional:

* `explore_entity`
* `explain_interface`

`explore_entity` is already unanimous from the prior discussions because it removes repeated multi-call setup. `explain_interface` is also now justified because the auditor and spec agents both need a compact contract view, even if it remains evidence-backed rather than interpretive.  

I would also add:

* `summarize_feature_surface(entity)` → entry points, user-visible outputs, tables consulted, state touched, adjacent systems
* `compare_entities(entities[])` → especially useful for spell clustering, affect variants, repeated command families

### 5. Structured data-table tools

These are mandatory in the final server.

Add tools like:

* `get_skill_entry(name_or_id)`
* `get_spell_entry(name_or_id)`
* `get_race_entry(name_or_id)`
* `get_class_entry(name_or_id)`
* `get_flag_definition(flag_set, symbol)`
* `get_attack_type(name_or_id)`
* `search_table_entries(query, table?, filters?)`
* `get_reset_instruction(reset_id or area/vnum/index)`
* `get_prototype(vnum, kind)` for mob/object/room prototypes
* `get_area_definition(area_id)`

This is the highest-value structural addition for spec work because the data is authoritative and already exists, but is currently buried. 

### 6. User-facing and builder-facing doc tools

Keep the proposed help/builder tool families, but make them richer:

* `search_help_docs`
* `get_help_topic`
* `list_related_help_topics`
* `search_builder_guide`
* `get_builder_guide_section`
* `list_related_builder_sections`

Also add:

* `get_command_syntax(command_name)`
* `get_related_player_contracts(entity_or_system)`

The main value is not just prose retrieval; it is linking legacy implementation to visible expectations and content constraints. 

### 7. Runtime and ordering tools

This family is missing and should exist explicitly.

Add:

* `get_runtime_phases()`
* `get_runtime_entry_points(phase?)`
* `get_phase_membership(entity_or_system)`
* `get_ordering_constraints(entity_or_system)`
* `explain_tick_path(entry_point)`
  Example: `game_loop_unix -> violence -> char_update -> object_update -> area_update`

This directly closes the timing/ordering gap.  

### 8. Verification and trace tools

This is the key addition for the auditor agent.

Add:

* `get_message_templates(entity_or_system)`
  Extract literal `act()`/`send_to_char()`/formatted output strings and categorize by audience/context.
* `get_numeric_constants(entity_or_system)`
  Return exact constants, macros, table fields, formulas, and provenance.
* `get_formula(entity_or_feature)`
  Structured formula extraction where possible.
* `get_edge_cases(entity_or_system)`
  Based on weak docs, branch patterns, guard conditions, special flags, and subsystem docs.
* `get_fidelity_trace(trace_id or concept)`
  Curated/derived behavioral scenarios and expected outputs.
* `search_fidelity_traces(query)`
* `get_coverage_report(feature_or_system)`
  What evidence exists: code, docs, help, builder, traces, tables, subsystem narrative.

This is the part that makes the server useful for **audit**, not just research. It also aligns with the consensus requirement that specs must be exact and testable. 

---

## 3. What prompts the final MCP server should provide

The current prompt idea is right, but it needs to expand to cover all three agents.

### Planning prompts

* `orient_to_system(system_id)`
* `map_dependencies(system_ids?)`
* `plan_research_surface(system_id)`
  returns a research checklist, not a migration plan

### Spec prompts

* `research_feature(feature_name)`
* `research_command(command_name)`
* `research_spell(spell_name)`
* `research_shared_interface(interface_name)`
* `research_runtime_behavior(system_or_entry_point)`

### Auditor prompts

These are new and necessary:

* `audit_spec_completeness(feature_or_system, spec_claims?)`
* `audit_contract_consistency(interface_or_system)`
* `audit_fidelity_surface(feature_or_system)`
  asks: do we have exact messages, constants, timing, ordering, edge cases, user-facing docs, config constraints?
* `collect_acceptance_evidence(feature_or_system)`

The server still should not “decide” if a spec passes. But it should provide canned workflows that help the auditor assemble the evidence quickly.

---

## 4. What must be precomputed vs curated vs extracted agentically

This is the core implementation question. I would split the final server build into four pipelines.

## A. Deterministic computed artifacts

These should be generated mechanically every build.

### Code graph and metadata

* entities
* call graph
* inheritance/includes
* fan-in/fan-out/bridge metrics
* runtime entry-point detection
* file/entity/source maps

### Table extraction

Parse authoritative legacy data into normalized structured stores:

* skill tables
* spell metadata
* race/class tables
* flags
* item/weapon/attack types
* resets
* prototype definitions
* constant/macros relevant to gameplay

This needs to be parser-driven, not hand-curated.

### Message extraction

Statically extract:

* `act()` format strings
* `send_to_char()` strings
* notable `printf`/formatter literals
* nearby guard/context metadata
* audience context where inferable

### Formula/constant extraction

Precompute:

* constant references
* macro expansions where useful
* table-field dependencies
* arithmetic-expression candidates for formulas

This does not need to be perfect, but it should make exact values queryable.

### Runtime ordering extraction

Mechanically derive:

* main loop phases
* functions called per phase
* pulse constants
* entry-point-to-phase mappings where possible

---

## B. Agentic extraction / offline analysis

Use offline LLM or analysis passes where the result is stored, reviewed, and served deterministically later.

### Good candidates

* entity briefs and docstrings
* subsystem narrative summaries
* integration surface drafts
* interface summaries
* spell/skill behavioral clustering
* edge-case summaries
* scenario/trace descriptions from code + docs
* mapping entities to subsystems, use-cases, and concerns

This is where you can do higher-order synthesis, but the outputs must be stored with provenance and confidence, not recomputed at query time. That is already consistent with the roadmap’s “pre-computed and deterministic” rule. 

---

## C. Human curation

This is the part I would not try to automate away.

### Must be curated by hand

* subsystem/component docs
* final subsystem boundaries
* entity↔subsystem links where ambiguity is high
* help-topic normalization and cross-linking
* builder-guide sectioning and cleanup
* trust labels on subsystem/help/builder content
* canonical runtime-phase descriptions
* curated fidelity traces for critical systems
* high-value spell family clustering review
* mapping from raw content docs to stable IDs

Also:

* **use-case layer curation** is important. CG.md is right that commands are not the right planning unit; you need use-cases bridging commands to chunks. That mapping should be curated, even if seeded automatically. 

---

## D. Hybrid: auto-extract, then review

Some artifacts should be machine-produced, then lightly curated.

Best examples:

* exact output templates
* table entries
* runtime-order summaries
* integration surfaces
* edge-case catalogs
* spell pattern clusters
* reset semantics extracts

That is the sweet spot: let tooling do the bulk extraction, then review high-value outputs rather than hand-authoring everything.

---

## 5. What the final server should know that it does not know today

There are four major gaps that should become explicit build targets.

### 1. Exact user-visible output

Not just help text. Actual inline message templates and their contexts. This gap was called out directly in Round 1. 

### 2. Exact data-level contracts

Not just builder prose. Structured values from the actual legacy tables. Again, this was identified as a top missing capability. 

### 3. Runtime ordering and timing

The server must expose what happens before what in the legacy loop. This is essential for fidelity and currently under-served.  

### 4. Verification artifacts

The server must help answer “do we have enough evidence to write or audit this spec?” not just “what code does this call?” The consensus process implicitly raised that bar by requiring exact formulas, timings, output strings, and tests. 

---

## 6. Recommended final shape

If I collapse this into one concrete recommendation:

The final MCP server should expose **three top-level work modes** backed by one unified knowledge store:

### Research mode

For spec agents:

* `explore_entity`
* `get_source_code`
* `get_behavior_slice`
* `explain_interface`
* `get_message_templates`
* `get_numeric_constants`
* `get_skill_entry` / `get_spell_entry`
* `get_subsystem_context`
* help/builder lookup

### Planning mode

For planning agents:

* `list_subsystems`
* `get_system_dependency_graph`
* `get_integration_surface`
* `compare_systems`
* `estimate_complexity`
* `get_runtime_phases`
* `find_system_by_concern`

### Audit mode

For auditor agents:

* `get_coverage_report`
* `get_fidelity_trace`
* `get_message_templates`
* `get_formula`
* `get_edge_cases`
* `audit_fidelity_surface` prompt
* `audit_contract_consistency` prompt

That gives each agent a clean entry surface without turning the server itself into a planner or reviewer.

---

## 7. What I would build first in the “complete server” implementation plan

Not rollout phases—just the highest-value missing artifacts:

1. **Structured legacy data extraction**

   * skills/spells/tables/flags/resets/prototypes

2. **Output template extraction**

   * `act()` strings and related player-visible messages

3. **Runtime ordering model**

   * phase graph and timing metadata

4. **Composite tools**

   * `explore_entity`, `explain_interface`, `get_integration_surface`

5. **Help + builder ingestion**

   * normalized docs with IDs and cross-links

6. **Verification layer**

   * traces, coverage reports, formula/constant extraction

That sequence closes the gaps most likely to block spec and audit quality.

The concise version: **the final MCP server should be a curated, queryable evidence base over code, systems, runtime, user-visible behavior, data tables, and verification artifacts.** Not just “docs plus graph,” and not just “search over markdown.”
