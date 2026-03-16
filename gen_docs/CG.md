# Capability Graph Extraction in the Migration Pipeline

## 1. Purpose

This document places capability-graph extraction in the larger Legacy migration process.

The capability graph is **not** the migration plan by itself, and it is **not** the target architecture. It is an intermediate analysis artifact whose job is to convert raw code-derived evidence into a more actionable understanding of what must be implemented, in what combinations, and with what likely dependencies.

The long-term goal is to produce a prioritized set of implementation **chunks**. Each chunk should be small enough to analyze thoroughly, large enough to be meaningful, and structured enough to pass through a repeatable pipeline:

1. derive evidence from the legacy codebase
2. interpret that evidence into user-visible behavior and technical contracts
3. define implementation chunks and their dependencies
4. write chunk-level specification documents
5. implement the chunk in the target system
6. validate user-visible fidelity and architectural fit

This document defines how capability-graph extraction supports that pipeline, what views it should produce, and how the artifact should evolve from the current prototype.

---

## 2. Why This Exists

The legacy codebase is too large to migrate effectively using any single naive ordering strategy.

* **Subsystem-first migration** is too coarse. Legacy subsystems are heavily interdependent, and subsystem boundaries do not cleanly determine reimplementation order.
* **Command-first migration** is too granular. There are too many commands, and many commands share the same underlying machinery.
* **Pure intuition-based planning** does not scale. Important dependencies are often non-obvious and buried in the code.

The existing capability-graph prototype already improves on all three by using the static call graph to derive functional groupings, dependencies, and command enablement ordering. It takes as input the current entity database, dependency graph, and generated documentation artifacts, and already produces a command-to-capability mapping, a derived capability dependency graph, implementation waves, and an uncategorized residual for iterative refinement. That foundation is worth preserving. It is built on a real artifact stack rather than informal judgment alone.

What needs to change is not the existence of the graph, but the meaning assigned to it.

The current prototype is best understood as a **first-pass evidence graph**. It captures static, direct call relationships between command handlers and their callees and uses those relationships to infer capability ordering. The prototype explicitly does **not** capture runtime behavior, data dependencies, Evennia-side replacement mappings, or quality-of-experience fidelity, and it already warns against overinterpreting the result.

The migration process therefore needs a second stage that converts code-derived evidence into a more semantically grounded planning model.

---

## 3. Position in the Overall Migration Path

Capability-graph extraction should sit in the migration pipeline as follows:

```text
Legacy code artifacts
  -> evidence extraction
  -> evidence graph
  -> semantic interpretation
  -> implementation chunk model
  -> chunk specification set
  -> coding-agent implementation
  -> validation and refinement
```

More concretely:

```text
Doxygen / graph / doc artifacts
  -> command and runtime entry-point extraction
  -> code-derived evidence graph
  -> capability / policy / projection / infrastructure interpretation
  -> prioritized implementation chunks
  -> per-chunk specs and contracts
  -> Evennia-aligned implementation
  -> parity validation against legacy behavior
```

The capability graph therefore serves two roles:

1. **early evidence reduction** — shrinking thousands of functions and tens of thousands of relationships into a manageable set of candidate migration units
2. **dependency-informed planning input** — giving later stages a principled starting point for chunk definition, sequencing, and spec scoping

It should not be treated as the final answer to architecture, implementation order, or spec contents.

---

## 4. Guiding Principles

### 4.1 Evidence first, interpretation second

The process should be deliberately multi-stage.

The first stage should preserve as much evidence as possible with minimal semantic overcommitment. The second stage should interpret that evidence into migration-relevant concepts.

This separation matters because static calls are evidence, not truth. A function calling another function is a useful signal, but not the same thing as a stable architectural dependency or a complete user-story requirement.

### 4.2 User-visible behavior is the north star

The migration target is not a line-by-line port of C++ internals. The target is user-visible behavioral fidelity within a target architecture that also aligns with Evennia conventions.

That means the planning model must stay connected to:

* player/admin/builder intents
* legacy command behavior and presentation
* target-system architectural expectations
* chunk-level contracts that can be implemented and tested

### 4.3 Chunks are the delivery unit

The end product of analysis is not merely a better graph. It is a queue of implementation chunks that can be handed to the coding agent.

A good chunk should:

* represent a meaningful unit of user-visible or architecturally necessary behavior
* have explicit dependencies
* have bounded scope
* be specifiable independently
* fit coherently into the target design
* be testable in isolation and in composition

### 4.4 Planning must distinguish evidence, semantics, and readiness

The pipeline should avoid collapsing these into a single concept.

* **Evidence**: what the legacy code appears to do and depend on
* **Semantics**: what user intent or domain responsibility that evidence implies
* **Readiness**: how complete a target implementation must be before the chunk is truly usable

This distinction prevents the common failure mode where a graph says a command is “enabled” even though it still lacks correct messaging, persistence semantics, or runtime integration.

---

## 5. Inputs Already Available

The current artifact stack is already sufficient to support a more mature process.

### 5.1 Entity database

`code_graph.json` provides a flat entity database of Doxygen-parsed entities with stable identifiers, kinds, definitions, argument strings, source locations, and reference metadata. It is the authoritative source for per-entity metadata and for joining across artifacts.

### 5.2 Dependency graph

`code_graph.gml` provides a typed multigraph over entities and locations, with relationship types including `CALLS`, `USES`, `INHERITS`, `INCLUDES`, `CONTAINED_BY`, and `REPRESENTED_BY`. The current capability-graph prototype only uses `CALLS`, but the larger graph can support richer interpretation later.

### 5.3 Generated documentation

The document database provides generated summaries and usage-oriented descriptions that can help classify functions when name matching is insufficient. The documentation pipeline already establishes a joinable layer of semantic hints over the raw code graph.

### 5.4 Evidence-graph pipeline (v2)

The evidence-graph pipeline (`build_capability_graph.py`) extracts all three entry-point families (do_\*, spell_\*, spec_\*), maps each to transitive callees via BFS, classifies callees against `capability_defs.json` locked lists (with embedding-similarity fallback for unlocked functions), derives typed cross-capability dependency edges, and computes implementation waves.

The output is `capability_graph.json`. It represents **View A** (evidence graph) as defined in §6.1, with the semantic typing from **View B** (§6.2) already layered in through the group `type` field and typed dependency edges.

---

## 6. Target Output Model

The process should eventually produce multiple related views rather than a single monolithic graph.

### 6.1 View A: evidence graph

This is the closest view to the current prototype.

Purpose:

* preserve code-derived evidence with minimal interpretation
* support auditing and refinement
* justify later planning decisions

Contents:

* command entry points
* non-command runtime entry points where known
* direct and possibly bounded transitive code relationships
* candidate function groupings
* supporting doc evidence
* confidence metadata
* unresolved / residual functions

This view answers:

* what does the code appear to call or use?
* what candidate families of behavior are visible?
* where are the blind spots and uncertainties?

### 6.2 View B: semantic dependency model

This is the main successor to the current capability graph.

Purpose:

* reinterpret evidence into migration-relevant concepts
* separate true domain behavior from policy, presentation, and infrastructure
* support chunk formation and sequencing

Contents:

* use cases / intents
* domain capabilities
* policy/rule services
* projection/presentation services
* infrastructure services
* runtime mechanisms
* typed dependencies between these
* confidence and evidence references

This view answers:

* what meaningful responsibilities exist?
* which of them are reusable?
* which are blockers versus support concerns?
* what kinds of dependency are present?

### 6.3 View C: implementation chunk plan

This is the planning artifact the migration program ultimately needs.

Purpose:

* define the units to analyze, specify, and implement
* provide prioritization and dependency information
* support coding-agent work packaging

Contents:

* chunk identifiers and descriptions
* chunk category and context
* dependencies
* readiness level expectations
* user-visible outcomes
* target architecture notes
* related commands/use cases
* legacy evidence links
* required spec documents

This view answers:

* what do we implement next?
* what must be understood before implementation?
* what must already exist?
* what spec work is required?

### 6.4 View D: traceability view

Purpose:

* connect code evidence, understanding, specs, implementation, and validation
* preserve auditability across the migration

Contents:

* legacy evidence links
* semantic nodes
* chunk nodes
* spec documents
* implementation modules
* validation cases

This view answers:

* why does this chunk exist?
* what legacy behavior justifies it?
* what specs and tests cover it?
* where is it implemented in the target system?

---

## 7. From Capabilities to Chunks

A key design point is that **capabilities are not automatically chunks**.

Some capabilities will map cleanly to a single implementation chunk. Others will be split, merged, or absorbed into a broader chunk depending on migration needs.

### 7.1 Why capabilities are not enough by themselves

The current prototype treats capabilities as the main units of dependency. That is useful, but not sufficient for implementation planning because a capability may be:

* too broad to spec safely
* too low-level to matter as a standalone deliverable
* cross-cutting rather than chunk-worthy
* mostly policy or projection rather than domain behavior
* tightly coupled to another capability and better migrated together

### 7.2 Chunk formation rules

Chunks should be formed using the semantic model, not raw graph topology alone.

A chunk may be:

* one capability
* several tightly related capabilities
* one capability plus its required policy/projection layer
* a user-facing use case composed of multiple lower-level capabilities
* a runtime-support chunk needed by many later chunks

### 7.3 Chunk quality criteria

A chunk should satisfy most of these:

* user-visible or architecturally necessary
* bounded enough for concentrated analysis
* reusable beyond one command where possible
* coherent in state responsibilities
* describable through stable contracts
* suitable for implementation under Evennia conventions
* testable for both semantics and presentation

### 7.4 Implementation modes

Not all chunks represent the same kind of work. The chunk registry classifies each chunk into one of five implementation modes:

* **native** — real target-side game logic that must be built. Evennia does not provide this; it is the actual migration work. Examples: combat, movement, affects, objects, state_rules.
* **adaptation** — a thin compatibility or integration layer over Evennia/Python behavior. The underlying capability exists in the target but needs a game-specific policy or presentation layer. Examples: output (over Evennia msg), entity_lookup (over DefaultObject.search), display (over return_appearance hooks).
* **reference** — preserves understanding and supports edge-case mapping, but is not implemented as a target-side system. The legacy behavior is replaced by Python stdlib or Evennia built-ins. Examples: flags (Evennia tags/locks), string_ops (Python str), memory (Python GC).
* **replacement** — replaced by an existing Evennia contrib or standard tool. Examples: text_editing (EvEditor), imaging (web-based map or deferred).
* **substrate** — Evennia already provides this infrastructure. The game-specific integration is an attachment to other chunks, not a standalone deliverable. Example: runtime (Evennia's game loop, tickers, Scripts).

This classification prevents reference and substrate concerns from consuming implementation energy that should go to native and adaptation chunks.

### 7.5 Umbrella chunks

Some chunks are internally coherent at the planning level but will likely need multiple spec dossiers during implementation. These are marked as **umbrella chunks** in the registry. They are not split during chunk formation — splitting happens during spec writing when the dossier reveals clearly separate implementation surfaces.

Current umbrella chunks: world_structure, affects, persistence, objects.

---

## 8. Recommended Semantic Model

The current prototype uses a single concept of “capability.” The next revision should use a typed model.

### 8.1 Node types

At minimum, the semantic model should distinguish:

* **command** — legacy command entry points such as `do_*`
* **runtime_entry** — non-command roots such as update/tick/script entry points
* **use_case** — player/admin/builder intent such as “attack target” or “inspect room”
* **domain_capability** — reusable gameplay/domain behavior
* **policy** — validation, permissions, state checks, visibility rules
* **projection** — rendering, messaging, room presentation, formatting visible output
* **infrastructure** — persistence, database, technical services
* **runtime_mechanism** — tick-driven or script-driven behavior, dynamic dispatch, event loops
* **utility** — low-level helper code that should not dominate migration ordering
* **residual** — unresolved functions pending classification

### 8.2 Edge types

Dependencies should also be typed. Suggested edge kinds:

* `invokes`
* `requires_core`
* `requires_policy`
* `requires_projection`
* `requires_infrastructure`
* `uses_utility`
* `emits_event`
* `consumes_event`
* `reads_state_from`
* `writes_state_for`
* `updated_by_runtime`
* `implemented_by`
* `evidenced_by`

Not all of these need to exist immediately, but the model should leave room for them.

### 8.3 Why typed nodes and edges matter

This prevents accidental peer treatment of concerns that are not architecturally equivalent.

For example:

* `combat_mechanics` and `movement` are domain capabilities
* `character_state_check` is likely a policy family
* `message_output` and `color_formatting` are projection services
* `memory_pool` is infrastructure or utility

Those should not contribute equally to chunk sequencing.

---

## 9. Use Cases as the Bridge Between Commands and Chunks

The migration is driven by user-visible behavior, but command handlers are not ideal planning units.

A legacy command often mixes:

* argument parsing
* state validation
* target lookup
* domain logic invocation
* output rendering
* side effects and persistence hooks

The model should therefore introduce a **use-case layer**.

Example pattern:

```text
command -> use_case -> semantic requirements -> implementation chunk(s)
```

Examples:

* `do_kill` -> initiate hostile action against a target
* `do_cast` -> invoke spell-like action on a target
* `do_get` -> transfer object into inventory
* `do_look` -> inspect local context or target

This layer prevents orchestration code from masquerading as a reusable chunk and better aligns the analysis with eventual spec writing.

---

## 10. Readiness Levels

The current prototype uses a binary notion of command enablement. That is useful as a first approximation, but not strong enough for chunk planning.

The next-stage model should distinguish at least these levels:

### 10.1 Structural readiness

The core semantic contracts exist. The main path can be executed in principle.

### 10.2 Interactive readiness

The feature can be exercised through the command interface with basic parsing, validation, and output.

### 10.3 Behavioral readiness

The feature broadly matches legacy behavior, including important rule interactions and side effects.

### 10.4 System readiness

Persistence, runtime integration, shared-state interactions, and lifecycle concerns are implemented.

### 10.5 UX-faithful readiness

Presentation, messaging, edge-case behavior, and overall user experience match the legacy system closely enough to be considered migration-faithful.

This lets the migration plan be honest about what it means for a chunk or command to be “done.”

---

## 11. Requirements for Each Implementation Chunk

Each implementation chunk should eventually have a chunk dossier or equivalent structured record containing:

### 11.1 Identity and scope

* chunk ID
* name
* context/domain
* short purpose statement
* included semantic nodes
* excluded responsibilities

### 11.2 Legacy evidence

* related commands and use cases
* supporting capability/policy/projection nodes
* source entity references
* relevant functions/files
* confidence notes and known blind spots

### 11.3 Behavioral contract

* user-visible behavior
* inputs and preconditions
* outputs and side effects
* state reads and writes
* invariants/rules
* interactions with adjacent chunks

### 11.4 Target-system design constraints

* intended Evennia-side placement
* relationships to existing target architecture
* reusable APIs or service contracts
* anti-patterns to avoid
* temporary stubs allowed or disallowed

### 11.5 Spec requirements

* required spec documents
* open questions
* comparison points against legacy behavior
* acceptance tests / validation scenarios

### 11.6 Implementation planning

* predecessor chunks
* blocking dependencies
* suggested implementation order within the chunk
* follow-on chunks unlocked by completion

This is the handoff unit for the coding agent.

---

## 12. Practical Evolution of the Current Prototype

The current prototype should be evolved incrementally rather than rewritten all at once.

### 12.1 Phase 1: stabilize the current evidence graph — ✅ DONE

The v2 pipeline (`build_capability_graph.py`) now produces a complete View A (§6.1). Coverage is total: all entry-point families included, transitive callees fully classified, zero uncategorized residual. The export is structured for downstream consumption with provenance metadata and per-member depth tracking.

### 12.2 Phase 2: introduce semantic typing — ✅ DONE

The 30-group taxonomy types every group as domain, policy, projection, infrastructure, or utility. Dependency edges are typed via a (src_type, tgt_type) → edge_kind matrix. Wave computation excludes utility edges to prevent helpers from dominating ordering. This means the evidence graph already carries the **semantic typing** anticipated by View B (§6.2) at the group level.

### 12.3 Phase 3: chunk formation — ✅ DONE

The evidence graph (View A) and semantic typing (View B at group level) are now stable. Phase 3 produced View C (§6.3): the implementation chunk plan.

The primary unit of chunk formation is the **capability group**, not the entry point. The 30 capability groups and their ~200 typed dependency edges form a tractable graph that can be reasoned about directly. Entry points are not implementation units, but they remain important validation inputs because they reveal which combinations of capabilities deliver user-visible behavior.

Use-case identification (§9) is deferred to Phase 5, where it informs spec writing and behavioral contracts. Chunk formation does not require it.

#### Chunk formation logic

Chunks are formed by bundling capability groups according to dependency coupling, type alignment, and implementation pragmatics:

1. **Service chunks from fan-in.** Groups with high fan-in are universal services: nearly every domain chunk will depend on them, so they must be implemented first as foundational infrastructure. The evidence graph already provides fan-in data. Candidates include state_rules, output, string_ops, flags, attributes, world_structure, admin, numerics.

2. **Domain chunks.** Each domain capability (combat, magic, movement, objects, affects, etc.) forms a natural candidate chunk. Where a domain group has a tight dependency on a specific policy or projection group that serves primarily that domain, bundle them together.

3. **Merge or split by size and coupling.** Small groups that exist only to serve one domain group are absorbed into it. Oversized groups that serve multiple unrelated consumers may warrant splitting, but the default is to keep them whole.

4. **Leaf capabilities.** Groups with zero fan-in (economy, imaging, notes, npc_behavior, pvp, quests, runtime, social, text_editing) depend on services and other domain groups but nothing depends on them. They can be scheduled freely once their dependencies are satisfied.

#### Chunk sequencing

Ordering follows from the dependency DAG:

- **Foundation tier**: universal-fan-in service chunks (implement first)
- **Shared tier**: moderate-fan-in capabilities used by multiple domain chunks
- **Domain tier**: domain chunks in wave order, subject to dependency constraints
- **Leaf tier**: zero-fan-in domain chunks, schedulable in any order once dependencies exist

Waves from the evidence graph provide initial ordering within each tier.

#### Entry points as consequences

Each chunk enables a set of entry points. When a chunk and all its transitive dependencies are implemented, the entry points that depend exclusively on those capabilities become available. This is tracked as a chunk annotation — a consequence of chunk completion, not a formation input.

#### Division of labor

Mechanics should propose; humans should ratify semantics.

**Automated** — fan-in tier assignment; default bundling via dependency shape; chunk-to-chunk dependency edges; entry-point enablement annotation; sequencing from wave structure and topological order; warnings for over-large chunks, cycles, and orphans.

**Curated** — final chunk boundaries; whether a capability is standalone or bundled; target-side packaging assumptions; readiness targets and sequencing exceptions.

#### Concrete steps

Phase 3 is structured as two passes.

**Pass 1 — automated draft:**

1. Read the capability dependency DAG from `capability_graph.json`.
2. Compute fan-in tiers (universal, shared, leaf) for each capability group.
3. Propose default chunk boundaries: one chunk per domain group (bundled with tightly-coupled policy/projection groups where appropriate); one service chunk per high-fan-in group.
4. Compute chunk-to-chunk dependency edges from the underlying capability edges.
5. Sequence chunks into implementation tiers using topological ordering of the chunk DAG.
6. Annotate each chunk with the entry points it enables.
7. Emit warnings for over-large chunks, dependency cycles, and orphan capabilities.

Output artifact: `candidate_chunks.json`

**Pass 2 — curated review:**

8. Accept, reject, split, or merge chunk candidates.
9. Assign implementation mode to each chunk (§7.4): native, adaptation, reference, replacement, or substrate.
10. Assign planning phase: B (foundational semantics), C (vertical slices), or D (heavier systemic features).
11. Mark umbrella chunks (§7.5) that will need multiple spec dossiers.
12. Annotate chunk rationale and readiness targets.
13. Freeze `chunk_registry.json`.

Input artifacts: `candidate_chunks.json`, `capability_graph.json`, `capability_defs.json`
Output artifact: `chunk_registry.json`

#### Results

The chunk registry contains 30 chunks classified as:

* **19 native** — the real implementation work (world_structure, state_rules, attributes, visibility_rules, skills_progression, movement, affects, objects, combat, quests, clans, pvp, social, notes, economy, npc_behavior, magic, numerics, persistence)
* **5 adaptation** — thin layers over Evennia surfaces (entity_lookup, output, display, arg_parsing, admin)
* **3 reference** — legacy behavior mapping only (flags, string_ops, memory)
* **2 replacement** — handled by Evennia contribs/tools (text_editing, imaging)
* **1 substrate** — Evennia-provided infrastructure (runtime)

Planning phases reflect target-side leverage rather than raw graph wave order:

* **Phase B** (foundational semantics): world_structure, state_rules, attributes, visibility_rules, output, entity_lookup, skills_progression, admin
* **Phase C** (first vertical slices): movement + display (inspect/navigate), objects (manipulate), social + notes (communication)
* **Phase D** (heavier systemic features): affects, combat, magic, quests, clans, pvp, npc_behavior, economy, persistence

Four chunks are marked as umbrellas: world_structure, affects, persistence, objects.

### 12.4 Phase 4: target-surface mapping and dependency refinement — NEXT

The chunk registry is now stable. The remaining phases require direct knowledge of the target framework (Evennia conventions, typeclass strategy, handler patterns, contrib availability). They are designed to be executed in the target implementation repository by an agent with access to both the chunk registry and the Evennia codebase.

#### Phase 4a: target substrate decisions

Before any chunk implementation, the target repository must commit to architectural surfaces:

* room/exit/object/character typeclass strategy
* handler strategy (traits, buffs, skills, clans, etc.)
* search/lookup policy approach
* messaging/display/appearance approach
* persistence strategy (AttributeHandler, SaverDict, etc.)
* Scripts/ticker/runtime strategy

Without these decisions, early chunks risk being implemented in incompatible shapes. This is architectural commitment, not chunk implementation.

#### Phase 4b: dependency refinement

The chunk registry's dependency edges inherit from capability-level typed edges. Some will be wrong or incomplete at the chunk level because call-count-based evidence does not capture all dependency kinds.

The current typed edges (requires_core, requires_policy, etc.) are derived from static call relationships. They miss:

* **State dependencies.** A chunk may read or write shared state that another chunk also touches, without any direct call.
* **Runtime coupling.** Tick-driven systems create implicit dependencies invisible in the call graph.
* **Ordering constraints from user expectations.** A player expects `look` to reflect `get` immediately, but there may be no call edge.
* **Evennia-side architectural coupling.** Two chunks may share a typeclass, handler, or database table in the target system.

Refinement steps:

1. Audit chunk-to-chunk edges: tag as `blocking`, `supportive`, or `informational`.
2. Add state-based dependencies from entity field usage analysis.
3. Add runtime dependencies from tick/event entry points.
4. Add target-side coupling notes where chunks share Evennia surfaces.
5. Re-sequence if the refined edges change the ordering.

Input artifact: `chunk_registry.json`
Output artifact: `chunk_registry.json` (refined edges)

### 12.5 Phase 5: chunk dossiers and spec generation

Each chunk becomes a handoff unit for the coding agent. This phase generates the structured records that make that handoff repeatable.

#### Chunk dossiers

For each chunk in the registry, generate a dossier following the §11 template:

* **Identity and scope** (§11.1) — from the chunk registry directly.
* **Legacy evidence** (§11.2) — from the evidence graph: related entry points, member functions, source files, capability groups, confidence notes.
* **Behavioral contract** (§11.3) — derived from generated documentation and command-level analysis. This is the section that requires the most new work: it must describe what the chunk *does* in user-visible terms, not just what functions it contains.
* **Target-system design constraints** (§11.4) — curated per chunk, informed by Evennia conventions and prior target-architecture decisions.
* **Spec requirements** (§11.5) — open questions, acceptance scenarios, comparison points against legacy behavior.
* **Implementation planning** (§11.6) — predecessor chunks, blocking dependencies, follow-on chunks.

#### Spec templates

Define a standard spec template that the coding agent consumes. The template should be structured enough to be machine-readable but flexible enough to accommodate chunks of varying complexity.

#### Readiness criteria

For each chunk, define explicit criteria for each readiness level (§10). This prevents the common failure mode where a chunk is marked "done" at structural readiness while still lacking interactive, behavioral, or system readiness.

#### Traceability convention (View D)

Establish a lightweight linking convention so that:

* every chunk points back to its legacy evidence
* every spec points to its chunk
* every implementation module points to its spec
* every validation case points to its behavioral contract

Stable identifiers and cross-reference fields in the JSON artifacts are sufficient.

#### Implementation progression

Specs should be written in planning-phase order, not strict graph-wave order:

1. **Phase B specs first** — foundational semantics: world_structure, state_rules, attributes, visibility_rules, output (adapter), entity_lookup (adapter), skills_progression, admin (adapter).
2. **Phase C specs next** — first vertical playable slices:
   * Slice 1 (inspect/navigate): movement + display + supporting foundations
   * Slice 2 (manipulate objects): objects + entity_lookup + supporting policy
   * Slice 3 (communication): social + notes
3. **Phase D specs last** — heavier systemic features: affects, combat, magic, quests, clans, pvp, npc_behavior, economy, persistence.

The first playable milestone is a thin vertical slice: room exists, can move, can look, can resolve targets, can pick up/drop basic objects, messaging roughly works.

Input artifact: `chunk_registry.json` (refined)
Output artifacts: `chunk_dossiers/` (per-chunk structured records), spec template, traceability index

## 13. How This Supports Evennia-Aligned Migration

The capability graph should remain legacy-grounded, but it must eventually support target-system decisions.

This means the later stages of the model should explicitly include:

* likely target modules/services in the new codebase
* Evennia-side conventions and constraints
* reusable systems that should replace multiple legacy implementations
* places where strict legacy structure should **not** be preserved because it conflicts with good target design

This is an important boundary:

* the evidence graph should remain honest to the legacy code
* the semantic and chunk layers should be free to reorganize behavior into better target-side abstractions

In other words, legacy evidence should constrain correctness, not force architectural mimicry.

---

## 14. Validation Expectations

A chunk is not complete merely because a graph says its dependencies are present.

Validation should operate at several levels:

### 14.1 Evidence validation

Does the chunk still accurately reflect the legacy evidence?

### 14.2 Semantic validation

Does the chunk definition correctly capture user-visible intent and technical responsibility?

### 14.3 Architectural validation

Does the chunk align with the target system and adjacent chunks without introducing poor boundaries?

### 14.4 Behavioral validation

Does the implementation match legacy semantics where required?

### 14.5 Presentation validation

Does the user experience match legacy expectations closely enough, including messaging and output style?

This reinforces the point that graph extraction is an input to implementation quality, not a substitute for it.

---

## 15. Recommended Near-Term Deliverables

The next rework of the prototype should aim to produce the following artifacts.

### 15.1 Revised evidence export — DONE

Produced by `build_capability_graph.py` as `capability_graph.json`. Contains all entry-point families (do_\*, spell_\*, spec_\*), transitive callees, locked-list classification with embedding fallback, typed dependency edges, wave ordering, and provenance metadata.

### 15.2 Semantic interpretation layer — DONE

The 30-group taxonomy in `capability_defs.json` types every group as domain, policy, projection, infrastructure, or utility. Dependency edges are typed via a (src_type, tgt_type) → edge_kind matrix. This layer is already embedded in the evidence graph rather than maintained as a separate artifact.

### 15.3 Initial chunk registry — DONE

Produced by `build_chunks.py` (automated draft) and `build_registry.py` (curated decisions) as `chunk_registry.json`. Contains 30 chunks with implementation mode classification, planning phase assignment, dependency edges, entry-point enablement annotations, umbrella markers, and reviewer decision notes.

### 15.4 Chunk spec template

A standard template for the analysis/spec stage that the coding agent can consume.

### 15.5 Traceability convention

A simple, stable way to connect:

* legacy evidence
* semantic nodes
* chunks
* specs
* target implementation modules
* validation cases

---

## 16. Decision Summary

The capability graph serves as a multi-view analysis pipeline:

1. **evidence graph** — code-derived structure and classification — ✅ `capability_graph.json`
2. **semantic model** — interpreted migration-relevant responsibilities and dependencies — ✅ `capability_defs.json` (30 typed groups)
3. **implementation chunk plan** — prioritized work packages classified by implementation mode — ✅ `chunk_registry.json`
4. **traceability layer** — links between evidence, understanding, specs, code, and validation — deferred to Phase 5

Views A, B, and C are complete. The pipeline's strongest feature is intact: planning decisions are grounded in auditable evidence from the legacy codebase rather than intuition alone.

The remaining work (Phases 4–5: target-surface mapping, dependency refinement, dossier/spec generation) requires direct access to the target framework and belongs in the implementation repository. The chunk registry is the handoff artifact.

---

## 17. Appendix: Operational Definitions

### Capability

A reusable semantic responsibility inferred from legacy evidence. In the current prototype this is a bucket of functions; in the mature model it should become a typed node in the semantic dependency model.

### Use case

A user-visible intent that may be served by one or more commands and implemented by multiple semantic responsibilities.

### Implementation chunk

A planned migration work package: the unit that is analyzed, specified, implemented, and validated.

### Evidence graph

The minimally interpreted graph of legacy-derived relationships and classifications.

### Semantic model

The interpreted model that separates domain behavior from policy, presentation, infrastructure, runtime, and utility concerns.

### Readiness

The degree to which a chunk or command is truly usable, ranging from structural existence to UX-faithful parity.
