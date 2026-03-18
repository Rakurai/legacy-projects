## 1. MCP server: what the agents actually need

### Assessment

V1+V2 already cover a lot of the factual substrate: entity docs, source, call/state/behavior analysis, capability groupings, and system narratives. That is enough for code-centric exploration and for broad architecture navigation. The roadmap is explicit that V1 is implementation-focused, V2 adds conceptual/system narrative, and V3/V4 are the user-facing and builder/specification layers. 

The main gap is not “more graph traversal.” It is **contract extraction**. The spec agent needs compact answers to questions like:

* what exact inputs/preconditions must hold,
* what state is read/written,
* what user-visible outputs occur,
* what adjacent systems this feature assumes exist,
* what data/config drives behavior.

The requirements doc asks for precisely that kind of contract-oriented view, and proposes `explore_entity` plus `explain_interface` for it. 

Against `migration-challenges.md`, V1+V2 are **insufficient** for several high-fidelity questions:

* `act()`/messaging fidelity needs player-visible output contracts, not just implementation and subsystem prose.
* area reset behavior needs authored-data semantics and reset conventions.
* spells/skills need level/mana/target/data-table semantics, not only code.
* NPC behavior needs both system narrative and authored trigger/config semantics.
* stat pipeline and affect timing need implementation detail plus explicit cross-system contracts. 

So the missing pieces are:

1. **user-facing contract data**,
2. **data/config contract data**,
3. **cross-system interface summaries**,
4. **verification artifacts**.

There is also real risk of tool sprawl. V1 already has 19 tools; V2 and the proposed additions add several more. The requirements document itself implicitly admits this by proposing `explore_entity`, `explain_interface`, and planning-oriented aggregators like `get_integration_surface` and `estimate_complexity`.

Boundary-wise, the server should remain a factual reference layer. It should provide:

* evidence,
* derived structure,
* provenance/confidence,
* compact summaries of effective contracts grounded in docs/graphs/source.

It should **not** decide target architecture, migration order, or Evennia design. The requirements document is explicit on that boundary. 

### Recommendation

Do the following:

1. **Add two composite tools before adding many more primitives.**

   * `explore_entity` should become the default spec-agent entrypoint.
   * `explain_interface` should become the default contract view for any function/entity that will be referenced across specs.

   That reduces 4–6 primitive calls into 1–2 calls for the common workflow.

2. **Add one more composite/planning tool that is not yet explicit enough:**

   * `get_integration_surface(system_id)` should be prioritized with a response shape centered on:

     * exposed entry points,
     * required upstream systems,
     * shared data structures/state,
     * outgoing calls depended on by others,
     * user-visible surfaces,
     * known weak-doc areas.

   This is essential for contract discipline between subsystem specs. The requirements doc already points in this direction. 

3. **Add a verification-oriented artifact/tool family.**
   Current roadmap focuses on understanding, not parity verification. For this migration, the server should surface:

   * canonical output strings/message templates,
   * timing constants,
   * formula/data-table extracts,
   * representative behavior traces or scenario records,
   * links between features and acceptance scenarios.

   Without this, specs will drift into “descriptive prose” instead of executable fidelity contracts.

4. **Prioritize V3 earlier than the roadmap suggests.**
   V3 is not optional polish. For this project, user-visible behavior is the product. The challenges doc explicitly says spec agents need all four layers for many hard problems. 

5. **Prioritize the data-contract subset of V4 early, not all of V4.**
   You do not need all builder guidance immediately. You do need:

   * area reset semantics,
   * mob/object/spell/skill table meanings,
   * value-field and flag semantics,
   * authored constraints that affect runtime behavior.

   Defer builder-UX/process docs.

### Open questions

The docs do not fully resolve:

* whether the help files are comprehensive enough to act as behavioral contracts,
* whether the builder guide is authoritative for runtime semantics or partially stale,
* whether existing artifacts already contain message strings/output examples in extractable form,
* whether the server can expose data-table values directly or only narrative about them.

---

## 2. Agent workflow: iterative, hierarchical, or both?

### Assessment

It should be **both**.

A pure bottom-up workflow will fragment the migration. Spec agents will rediscover the same shared assumptions about messaging, stats, positions, and resets, and they will diverge. A pure top-down workflow will produce architecture-level plans that are too abstract to write faithful specs.

The capability-graph/chunk work already points toward a layered approach: evidence graph → semantic model → chunk plan → dossiers/specs. It also explicitly distinguishes chunk planning from later use-case/spec writing.

That is the right backbone:

* planning agent defines chunk order, boundaries, shared contracts, and blockers;
* spec agents work per chunk/use case within that framework;
* specs are revised when adjacent chunk contracts solidify.

A one-pass spec flow is too risky for this codebase. The migration challenges are dominated by cross-cutting infrastructure and latent assumptions: tick order, messaging, effective-stat aggregation, world reset semantics, unified character model, etc. 

### Recommendation

Use this workflow:

**1. Planning pass**

* produce a migration wave plan,
* freeze a shared contract registry skeleton,
* identify infrastructure specs that must exist first,
* define chunk boundaries and adjacency expectations.

**2. Spec pass**

* each chunk gets one primary dossier/spec,
* umbrella chunks are split into implementation dossiers only where the contract surface is separable.

**3. Audit pass**

* every spec is reviewed before implementation.

**4. Implementation pass**

* coding agent works only from approved specs plus contract registry.

**5. Regression/spec revision pass**

* adjacent specs and contracts are updated when new evidence or implementation feedback exposes gaps.

Use revision triggers:

* adjacent spec introduces/changes a shared interface,
* implementation agent finds ambiguity or contradiction,
* auditor finds missing user-visible behavior or unverifiable claims,
* parity test/traces fail.

Create a **separate auditor agent**. It should check:

* completeness,
* consistency with shared contracts,
* fidelity to legacy evidence,
* testability/verifiability,
* proper separation of feature logic vs infrastructure assumptions.

Run the auditor **per spec**, with an additional **per wave** audit for contract coherence.

Create a **contract registry** as a first-class artifact. It should hold:

* messaging contracts,
* stat/effective-value interfaces,
* position/state predicates,
* combat resolution interfaces,
* affect application/removal interfaces,
* reset lifecycle interfaces,
* object/spell/skill identifiers and lookup contracts.

That registry is the anti-drift mechanism.

### Open questions

Need human decisions on:

* who owns the contract registry updates,
* whether auditors may block specs or only annotate them,
* whether contracts are versioned independently of specs,
* whether implementation may proceed against “provisional” contracts.

---

## 3. Migration ordering and bootstrapping

### Assessment

The dependency material is clear that some infrastructure is unavoidable before real system work:

* command interpreter,
* data tables,
* character data,
* world/reset substrate,
* affect/stat pipeline,
* output/messaging layer.

The chunk registry also already identifies foundational semantics before vertical slices: world_structure, state_rules, attributes, visibility_rules, output, entity_lookup, skills_progression, admin; then movement/display, objects, social/notes; then affects/combat/magic/etc. 

That matches the migration challenges better than “start with combat.” Combat depends on too much hidden infrastructure:

* deterministic timing,
* position system,
* effective stat computation,
* affect caching,
* messaging,
* corpse lifecycle,
* group contracts,
* equipment interaction. 

### Recommendation

Minimum infrastructure before the first serious combat spec:

1. **Data/config substrate**

   * canonical race/class/skill/spell/item/flag tables,
   * stable identifiers for effects/skills/spells.

2. **Entity/state substrate**

   * character/NPC shared capability model,
   * object/equipment slots,
   * room/world skeleton,
   * position state model.

3. **Messaging substrate**

   * `act()`-equivalent contract,
   * audience routing,
   * visibility filtering,
   * pronoun/object substitution.

4. **Stat pipeline substrate**

   * base stats,
   * equipment modifiers,
   * affect modifiers,
   * cache/invalidation rules,
   * “effective stat” API.

5. **Timing/runtime substrate**

   * deterministic phase ordering for combat/regen/affects/object/world updates,
   * exact cadence constants.

6. **World lifecycle/reset substrate**

   * area aging,
   * occupancy checks,
   * respawn/decay/relock lifecycle,
   * corpse/item decay semantics.

Only after those are specced should combat be written in earnest.

A reasonable wave structure:

**Wave 0: substrate decisions**

* Evennia surfaces, typeclass strategy, handler strategy, timing orchestration model.

**Wave 1: foundational contracts**

* output/messaging,
* state rules + visibility + position,
* data tables/registries,
* world structure + lookup,
* stat pipeline.

**Wave 2: thin playable vertical slice**

* look/move/display,
* minimal objects,
* minimal communication.

**Wave 3: lifecycle/world semantics**

* resets,
* NPC/object/corpse/item lifecycle,
* persistence inversion handling.

**Wave 4: heavy mechanics**

* affects,
* combat,
* magic,
* skills progression.

**Wave 5: higher systems**

* npc_behavior,
* quests,
* economy,
* clans/pvp,
* admin/builder-heavy features.

Parallelizable:

* display/social/notes after core messaging exists,
* objects and movement can overlap once world/state/output exist,
* later quests/economy/social can parallelize after combat/world/object contracts stabilize.

Strictly sequential:

* messaging before any player-facing feature,
* stat pipeline before affects/combat/magic,
* world reset lifecycle before NPC behavior that depends on respawn semantics,
* position/state rules before command behavior specs.

Use **stubbed contracts**, not stubbed behavior, across dependencies.

* Specs may target a stable interface before full implementation exists.
* Do not fully implement every dependency first.
* But the shared interface contract must be frozen before downstream specs depend on it.

That balances throughput with coherence.

### Open questions

Need explicit decisions on:

* exact timing orchestration model in Evennia,
* unified vs split PC/NPC typeclass strategy,
* reset object lifecycle strategy,
* whether persistence/world reset are one umbrella spec or two linked specs.

---

## 4. Fidelity verification

### Assessment

“Indistinguishable” cannot mean bit-identical internals. It must mean **player-visible parity within defined tolerances**.

The docs already imply multiple validation levels: evidence, semantic, architectural, behavioral, presentation. The capability-graph document also calls for a traceability layer linking evidence, specs, implementation, and validation.

For this project, the fidelity hierarchy should be:

1. **Exact**

   * output text/content,
   * command syntax,
   * timing intervals in gameplay terms,
   * formulas, caps, and ordering where they affect outcomes,
   * visibility/message routing semantics.

2. **Statistically equivalent or discretely equivalent**

   * RNG distributions,
   * proc chances,
   * loot table probabilities,
   * repeated combat outcome distributions.

3. **Operationally irrelevant tolerance**

   * microsecond-scale scheduler noise that does not change tick-level behavior,
   * internal storage/layout differences.

V1 behavior slices help with impact analysis, but they are not enough for parity verification. What is missing is **scenario capture** and **contract-to-test traceability**.

### Recommendation

Define fidelity verification as three artifact classes:

**1. Contract tests**

* formulas,
* caps,
* ordering,
* target selection,
* state transitions,
* interface behavior.

**2. Golden transcript tests**

* command input → exact output text,
* combat round messages,
* spell cast messaging,
* look/inventory/display formatting.

**3. Scenario/parity traces**

* multi-step logs from legacy behavior:

  * fight sequences,
  * affect expiration sequences,
  * reset/respawn timing,
  * NPC behavior triggers.

Use the MCP layer to index and expose these artifacts, but do not force the MCP server itself to become the executor of validation. It should be the traceability backbone.

When spec B follows spec A:

* spec B must cite the relevant shared contracts from A,
* auditor checks for contradictions,
* CI should run contract tests derived from the registry,
* any contract change forces downstream spec revalidation.

### Open questions

Not resolved by the docs:

* whether you can instrument the legacy server to emit authoritative traces,
* whether existing test logs/help files already cover enough scenarios,
* how much variance in RNG behavior is acceptable before players would notice.

---

## 5. Spec granularity and scope

### Assessment

A full “combat system” spec is too broad for faithful implementation. The chunking document explicitly warns that capabilities can be too broad to spec safely and that umbrella chunks should split during spec writing.

For high-risk systems like combat, magic, affects, objects, and persistence, smaller specs are mandatory because:

* the interface surfaces are shared,
* validation needs exact formulas/ordering,
* implementation feedback will revise assumptions.

### Recommendation

Use this granularity rule:

* **Chunk dossier** = planning/handoff umbrella.
* **Implementation spec** = one stable contract surface or tightly coherent mechanic.
* **PR/module** = may implement one or more small specs, but should not outrun auditability.

For combat, split into at least:

* encounter lifecycle and timing,
* hit resolution,
* damage calculation,
* defensive checks,
* death/corpse processing,
* group assist/xp/loot split,
* flee/recall/escape behavior,
* combat messaging.

For magic:

* casting pipeline,
* targeting/validation,
* effect application framework,
* damage spell family rules,
* affect spell family rules,
* object casting,
* per-spell exception catalog.

For affects/stat pipeline:

* effective stat aggregation,
* affect lifecycle/duration/expiry,
* stacking/replacement rules,
* object affects,
* room affects,
* cache invalidation.

Specs should emphasize **data contracts over narrative prose**.
A good spec must include:

* formulas,
* timing constants,
* exact message strings/templates,
* state reads/writes,
* preconditions,
* ordering rules,
* failure cases,
* test cases.

Behavioral prose is supplemental.

### Open questions

Need policy on:

* maximum acceptable spec size,
* whether every spec must produce executable tests before implementation,
* whether message strings live in specs or a shared golden-text artifact referenced by specs.

---

## 6. The shared infrastructure problem

### Assessment

The migration challenges identify the right cross-cutting pieces: messaging, stat computation, position. They should be standalone infrastructure specs, not folded into downstream feature specs. 

There are also additional blockers not highlighted strongly enough:

* deterministic timing/orchestration,
* lifecycle/reset semantics,
* identifier/registry mapping for skills/spells/effects,
* target/entity lookup and visibility,
* corpse/decay/cleanup lifecycle,
* group model.

### Recommendation

Specify these as standalone infrastructure specs first:

**1. Messaging layer**
Minimal viable surface:

* audience classes: actor/victim/room/observers/extra recipients,
* visibility filtering,
* substitution for actor/victim/object/pronouns,
* exact text preservation,
* snoop/spectator extension points.

**2. Stat computation pipeline**
Standalone spec, not buried in character model.
It is a shared rules service used by character, combat, magic, affects, equipment, progression.

**3. Position/state rules**
Separate spec.
Commands depend on it, combat mutates it, skills/spells gate on it.
Then command interpreter specs can consume it.

**4. Deterministic timing/runtime orchestration**
Separate infrastructure spec.
This is the hidden dependency behind combat, regen, affect expiry, object decay, area reset, weather.

**5. World lifecycle/reset system**
Separate infrastructure spec.
It governs area age, occupancy, respawn, relock, cleanup, corpse/item decay.

**6. Registry/identifier system**
Separate infrastructure spec.
Replaces integer indexes/function-pointer IDs for spells, skills, effects, flags, item types.

**7. Lookup/visibility surface**
Separate adaptation spec.
Target resolution, `2.sword`-style disambiguation, visibility-aware search, room-local/global lookup rules.

Those seven are the real shared substrate.

### Open questions

Need explicit architectural choices for:

* whether timing is one orchestrator or coordinated scripts,
* whether lookup lives on objects/handlers or a shared rules module,
* whether registry data is code-backed, DB-backed, or hybrid,
* whether group handling belongs to combat or character/social infrastructure.

---

## Tensions and priorities

There is one central tension:

* **Infrastructure-first** reduces downstream contradiction.
* **Vertical-slice-first** reduces planning risk and proves the substrate.

I would prioritize **infrastructure contracts first**, then a **thin vertical slice**, then heavy mechanics.

Reason: in this project, the dangerous failure mode is not “we built too little gameplay early.” It is “we built gameplay on incompatible hidden assumptions about messaging, timing, stats, and resets.” The docs repeatedly point to those cross-cutting assumptions as the real risk.

The practical sequence is:

* freeze substrate decisions,
* write shared infrastructure specs,
* prove them with a thin playable slice,
* then scale into combat/magic/affects using a contract registry and auditor loop.
