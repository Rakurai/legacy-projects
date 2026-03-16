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

### 12.3 Phase 3: add use-case and chunk modeling — NEXT

The evidence graph (View A) and semantic typing (View B at group level) are now stable. The next step is to bridge from what the code *does* to what should be *implemented* — that is, to produce View C (§6.3): the implementation chunk plan.

This requires two new layers that do not yet exist:

**Use-case layer.** §9 defines use cases as the bridge between commands and chunks. The evidence graph currently connects entry points directly to capabilities. A use-case layer would cluster entry points by shared intent (e.g. "initiate hostile action," "inspect local context") so that chunk formation can reason about user-visible behavior rather than individual command handlers.

**Chunk formation.** §7.2 defines formation rules. Chunks are not 1:1 with capabilities — they may merge tightly-coupled groups, split oversized ones, or bundle a domain group with its required policy/projection layer. The formation step needs the typed dependency edges and the use-case clusters as inputs.

#### Division of labor

Mechanics should propose; humans should ratify semantics.

**Automated** — service-chunk identification from fan-in and dependency shape; entry-point clustering from capability profiles; suggested merges/splits from similarity and dependency overlap; outlier and suspicious-cluster warnings.

**Curated** — use-case names; final chunk boundaries; whether a capability is standalone or bundled; target-side packaging assumptions; readiness targets and sequencing exceptions.

#### Similarity model

Raw capability-set Jaccard is dominated by ubiquitous support groups (state_rules, output, entity_lookup appear almost everywhere). Domain-only Jaccard corrects for that but discards meaningful policy/projection distinctions.

Use a typed weighted similarity with inverse-frequency downweighting:

1. Build per-entry-point capability vectors partitioned by type (domain, policy, projection, infrastructure, utility).
2. Apply IDF-style weighting: capabilities that appear in nearly every entry point contribute less.
3. Compute similarity with domain-heavy weights (e.g. domain 0.60, policy 0.20, projection 0.10, infrastructure 0.10).
4. Cluster primarily on domain-heavy similarity; refine within each family using policy/projection cues and entry-point description embeddings.

#### Drafting window

Start with the earliest entry points that expose meaningful domain behavior, not merely the lowest wave numbers. Use waves 0–6 as the initial search window, but filter out preference-only and configuration-only commands. The cohort should include at least movement, room inspection, object manipulation, combat, magic, skills/progression, notes/social, and entity lookup.

#### Concrete steps

Phase 3 is structured as two passes.

**Pass 1 — automated draft:**

1. Compute typed weighted similarity across all entry points.
2. Cluster entry points into candidate use-case families.
3. Identify high-fan-in capability groups as service-chunk candidates.
4. Emit suggested chunk candidates with supporting evidence, merge/split warnings, and cluster explanations.

Output artifacts: `candidate_use_cases.json`, `candidate_chunks.json`

**Pass 2 — curated review:**

5. Assign human-readable use-case names.
6. Accept, reject, split, or merge chunk candidates.
7. Annotate chunk rationale and readiness targets.
8. Freeze first-draft `chunk_registry.json`.

Input artifacts: `capability_graph.json`, `capability_defs.json`
Output artifact: `chunk_registry.json`

### 12.4 Phase 4: refine dependency semantics

Once the chunk registry exists, its dependency edges inherit from the capability-level typed edges. Some of those edges will be wrong or incomplete at the chunk level because call-count-based evidence does not capture all dependency kinds.

This phase refines chunk-to-chunk dependencies using the chunk registry as the unit of analysis.

#### What the evidence graph cannot tell us

The current typed edges (requires_core, requires_policy, etc.) are derived from static call relationships. They miss:

* **State dependencies.** A chunk may read or write shared state (e.g. character attributes, room contents) that another chunk also touches, without any direct function call between them.
* **Runtime coupling.** Tick-driven systems (combat rounds, affect decay, weather) create implicit dependencies that are invisible in the call graph.
* **Ordering constraints from user expectations.** A player expects `look` to reflect the results of `get` immediately, but there may be no call edge between them.
* **Evennia-side architectural coupling.** Two chunks may need to share a typeclass, handler, or database table in the target system even though they are independent in the legacy code.

#### Concrete steps

1. **Audit chunk-to-chunk edges.** For each dependency edge in the chunk registry, verify whether it represents a true blocking dependency, a soft co-occurrence, or an artifact of shared utility code. Tag edges as `blocking`, `supportive`, or `informational`.

2. **Add state-based dependencies.** Using the entity database and generated documentation, identify shared data structures (Character fields, Object fields, Room state) and add `reads_state_from` / `writes_state_for` edges where chunks touch the same state.

3. **Add runtime dependencies.** Identify tick-driven and event-driven entry points (update functions, event handlers) and connect them to the chunks whose behavior they drive. These become `updated_by_runtime` edges.

4. **Add target-side coupling notes.** Where two chunks will share an Evennia-side surface (typeclass, handler, contrib), annotate the dependency even if legacy code shows no link.

5. **Re-sequence waves.** Recompute the wave ordering using the refined edge set. Compare against the evidence-only ordering and flag meaningful changes.

Input artifact: `chunk_registry.json`
Output artifact: `chunk_registry.json` (refined edges)

This phase may be partially automated (state-dependency detection from entity field usage) and partially curated (runtime coupling, target-side notes).

### 12.5 Phase 5: connect chunk planning to spec generation

Once the chunk registry is stable — boundaries curated, dependencies refined — each chunk becomes a handoff unit for the coding agent. This phase generates the structured records that make that handoff repeatable.

#### Chunk dossiers

For each chunk in the registry, generate a dossier following the §11 template:

* **Identity and scope** (§11.1) — from the chunk registry directly.
* **Legacy evidence** (§11.2) — from the evidence graph: related entry points, member functions, source files, capability groups, confidence notes.
* **Behavioral contract** (§11.3) — derived from generated documentation and command-level analysis. This is the section that requires the most new work: it must describe what the chunk *does* in user-visible terms, not just what functions it contains.
* **Target-system design constraints** (§11.4) — curated per chunk, informed by Evennia conventions and prior target-architecture decisions.
* **Spec requirements** (§11.5) — open questions, acceptance scenarios, comparison points against legacy behavior.
* **Implementation planning** (§11.6) — predecessor chunks, blocking dependencies, follow-on chunks. Derived from the refined dependency graph.

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

This does not need to be a sophisticated tool — stable identifiers and cross-reference fields in the JSON artifacts are sufficient.

#### Concrete steps

1. **Scaffold dossiers.** Auto-generate the evidence-derivable sections (identity, legacy evidence, implementation planning) from the chunk registry and evidence graph.
2. **Draft behavioral contracts.** For each chunk, synthesize a behavioral description from the generated documentation of its member functions. Flag sections that need human review.
3. **Define readiness criteria.** For each chunk, specify what constitutes structural, interactive, behavioral, system, and UX-faithful readiness.
4. **Produce spec templates.** Create a standard template and populate it for the first batch of chunks (starting with service chunks and early-wave domain chunks).
5. **Establish traceability IDs.** Assign stable identifiers to chunks and define the cross-reference convention.

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

### 15.1 Revised evidence export

A structured export that preserves:

* commands
* direct callees
* classified functions
* matching provenance
* uncategorized residual classes
* raw capability dependencies
* confidence metadata

### 15.2 Semantic interpretation layer

A curated mapping from raw capability buckets into typed semantic nodes.

### 15.3 Initial chunk registry

A first-pass registry of implementation chunks with:

* chunk ID
* purpose
* dependencies
* related commands/use cases
* readiness targets
* target-side notes

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

The capability graph should remain part of the migration process, but with a narrower and more precise role.

It should be treated as a multi-view analysis pipeline:

1. **evidence graph** — code-derived structure and classification
2. **semantic model** — interpreted migration-relevant responsibilities and dependencies
3. **implementation chunk plan** — prioritized work packages for analysis, spec writing, and coding-agent implementation
4. **traceability layer** — links between evidence, understanding, specs, code, and validation

The current prototype is therefore not a dead end. It is the first stage of a larger migration factory.

The rework should focus on evolving it from “call-graph-based capability ordering” into “code-backed chunk discovery and planning,” while preserving its strongest feature: grounding planning decisions in auditable evidence from the legacy codebase rather than relying only on intuition.

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
