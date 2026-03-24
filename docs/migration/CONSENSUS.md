# Migration Planning — Consensus Record

> **Status:** Living document. Updated as discussion rounds lock down decisions.
> Each entry records the decision, which round settled it, and whether all three
> agents agreed or a majority ruled.
>
> **Scope:** Architectural commitments that downstream specs and implementation
> may treat as settled. Anything not in this document is still open.

---

## 1. Workflow and Process

### 1.1 Agent Pipeline

**Decision:** Hierarchical + iterative workflow.

- **Planning agent** → produces migration manifest (chunk ordering, dependency
  annotations, integration contracts). Human review before proceeding.
- **Spec-creating agents** (per chunk/dossier) → receive manifest + MCP server +
  previously accepted specs. Produce spec following the chunk dossier template.
- **Auditor step** (per spec) → checks completeness, consistency with shared
  contracts, fidelity to legacy evidence, testability. Additional per-wave audit
  for contract coherence.
- **Implementation agent** → works only from approved specs + contract registry.
- **Revision pass** → triggered by: adjacent spec changing a shared interface,
  implementation finding ambiguity/contradiction, auditor finding missing
  behavior, parity test failure.

**Settled:** Round 1 (unanimous).

### 1.2 Contract Registry

**Decision:** A `contracts/` directory in the migration repository. One YAML file
per infrastructure piece. Versioned with semver (patch = clarification, minor =
backward-compatible expansion, major = breaking change).

- Planning agent creates skeleton contracts.
- Infrastructure spec agents fill in preconditions, postconditions, behavioral
  guarantees. Contract moves to `accepted` when infrastructure spec passes audit.
- Downstream spec dossiers declare `depends_on_contracts: [ID@version]`.
- When a contract is revised, `depended_on_by` identifies which downstream specs
  need review. Human decides compatibility.
- Contracts are the only shared interface artifact — feature specs do not become
  contracts.

**Settled:** Round 2 (unanimous on structure; minor format differences resolved
below in §1.3).

### 1.3 Contract Entry Format

**Decision:** YAML files with these fields:

```yaml
contract_id: INF-STAT-001    # stable identifier
name: stat_pipeline           # human-readable name
version: 1.0.0
status: accepted              # draft | accepted | revised
chunk: attributes             # owning chunk from registry
summary: ...

depends_on: [...]             # upstream contract IDs
used_by: [...]                # downstream chunk names (populated as specs are accepted)

apis:
  - name: method_name
    signature: "method_name(args) -> return_type"
    preconditions: [...]
    postconditions: [...]
    behavioral_guarantees: [...]

acceptance_tests:
  - id: INF-STAT-001-T1
    description: ...

downstream_impact:
  breaking_change_requires: [...]

changelog:
  - version: 1.0.0
    date: ...
    change: Initial contract definition
```

Location: `migration/contracts/`. Index file: `migration/contracts/index.yaml`.

**Settled:** Round 2 (synthesized from Claude and GPT formats; Gemini proposed
JSON-Schema-backed YAML which is compatible).

---

## 2. Migration Ordering

### 2.1 Wave Structure

**Decision:** Five waves.

| Wave | Focus | Prerequisites |
|------|-------|---------------|
| **0** | Substrate decisions: typeclass strategy, handler strategy, timing model | None |
| **1** | Foundational contracts: data tables, messaging, stat pipeline, position, entity lookup, timing runtime, world lifecycle skeleton | Wave 0 decisions |
| **2** | Thin vertical slice: move/look/display, minimal objects, minimal communication | Wave 1 infrastructure |
| **3** | World lifecycle: resets, NPC/object/corpse lifecycle, persistence handling | Wave 1 + 2 |
| **4** | Heavy mechanics: affects, combat, magic, skills progression | Wave 1–3 |
| **5** | Higher systems: NPC behavior, quests, economy, clans/PvP, admin/builder tools | Relevant Wave 4 systems |

**Parallelizable:** Within Wave 2, display/social/notes can overlap once messaging
exists. Within Wave 5, quests/economy/social can parallelize after combat/world
contracts stabilize.

**Strictly sequential:** Messaging before any player-facing feature. Stat pipeline
before affects/combat/magic. World reset lifecycle before NPC behavior. Position
rules before command behavior specs.

**Settled:** Round 1 (unanimous), refined in Round 2.

### 2.2 Stub vs. Implementation Rule

**Decision:** Two-tier rule based on behavioral dependency.

**Must be implemented before downstream game-system specs:**
- Stat computation pipeline — aggregation order affects combat formulas
- Messaging layer — exact output contracts needed for every spec
- Timing/runtime orchestration — ordering guarantees shape every timed system

**Stub-safe (frozen contract surface, implementation deferred):**
- Data tables/registries — API is simple lookup, contents are fixed legacy data
- Entity lookup — downstream specs need return type and "not found" behavior only
- Position system — trivial boolean check
- World lifecycle/resets — stub-safe for Wave 2; must be implemented before Wave 3
- Affect system external API — stub-safe for early combat formulas; full semantics
  needed before combat integration and magic specs are accepted

**Rule:** A stub is risky when the downstream spec needs to reason about what
happens *inside* the box, not just what comes out. If internal ordering, caching
semantics, or aggregation rules affect downstream correctness, implement first.

**Settled:** Round 2 (Claude/GPT aligned fully; Gemini wanted entity lookup and
data tables as "must be full" but the behavioral dependency argument resolved
this — their APIs are opaque to consumers).

### 2.3 Wave 1 Vertical Slice Scope

**Decision:** Wave 1 proves login → navigate → inspect → interact with objects →
position enforcement → stat display → basic communication. Pre-created test
characters; no character creation flow, no combat, no channels.

| Action | Status | Justification |
|--------|--------|---------------|
| Connect and log in (pre-created test character) | **In scope** | Baseline for all testing. Admin-created characters, no creation wizard. |
| `look` (room description, exits, contents, characters) | **In scope** | Core navigation proof. Tests messaging, display hooks, visibility. |
| `look <object>` / `look <character>` | **In scope** | Part of the navigable world proof. |
| Move through exits (`north`, `south`, etc.) | **In scope** | Tests room/exit typeclasses, position enforcement. |
| `exits` (list available exits) | **In scope** | Trivial companion to `look`; standard navigation tool. |
| `get` / `drop` (pick up and drop items) | **In scope** | Core object interaction proof. Tests entity lookup, GameItem typeclass. |
| `inventory` (list carried items) | **In scope** | Validates inventory display. Trivial once `get` works. |
| `say` (local room speech) | **In scope** | Simplest live proof that `game_act()` works for social messaging. |
| `sleep` / `wake` (position changes + command gating) | **In scope** | Proves position system contract: sleep → movement blocked → wake → movement works. |
| Entity lookup: `get 2.sword`, partial matching | **In scope** | Must work for the object interaction proof to be meaningful. |
| `score` (character stat display) | **In scope** | Most direct proof that the stat pipeline works — player types `score`, sees correct base stats, HP/mana/move. Wave 1 shows correct *values* in simplified format; legacy-matching display formatting is a later refinement. |
| `who` (list online players) | **In scope** | Simple connected-session query. Proves Account/Character relationship. |
| `kill goblin` | **Stub** | Command exists, returns explicit dev message: "That command is not available yet." Not "command not found." |
| `wear` / `remove` (equip and unequip) | **Deferred** | Requires equipment↔stat aggregation integration. `get`/`drop` is sufficient for the object interaction proof. |
| Full character creation flow | **Deferred** | Separate mini-spec. Legacy creation state machine (race, class, stat rolling, skill groups) is its own dossier. |
| Chat channels (gossip, etc.) | **Deferred** | Requires channel infrastructure. `say` covers messaging proof. |

**Wave 1 validates:** All seven infrastructure contracts (stat pipeline,
messaging, timing, position, entity lookup, data tables, world lifecycle
skeleton) in a player-visible way.

**Wave 1 does NOT prove:** Combat, affects, equipment stat modification, spells,
skills, NPC behavior, resets, channels, economy, quests, character creation.

**Risk:** Including `score` creates risk of stat display formatting becoming a
time sink. Mitigation: Wave 1 `score` shows correct values in a simplified
format; legacy-matching formatting is deferred.

**Settled:** Round 3 (unanimous on core; `wear/remove` deferred by Claude+GPT
majority; `score` in scope by Claude+Gemini majority; GPT deferred `score` but
reasoning was about formatting, which is mitigated by the simplified-format
rule).

---

## 3. Architecture

### 3.1 Typeclass Strategy

**Decision:** Split PC/NPC with shared `LivingMixin`.

```
LivingMixin
  ├── stats: StatHandler
  ├── affects: AffectHandler
  ├── equipment: EquipmentHandler
  ├── skills: SkillHandler
  ├── position, in_combat, take_damage(), heal(), apply_affect()
  └── (all symmetric combat/stat/affect/equipment behavior)

PlayerCharacter(DefaultCharacter, LivingMixin)
  ├── preferences: PreferenceHandler
  ├── quest_log: QuestHandler
  ├── remort: RemortHandler
  ├── aliases: AliasHandler
  └── at_death() → ghost state + XP penalty

NPC(DefaultCharacter, LivingMixin)
  ├── behaviors: BehaviorHandler (spec_fun + MobProg)
  ├── shop: Optional[ShopHandler]
  ├── prototype_vnum
  └── at_death() → corpse + loot generation, no ghost state
```

**IS_NPC() decomposition rule:** If behavior is mechanically identical for PC and
NPC, it lives on `LivingMixin`. If behavior differs, it's a polymorphic method
on the specific typeclass. Combat participation, stat computation, affect
application, equipment interaction, and damage pipeline are all on the mixin.

**Settled:** Round 2 (unanimous).

### 3.2 Object Strategy

**Decision:** Single `GameItem(DefaultObject)` typeclass with `item_type` enum
and type-specific handler/payload data. No separate typeclasses per item kind.

Rationale: matches legacy unified Object model, avoids typeclass swapping for
items that change type at runtime, reduces class sprawl.

```
GameItem(DefaultObject)
  ├── item_type: ItemType (weapon, armor, container, food, etc.)
  ├── item_data: ItemDataHandler (type-polymorphic values)
  └── item_affects: ItemAffectHandler (stat modifiers when worn/wielded)
```

**Settled:** Round 2 (unanimous).

### 3.3 Room and Exit Strategy

**Decision:** Standard subclasses with minimal extensions.

```
GameRoom(DefaultRoom)
  ├── sector_type, room_flags (Attributes)
  └── room_affects: RoomAffectHandler

GameExit(DefaultExit)
  ├── lock_state, hidden, key_vnum (Attributes)
  └── Standard Evennia lock system for access control
```

**Settled:** Round 2 (unanimous).

### 3.4 Messaging Layer

**Decision:** Custom `game_act()` function with legacy token vocabulary. Not
FuncParser-based. One call per audience mode; function handles token substitution,
visibility filtering, and recipient routing internally.

**Function signature (locked):** Flat positional core.

```python
class Audience(IntFlag):
    TO_CHAR    = 1   # actor only
    TO_VICT    = 2   # target only
    TO_ROOM    = 4   # all in room except actor (target receives)
    TO_NOTVICT = 8   # all in room except actor and target
    TO_ALL     = 15  # everyone in room

def game_act(
    format_str: str,
    actor: "LivingMixin",
    target: "LivingMixin | None" = None,
    obj: "GameItem | None" = None,
    obj2: "GameItem | None" = None,
    text: str | None = None,
    audience: Audience = Audience.TO_ROOM,
) -> None:
```

**Signature rationale:** `game_act()` will have 500+ call sites. A dataclass
wrapper (`ActContext`) adds construction overhead at every site with no benefit
for the dominant single-audience-per-call pattern. Positional args match the
legacy `act()` shape, easing porting. Type annotations (`LivingMixin` vs
`GameItem`) catch argument-order mistakes at static analysis time.

**Parameter notes:**
- `target` (not `victim`) — semantically accurate for non-combat uses too.
- `text` — for `$t` token (literal string, no visibility check). Covers cases
  like "Warrior leaves $t." where `$t` = "north".
- `obj2` — for `$P` token (second object). Rare but needed for some legacy
  patterns.

**Return value:** `None`. Callers never branch on recipient count.

**`origin` / `recipients` (deferred):** The room defaults to `actor.location` in
99%+ of cases. The ~10-20 cross-room messaging sites (adjacent room echoes, room
transitions) will use a separate helper (`game_act_to_room()`) or optional
keyword-only overrides when those call sites are encountered in Wave 3+. Snoop
forwarding and arena spectating are also deferred.

**Core tokens (Wave 1):**
- `$n`/`$N` — actor/target name (or "someone" if invisible)
- `$e`/`$E`, `$m`/`$M`, `$s`/`$S` — pronouns (subject/object/possessive)
- `$p`/`$P` — obj/obj2 short description (or "something" if invisible)
- `$t` — text (literal string, no visibility check)

**Audience modes:** `TO_CHAR`, `TO_VICT`, `TO_ROOM`, `TO_NOTVICT`, `TO_ALL`.
Legacy-accurate semantics: `TO_ROOM` includes the target; `TO_NOTVICT` excludes
both actor and target.

**Visibility:** Handled internally. `game_act()` checks `can_see(recipient, entity)`
per token per recipient. Invisible actors suppress room messages for non-detecting
observers (matching legacy behavior).

**Deferred:** Snoop forwarding, arena spectating, channel messaging. ANSI color
codes pass through as-is.

**Settled:** Round 2 (unanimous on concept and behavior), Round 3 (unanimous on
flat positional signature, return None, deferred origin/recipients). Minor
variations in naming (`victim`/`target`) and whether `origin`/`recipients` are
fully deferred vs keyword-only resolved in favor of deferral (majority).

### 3.5 Timing/Runtime Orchestration

**Decision:** Single global `RuntimeScheduler` as the **default design** — one
authoritative Script/service ticking at the legacy pulse quantum (~100ms).
Maintains a monotonic `pulse_count` and fires subsystem phases in fixed order at
their respective pulse multiples.

| Phase | Pulse multiple | Effective interval |
|-------|---------------|--------------------|
| Violence (combat) | 20 | 2.0s |
| Character update (regen, affects) | 40 | 4.0s |
| Object update (decay, timers) | varies | varies |
| Area reset check | ~1800 | ~3 min |
| Weather | varies | varies |

**Phase ordering per tick:** command flush → violence → character update → object
update → area check → weather → output flush. This matches the legacy
`game_loop_unix()` ordering exactly.

**Combat encounter handlers** own combatant membership and combat state, but are
*invoked by* the scheduler on violence ticks — they do not tick independently.

**Rationale (human decision):** A global scheduler is how the legacy system avoids
race conditions in multi-character operations. The classic MUD threading problem
("walking through a recently closed door" — two characters acting on the same
world state in the same tick must see consistent state) is solved by processing
all actions in a single deterministic pass. Independent per-character or
per-encounter timers reintroduce this class of race condition.

**Alternative under consideration: per-system schedulers with atomic DB
transactions.** Since Evennia operates on atomic database transactions, race
conditions in interaction systems (combat, area resets) could potentially be
solved without a global tick — as long as each system manages ordering
dependencies within its own transaction boundary. For example, a per-encounter
CombatHandler could resolve a full round atomically, and concurrent encounters
wouldn't conflict because they touch disjoint entity sets.

The open problem with this approach is **observer management**: each system-local
scheduler must know the complete set of entities that could observe or be affected
by its actions, and must prevent overlapping schedulers from producing inconsistent
state for shared observers (a character standing between two rooms with concurrent
encounters, area-wide effects, etc.). This is solvable but adds complexity that
the global scheduler avoids by construction.

**Status:** Global scheduler is the working assumption for spec writing. The
per-system alternative remains viable and should be evaluated during Wave 1
implementation if the global scheduler integrates poorly with Evennia's runtime.

**Round 3 analysis (all three agents reinforce global scheduler):** Key findings:

- Evennia's `at_repeat()` callbacks run in autocommit mode — each ORM write is
  its own transaction. Explicit `transaction.atomic` wrapping is possible but not
  default, and Evennia's in-memory Attribute cache does not roll back on
  transaction failure, risking memory/DB inconsistency on partial failures.
- The observer problem is not just shared mutable entities but **shared observers
  and shared transcripts** — output message ordering visible to players becomes
  non-deterministic with concurrent independent schedulers.
- Per-system scheduling is more idiomatic in Evennia (localized Scripts/handlers),
  but the ordering guarantee matters more than idiomatic purity for fidelity.
- Global scheduler risks are real but manageable: (1) developer confusion (Evennia
  docs teach per-object Scripts), (2) 100ms tick overhead (negligible for MUD
  scale), (3) restart/reload state reconstruction, (4) testability (phase
  entrypoints are independently testable; integration tests tick the scheduler).
- If the global scheduler proves impractical during Wave 1, per-encounter
  CombatHandlers remain a viable fallback for combat specifically, since combat
  encounters *are* mostly disjoint. But global scheduler should be the first
  implementation attempt because it solves ordering by construction.

**Settled:** Human decision (Round 2→3 interlude), with alternative noted. Round 3
analysis (unanimous) reinforces the global scheduler as the correct default.

### 3.6 Spell System Approach

**Decision:** Framework + pattern catalog + bespoke exception catalog.

1. **Casting pipeline spec** (one dossier) — mana cost, skill check,
   interruption, position, target parsing, verbal components, object casting.
2. **Spell-effect framework spec** (one dossier) — data-driven `SpellDefinition`
   entries for pattern-fitting spells. Pattern handlers: `spell_damage`,
   `spell_affect`, `spell_heal`, `spell_transport`, `spell_detect`.
3. **Data-driven spell catalog** (one dossier) — YAML/dict registry of the ~150
   pattern-fitting spells with their parameters.
4. **Bespoke spell specs** — grouped by category for the ~30-50 spells with
   genuinely unique mechanics.

**Use MCP V1 behavior slices** to cluster spells by call-graph shape before
writing specs. Expected pattern clusters: direct-damage (~40-50), affect
application (~40-50), healing (~15-20), transportation (~10-15), detection
(~10-15), bespoke (~30-50).

**Migration ordering:** Casting pipeline → spell-effect framework → data catalog
→ bespoke groups. Casting pipeline validated with one spell per target type.

**Settled:** Round 2 (unanimous).

### 3.7 Spec Granularity

**Decision:** Umbrella chunks split into implementation dossiers. Each dossier
maps to roughly one implementation PR. Dossiers emphasize data contracts: every
formula, constant, timing value, and output string must be explicit.

Combat dossier decomposition (example):
- Encounter lifecycle and timing
- Hit resolution pipeline
- Damage calculation
- Defensive checks
- Death/corpse processing
- Group assist/XP/loot split
- Flee/recall/escape
- Combat messaging

**Settled:** Round 1 (unanimous), confirmed Round 2.

---

## 4. Fidelity

### 4.1 Fidelity Definition

**Decision:** Player-visible parity within defined tolerances.

| Level | Requirement |
|-------|-------------|
| **Exact** | Output text/content, command syntax, timing intervals (gameplay-scale), formulas/caps/ordering where they affect outcomes, visibility/message routing |
| **Statistical** | RNG distributions, proc chances, loot table probabilities, repeated combat outcome distributions |
| **Tolerance** | Sub-tick scheduler noise, internal storage layout, exact RNG sequences |

**Settled:** Round 1 (unanimous), refined Round 2.

### 4.2 Verification Artifacts

**Decision:** Three artifact classes.

1. **Contract tests** — formulas, caps, ordering, target selection, state
   transitions, interface behavior. Derived from spec data contracts.
2. **Golden transcript tests** — command input → exact output text. Combat round
   messages, spell messaging, look/inventory formatting.
3. **Scenario/parity traces** — multi-step behavior logs from legacy (if the
   legacy server can be instrumented) or reconstructed from source analysis.

Each accepted spec deposits fidelity cases into a shared test suite. Auditor
checks for cross-spec contradictions.

**Settled:** Round 2 (unanimous).

### 4.3 Spec Data Contract Requirements

**Decision:** Every spec dossier must include:

- Exact formulas (not "matching the original")
- Timing constants with units
- Exact message strings/templates (with act() tokens)
- State reads and writes
- Preconditions and postconditions
- Ordering rules (what happens before what)
- Failure/edge cases (at least 3-5 per spec)
- Test cases

**Settled:** Round 1 (unanimous), confirmed Round 2.

---

## 5. Open Items (Not Yet Settled)

### ~~5.1 `game_act()` Function Signature~~ — RESOLVED

Moved to §3.4. Resolved Round 3 (unanimous on flat positional signature).

### ~~5.2 Timing/Runtime Orchestration Architecture~~ — RESOLVED

Moved to §3.5. Resolved by human decision (Round 2→3 interlude), reinforced by
Round 3 advisory analysis (unanimous).

### ~~5.3 Wave 1 Acceptance Criteria Detail~~ — RESOLVED

Moved to §2.3. Resolved Round 3 (unanimous on core, majority votes on edge
items).

---

## Appendix: Decision Provenance

| Decision | Round | Agreement |
|----------|-------|-----------|
| Hierarchical + iterative workflow | R1 | Unanimous |
| Infrastructure-first ordering | R1 | Unanimous |
| Seven infrastructure specs | R1 | Unanimous |
| Fidelity = player-visible parity | R1 | Unanimous |
| Data contracts over prose in specs | R1 | Unanimous |
| Umbrella chunks → implementation dossiers | R1 | Unanimous |
| Build `explore_entity` composite tool | R1 | Unanimous |
| Prioritize V3 earlier | R1 | Unanimous |
| Contract registry (YAML, versioned) | R2 | Unanimous |
| LivingMixin + PC/NPC split | R2 | Unanimous |
| Single GameItem typeclass | R2 | Unanimous |
| Custom `game_act()`, not FuncParser | R2 | Unanimous |
| Framework + catalog for spells | R2 | Unanimous |
| Stub rule (behavioral dependency test) | R2 | Claude+GPT; Gemini partially disagrees on data tables/lookup |
| Stat pipeline: implement first | R2 | Unanimous |
| Messaging: implement first | R2 | Unanimous |
| Timing: implement first | R2 | Unanimous |
| Timing architecture: global scheduler | R2→3 | **Human decision** — GPT's Design B closest |
| Timing advisory analysis | R3 | Unanimous — reinforces global scheduler |
| `game_act()` flat positional signature | R3 | Unanimous |
| `game_act()` returns None | R3 | Unanimous |
| `origin`/`recipients` deferred | R3 | Claude+Gemini (full defer); GPT (keyword-only); majority: defer |
| Wave 1 core scope (login→navigate→interact) | R3 | Unanimous |
| Wave 1: `wear/remove` deferred | R3 | Claude+GPT; Gemini in-scope |
| Wave 1: `score` in scope (simplified) | R3 | Claude+Gemini; GPT deferred |
| Wave 1: `say` in scope | R3 | Unanimous |
