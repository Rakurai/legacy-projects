# Migration Planning Analysis

## 1. MCP Server: What Do the Agents Actually Need?

### Assessment

The V1 tool surface is strong for bottom-up entity research. A spec-creating agent can resolve an entity, read its docs and source, trace its call graph, and get a behavioral footprint — the fireball example in the roadmap doc demonstrates this well. V2 adds the architectural lens that V1 lacks, and the design is sound: grounding signals, narrative roles, and entity↔subsystem links give agents the ability to move between code-level and system-level reasoning.

However, cross-referencing the tool surface against `migration-challenges.md` reveals specific coverage gaps:

**Timing and ordering information is absent.** Challenge §2 (timing model) identifies that the legacy tick loop imposes an implicit execution order — combat before healing before area resets. No V1 or V2 tool exposes this. The behavior slice can show that `violence_update()` calls `multi_hit()`, but it cannot tell an agent that `violence_update()` runs before `char_update()` within the same tick. This ordering is load-bearing for fidelity and must be reconstructed from `game_loop_unix()` source reading, not from any structured tool.

**Output string extraction is V3-dependent.** Challenge §6 (messaging) states that every player-facing feature flows through `act()` with specific format strings. A spec agent writing the combat spec needs to know that the player sees "You hit the goblin with a sword" — the exact string with the exact token pattern. V1's behavior slice can mark messaging as a side-effect category, but it does not extract the actual format strings from `act()` calls. The agent must fall back to reading source code and manually reconstructing output. V3 (help entries) would partially address this for documented commands, but most combat/spell output is not in the help system — it's inline in the C++ code.

**Data-level constants are buried.** Challenge §10 (data tables) identifies ~15 races, ~6 classes, ~200 spells, and ~150 flag definitions as static tables in `const.cc` and `tables.cc`. A spec agent writing the fireball spec needs to know: fireball costs 15 mana at level 10, available to mages at level 5, target type is offensive character. These values live in `skill_table[]` entries. V1's `get_entity` can retrieve the function `spell_fireball`, and `get_source_code` can show the table entry if the agent knows where to look, but there is no tool that directly queries the skill/spell table by name to return structured metadata (level requirements, mana cost, target type, damage noun). V4 (builder's guide) may address some of this, but the in-code tables are the authoritative source and they're not surfaced as structured data.

**Stacking rules and affect interactions are not captured.** Challenge §5 identifies that affect stacking behavior (same-affect-twice → replace vs. extend vs. reject) is per-affect-type logic buried in the spell implementations. No tool extracts this — the agent must read each spell's source to determine stacking behavior. This is a significant gap for the affect system spec.

**Tool sprawl is a moderate risk, but manageable.** V1 has 19 tools, V2 adds 5 new + 2 enhanced, and the speculative requirements propose `explore_entity` and `explain_interface` as composite tools. The composite tools are well-motivated — `explore_entity` in particular saves a spec agent 4-5 sequential tool calls on every new entity. The risk is not that there are too many tools, but that agents won't know which tool to use when. The prompt system (§6 in the agent reqs) mitigates this by providing workflow recipes.

**Boundary discipline is correctly drawn.** The server surfaces facts; the agent interprets them. The "effective contract" question is the right place for the boundary — the server provides side-effect markers, call graphs, and grounding signals; the agent synthesizes those into a contract. `explain_interface` (proposed) is the closest tool to crossing this line, but its description frames it as extracting pre-existing documentation fields (params, return values, side effects from markers), not generating new interpretations. That's acceptable.

### Recommendation

**Build a structured spell/skill table query tool for V1.** Add a tool like `get_skill_entry(skill_name)` that returns the `skill_table` row for a given skill or spell: level requirements per class, mana cost, target type, damage noun, minimum position, spell group membership. This is the single highest-value addition for spec agents. The data already exists in the parsed code graph (it's in `const.cc` / `tables.cc`); it just needs a structured access path. Without it, every spec agent researching any of the ~200 spells must manually read source code to extract configuration data that is already tabular.

**Build `explore_entity` now, defer `explain_interface`.** `explore_entity` is a justified composite — it reduces the most common agent workflow from 4-5 calls to 1. `explain_interface` is more speculative and its value depends on doc quality being uniformly high, which it isn't (the agent reqs note `doc_quality` can be low). Defer it until the V2 tools are in production and agent workflow patterns are observed.

**Extract `act()` format strings as a V1 enhancement, not a V3 dependency.** For each function that calls `act()`, parse the format string arguments from the source and expose them as a `messaging_templates` field on the behavior slice or entity record. This is mechanically extractable from the source code (it's string literals passed to `act()` calls) and gives spec agents the output text they need without waiting for V3.

**Prioritize V3 before V4.** Given the fidelity goal, player-visible behavior contracts (V3) are more immediately useful than builder's guide data (V4). Most spec agents can work from V1+V2 for implementation mechanics and need V3 for the "what does the player see?" question. V4 matters most for the area reset system, loot generation, and NPC configuration — important but narrower scope. V3 should be prioritized to at least a proof-of-concept ingestion for the most heavily referenced help topics (combat, spells, skills, movement).

### Open Questions

- What is the actual format of the in-game help files? The roadmap says "format TBD." If they're structured (topic + body + see-also), ingestion is straightforward. If they're free-form text, linking them to code entities becomes the main engineering challenge.
- Can `act()` format strings be mechanically extracted from the C++ source with enough reliability to be useful? The format is consistent (`act("format", ch, obj, vict, TO_*)`) but macros and conditional formatting may complicate extraction.
- How many of the ~200 spell/skill implementations have structured table entries vs. hard-coded constants? If a significant minority hard-code their parameters inline rather than reading from `skill_table`, the structured query tool would have incomplete coverage.

---

## 2. Agent Workflow: Iterative, Hierarchical, or Both?

### Assessment

The documents describe a migration of ~20 subsystems with complex, layered dependencies. The CG.md document has already done significant work here: it defines a pipeline from evidence extraction → semantic interpretation → chunk formation → spec writing → implementation → validation. The chunk registry (30 chunks, classified by implementation mode and planning phase) is the most concrete planning artifact in the set.

The question is how agents fit into this pipeline. The two agent types (spec-creating and system planning) map to different phases:

- The system planning agent operates at the CG.md Phase 3-4 level: chunk formation, dependency refinement, target-surface mapping.
- The spec-creating agent operates at Phase 5: chunk dossier generation, behavioral contract extraction, spec writing.

The pipeline is inherently hierarchical. A single agent session cannot hold the context of 30 chunks, ~5,300 entities, and 20+ subsystems. The CG.md document implicitly assumes human curation at the boundaries (Phase 3 Pass 2 is curated review), which is correct — agents should not make irreversible architectural decisions without human ratification.

**The iteration question is real.** Specs will need revision. The most common triggers will be: (a) discovery during implementation that a behavioral assumption was wrong, (b) adjacent spec completion revealing an interface mismatch, and (c) V3/V4 data becoming available and revealing user-visible contracts that weren't captured. A one-pass model will not work for the complex systems (combat, magic, affects).

**The auditor role fills a real gap.** The CG.md document defines five validation levels (§14: evidence, semantic, architectural, behavioral, presentation) but doesn't describe who or what performs them. An auditor agent — or more precisely, an auditor step in the pipeline — would check specs against the fidelity criteria before they go to implementation.

### Recommendation

**Use the hierarchical pipeline that CG.md already defines, with agents slotted in as follows:**

1. **System planning agent** (one session, or a small number): consumes the chunk registry and the V2 subsystem tools to produce a refined migration plan — confirmed chunk ordering, dependency annotations, and integration contracts for shared infrastructure. This agent's output is the "migration manifest": an ordered list of chunks with their dependencies, interface contracts, and blocking relationships. Human review before proceeding.

2. **Spec-creating agents** (one per chunk or per spec dossier): each receives the migration manifest, the MCP server, and any previously completed specs for adjacent systems. Produces a spec following the §11 template. The agent's scope is bounded by the chunk definition — it does not discover its own scope.

3. **Auditor step** (per spec, not per system): a separate agent session or a structured checklist that reviews each spec against three criteria:
   - **Completeness**: does the spec cover all entry points the chunk enables? Cross-reference against the chunk registry's entry-point annotations.
   - **Consistency**: do this spec's interface contracts match what adjacent specs expect? Cross-reference against the migration manifest's integration contracts.
   - **Fidelity**: does the spec include exact values (damage formulas, timing intervals, output strings) rather than vague descriptions? Flag any spec section that says the equivalent of "matching the original" without specifying what the original does.

**Build revision into the process by design, not as an exception.** Specs for Phase D chunks (combat, magic, affects) should explicitly plan for a revision pass after their immediate dependencies are also specified. The spec template (CG.md §11) should include a "pending integration questions" section that is resolved during the revision pass.

**Cross-system contract management requires a shared contract registry.** Multiple specs will reference the stat computation pipeline, the messaging layer, and the affect system's API surface. Create a `contracts/` directory alongside the chunk registry that contains interface definitions (function signatures, expected behaviors, shared data structures) for the infrastructure chunks. Spec agents consume these contracts and flag deviations. The contract registry is updated when a spec is accepted, not when it's drafted — accepted specs are the source of truth.

### Open Questions

- How do we handle the case where an implementation agent discovers that a spec is wrong? Does it file a revision request and stop, or attempt a fix and flag it? The answer affects how much autonomy the implementation agent should have.
- Should the auditor step have access to the legacy codebase (via MCP server) to verify fidelity claims, or should it work purely from the spec and the contracts?
- How many spec iterations are realistic for the complex systems (combat, magic)? The answer affects timeline planning.

---

## 3. Migration Ordering and Bootstrapping

### Assessment

The dependency chains are clearly documented across the sources. From the legacy system architecture doc (§ "Migration-critical dependency chains") and the CG.md chunk registry (§12.3), the ordering constraints are:

**Absolute prerequisites before any game system spec can be written:**

1. **Data tables as Python dictionaries/modules** — race, class, skill, spell, attack type, item type, weapon type, flag definitions. Every system reads from these. In CG.md terms, these are Phase B: `attributes`, `state_rules`, `skills_progression` (for table structure).

2. **Messaging layer (`act()` equivalent)** — every system produces output. Without a messaging layer, no spec can describe what the player sees, and no implementation can verify it. This is CG.md's `output` chunk (Phase B, adaptation mode).

3. **Character data model** — combat, magic, skills, and affects all operate on character attributes. The stat computation pipeline (base + equipment + affects + remort bonuses) must be defined. This spans `state_rules`, `attributes`, and the character typeclass strategy.

4. **Position system** — nearly every command checks position. This is part of `state_rules` (Phase B).

5. **Entity lookup** — target resolution (`2.sword`, `bob`, visibility-filtered search) is needed by any command that operates on a target. This is CG.md's `entity_lookup` chunk (Phase B, adaptation mode).

**The CG.md phase structure is well-aligned with these constraints:**

- Phase B (foundational semantics) captures all five prerequisites above.
- Phase C (vertical slices) is the right next step: movement + display gives a navigable world, objects gives item interaction, social gives communication — a minimal playable game.
- Phase D (combat, magic, affects, etc.) is correctly deferred until the foundation exists.

**The stub vs. full implementation question is the key tension.** Combat depends on the affect system. The affect system depends on character data. If combat is being specced before affects are fully implemented, the spec must work against an affect system interface contract (a stub), not the full implementation. This is workable if the interface contract is stable, but it's risky if the affect system's stacking rules or duration semantics change during implementation.

The CG.md document handles this well with its "umbrella chunk" concept — affects is marked as an umbrella that will need multiple spec dossiers. The first dossier can define the interface contract (add/remove/query affects, stat aggregation API), and combat can be specced against that contract. Later dossiers fill in the implementation details (stacking rules, duration management, room/object affects).

### Recommendation

**Implement Phase B infrastructure in this order:**

1. **Constants/enums/data tables** — Python modules defining races, classes, skills, spells, attack types, etc. Pure data, no framework dependencies. This is the Evennia model's bottom layer (Constants/Enums).

2. **Character typeclass + stat computation handler** — the `LivingMixin` or equivalent that provides stats, affects interface, equipment interface, position state. Define the handler API surfaces even if implementations are stubs. This answers the `IS_NPC()` question: use a shared `LivingMixin` with `CharacterBase` → `PlayerCharacter` / `NPC` split.

3. **Messaging layer** — a project-specific `act()` wrapper over Evennia's `msg_contents()` + `FuncParser`. Minimal viable surface: format string with `$n/$N/$e/$m/$s/$p` tokens, three-audience delivery (actor/victim/room), visibility filtering. Snoop and arena spectating can be deferred.

4. **Entity lookup adapter** — a wrapper over Evennia's `DefaultObject.search()` that supports the legacy patterns: `2.sword` numbered targeting, partial matching, visibility-filtered results.

5. **Position system** — position as an Attribute or Tag on characters, enforced either via a pre-command hook or CmdSet swapping. CmdSet swapping is cleaner (sleeping characters literally cannot access movement commands) but more complex to manage. A pre-command hook is simpler and more faithful to the legacy pattern (the legacy system checks position in each command handler).

**Use interface-first stubs for cross-system dependencies.** When a chunk depends on something not yet implemented, define the interface contract (method signatures, expected return types, behavioral guarantees) in the `contracts/` registry. Specs are written against contracts. Implementations are written against contracts. The contract is the integration surface. This is the "stub" approach, and the risk (contract instability) is manageable if the contracts are reviewed as part of the auditor step.

**Parallelize within phases where the dependency graph allows.** Within Phase C: movement + display, objects, and social/notes are largely independent once Phase B infrastructure exists. They can be specced and implemented in parallel. Within Phase D: combat and magic are tightly coupled (spells deal damage through the combat pipeline), but quests, clans/pvp, economy, and npc_behavior are leaf nodes that can proceed independently once their dependencies (combat, world system) exist.

### Open Questions

- The tick timing problem (Challenge §2) is not addressed by the chunk registry. Should it be a separate infrastructure decision (one orchestrating tick vs. independent timers) that is made before any Phase D spec begins? Or should each Phase D spec propose its own timing approach?
- The persistence inversion (Challenge §3) is similarly not a single chunk but affects every system that creates/destroys game objects. Should there be an explicit "NPC/object lifecycle" infrastructure decision before Phase D?
- How do we handle the world system (area loading, room creation, exit linking) — it's the foundation for everything spatial, but the CG.md chunk registry treats `world_structure` as Phase B (native, umbrella). What is the minimal world structure needed for Phase C vertical slices?

---

## 4. Fidelity Verification

### Assessment

The fidelity goal is stated clearly: "indistinguishable from the original in player-facing behavior." The migration challenges document specifies this means combat timing, output text, spell effects, NPC behavior, and skill mechanics must match.

**"Indistinguishable" needs a practical definition.** Exact byte-for-byte output matching is unrealistic (Python string formatting will produce minor differences vs. C++ printf). RNG distributions will differ (Python's Mersenne Twister vs. whatever the legacy system uses). Floating-point rounding in damage calculations may differ. The fidelity target should be:

- Output text: same information content and structure, same pronoun handling, same visibility filtering. Minor whitespace or punctuation differences are acceptable; different words, missing information, or wrong pronouns are not.
- Timing: same interval cadences (2-second violence pulse, 4-second regen, etc.). Sub-second timing differences are acceptable; different round lengths are not.
- Mechanics: same formulas, same caps, same stacking rules. The exact sequence of RNG rolls may differ, but the probability distributions and stat interactions must match.
- Edge cases: same behavior on boundary conditions (0 HP, max level, empty inventory, etc.). These are where fidelity failures are most likely and most player-noticeable.

**The MCP server's V1 tools partially support verification.** Behavior slices show side-effect categories, and the call graph reveals the damage pipeline. But the tools don't produce test cases. What's needed for verification is input/output pairs: "given a level 10 warrior with STR 18, DEX 14, wielding a long sword against a goblin with AC 5 — the hit roll succeeds if random(1,20) + hitroll + skill/20 >= threshold." This formula must be extracted by the spec agent from source code and V1 tools, then encoded as a test case in the spec.

**Behavioral validation (CG.md §14.4) and presentation validation (§14.5) are the two levels that matter most for the fidelity goal.** Evidence and semantic validation ensure the spec is correct; architectural validation ensures it fits Evennia. But the player only cares about behavioral and presentation fidelity.

### Recommendation

**Define fidelity as "same observable outcome for same game state" rather than "identical implementation."** Encode this in spec templates: every spec must include a "Fidelity Verification" section with:

1. **Exact formulas** — damage = dice_roll(weapon_dice) + damroll + skill_modifier + enhanced_damage_bonus, capped at [max], with sanctuary halving applied after resistance calculation. Not "damage is calculated per the original."

2. **Output templates** — the exact `act()` format strings for each player-visible message, with token substitutions documented. For combat: "Your slash hits $N" (actor), "$n's slash hits you" (victim), "$n's slash hits $N" (room).

3. **Boundary conditions** — at least 3-5 edge cases per spec: zero HP behavior, maximum stat values, empty containers, invisible actors, sleeping targets.

4. **Timing contracts** — for any system with periodic behavior: the exact interval, what triggers it, what order it runs relative to other periodic systems.

**Extract legacy behavior traces where feasible.** If the legacy server can be run, instrument it to log combat rounds, spell effects, and NPC actions with full state. These logs become golden test data. If the server cannot be run, reconstruct expected behavior from source code analysis — the MCP server's `get_source_code` and `get_behavior_slice` tools are the right starting point, but the spec agent must do the synthesis work.

**Automate regression testing across specs.** Each accepted spec deposits its fidelity verification cases into a shared test suite. When a new spec is accepted, its test cases are checked against existing ones for contradictions (e.g., spec A says sanctuary halves before resistance; spec B says after). This is the "regression across specs" mechanism.

### Open Questions

- Can the legacy server be run to produce behavior traces? This would dramatically reduce the effort of extracting exact formulas and edge-case behaviors.
- How do we handle the RNG question? If legacy uses `random()` with a specific seed behavior and the reimplementation uses Python's `random`, the exact sequence of rolls will differ. Is statistical equivalence sufficient, or do specific interactions depend on deterministic RNG ordering?
- Some legacy behavior is arguably "bugs" that players have adapted to (e.g., specific rounding errors that result in damage values players have memorized). Should the fidelity target preserve bugs, or is "correct implementation of the intended formula" sufficient?

---

## 5. Spec Granularity and Scope

### Assessment

The CG.md document already resolves much of this question. The chunk registry defines 30 implementation chunks, four of which are marked as umbrellas (world_structure, affects, persistence, objects) that will need multiple spec dossiers. This is the right granularity level — chunks are larger than individual commands but smaller than full subsystems.

The key tension is between spec self-containment and spec interdependence. A combat spec that tries to cover the entire damage pipeline, group combat, flee/recall, and death processing in one document will be too large for a single agent context window and too complex for a single review. But splitting it into sub-specs (hit resolution, damage calculation, death processing, group mechanics) creates interface dependencies between sub-specs that must be managed.

**The CG.md chunk dossier template (§11) is well-structured for this.** Identity/scope, legacy evidence, behavioral contract, target-system constraints, spec requirements, and implementation planning — this covers what a coding agent needs. The missing piece is the "data contract emphasis" the discussion prompt calls out.

### Recommendation

**Use the CG.md umbrella chunk model: one chunk can produce multiple spec dossiers, each focused on a self-contained implementation surface.** For combat:

- Dossier 1: Hit resolution pipeline — hit roll formula, defensive checks (dodge/parry/shield block), weapon skill interactions. Depends on: stat computation, equipment handler, skill proficiency lookup.
- Dossier 2: Damage pipeline — base damage, modifiers, resistance/vulnerability, sanctuary, elemental cascading, HP reduction. Depends on: hit resolution, affect system (for sanctuary/resistance queries), object system (for equipment degradation).
- Dossier 3: Death processing — corpse creation, inventory transfer, ghost state, XP distribution, group loot splitting. Depends on: damage pipeline, object system, economy (gold splitting).
- Dossier 4: Combat loop and group mechanics — `violence_update` equivalent, multi-hit resolution, group assist, flee/recall, auto-attack cadence. Depends on: all three previous dossiers, timing infrastructure.

**Each spec dossier must emphasize data contracts over behavioral descriptions.** Enforce this in the spec template: every formula, every constant, every timing value, every output string must be explicit. Add a "Numeric Constants" section to the spec template that lists every hardcoded value referenced in the spec, with its source (which `const.cc` table entry, which `skill_table` row, which `#define`). A spec that references a value by description rather than by exact number ("the mana cost for fireball" rather than "mana cost: 15 at level 10, scaling per `skill_table[gsn_fireball].min_mana`") is incomplete.

**Target a 1:1 relationship between spec dossier and implementation PR where possible.** This makes review tractable: one spec, one PR, one review cycle. For umbrella chunks, each dossier maps to one PR. This does not mean the PRs are merged independently — combat dossier 1's PR can be merged only when its dependencies exist — but it means each PR has a clear scope and a clear spec to review against.

### Open Questions

- What is the maximum spec dossier size that a coding agent can effectively work from? If a dossier exceeds the context window, the agent will miss details. This constrains how much a single dossier can cover.
- Should the ~200 spell implementations get individual spec dossiers, or should they be grouped by category (offensive spells, healing spells, transportation spells, etc.)? Grouping by category allows pattern extraction (many offensive spells share the same structure: check saves → apply damage → send messages); individual specs are more precise but 200x the work.
- The CG.md document identifies 19 native chunks. If each produces 2-3 dossiers on average, that's 40-60 specs. Is this feasible for the agent pipeline, or does it need further consolidation?

---

## 6. The Shared Infrastructure Problem

### Assessment

The migration challenges document and the legacy architecture overview both identify the same infrastructure dependencies. The CG.md Phase B captures them as chunks, but doesn't fully specify their minimal viable surfaces.

**Messaging (`act()` equivalent)** is the most pervasive dependency. The legacy architecture doc says "every piece of player-visible text flows through this." The migration challenges doc (§6) identifies four requirements: token substitution ($n/$N/$e/$m/$s/$p), three-audience delivery, visibility filtering, and snoop forwarding. The Evennia model provides `msg_contents()` + `FuncParser`, which covers token substitution and audience delivery but not visibility filtering or snoop forwarding.

**Stat computation pipeline** is the second most critical. Combat, skills, magic, and affects all query "effective stat" values. The legacy system pre-computes aggregates in a cache (Challenge §5). The question is whether this cache belongs in the character data model spec (since it's an attribute of the character) or the affect system spec (since affects are the primary modifier). Answer: it belongs in a standalone stat computation handler spec, because equipment modifiers, remort bonuses, and admin overrides also participate — it's not purely an affect concern.

**Position system** is architecturally simple but pervasive. The legacy architecture doc notes that "nearly every command checks character position." Two Evennia approaches are viable: a pre-command hook that checks `character.db.position` against the command's minimum position requirement, or CmdSet swapping where different positions grant different command sets. The pre-command hook is simpler and more faithful; CmdSet swapping is more Evennia-idiomatic.

**Additional infrastructure not called out but likely blocking:**

- **Tick/timing infrastructure.** The timing model decision (§3 of migration challenges — one orchestrating tick vs. independent timers) affects every system with periodic behavior. Combat, regen, affects, area resets, NPC AI, and object decay all need timing. If each system implements its own timing approach, inconsistencies are likely.

- **Area loading and room creation.** Phase C's first vertical slice (movement + display) needs rooms to exist. Rooms need areas. Areas need to be loadable from some data source (converted area files, a seed script, or manual creation). The `world_structure` chunk is Phase B but it's an umbrella — the minimal viable surface for Phase C is just "rooms exist, have exits, can be traversed."

- **The `IS_NPC()` resolution.** Every system that operates on characters branches on whether the target is a PC or NPC. The architectural decision (LivingMixin vs. unified Character typeclass) must be made before any system that handles both PCs and NPCs can be specified. This is a typeclass strategy decision, not a chunk — but it blocks spec work.

### Recommendation

**Specify and implement the messaging layer first, before any game system.** Minimal viable surface:

- `game_act(format_string, actor, [obj, victim], audience)` — a function that takes an `act()`-style format string with `$n/$N/$e/$m/$s/$p` tokens, resolves them for each recipient, filters by visibility (can the recipient see the actor?), and delivers via Evennia's `msg()`.
- Three audience modes: `TO_CHAR` (actor only), `TO_VICT` (victim only), `TO_ROOM` (all in room except actor and victim), `TO_ALL` (entire room including actor).
- Visibility filtering: if actor is invisible and recipient lacks detect-invisible, suppress the message or replace actor name with "someone."
- Snoop forwarding and arena spectating are deferred to a later revision — they are admin/event features, not core messaging.

**Specify the stat computation pipeline as a standalone handler spec, owned by the character typeclass but independent of the affect system implementation.** The handler exposes:

- `get_effective_stat(stat_name) → int` — returns base + equipment + affects + remort + admin overrides, with caching.
- `invalidate_stat_cache()` — called when any modifier changes (equip/remove item, add/remove affect, admin set).
- The affect system, equipment handler, and remort system all call `invalidate_stat_cache()` when they modify a character. The stat handler re-aggregates on next query.

This decouples the stat query interface from the affect system's internal implementation. Combat specs call `get_effective_stat('strength')`; they don't need to know how affects or equipment work internally.

**Make the tick/timing decision as an explicit infrastructure commitment before Phase D.** The recommended approach: a single-character orchestrating script that ticks at the violence pulse rate (2 seconds) and calls subsystem handlers in the legacy order (combat → healing → affect duration → regen). This is not a global sweep (which would be an antipattern) but a per-character script that maintains the ordering invariant within each character's update cycle. Area resets are separate (per-area scripts on a different cadence). This preserves the legacy ordering guarantee without fighting Evennia's design — each character has one script, not one global loop.

**Position enforcement via pre-command hook.** Add a `at_pre_cmd` hook on the character typeclass that checks `self.db.position` against `cmd.min_position`. If the check fails, send "You can't do that while sleeping." and abort. This is simpler than CmdSet swapping, matches the legacy behavior pattern exactly, and is easy to understand for spec agents.

**Resolve the typeclass strategy now.** Use `LivingMixin` providing shared behavior (stats, affects, combat participation, position, inventory) applied to both `PlayerCharacter(DefaultCharacter, LivingMixin)` and `NPC(DefaultCharacter, LivingMixin)`. This is the clean Evennia approach and avoids the unified-Character antipattern. The cost is systematically decomposing every `IS_NPC()` branch — but the CG.md pipeline already handles this because specs are written per-chunk, and each chunk can document which behaviors differ between PCs and NPCs.

### Open Questions

- How many concurrent NPCs will exist simultaneously in the reimplemented game? This determines whether per-NPC Scripts (for AI ticking) are feasible or whether a batch processor is needed. The answer has implications for the tick/timing infrastructure.
- Should the messaging layer support ANSI color codes from the start, or is that a Phase C concern? Many legacy `act()` calls embed color codes in the format strings.
- The stat computation pipeline depends on knowing all modifier sources (equipment, affects, remort, admin). Should the handler spec enumerate all known modifier types now, or should it provide an extensible registration mechanism that new modifier sources can plug into?

---

## Cross-Topic Tensions and Prioritization

Two recommendations conflict:

1. **"Start with infrastructure" (Topics 3, 6)** says: build messaging, stat pipeline, timing, and data tables before game systems.
2. **"Deliver playable vertical slices early" (CG.md Phase C)** says: get movement + display + objects working as soon as possible to validate the architecture.

These are reconcilable. Phase B infrastructure (data tables, messaging, stat pipeline, entity lookup, position system) is relatively small scope — these are adapter layers and data structures, not complex game logic. A focused effort can deliver them in weeks, not months. Once Phase B exists, Phase C's first vertical slice (navigate rooms, look at things, pick up objects) validates that the infrastructure actually works. Phase D's complex systems (combat, magic) follow only after the vertical slice confirms the foundation is sound.

**Prioritize in this order:**

1. **Typeclass strategy decision + data table migration** (pure prerequisites, no Evennia integration needed for tables)
2. **Messaging layer + entity lookup + position system** (Phase B adapters)
3. **Character data model + stat computation handler** (Phase B core)
4. **First vertical slice: movement + display** (Phase C, validates everything above)
5. **Object interaction** (Phase C, second vertical slice)
6. **Affect system interface contract** (enables Phase D specs to be written)
7. **Combat, magic, and remaining Phase D systems** (the bulk of the migration work)

This ordering delivers a playable (if minimal) game at step 4 while front-loading the infrastructure decisions that all later work depends on.
