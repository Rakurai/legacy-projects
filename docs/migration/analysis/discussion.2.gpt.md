Accepted: I agree with the Round 1 consensus and treat it as settled. The remaining work is to lock the interfaces and sequencing around the unresolved decisions. The docs support doing that now: Phase 4a explicitly calls for target substrate decisions before chunk implementation, because otherwise early chunks will take incompatible shapes. 

## Topic A: The stubs disagreement

### Decision

Use **contract-first stubs** for most cross-system dependencies, but require **working implementations** for three infrastructure pieces before downstream game-system specs are written:

* **Must be implemented first**

  * stat computation pipeline
  * messaging layer
  * timing/runtime orchestration

* **Stub-safe**

  * entity lookup
  * position/state rules
  * world lifecycle/reset contract
  * registry/data-table access surfaces
  * affect-system external API surface, as long as combat is limited to consuming the frozen query interface and not specifying affect internals

### Rationale

There are three distinct stub risks:

1. **Contract instability risk**
   The API surface is likely to change once implemented.

2. **Behavioral dependency risk**
   Downstream specs need the actual behavior, not just the shape of the call.

3. **Discovery risk**
   Implementation work is likely to reveal hidden semantics that invalidate downstream specs.

The stat pipeline fails all three tests. The challenges doc is explicit that this is the hottest path in the game and that legacy relies on precomputed aggregates and cache invalidation semantics because stat queries happen repeatedly during combat. A naive “computed on access” abstraction is not equivalent enough to spec combat safely.

Combat does **not** need to know every internal detail of aggregation when consuming the stat pipeline, but the migration team does need a real implementation first because:

* combat fidelity depends on performance-sensitive repeated reads,
* equipment/affects/remort/admin overrides all participate,
* cache invalidation rules are part of the observable behavior under repeated state changes.

So the concrete resolution is:

* A combat spec may depend on `get_effective_stat("dex") -> int`.
* But that is only safe **after** the stat pipeline implementation and tests prove what counts as an effective stat, when recomputation happens, and what invalidates cache.

Messaging also requires implementation first because nearly every spec depends on exact player-visible output and recipient-class behavior, including visibility suppression and pronoun substitution. That is not just an API shape question.

Timing also requires implementation first because ordering is load-bearing. The docs are explicit that combat, regen, object timers, and area updates are phase-locked in legacy and Twisted gives no ordering guarantee across independent callbacks. 

### Contract shape

Use this rule:

```text
Stub-safe:
- Consumer only needs a stable method signature and return contract.
- Producer behavior is not timing-sensitive or hot-path sensitive.
- Hidden semantics are unlikely to change downstream formulas or output.

Must-implement-first:
- Consumer depends on exact ordering, caching, delivery semantics, or repeated-call behavior.
- Hidden semantics likely affect formulas, timing, or user-visible output.
```

Applied:

```text
Messaging: must implement first
Stat pipeline: must implement first
Timing runtime: must implement first

Position/state rules: stub-safe after contract freeze
Entity lookup: stub-safe after contract freeze
Reset/lifecycle: stub-safe for early non-reset systems; implement before NPC/world lifecycle specs
Affect external query API: stub-safe for early combat formula writing, but full affect semantics must be implemented before combat integration and magic specs are accepted
```

### Risks

The main risk is partial freeze drift: downstream specs start treating provisional contracts as final. Mitigation: mark contract entries with `status: provisional|accepted`, and do not allow downstream spec acceptance against provisional contracts for the three must-implement-first systems.

---

## Topic B: Timing orchestration — the actual decision

### Decision

Use a **single global phase-locked runtime scheduler** implemented as one authoritative repeating Script/service ticking every legacy pulse quantum. It maintains a monotonic `pulse_count` and executes subsystem phases in fixed order. Combat is coordinated by **per-encounter handlers**, but they do not own time. They are invoked by the global scheduler on violence ticks.

Do **not** use per-character Scripts as the authoritative combat clock.

### Rationale

The legacy behavior is a global pulse loop with fixed ordering and shared cadence. The challenges doc explicitly identifies phase locking as load-bearing and warns that independent timers in Evennia/Twisted do not preserve ordering.

Per-character Scripts drift. That changes the feel:

* character A resolves before B because of timer skew,
* simultaneous combat becomes serialized by timer accident,
* affect expiry and regen can desynchronize from violence resolution.

That is a real player-visible behavioral change. The docs call simultaneous multi-hit resolution and pulse cadence part of the game feel. 

Per-encounter handlers are still the right combat ownership model. The challenges doc already points to per-encounter combat handlers as the likely architecture. The fix is to separate **state ownership** from **time ownership**:

* encounter handlers own combatant membership and combat state,
* global scheduler owns cadence and ordering. 

Area reset remains per-area state, but its timer is evaluated by the same global scheduler so it stays phase-locked to the same clock.

### Contract shape

```python
# runtime/scheduler.py

class RuntimeScheduler:
    pulse_ms: int = 100
    pulse_count: int

    # fixed pulse divisors
    VIOLENCE_PULSE = 20      # 2.0s at 100ms
    REGEN_PULSE = 40         # 4.0s
    AREA_PULSE = 1800        # 180s, example if legacy-equivalent
    WEATHER_PULSE = ...
    OBJECT_PULSE = ...

    def at_repeat(self) -> None:
        self.pulse_count += 1
        self.run_command_flush_phase()
        self.run_violence_phase_if_due()
        self.run_character_update_phase_if_due()
        self.run_object_update_phase_if_due()
        self.run_area_update_phase_if_due()
        self.run_weather_phase_if_due()
        self.run_output_flush_phase()
```

```python
# combat/encounter.py

class CombatEncounterHandler:
    encounter_id: str
    combatants: list["LivingMixin"]

    def resolve_round(self, pulse_count: int) -> None:
        """
        Called only by RuntimeScheduler on violence pulses.
        Resolves one full round for all combatants in deterministic order.
        """
```

Deterministic round order:

```python
def resolve_round(self, pulse_count: int) -> None:
    ordered = self.get_round_order()  # stable, legacy-compatible ordering rule
    planned_actions = [self.plan_action(c) for c in ordered]
    for action in planned_actions:
        self.resolve_action(action)
    self.finalize_round()
```

Area reset:

```python
class AreaResetController:
    area_id: str
    age_pulses: int
    min_reset_pulses: int

    def on_area_phase(self, pulse_count: int) -> None:
        if self.should_attempt_reset():
            self.attempt_reset()
```

### Risks

The main risk is “global loop antipattern” creep. Mitigation:

* keep the global scheduler thin and phase-oriented,
* put rules in handlers/modules, not in the scheduler,
* scheduler only calls phase entrypoints.

The other risk is Evennia integration awkwardness. Mitigation:

* one Script/service owns time,
* domain objects still own behavior through handlers, which matches the Evennia handler model.

---

## Topic C: Typeclass strategy — the actual decision

### Decision

Use this hierarchy:

```python
class LivingMixin:
    # shared combat/stat/position/inventory-facing API

class PlayerCharacter(DefaultCharacter, LivingMixin):
    # account-facing, player file/preferences/aliases/social state

class NPC(DefaultCharacter, LivingMixin):
    # prototype/template id, shop/healer/spec_fun/mobprog state

class GameItem(DefaultObject):
    # common item API + typed handlers/enum-driven behavior

class GameRoom(DefaultRoom):
    # room flags, sector, reset hooks, visibility/rendering

class GameExit(DefaultExit):
    # exit flags, closed/locked/trapped/gate semantics
```

Do **not** preserve the unified legacy `Character` typeclass. Preserve the **shared logic surface** instead.

Use one common `LivingMixin` API for all symmetric mechanics, and route `IS_NPC()` divergences into polymorphic methods on `PlayerCharacter` and `NPC`.

### Rationale

The legacy code uses one character type with pervasive `IS_NPC()` checks. The migration challenges call that out as a cross-cutting problem that must be systematically decomposed. 

The mixin split is the cleanest target-side answer because:

* combat must be symmetric across PCs and NPCs,
* Evennia expects concrete typeclass subclasses for domain objects,
* the handler pattern is already the intended composition model.

That means `IS_NPC()` decomposition rule is:

* if behavior is mechanically identical, it stays in `LivingMixin` or shared handlers;
* if behavior differs by actor kind, call a polymorphic hook.

### Contract shape

```python
class LivingMixin:
    @lazy_property
    def stats(self) -> "StatHandler": ...
    @lazy_property
    def affects(self) -> "AffectHandler": ...
    @lazy_property
    def equipment(self) -> "EquipmentHandler": ...
    @lazy_property
    def combat(self) -> "CombatantState": ...
    @lazy_property
    def position(self) -> "PositionHandler": ...

    def is_npc(self) -> bool: ...
    def on_death(self, killer: "LivingMixin | None") -> None: ...
    def get_display_name_for_act(self, viewer) -> str: ...
    def can_use_aliases(self) -> bool: ...
    def get_spawn_identity(self) -> str | None: ...
```

```python
class PlayerCharacter(DefaultCharacter, LivingMixin):
    def is_npc(self) -> bool: return False
    def on_death(self, killer): ...
    def can_use_aliases(self) -> bool: return True
    def get_spawn_identity(self) -> None: return None

class NPC(DefaultCharacter, LivingMixin):
    def is_npc(self) -> bool: return True
    def on_death(self, killer): ...
    def can_use_aliases(self) -> bool: return False
    def get_spawn_identity(self) -> str: return self.db.prototype_key
```

Examples:

* NPC death → `NPC.on_death()`: corpse + reset-managed respawn semantics
* PC death → `PlayerCharacter.on_death()`: ghost state + XP penalty
* shop/healer/spec_fun/MobProg → NPC-specific handlers
* aliases/preferences → PlayerCharacter-specific handlers
* hit/damage pipeline → `LivingMixin` + shared rules modules

#### Object strategy

Use **one `GameItem` typeclass**, not a separate typeclass per item kind.

Store item kind as an enum/tag plus validated typed data payloads:

* weapon payload
* container payload
* drink container payload
* food payload
* wand/staff payload

```python
class GameItem(DefaultObject):
    item_type: ItemType
    @lazy_property
    def itemdata(self) -> "ItemDataHandler"
```

Why:

* the legacy model is one object class with type-dependent values,
* object interaction commands are already one large shared behavioral surface,
* separate typeclasses per item kind will cause class sprawl and make conversion/import harder. 

Use typed validators and helper accessors rather than raw `value[0..4]` semantics.

#### Room and Exit strategy

`GameRoom(DefaultRoom)` and `GameExit(DefaultExit)` are enough, but add:

* room flags / sector / light / heal-mana modifiers
* reset membership hooks
* display hooks for legacy formatting
* exit-state flags: closed, locked, hidden, pickproof, etc.

### Risks

The main risk is leaving `IS_NPC()` logic as ad hoc flag checks in shared code. Mitigation: ban new raw `is_npc()` branching in rules modules unless there is no better polymorphic hook.

For items, the risk is a monolithic `GameItem` becoming a new god object. Mitigation: push per-type behavior into typed payload helpers and rule modules, not giant `if item_type == ...` blocks.

---

## Topic D: Messaging layer contract shape

### Decision

Implement one authoritative `game_act()` function that handles legacy audience routing, visibility filtering, and token substitution. Do not make callers manually assemble three separate Evennia messages.

### Rationale

The legacy `act()` is one of the most pervasive contracts in the codebase. It owns token substitution, recipient routing, visibility checks, snoop forwarding, and arena spectating. The migration challenges explicitly say this needs a custom `act()`-equivalent on Evennia, and that one call in legacy often maps to multiple differently worded recipient messages.

So the correct boundary is:

* caller supplies one legacy-style template and context,
* `game_act()` produces per-recipient renderings and routing.

Do not use FuncParser as the primary contract surface. It is useful internally, but the spec and compatibility layer should preserve legacy token vocabulary. The docs note Evennia has analogous capabilities, but different recipient routing semantics.

### Contract shape

```python
from enum import Enum
from dataclasses import dataclass
from typing import Iterable

class AudienceMode(str, Enum):
    TO_CHAR = "to_char"
    TO_VICT = "to_vict"
    TO_ROOM = "to_room"
    TO_NOTVICT = "to_notvict"
    TO_ALL = "to_all"

@dataclass(frozen=True)
class ActContext:
    actor: "LivingMixin | None" = None
    target: "LivingMixin | None" = None
    obj1: "GameItem | None" = None
    obj2: "GameItem | None" = None
    text: str | None = None   # for $t-style secondary text/object

def game_act(
    template: str,
    *,
    ctx: ActContext,
    mode: AudienceMode,
    origin: "GameRoom | None" = None,
    recipients: Iterable["DefaultObject"] | None = None,
    msg_type: str = "action",
    allow_snoop: bool = False,
    allow_spectators: bool = False,
) -> int:
    """
    Render and deliver a legacy-compatible act() message.
    Returns number of recipients actually sent to.
    """
```

Token support in Wave 1 contract:

* `$n`, `$N`
* `$e/$E`, `$m/$M`, `$s/$S`
* `$p/$P`
* `$t` for secondary object/text

Per-recipient name resolution lives in helper functions:

```python
def resolve_act_name(subject, viewer) -> str: ...
def resolve_pronoun(subject, viewer, case: str) -> str: ...
def can_receive_act(viewer, ctx, msg_type: str) -> bool: ...
def render_act(template: str, viewer, ctx: ActContext) -> str: ...
```

Audience routing:

```python
def get_act_recipients(mode, ctx, origin, recipients=None) -> list:
    # TO_CHAR   -> actor only
    # TO_VICT   -> target only
    # TO_ROOM   -> room occupants except actor and target
    # TO_NOTVICT-> room occupants except actor and target
    # TO_ALL    -> actor + target + room occupants deduped
```

Visibility filtering:

* implemented inside `resolve_act_name()` and `can_receive_act()`
* bystander may see nothing
* victim may see “someone”
* actor still sees self as “you”

Deferred from minimal contract:

* snoop forwarding
* arena spectator injection
* channel messaging
* ANSI policy beyond preserving embedded codes already present in strings

### Risks

The biggest risk is under-modeling edge-case visibility and ending up with subtly wrong perspective text. Mitigation: golden transcript tests for actor/victim/bystander/invisible permutations.

---

## Topic E: Contract registry format

### Decision

Use a `contracts/` directory with **one file per infrastructure contract** plus one index file. Contracts are versioned independently and every spec records which contract version it was written against.

### Rationale

The planning/spec flow already assumes shared contracts and traceability. CG.md explicitly calls for stable identifiers and a traceability convention linking chunk, spec, implementation, and validation artifacts.

A single monolithic registry file will become noisy. One file per infrastructure piece is easier to diff, version, and invalidate downstream specs against.

### Contract shape

Example: `contracts/stat_pipeline.yaml`

```yaml
contract_id: INF-STAT-001
name: stat_pipeline
version: 1.0.0
status: accepted
owners:
  - planning-agent
  - human-review
chunk: attributes
depends_on:
  - INF-DATA-001
used_by:
  - combat
  - magic
  - skills_progression
  - affects
summary: >
  Effective-stat query surface for all character stat reads.

types:
  StatName:
    kind: enum
    values: [str, dex, int, wis, con, hp, mana, move, hitroll, damroll, ac]

apis:
  - name: get_effective_stat
    signature: get_effective_stat(stat: StatName) -> int
    preconditions:
      - owner is a LivingMixin
    postconditions:
      - returns fully aggregated effective value
      - does not mutate state
    behavioral_guarantees:
      - includes base + equipment + affects + remort + admin overrides
      - reads from cached aggregate when cache is valid
      - recomputes cache lazily on first read after invalidation

  - name: invalidate
    signature: invalidate(reason: str, fields: list[StatName] | null = null) -> None
    behavioral_guarantees:
      - marks aggregate cache dirty
      - next get_effective_stat recomputes affected values before returning

invalidation_sources:
  - equipment equip/remove
  - affect add/remove/expire
  - remort bonus change
  - admin set-stat
  - race/class recalculation

non_goals:
  - no direct exposure of affect list internals
  - no guarantee about internal storage layout

acceptance_tests:
  - id: INF-STAT-001-T1
    description: equipping item with +2 str changes get_effective_stat(str) by 2 after invalidation
  - id: INF-STAT-001-T2
    description: repeated reads without mutation do not change value
  - id: INF-STAT-001-T3
    description: affect expiry invalidates cache before next read

downstream_impact:
  revision_policy: minor
  breaking_change_requires:
    - combat
    - magic
    - skills_progression
```

Index file: `contracts/index.yaml`

```yaml
contracts:
  - INF-DATA-001
  - INF-MSG-001
  - INF-STAT-001
  - INF-POS-001
  - INF-LOOKUP-001
  - INF-RUNTIME-001
  - INF-RESET-001
```

Update policy:

* planning agent creates skeleton
* spec agents may propose edits
* auditor validates impact
* contract becomes `accepted` only after review
* accepted contracts are the only ones implementation and downstream spec approval may target

Versioning:

* patch: clarification only
* minor: backward-compatible expansion
* major: breaking change

Every spec header includes:

```yaml
depends_on_contracts:
  - INF-STAT-001@1.0.0
  - INF-MSG-001@1.0.0
```

### Risks

The main risk is registry bureaucracy. Mitigation: keep entries short, machine-readable, and limited to shared interfaces only. Do not turn feature specs into contracts.

---

## Topic F: The 200-spell problem

### Decision

Use a **framework + pattern catalog + exception catalog** approach.

* One spec for the **casting pipeline**
* A small number of **spell family pattern specs**
* Individual dossiers only for genuinely bespoke spells or small bespoke clusters

Do **not** write 200 full bespoke specs unless evidence proves the patterns are too weak.

### Rationale

The docs say `magic.cc` is ~7,000 LOC with ~200 individually coded spells, but they also identify recognizable categories and a shared casting pipeline: offensive, defensive, healing, enhancement, transportation, detection, affliction, utility; plus shared concerns like mana cost, skill check, interruption, target parsing, and saves.

That means the right decomposition is:

1. common casting pipeline,
2. common effect families,
3. bespoke exceptions.

The MCP server is well positioned to help cluster spells because V1 behavior slices and call-graph shapes can expose repeated patterns. The roadmap and requirements already frame behavior slices as the way agents answer “what does this do?” and “what state does it touch?”.

### Contract shape

Initial spell dossier structure:

1. `MAG-CAST-001` — casting pipeline

   * mana cost
   * skill check
   * interruption
   * target parsing
   * position requirement
   * save/check entrypoints
   * spoken incantation display

2. Pattern dossiers

   * `MAG-PAT-ATTACK-001` — direct damage with save
   * `MAG-PAT-BUFF-001` — beneficial affect application
   * `MAG-PAT-DEBUFF-001` — hostile affect application
   * `MAG-PAT-HEAL-001` — healing/restoration
   * `MAG-PAT-TRANSPORT-001` — recall/gate/summon/teleport
   * `MAG-PAT-DETECT-001` — perception/vision/status senses
   * `MAG-PAT-OBJCAST-001` — wand/staff/scroll/potion wrappers

3. Exception catalog

   * one dossier per bespoke spell or tightly coupled mini-family

Spell catalog entry format:

```yaml
spell_id: fireball
pattern: MAG-PAT-ATTACK-001
exceptions:
  - custom_message_set
  - custom_damage_formula
depends_on_contracts:
  - INF-MSG-001@1.0.0
  - INF-STAT-001@1.0.0
  - MAG-CAST-001@1.0.0
```

Minimal spell set to validate casting pipeline:

* one direct-damage offensive spell
* one buff
* one debuff
* one heal
* one transport spell
* one detection spell
* one object-cast spell

### Risks

The main risk is over-abstracting and missing bespoke quirks. Mitigation: require clustering to be evidence-backed from behavior slices/call shapes, and automatically promote any outlier cluster into its own exception dossier.

---

## Topic G: What does “done” look like for Wave 1?

### Decision

Wave 1 is done when all seven infrastructure specs exist as:

* accepted contract entry,
* implementation skeleton or real module,
* tests proving the contract,
* enough integrated behavior to support the first thin vertical slice.

Wave 1 validation is **not** “all infrastructure implemented perfectly.” It is “the substrate is real enough to prove inspect/navigate/manipulate-object behavior without contract drift.”

### Rationale

CG.md already states that the first playable milestone is a thin vertical slice: room exists, can move, can look, can resolve targets, can pick up/drop basic objects, messaging roughly works. 

So Wave 1 acceptance should map directly to that slice.

### Contract shape

Deliverables per infrastructure piece:

#### 1. Data tables / registries

* Deliverable:

  * `world/data/*.py` or `world/rules/registry.py`
  * accepted contract `INF-DATA-001`
  * tests for lookup by stable string/enum id
* Must prove:

  * spell/skill/flag/type lookup works without integer-index assumptions

#### 2. Messaging layer

* Deliverable:

  * `world/output/act.py`
  * accepted contract `INF-MSG-001`
  * transcript tests for actor/victim/bystander visibility cases
* Must prove:

  * `$n/$N/$e/$m/$s/$p` rendering and audience routing

#### 3. Stat pipeline

* Deliverable:

  * `world/stats/handler.py`
  * accepted contract `INF-STAT-001`
  * cache invalidation tests
* Must prove:

  * effective stat reads and invalidation semantics

#### 4. Position/state rules

* Deliverable:

  * `world/state/position.py`
  * command precheck hook
  * accepted contract `INF-POS-001`
  * tests for min-position enforcement
* Must prove:

  * command gating by position

#### 5. Entity lookup

* Deliverable:

  * `world/lookup/search.py`
  * accepted contract `INF-LOOKUP-001`
  * tests for `2.sword`, partial matching, visibility filtering
* Must prove:

  * legacy target resolution semantics for early slices

#### 6. Timing/runtime

* Deliverable:

  * `world/runtime/scheduler.py`
  * accepted contract `INF-RUNTIME-001`
  * tests for deterministic phase order at shared pulses
* Must prove:

  * violence before character update before area phase on coincident ticks

#### 7. World lifecycle/reset

* Deliverable:

  * `world/resets/controller.py`
  * accepted contract `INF-RESET-001`
  * tests for age + occupancy reset eligibility
* Must prove:

  * reset logic surface exists, though full NPC/object reset behavior may remain deferred

### Wave 1 validation slice

Required player-visible actions:

* connect/log in to a test character
* exist in a room with exits and objects
* `look`
* `exits`
* move through exits
* see room name/description/contents after movement
* see other visible characters in room rendering
* target an object via lookup (`get sword`, `get 2.sword` if applicable in fixture)
* pick up and drop a basic item
* wear/remove one basic wearable item if equipment integration is already included in the object slice
* receive correct action messaging for room-visible object interaction

This is sufficient for Wave 1.

Explicitly out of scope:

* combat
* spells
* affects
* skill use
* NPC AI / MobProg
* reset-driven repopulation beyond infrastructure proof hooks
* channels / social systems beyond trivial local output
* corpse lifecycle
* economy / loot

If a player types `kill goblin` in Wave 1:

* command exists only as a stub or is absent,
* response should be a clear non-legacy temporary message in dev mode, not partial combat behavior.

### Risks

The main risk is calling the reset system “done” too early when only the contract exists. Mitigation: distinguish `Wave1-contract-complete` from `Wave3-world-lifecycle-complete`.

---

## Bottom line

The main Round 2 commitments are:

* **Stat pipeline, messaging, and timing are not stub-safe. Build them first.**
* **Use one global phase-locked scheduler as the game clock; encounter handlers own combat state, not time.**
* **Use `LivingMixin + PlayerCharacter/NPC` polymorphism.**
* **Use one `GameItem` typeclass with typed payloads, not one class per item kind.**
* **Implement one authoritative `game_act()` compatibility layer.**
* **Store contracts as versioned files in `contracts/`, and make specs depend on explicit contract versions.**
* **Handle magic as framework + patterns + exceptions, not 200 bespoke dossiers.**
* **Wave 1 is done when the seven infrastructure contracts are real, tested, and sufficient to prove a thin inspect/navigate/object slice.**
