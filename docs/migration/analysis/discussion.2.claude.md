# Round 2: Decisions and Contract Shapes

## Round 1 Consensus — Accepted

All eight consensus points are sound. No objections. Moving to decisions.

---

## Topic A: The Stubs Disagreement

### Decision

Use a **two-tier rule**: infrastructure whose API surface is deterministic and whose internal behavior is opaque to consumers is stub-safe. Infrastructure whose internal behavior leaks into downstream correctness requires a working implementation.

Concretely:

| Infrastructure Piece | Verdict | Reason |
|---|---|---|
| Data tables / registries | **Stub-safe** | The API is `get_skill_entry('fireball') → SkillRecord`. The record contents are fixed legacy data. A stub that returns hardcoded records is indistinguishable from a full registry. |
| Messaging layer (`game_act`) | **Stub-safe** | Consumers call `game_act(fmt, actor, obj, victim, audience)`. What matters to downstream specs is the function signature and the output contract, not internal formatting mechanics. A stub that formats strings and prints them validates the interface. |
| Entity lookup | **Stub-safe** | `find_target(searcher, argument, location) → Optional[Object]`. Downstream specs care about the return type and the "not found" behavior, not the matching algorithm internals. |
| Position system | **Stub-safe** | `check_position(character, min_position) → bool`. Trivially stubbable — it's a comparison. |
| **Stat computation pipeline** | **Must be implemented first** | Gemini is right, but for a more specific reason than "hot path." The problem is **behavioral dependency**: a combat spec agent writing the hit-roll formula needs to know what `get_effective_stat('dexterity')` actually returns for a character with base DEX 14, +2 from equipment, -3 from a blindness affect, +1 from remort. If the aggregation order matters (it does — equipment applies before affects in legacy, and some caps apply between layers), then the spec agent must be able to reason about the aggregation semantics, not just the return type. A stub that returns `int` tells the combat spec nothing about whether sanctuary halving happens inside or outside the stat pipeline. |
| **Timing / runtime orchestration** | **Must be implemented first** | The combat spec must know the tick cadence, the ordering guarantees, and the relationship between violence pulses and regen pulses. These are not API questions — they are behavioral constraints that shape every formula and timing constant in the combat spec. A stub that says "2-second tick" is meaningless without the ordering contract. |
| World lifecycle / resets | **Stub-safe for Phase C; must be implemented before Phase D NPC specs** | The first vertical slice (move/look/objects) doesn't need resets. Combat specs don't directly depend on resets. But NPC behavior specs and area-population specs do. |

### Rationale

A stub is risky when the downstream spec needs to reason about **what happens inside the box**, not just what comes out of it. The stat pipeline and timing system are the two cases where internals leak: the stat pipeline because aggregation order affects outcomes, and timing because ordering guarantees shape combat formulas. Everything else is safely opaque — downstream specs only need the contract surface.

### Risk

The stat pipeline implementation may reveal aggregation edge cases (cap application order, negative modifier handling) that force revision of the combat spec even if the API doesn't change. Mitigation: the stat pipeline spec must document aggregation order explicitly, and the combat spec must cite which aggregation assumptions it depends on. If those assumptions change, the traceability link triggers revision.

---

## Topic B: Timing Orchestration

### Decision

**Per-encounter CombatHandler Script for combat; per-character Script for non-combat periodic effects; per-area Script for resets. No global tick.**

Here is the design:

**Combat timing.** When combat starts in a room, a `CombatHandler` Script is created for that encounter (or the existing one is joined). The CombatHandler ticks at 2-second intervals. Each tick, it resolves all combatants in a deterministic order: iterate combatants sorted by a stable key (e.g., database ID — the legacy system iterates `char_list` in insertion order, which is effectively arbitrary but deterministic). For each combatant, the handler calls: `resolve_attacks(combatant)` → `resolve_healing(combatant)` → `resolve_affect_ticks(combatant)`. This preserves the legacy invariant: within a single round, for a single character, damage resolves before healing resolves before affect expiry. The CombatHandler owns the round — individual characters do not tick independently during combat.

**Non-combat periodic effects.** Characters not in combat still need regen (4-second cycle), affect duration ticking, hunger/thirst updates. These are handled by a per-character `UpdateHandler` Script that ticks at 4-second intervals. When a character enters combat, their `UpdateHandler` pauses (or the CombatHandler subsumes its responsibilities at the 2-second cadence, checking for 4-second-multiple events). When combat ends, the `UpdateHandler` resumes.

**Area resets.** A per-area `ResetHandler` Script ticks at the area's reset interval (typically 3-15 minutes). It checks occupancy (players present, ignoring immortals) and area age. It runs independently of combat and character timing — there is no ordering dependency between resets and combat. In legacy, resets happen in the same tick loop but at a different pulse multiple, and combat that's mid-round doesn't interact with a concurrent reset. The Evennia async model preserves this independence naturally.

**Why per-encounter, not per-character, for combat.** A room with 10 NPCs fighting a player: per-character means 11 Scripts ticking at 2-second intervals, drifting out of phase, with no ordering guarantee between them. Character A's round resolving before character B's changes the player experience — in legacy, all violence for a round resolves in one pass, so you see "Goblin A hits you" and "Goblin B hits you" as one block of output, not staggered over 200ms of timer jitter. The per-encounter handler resolves everyone in one tick callback, producing one output block. This is both more faithful and more efficient.

**Why not global.** A global violence sweep iterating all characters every 2 seconds is the Diku antipattern that scales poorly in Evennia (iterating all DB-backed characters). Per-encounter scopes the sweep to active combat, which is typically a small number of encounters.

**Drift prevention.** Per-encounter handlers don't drift relative to each other within an encounter (one handler, one tick). Different encounters in different rooms may drift relative to each other — this is acceptable because legacy players in different rooms also don't observe each other's combat timing. The 2-second interval will have sub-second jitter from Twisted's reactor, but this is within the "operationally irrelevant tolerance" from the fidelity consensus.

### Contract shape

```python
class CombatHandler(DefaultScript):
    """Per-encounter combat coordinator. Created when combat starts in a location."""

    # Ticks every ROUND_DURATION seconds
    ROUND_DURATION = 2.0  # legacy PULSE_VIOLENCE equivalent

    def at_script_creation(self):
        self.db.combatants = {}  # {character: CombatState}
        self.key = "combat_handler"
        self.interval = self.ROUND_DURATION
        self.persistent = True

    def add_combatant(self, character, target):
        """Register a character in this encounter."""

    def remove_combatant(self, character):
        """Remove a character (fled, died, combat ended)."""

    def at_repeat(self):
        """One combat round. Resolves all combatants in deterministic order."""
        for combatant in self._sorted_combatants():
            if combatant is dead or not fighting:
                continue
            self._resolve_attacks(combatant)     # violence_update equivalent
            self._resolve_healing(combatant)      # char_update heal portion
            self._resolve_affect_ticks(combatant)  # affect duration decrement
        self._flush_round_output()  # batch output delivery
        self._cleanup_dead()

    def _sorted_combatants(self) -> list:
        """Deterministic iteration order. Sorted by dbref for stability."""

class CharacterUpdateHandler(DefaultScript):
    """Per-character non-combat periodic effects."""

    UPDATE_INTERVAL = 4.0  # legacy PULSE_TICK equivalent

    def at_repeat(self):
        """Regen, hunger/thirst, affect ticking when NOT in combat."""
        if self.obj.in_combat:
            return  # CombatHandler owns timing during combat
        self._resolve_healing(self.obj)
        self._resolve_affect_ticks(self.obj)
        self._resolve_condition_updates(self.obj)  # hunger, thirst
```

### Risk

The CombatHandler approach means all combatants in a room share one handler. Multi-room combat (pursuit, ranged attacks across rooms) doesn't fit cleanly. Mitigation: for initial implementation, combat is per-room as in legacy. If pursuit mechanics require cross-room combat later, the handler can be extended to span rooms, but this is an edge case that doesn't need to be solved in Wave 1.

---

## Topic C: Typeclass Strategy

### Decision

**Split PC/NPC with a shared `LivingMixin`. Single `GameItem` typeclass with type-specific handlers, not per-item-type typeclasses. Standard Room/Exit subclasses with minimal extensions.**

#### Character hierarchy

```python
class LivingMixin:
    """Shared behavior for all entities that can fight, have stats, carry items."""

    @lazy_property
    def stats(self) -> StatHandler:
        """Stat computation: base + equipment + affects + remort."""

    @lazy_property
    def affects(self) -> AffectHandler:
        """Active affects/buffs/debuffs."""

    @lazy_property
    def equipment(self) -> EquipmentHandler:
        """Equipment slots and worn items."""

    @lazy_property
    def skills(self) -> SkillHandler:
        """Skill/spell proficiency tracking."""

    @property
    def in_combat(self) -> bool: ...
    @property
    def position(self) -> Position: ...

    def take_damage(self, amount, damage_type, attacker) -> DamageResult: ...
    def heal(self, amount) -> int: ...
    def apply_affect(self, affect) -> bool: ...


class PlayerCharacter(LivingMixin, DefaultCharacter):
    """Player-controlled character."""

    @lazy_property
    def preferences(self) -> PreferenceHandler:
        """auto_loot, auto_gold, brief_mode, color settings, etc."""

    @lazy_property
    def quest_log(self) -> QuestHandler: ...
    @lazy_property
    def remort(self) -> RemortHandler: ...
    @lazy_property
    def aliases(self) -> AliasHandler: ...

    def at_death(self, killer):
        """Ghost state, XP penalty, corpse creation."""

    def at_login(self): ...
    def at_logout(self): ...


class NPC(LivingMixin, DefaultCharacter):
    """Non-player character."""

    @lazy_property
    def behaviors(self) -> BehaviorHandler:
        """spec_fun + MobProg trigger processing."""

    @lazy_property
    def shop(self) -> Optional[ShopHandler]: ...

    def at_death(self, killer):
        """Corpse creation, loot generation. No ghost state. Reset respawns."""

    @property
    def prototype_vnum(self) -> int: ...
```

#### The `IS_NPC()` decomposition

Each divergence maps to a specific location:

| Legacy `IS_NPC()` branch | Evennia location |
|---|---|
| Death → respawn vs. ghost state | `NPC.at_death()` vs. `PlayerCharacter.at_death()` |
| Has prototype vnum | `NPC.prototype_vnum` property |
| Has spec_fun / MobProg | `NPC.behaviors` handler (absent on PC) |
| Has player file / preferences | `PlayerCharacter.preferences` handler |
| Shop / healer services | `NPC.shop` handler (absent on PC) |
| Combat participation | `LivingMixin` — identical for both |
| Stat computation | `LivingMixin.stats` — identical pipeline, different modifier sources (NPC has no remort, PC has no prototype-level stats) |
| Equipment interaction | `LivingMixin.equipment` — identical |
| Affect application | `LivingMixin.affects` — identical |
| XP gain | `PlayerCharacter` only — NPCs don't gain XP |
| Skill practice/gain | `PlayerCharacter` only |

The rule: if both PC and NPC share the behavior, it goes on `LivingMixin`. If only one needs it, it goes on the specific typeclass. Combat, stats, affects, equipment, positioning, and damage are all on the mixin. Persistence preferences, progression, and remort are PC-only. Behaviors, shop, and prototype linkage are NPC-only.

#### Object strategy

**Single `GameItem(DefaultObject)` typeclass, with a `item_type` Attribute and type-specific handlers.**

Rationale: the legacy `Object` type is unified with a type-polymorphic value union. Creating separate typeclasses (`Weapon`, `Container`, `Food`, `Furniture`) for every item type means any item that changes type at runtime (a legacy pattern — some magic items change type on use) would need typeclass swapping, which is expensive in Evennia. A single typeclass with type-conditional behavior in handlers is simpler and matches the legacy model.

```python
class GameItem(DefaultObject):
    """All game items. Type-specific behavior delegated to handlers."""

    @lazy_property
    def item_data(self) -> ItemDataHandler:
        """Type-polymorphic values: weapon dice, container capacity,
        food nutrition, potion spells, etc. Reads item_type to determine
        which fields are valid."""

    @lazy_property
    def item_affects(self) -> ItemAffectHandler:
        """Stat modifiers applied when worn/wielded."""

    @property
    def item_type(self) -> ItemType: ...  # weapon, armor, container, etc.
```

#### Room and Exit strategy

Standard subclasses. Rooms need: sector type (for movement cost / skill modifiers), room flags (dark, no_mob, safe, etc.), room affects handler (darkness, silence). Exits need: lock state, hidden flag, key vnum. Nothing exotic.

```python
class GameRoom(DefaultRoom):
    @lazy_property
    def room_affects(self) -> RoomAffectHandler: ...
    # sector_type, room_flags stored as Attributes

class GameExit(DefaultExit):
    # lock_state, hidden, key_vnum stored as Attributes
    # Standard Evennia lock system handles access control
```

### Risk

The mixin approach requires discipline: every new system that touches characters must decide "is this LivingMixin, PC-only, or NPC-only?" If a developer puts PC-specific logic on the mixin, NPC behavior breaks silently. Mitigation: the auditor step catches this — any spec that adds behavior to LivingMixin must justify why NPCs also need it.

---

## Topic D: Messaging Layer Contract Shape

### Decision

A single `game_act()` function with a custom token formatter. Not FuncParser-based — the legacy token system is simpler and more efficient than FuncParser's callable syntax, and trying to map `$n` to `$You()` introduces translation complexity for no fidelity gain.

### Contract shape

```python
from enum import IntFlag
from typing import Optional
from evennia.objects.objects import DefaultObject, DefaultCharacter

class Audience(IntFlag):
    TO_CHAR  = 1   # actor only
    TO_VICT  = 2   # victim only
    TO_ROOM  = 4   # everyone in room except actor and victim
    TO_ALL   = 7   # everyone in room (TO_CHAR | TO_VICT | TO_ROOM)


def game_act(
    format_str: str,
    actor: DefaultCharacter,
    obj: Optional[DefaultObject] = None,
    victim: Optional[DefaultCharacter] = None,
    audience: Audience = Audience.TO_ROOM,
    obj2: Optional[DefaultObject] = None,
) -> None:
    """
    Format and deliver a context-sensitive message to one or more audiences.

    Token substitution (resolved per-recipient):
        $n  → actor's name (or "someone" if actor invisible to recipient)
        $N  → victim's name (or "someone" if victim invisible to recipient)
        $e  → actor's subject pronoun (he/she/it)
        $E  → victim's subject pronoun
        $m  → actor's object pronoun (him/her/it)
        $M  → victim's object pronoun
        $s  → actor's possessive pronoun (his/her/its)
        $S  → victim's possessive pronoun
        $p  → obj's short description (or "something" if invisible)
        $P  → obj2's short description (or "something" if invisible)

    Audience routing:
        TO_CHAR  → actor receives (with $n replaced by "you", verbs adjusted)
        TO_VICT  → victim receives (with $N replaced by "you")
        TO_ROOM  → all in actor's room except actor and victim
        TO_ALL   → all in actor's room

    Visibility filtering:
        For each recipient, each entity reference ($n, $N, $p, $P) is resolved
        with a visibility check: can_see(recipient, entity). If not visible,
        the name is replaced with "someone" / "something". If actor is invisible
        to a room recipient and the message is TO_ROOM, the message is
        **suppressed entirely** for that recipient (matching legacy act() behavior
        where invisible actors don't generate room messages for non-detecting
        observers).

    Returns: None. Messages are delivered via obj.msg() side effect.
    """
```

**Token resolution implementation approach:** A per-recipient string formatter. For each recipient in the audience, resolve all tokens against that recipient's visibility, then deliver via `recipient.msg()`. Not FuncParser — a simple `str.replace()` chain with per-token visibility checks. The actor-perspective version (TO_CHAR) replaces `$n` with "you" and adjusts verb conjugation via a helper (e.g., `$n hit$% $N` → "You hit the goblin" for actor, "The warrior hits the goblin" for room).

**Verb conjugation:** Add a `$%` token that appends "s" when the subject is third-person (room/victim perspective) and nothing when second-person (actor perspective). This handles the common pattern `$n hit$% $N` → "You hit..." / "Warrior hits..."

### What is deferred

| Feature | Status |
|---|---|
| Snoop forwarding | **Deferred.** Extension point: after delivering to all audiences, check if any recipient has an active snoop and forward. Added as a separate spec when admin tools are specced. |
| Arena spectating | **Deferred.** Same extension mechanism as snoop — additional recipient list. |
| ANSI color codes | **Included in minimal contract.** Color codes in format strings are passed through as-is. Evennia's client handles ANSI interpretation. The messaging layer doesn't strip or transform them. |
| Channel messaging | **Out of scope.** Channels use a different delivery path (Evennia's `ChannelHandler`), not `game_act()`. |

### Risk

The custom formatter diverges from Evennia's idiomatic `FuncParser` approach. Developers who know Evennia will expect `$You()` syntax and won't find it. Mitigation: document the design decision prominently. The migration goal is fidelity to legacy, not Evennia idiom purity. The custom formatter is simpler for the 500+ `act()` calls that will be ported.

---

## Topic E: Contract Registry Format

### Decision

A `contracts/` directory in the migration repository, one YAML file per infrastructure piece. Updated when a spec is **accepted** (not drafted). Versioned with monotonic integers. Downstream dependency tracking via explicit `depends_on_contract` fields in spec dossiers.

### Contract entry shape

```yaml
# contracts/stat_pipeline.yaml
contract_id: stat_pipeline
version: 1
status: accepted  # draft | accepted | revised
last_updated: 2026-03-18

summary: >
  Computes effective stat values for any LivingMixin entity by aggregating
  base stats, equipment modifiers, active affects, and remort bonuses.

methods:
  - name: get_effective_stat
    signature: "(stat_name: str) -> int"
    description: >
      Returns the current effective value of the named stat for this entity.
    preconditions:
      - stat_name is one of: str, int, wis, dex, con, cha, hitroll, damroll, ac, saves
    postconditions:
      - Return value reflects: base + equipment_modifiers + affect_modifiers + remort_modifiers
      - Each modifier layer is applied in order: base → equipment → affects → remort
      - Per-layer caps are applied after each addition (e.g., stat cannot exceed race_max + 4)
      - Return value is cached until invalidated
    aggregation_order: |
      1. base_stat (from level, race, class)
      2. + equipment apply values (sum of all worn item apply_stat modifiers)
      3. apply race_max cap
      4. + affect modifiers (sum of all active affect apply_stat modifiers)
      5. apply absolute cap (max 25 for primary stats)
      6. + remort permanent modifiers
      7. apply final cap
    notes: >
      Combat specs depend on this aggregation order. If the order changes,
      hit_resolution and damage_calculation specs must be revised.

  - name: invalidate_stat_cache
    signature: "() -> None"
    description: >
      Marks all cached effective stats as stale. Called by equipment handler
      on equip/remove, affect handler on apply/remove/expire, and admin set commands.

  - name: get_max_stat
    signature: "(stat_name: str) -> int"
    description: >
      Returns the maximum allowed value for the named stat, considering race and class.

depends_on:
  - contract_id: data_tables
    fields_used: [race_table.max_stats, class_table.stat_priorities]
  - contract_id: affect_system  # once it exists
    fields_used: [AffectHandler.get_modifiers_for_stat]

depended_on_by: []  # populated as downstream specs are accepted

changelog:
  - version: 1
    date: 2026-03-18
    change: Initial contract definition
```

### Lifecycle

1. **Planning agent** creates skeleton contracts for all seven infrastructure pieces — method signatures and behavioral summaries, no implementation detail.
2. **Infrastructure spec agents** fill in preconditions, postconditions, aggregation semantics, and edge-case behavior. Contract status moves to `accepted` when the infrastructure spec passes audit.
3. **Downstream spec agents** declare `depends_on_contract: stat_pipeline@v1` in their dossier header. The auditor checks that the spec's assumptions match the cited contract version.
4. **If a contract is revised** (version bumped), the `depended_on_by` list identifies which downstream specs need review. The auditor flags them. No automatic invalidation — human decides whether the change is compatible.

### Where it lives

```
migration/
  contracts/
    stat_pipeline.yaml
    messaging.yaml
    position_rules.yaml
    timing.yaml
    entity_lookup.yaml
    data_tables.yaml
    world_lifecycle.yaml
  specs/
    ...per-chunk dossiers...
  chunk_registry.json
```

### Risk

YAML contracts can become stale if the spec and implementation diverge. Mitigation: the auditor step explicitly checks contract-spec alignment, and the implementation agent must cite the contract version it implements against.

---

## Topic F: The 200-Spell Problem

### Decision

**Framework + catalog approach.** Define a data-driven spell-effect framework that handles the common patterns, then individually specify only the spells with genuinely unique mechanics. Use MCP server behavior slices to cluster spells by call-graph shape before writing anything.

### Approach

**Step 1: Cluster spells by behavioral pattern using V1 tools.**

Call `get_behavior_slice` for every `spell_*` entry point. Compare the call-graph shapes. The expected clusters (based on the legacy architecture doc's description of `magic.cc`):

| Pattern | Expected count | Signature |
|---|---|---|
| **Damage spell** — check saves → `damage()` → `act()` messages | ~40-50 | Call graph: spell → damage → act. Side effects: HP mutation, messaging. |
| **Affect spell** — check saves → `affect_to_char()` → `act()` messages | ~40-50 | Call graph: spell → affect_to_char → act. Side effects: affect application, messaging. |
| **Healing spell** — compute amount → modify HP → `act()` messages | ~15-20 | Call graph: spell → heal/gain_hit → act. No saves check. |
| **Transportation spell** — validate target → move character → `act()` messages | ~10-15 | Call graph: spell → char_from_room/char_to_room → act. |
| **Detection spell** — apply detection affect → `act()` messages | ~10-15 | Subset of affect spells, but simpler — no saves, no stacking complexity. |
| **Bespoke spells** — unique mechanics not fitting any pattern | ~30-50 | Unique call-graph shapes. Individually handled. |

**Step 2: Spec the casting pipeline separately from spell effects.**

The casting pipeline spec covers: mana cost deduction, skill check (success/failure), interruption from damage, position requirements, target parsing (self/char/obj/room/direction), verbal component display (garbled text for observers), object casting (scrolls/wands/staves/potions). This is one spec dossier, tested with a minimal set of spells (one per target type: one self-only, one offensive-character, one defensive-character, one object-target, one room-target).

**Step 3: Spec the spell-effect framework.**

Define a data-driven `SpellEffect` system:

```python
@dataclass
class SpellDefinition:
    key: str                    # "fireball"
    spell_fun: str              # "spell_damage" (pattern handler) or "spell_fireball" (custom)
    target_type: TargetType     # TAR_CHAR_OFFENSIVE, TAR_CHAR_DEFENSIVE, TAR_SELF, etc.
    min_position: Position      # POS_FIGHTING
    mana_cost: int              # or callable for level-scaled costs
    level_per_class: dict       # {"mage": 5, "cleric": -1, ...}  (-1 = unavailable)
    damage_noun: str            # "blast of fire"
    spell_group: str            # "offensive"

    # For data-driven patterns:
    damage_type: DamageType     # FIRE, COLD, LIGHTNING, etc.
    base_dice: str              # "6d8+10" or level-scaled formula
    apply_affect: Optional[AffectDefinition]  # for affect-applying spells
    save_effect: SaveEffect     # SAVE_HALF, SAVE_NEGATE, SAVE_NONE


# Pattern handlers:
def spell_damage(caster, victim, spell_def):
    """Generic damage spell. Handles: saves check, damage(), act() messages."""
    if saves_spell(victim, spell_def):
        damage_amount = roll_dice(spell_def.base_dice) // 2  # SAVE_HALF
    else:
        damage_amount = roll_dice(spell_def.base_dice)
    damage(caster, victim, damage_amount, spell_def.damage_type)
    # act() messages use damage_noun

def spell_affect(caster, victim, spell_def):
    """Generic affect spell. Handles: saves check, affect_to_char(), act() messages."""
    if saves_spell(victim, spell_def):
        return  # SAVE_NEGATE
    apply_affect(victim, spell_def.apply_affect)
```

**Step 4: Catalog the exceptions.**

Each bespoke spell gets an individual entry in the spec with its unique mechanics documented: `spell_teleport` (random room selection with safety checks), `spell_identify` (display item stats), `spell_enchant_weapon` (modify item values), `spell_gate` (summon mob), etc. These are individually coded Python functions, not data-driven. Expected count: 30-50.

### Migration ordering for spells

1. **Casting pipeline** spec (one dossier, Wave 4 — after combat/affects exist)
2. **Spell-effect framework** spec (one dossier, defines pattern handlers)
3. **Data-driven spell catalog** (one dossier — a YAML/dict registry of the ~150 pattern-fitting spells with their SpellDefinition data)
4. **Bespoke spell specs** (grouped by category — all transportation spells in one dossier, all detection spells in one, etc.)

### Risk

The pattern classification may be wrong. A spell that looks like a damage spell in the call graph may have subtle unique behavior (e.g., `spell_burning_hands` hits all enemies in the room, not just the target — a different targeting model under the same call-graph shape). Mitigation: the behavior slice shows side effects — "messaging to room" with multiple targets is a signal that the spell doesn't fit the single-target damage pattern. The spec agent should check target handling, not just the damage path.

---

## Topic G: What Does "Done" Look Like for Wave 1?

### Decision

Wave 1 has two phases: **infrastructure contracts** (spec + implementation + tests for all seven pieces) and **vertical slice validation** (a playable proof that the infrastructure works).

### Infrastructure deliverables

| Piece | Deliverable | Format |
|---|---|---|
| Data tables | Python module `world/data/tables.py` with `race_table`, `class_table`, `skill_table`, `spell_table`, `attack_table`, `item_type_table`, `flag_defs` as Python dicts. Importable, no DB dependency. | Module + tests |
| Messaging | `world/utils/messaging.py` with `game_act()` function. | Module + tests (test: format string + mock characters → expected output per audience) |
| Stat pipeline | `StatHandler` class on `LivingMixin`. | Handler + tests (test: set base stats + equip items + apply affects → verify `get_effective_stat` returns expected values with correct aggregation order) |
| Position system | `Position` enum + `check_position()` function + `at_pre_cmd` hook on character typeclass. | Enum + hook + tests |
| Entity lookup | `find_target()` adapter wrapping Evennia search with `2.sword` support, visibility filtering, partial matching. | Module + tests |
| Timing | `CombatHandler` Script + `CharacterUpdateHandler` Script. | Script classes + tests (test: add combatants, tick, verify ordering) |
| World lifecycle | `ResetHandler` Script + room/area creation utilities. Minimal: rooms exist, exits connect them, can traverse. Resets not needed for Wave 1 validation. | Script class + seed data loader |

### Vertical slice acceptance criteria

A player can perform this exact sequence and get correct output:

1. **Connect and log in.** See the login screen, authenticate, enter the game in a starting room.
2. **Look.** See the room name, description, exits, objects present, other characters. Formatted correctly with the messaging layer.
3. **Move.** `north` → arrive in new room → see new room description. `south` → return. Movement costs checked against sector type (if applicable). Position must be standing.
4. **Examine objects.** `look sword` → see object description, type, condition. Object is a `GameItem` with `item_data` handler.
5. **Pick up and drop.** `get sword` → sword moves to inventory. `inventory` → see sword listed. `drop sword` → sword on ground. Messaging: "You get a sword." / "Warrior gets a sword." to room.
6. **See other characters.** A second player (or a manually spawned test NPC) is in the room. `look` shows them. Messages from their actions are visible.
7. **Position enforcement.** `sleep` → `north` → "You can't do that while sleeping." `wake` → `north` → movement succeeds.
8. **Entity lookup.** Room has two swords. `get 2.sword` → picks up the second one. `get flaming` → partial match finds "flaming sword."

### What is explicitly out of scope for Wave 1

| Feature | Status |
|---|---|
| Combat | Out of scope. `kill goblin` → "That command is not available yet." (Command not in the Wave 1 CmdSet.) |
| Affects / buffs | Out of scope. The `AffectHandler` exists as a stub on `LivingMixin` (API defined, no affect ticking or application). |
| Spells / skills | Out of scope. No casting, no skill use. |
| NPC behavior | Out of scope. NPCs exist as placed entities but have no AI, no spec_fun, no MobProg. |
| Area resets | Out of scope. World is manually seeded. No automatic respawn. |
| Chat channels | Out of scope. `say` works (it's a simple `game_act` call), but no global channels. |
| Shops / economy | Out of scope. |
| Quests | Out of scope. |
| Character creation | **Deferred to a separate mini-spec.** For Wave 1 validation, characters are created via admin commands or a simplified flow. The full legacy character creation state machine (race, class, stat rolling, skill selection) is its own spec. |

### What signals Wave 1 is "done"

All eight acceptance criteria pass in a live Evennia instance. The seven infrastructure modules have passing test suites. The contract registry has accepted contracts for all seven pieces. A spec agent can begin writing the combat chunk dossier against the accepted contracts without needing any Wave 1 code changes.

### Risk

Wave 1 could take longer than expected if Evennia's built-in search/matching doesn't support the `2.sword` pattern and a custom implementation is needed. Mitigation: the entity lookup adapter spec should assess Evennia's native capabilities early and scope the custom work.