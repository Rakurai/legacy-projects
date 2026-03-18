# Discussion Round 2: Resolving Decisions and Shaping Infrastructure

> **For:** A second-round review session. You have access to the original prompt
> (`discussion.1.PROMPT.md`), the three Round 1 responses (`discussion.1.claude.md`,
> `discussion.1.gemini.md`, `discussion.1.gpt.md`), and all previously attached
> reference documents.
>
> **What happened in Round 1:** Three agents independently analyzed six topics
> covering MCP server needs, agent workflow, migration ordering, fidelity
> verification, spec granularity, and shared infrastructure. Round 1 established
> broad consensus on the overall approach. Round 2 asks you to resolve the open
> disagreements, make concrete architectural commitments, and begin defining the
> actual shape of the first deliverables.

---

## Round 1 Consensus (treat as settled unless you disagree)

The three Round 1 responses converged on these points. Do not re-argue them
unless you see a flaw. If you accept them, say so briefly and move on.

1. **Hierarchical + iterative workflow:** Planning agent → spec agents (per chunk)
   → auditor step → implementation agent → revision pass. One-pass is
   insufficient. A contract registry is the anti-drift mechanism.

2. **Infrastructure-first, then vertical slice, then heavy mechanics.** The
   migration ordering is: substrate decisions → shared infrastructure contracts →
   thin playable slice (move/look/objects) → lifecycle/resets → combat/magic/affects
   → higher systems.

3. **Seven infrastructure pieces must be specified before game system specs:**
   (a) data tables/registries, (b) messaging layer (`act()` equivalent),
   (c) stat computation pipeline, (d) position/state rules, (e) entity lookup
   adapter, (f) timing/runtime orchestration, (g) world lifecycle/reset system.

4. **Fidelity = player-visible parity, not identical internals.** Exact output
   text, exact formulas, exact timing cadences. Statistical equivalence for RNG.
   Tolerance for sub-tick scheduler noise and internal storage differences.

5. **Specs must emphasize data contracts over prose.** Every formula, constant,
   timing value, and output string must be explicit. "Matching the original"
   without specifying what the original does is a spec failure.

6. **Umbrella chunks split into implementation dossiers.** Combat becomes 4–8
   dossiers (encounter lifecycle, hit resolution, damage calculation, death/corpse,
   group mechanics, etc.). Each dossier maps to roughly one implementation PR.

7. **`explore_entity` composite tool should be built.** Reduces 4–5 sequential
   tool calls to one for the common spec-agent workflow.

8. **V3 (user-facing help) should be prioritized earlier than the roadmap
   suggests.** Player-visible output contracts are core to the fidelity goal.

---

## Topics for Round 2

### Topic A: The Stubs Disagreement

Round 1 produced a concrete disagreement. Claude and GPT recommend **stubbed
interface contracts** for cross-system dependencies — freeze the API surface,
write specs against it, implement the full behavior later. Gemini recommends
**full implementations** for the stat pipeline specifically, arguing stubs are
"too risky for the hot path."

This matters because it determines how much must be built before the first
game-system spec (combat) can be written.

Address:

- Which infrastructure pieces can safely use stubbed contracts (frozen API, spec
  against it, implement later) vs. which require working implementations before
  downstream specs can be written?
- What specifically makes a stub risky? Is it that the API surface might change
  (contract instability), that downstream specs need to observe real behavior to
  be accurate (behavioral dependency), or that implementation feedback will
  force contract revision (discovery risk)?
- For the stat pipeline specifically: can a combat spec agent write a correct
  hit-roll formula against `get_effective_stat('dexterity') → int` without
  knowing how the aggregation works internally? Or does the combat spec need
  to know about affect stacking, equipment layering, and cache invalidation
  to produce a faithful spec?
- Propose a concrete rule: "Infrastructure piece X is stub-safe / must be
  implemented first because Y."

---

### Topic B: Timing Orchestration — The Actual Decision

All three responses identify timing as a critical infrastructure decision, but
none fully commit to an architecture. Claude proposes a per-character
orchestrating Script that ticks at 2-second cadence and calls subsystem handlers
in legacy order. GPT lists it as a standalone infrastructure spec without
proposing a design. Gemini doesn't address it in detail.

The legacy system works like this: one global loop, every pulse (~100ms), calls
subsystems in a fixed order. Different subsystems fire at different pulse
multiples. The ordering is load-bearing — combat damage resolves before healing,
healing before affect expiry, affect expiry before area resets.

Evennia provides: `TickerHandler` (global subscriptions at configurable intervals),
`Script` (per-object timer with `at_repeat()`), `utils.delay()` (one-shot timer),
and Twisted's reactor (which makes no ordering guarantees between callbacks
scheduled for the same moment).

Address:

- **Design the timing system.** Not "consider options" — commit to an
  architecture. How does the 2-second violence pulse work? How does the
  4-second regen pulse work? How do they relate to each other? What guarantees
  their ordering?
- **Per-character vs. per-room vs. per-encounter vs. global:** The legacy system
  is a global sweep. Evennia-native is per-object Scripts. Claude proposes
  per-character. What are the tradeoffs? A room with 10 NPCs in combat — does
  each have its own script ticking at 2 seconds, or does a room/encounter
  handler coordinate them?
- **The area reset timer:** Legacy areas reset based on age + occupancy. This
  is naturally a per-area Script in Evennia. But how does it interact with the
  combat/regen timing? Does it need to be phase-locked, or is it independent?
- **Drift prevention:** If 50 characters each have a 2-second script, they will
  drift out of phase over time. Does this matter for gameplay? In legacy,
  all violence resolves simultaneously in one pass. In per-character scripts,
  character A's round resolves before character B's. Does this change the
  player experience?

---

### Topic C: Typeclass Strategy — The Actual Decision

Claude proposes `LivingMixin` applied to both `PlayerCharacter(DefaultCharacter,
LivingMixin)` and `NPC(DefaultCharacter, LivingMixin)`. The other responses
acknowledge the question without committing. The legacy system uses a unified
`Character` class for PCs and NPCs, distinguished by flags and the
presence/absence of a `Player` sub-object.

Address:

- **Commit to a typeclass hierarchy.** What are the concrete classes? What goes
  on the mixin vs. the PC-specific class vs. the NPC-specific class?
- **The `IS_NPC()` decomposition:** The legacy codebase branches on `IS_NPC()`
  pervasively. In a mixin approach, where does each divergence live? Examples:
  - NPC death → respawned by area reset; PC death → ghost state + XP penalty
  - NPC has a prototype vnum; PC has a player file
  - NPC may have `spec_fun` and MobProg triggers; PC has aliases and preferences
  - NPC shops, NPC healer services
  - Both participate in combat identically (same hit/damage pipeline)
- **Object typeclass strategy:** The legacy `Object` class uses a type-polymorphic
  `ObjectValue` union (weapon → damage dice, container → capacity, food → poison
  status). In Evennia, should each item type be a separate typeclass
  (`Weapon`, `Container`, `Food`), or a single `GameItem` typeclass with
  type-specific Attributes? What are the tradeoffs?
- **Room and Exit strategy:** Anything non-obvious needed beyond standard Evennia
  `DefaultRoom` / `DefaultExit` subclasses?

---

### Topic D: Messaging Layer Contract Shape

All three responses agree the messaging layer is the first infrastructure spec
and the most pervasive dependency. Claude provides the most detail (function
signature, audience modes, visibility filtering). Round 2 should finalize the
contract.

Address:

- **Define the function signature.** What arguments does `game_act()` take?
  What does it return? Be specific about types.
- **Token substitution:** The legacy tokens are `$n` (actor name), `$N` (victim
  name), `$e`/`$E` (he/she/it), `$m`/`$M` (him/her/it), `$s`/`$S` (his/her/its),
  `$p`/`$P` (object short description), `$t` (secondary object). How should
  these map to the Evennia approach? FuncParser inline functions? Pre-resolved
  string formatting? A custom formatter?
- **Audience routing:** Legacy has `TO_CHAR`, `TO_VICT`, `TO_ROOM`,
  `TO_NOTVICT` (room minus actor and victim), `TO_ALL`. The idiomatic way in
  Evennia is `msg_contents()` with `exclude` lists. Should `game_act()` handle
  all audience modes, or should it be one call per audience with the caller
  managing exclusions?
- **Visibility filtering:** If actor is invisible and recipient lacks
  detect-invisible, the actor's name is replaced with "someone" (or the message
  is suppressed entirely for some message types). Where does this logic live —
  in `game_act()` itself, or in a name-resolution helper that `game_act()` calls?
- **What is deferred?** Snoop forwarding, arena spectating, ANSI color codes,
  channel-based messaging — which of these are in the minimal viable contract
  and which are explicitly deferred?

---

### Topic E: Contract Registry Format

All three responses recommend a contract registry. None define its format.

Address:

- **What does a contract entry look like?** Give a concrete example — the stat
  computation pipeline contract. What fields does the entry have? Method
  signatures? Behavioral guarantees? Pre/post conditions? Expected return types?
- **Where does it live?** A `contracts/` directory with one file per
  infrastructure piece? A single registry file? Something else?
- **Who updates it?** The planning agent creates the skeleton. Spec agents
  consume it. When does it get updated — when a spec is drafted, when it's
  audited, or when it's accepted?
- **Versioning:** If a contract changes after downstream specs have been written
  against it, how is the impact tracked? Which downstream specs need revision?

---

### Topic F: The 200-Spell Problem

Claude raises a practical question: should the ~200 spell implementations get
individual spec dossiers, grouped-by-category dossiers, or a framework +
exceptions approach? This is a microcosm of the granularity question applied
to the single largest system (magic.cc, ~7,000 LOC).

Address:

- **Pattern analysis:** How many of the ~200 spells share a common structure
  (check saves → apply damage → send message)? How many are truly unique in
  their mechanics? If 150 follow 5-6 patterns and 50 are bespoke, the approach
  should differ for each group.
- **Framework vs. catalog:** Should the spec define a spell-effect framework
  (a data-driven system that handles the common patterns) and then catalog the
  exceptions that need custom code? Or should every spell be individually
  specified?
- **The MCP server's role:** Can the V1 tools (behavior slices, call graph)
  help cluster spells by behavioral similarity? If `spell_fireball`,
  `spell_lightning_bolt`, and `spell_chill_touch` all follow the pattern
  "check saves → damage() → act() messages", the behavior slice should show
  identical call-graph shapes. Can this clustering be automated or
  semi-automated to reduce the spec-writing burden?
- **Migration ordering for spells:** Should the casting pipeline infrastructure
  (mana cost, skill check, interruption, target parsing) be a separate spec
  from the spell catalog? If so, what is the minimal set of spells needed to
  validate the casting pipeline (one per target type? one per effect category?)?

---

### Topic G: What Does "Done" Look Like for Wave 1?

Round 1 agrees on the wave structure but doesn't define acceptance criteria.

Address:

- **For each of the seven infrastructure specs** (data tables, messaging, stat
  pipeline, position, entity lookup, timing, world lifecycle): what is the
  concrete deliverable? A Python module? An Evennia typeclass? A handler class?
  A spec document? A spec + implementation + tests?
- **What validates Wave 1?** A thin vertical slice (move/look/objects) is the
  agreed proof. What specific player actions must work for Wave 1 to be
  considered complete? "A player can log in, move between rooms, look at rooms
  and objects, pick up and drop items, and see other characters" — is that
  sufficient, or does it need more?
- **What is explicitly out of scope for Wave 1?** Combat? Affects? Spells?
  NPC behavior? Area resets? Chat channels? If a player types `kill goblin`
  during Wave 1 validation, what happens?

---

## Output Format

For each topic, provide:

1. **Decision** — a concrete commitment, not an exploration of options. "We
   should do X" not "options include X, Y, and Z."
2. **Rationale** — why this decision, briefly. Reference Round 1 analysis where
   it supports the decision.
3. **Contract shape** (where applicable) — actual function signatures, data
   structures, or acceptance criteria. Pseudocode is fine. Prose descriptions
   of what a contract "should include" are not.
4. **Risks** — what could go wrong with this decision, and what is the
   mitigation.

Avoid re-analyzing the Round 1 topics. This round is about decisions and
concrete shapes, not further exploration.
