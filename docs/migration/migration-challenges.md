# Migration Challenges: Legacy Mechanics on the Evennia Substrate

> **Purpose:** Identify the hard engineering problems in faithfully recreating the
> legacy MUD on Evennia — places where the original design assumptions and the
> target framework's assumptions collide, and where naive porting would introduce
> Diku antipatterns. This is a planning document for agents and developers.
>
> **Fidelity goal:** The reimagined game must be **indistinguishable from the
> original** in player-facing behavior — combat timing, output text layout,
> skill mechanics, spell effects, NPC behavior. The internal architecture will
> differ (clean Evennia patterns, not Diku internals), but what the player sees,
> feels, and experiences must match. A few systems warrant deliberate UX changes
> (login flow, character saving) and those are called out explicitly.
>
> **Out of scope:** Opportunities to redesign systems in ways that go beyond
> faithful recreation are tracked separately in
> [redesign-opportunities.md](redesign-opportunities.md) to avoid confusing
> fidelity goals with aspirational improvements.
>
> **See also:** [EVENNIA_MIGRATION.md](EVENNIA_MIGRATION.md) (concept mapping) ·
> [EVENNIA_MODEL.md](EVENNIA_MODEL.md) (Evennia architecture) ·
> [EVENNIA_CODING.md](EVENNIA_CODING.md) (coding guide) ·
> [doc_server_roadmap.md](doc_server_roadmap.md) (MCP server information layers)

---

## 1. The Core Tension

The legacy codebase is a Diku/ROM derivative: a single-threaded C++ server where
the world is ephemeral, state lives in memory, and a global tick loop drives
everything in lockstep. Evennia is a Django+Twisted Python framework where the
world is persistent in a database, state is transparently persisted, and behavior
is event-driven with no global tick.

These are not minor stylistic differences. They affect how every system is
designed. The challenge is: **reproduce the exact player-facing behavior of the
legacy game on a substrate that shares almost none of its architectural
assumptions, without importing the Diku internals that make the original hard
to maintain.**

The sections below describe specific collision points. For each, the question
is not "should we change this?" but "how do we make this feel identical to the
original on Evennia?" Where the answer requires creative engineering, the
challenge section explains why.

---

## 2. Timing Model: Global Tick vs. Event-Driven

### How the legacy system works

A single main loop runs every pulse (~100ms). Within each iteration, subsystems
execute in a fixed order: process input → dispatch commands → resolve combat →
update characters (regen, hunger, affects) → update objects (decay, timers) →
update areas (reset timers) → update weather → flush output. Different subsystems
fire at different pulse multiples (violence every 2 seconds, regen every 4
seconds, area resets every ~3 minutes), but they are all **phase-locked to the
same clock**.

This means all systems share an implicit contract: combat resolution happens
before healing, healing happens before area resets, and output is flushed after
everything has settled. The ordering is invisible but load-bearing.

### How Evennia works

There is no global tick. Each timed behavior is an independent `Script`, a
`TickerHandler` subscription, or a `utils.delay()` call. These fire asynchronously
via Twisted's reactor. There is no guaranteed execution order between independent
timers.

### The challenge

**Ordering dependencies become explicit design problems.** In the legacy system,
combat damage and healing never race because they run in the same loop iteration
in a fixed order. In Evennia, a combat Script and a healing Script are independent
timers. If they fire in the same reactor tick, their execution order is undefined.

This matters for gameplay correctness. Consider: a character at 10 HP is both
taking damage (50 HP) and regenerating (20 HP) this round. In legacy, the
resolution order is deterministic. In Evennia, it depends on which timer fires
first — or on whichever handler the reactor invokes in that cycle.

**Design questions:**

- Which subsystems actually need ordering guarantees to reproduce the legacy
  feel? Combat and healing obviously do. Do affect ticking and area resets?
- Should combat, healing, and affect ticking be handled by a single orchestrating
  Script per character (preserving deterministic ordering) or by independent
  handlers? The player-facing timing must match — the internal mechanism is
  flexible.
- The legacy violence pulse is ~2 seconds and regen is ~4 seconds. These
  intervals define the game's rhythm. How do we guarantee these exact cadences
  in Evennia's async model without drift?

---

## 3. World Persistence: Ephemeral vs. Permanent

### How the legacy system works

The world is defined in area files and rebuilt from them on every server boot.
NPCs and ground objects exist only in memory. When an NPC is killed, it is gone
until the area's reset timer fires and respawns it from the prototype definition.
When an item is dropped on the ground, it exists until the next reset or object
decay timer removes it. Player characters are the only entities saved to disk.

This model is simple and self-healing: no matter how much the world degrades
during play, a reset restores it to a known-good state.

### How Evennia works

Every object created is a database row that persists indefinitely. There are no
resets. If you create an NPC and it is killed, the NPC object persists in the
database (dead) until explicitly deleted. If items accumulate on the ground, they
persist forever unless cleaned up.

### The challenge

**The "self-healing world" must be explicitly engineered.** The legacy area reset
system is trivial in Diku (reset instructions specify "spawn mob X in room Y,
equip it with object Z") but has no Evennia equivalent. Reimplementing it requires:

- A zone-controller Script per area that periodically checks what should exist.
- Logic to decide: does the mob need respawning? Is the item still there or was
  it taken? Should the door be re-locked?
- Decisions about NPC lifecycle: when a mob is "killed", is the database object
  soft-deleted and respawned (reused), or is it hard-deleted and a new one
  spawned from the prototype? Soft-delete avoids DB churn but accumulates dead
  objects. Hard-delete keeps the DB clean but means constant create/delete cycles.

**Object lifecycle pollution** is the deepest risk. In the legacy system, a
mobmaker creates hundreds of NPCs at boot time and they exist only in memory — no
cost. In Evennia, creating hundreds of database objects at boot is a real load.
Destroying and recreating them on every reset is worse. The naive port creates
thousands of DB objects and then thrashes them on every reset cycle.

**Design questions:**

- What is the NPC lifecycle? Pool objects and respawn by resetting state?
  Soft-delete with a "dead" tag and respawn by clearing it? Hard-delete and
  re-spawn from prototype? The player must see the same behavior: mob dies,
  mob reappears after the reset interval.
- Ground items must decay and resets must repopulate, matching legacy timing.
  What is the lightest Evennia mechanism to achieve this without DB thrashing?
- Area resets in the legacy system fire based on area age and player presence
  (empty areas reset faster, areas with only immortals don't count as
  occupied). How do we reproduce these exact conditions?

---

## 4. Combat: Auto-Attack Loop vs. Action-Based

### How the legacy system works

Combat is an **automatic attack loop** driven by the global tick. Once a character
enters combat (`position = POS_FIGHTING`), every violence pulse (2 seconds) calls
`multi_hit()` which resolves primary attack, secondary attack, and dual-wield
without any player input. Players can issue commands *during* combat (cast a spell,
flee, use a skill), but doing nothing results in the character auto-attacking
indefinitely.

The damage pipeline is deep: hit roll → defensive checks (dodge, parry, shield
block) → base damage → weapon skill modifier → enhanced damage → critical hit →
sanctuary halving → vulnerability/resistance → damage type effects (elemental
cascading to equipment) → HP reduction → death check → corpse creation → XP
distribution → group auto-loot/gold split.

This pipeline is one of the densest codepaths in the legacy system. It touches
the combat system, the affect system, the object system (equipment damage), the
character data model, the group system, and the economy (gold/XP splitting).

### How Evennia approaches combat

Evennia provides no combat system. The EvAdventure tutorial demonstrates two
patterns: **twitch combat** (real-time auto-attack via Script timer, closest to
Diku) and **turn-based combat** (explicit per-turn action selection). Both use a
`CombatHandler` Script that manages combatant state.

### The challenge

**The auto-attack loop is the most recognizable Diku mechanic, and the one most
likely to introduce antipatterns if ported naively.** In the legacy system, combat
is a global sweep: `violence_update()` iterates every fighting character in the
game. Porting this as a global Script that walks all characters is both an
antipattern (global sweep instead of per-encounter handler) and a performance
concern (iterating all DB-backed characters every 2 seconds).

The Evennia-native approach is a **per-encounter CombatHandler Script**: when combat
starts, a Script is created (or fetched) for the encounter, combatants are
registered, and the Script ticks at round speed, calling resolution logic for each
participant. This is architecturally clean but represents a fundamentally different
model — combat state is per-encounter, not global.

**The damage pipeline itself** must be rebuilt as a rules module. The challenge is
decomposing a 500-line C++ function chain (`one_hit → damage → raw_kill`) into
clean Python: hit resolution, damage calculation, defensive checks, death
processing — each as a separate testable function. The cross-system coupling
(elemental cascading to equipment, group XP splitting, affect-based modifiers)
needs explicit dependency injection rather than the global variable access the
legacy code uses.

**Group combat** is an additional layer: the legacy system manages groups via a
linked-list leader/follower structure. Group assist, group XP split, and
auto-loot/auto-gold happen implicitly. In Evennia, groups must be an explicit data
structure (handler or Attribute on the leader) with logic to coordinate group-wide
combat events.

**Design questions:**

- The auto-attack loop defines the game's combat feel. How do we reproduce the
  exact 2-second violence pulse, simultaneous multi-hit resolution, and "do
  nothing and still fight" rhythm on Evennia without a global violence sweep?
  Per-encounter CombatHandler Scripts are the likely architecture, but they
  must tick at precisely the legacy cadence.
- Should combat handlers be per-room or per-encounter? Per-room is simpler
  but doesn't handle multi-room combat or pursuit. Per-encounter is more
  flexible but harder to manage.
- Death must create a corpse containing the victim's inventory, with the same
  ghost/penalty behavior for PCs and the same looting window for NPCs. In a
  persistent world, corpses need explicit decay timers. What is the lifecycle
  of a corpse object?
- The damage pipeline must be symmetric (NPC-on-player and player-on-NPC use
  the same rules, as in the legacy system). How do we decompose the 500-line
  C++ chain into testable Python modules while preserving identical outcomes?

---

## 5. The Affect System: Hot-Path Performance in a DB-Backed World

### How the legacy system works

Affects are in-memory structs with a pre-computed aggregate cache. When combat
code asks "what is this character's effective strength?", it reads a cached value
that was updated when affects were added/removed — no per-query computation, no
iteration over the affect list. This matters because stat queries happen dozens of
times per combat round (hit rolls, damage rolls, saving throws, defensive checks),
and the legacy system handles hundreds of NPCs in combat simultaneously.

### How Evennia stores state

Attributes are key-value pairs backed by the Django ORM. While Evennia caches
Attributes in memory per-object, the cost model is different: reading
`character.db.strength` is not the same as reading a C struct field. Complex
derived values (effective strength = base + equipment + affects + remort bonuses)
require aggregation.

### The challenge

**The stat computation hot path is the most performance-sensitive area of the
migration.** If every combat hit requires reading base stats, iterating equipment
modifiers, iterating active affects, and summing them — and this happens 4–6 times
per combatant per round, for potentially dozens of concurrent combatants — the
cost adds up.

Evennia's `contrib.rpg.traits` provides TraitHandler with static/counter/gauge
trait types, but it doesn't provide the aggregate caching that the legacy affect
system relies on. The handler pattern (`@lazy_property`) gives per-object handler
instances cached in memory, which helps, but the aggregation logic itself must be
efficient.

**Affect duration management** is a secondary challenge. Legacy affects decrement
their duration counter in the global `char_update()` sweep. In Evennia, each
affect needs a timer — either a per-affect `utils.delay`, a per-character Script
that ticks and checks all active affects, or an on-demand calculation ("this buff
was applied at time T with duration D; is it still active?").

The on-demand approach (store start time + duration, compute remaining on access)
avoids tick-based overhead entirely and maps well to Evennia's `OnDemandHandler`.
But it changes the gameplay semantics: legacy affects fire their removal callback
at the exact tick they expire, which can trigger gameplay events. On-demand
expiration delays those callbacks until something queries the affect state.

**Design questions:**

- Is a computed-on-access model (base + equipment + buffs, recalculated each
  query) fast enough for combat, or does the hot path require explicit caching
  with invalidation? The legacy system pre-computes aggregates for a reason.
- Affect durations must feel tick-based to the player ("this spell lasts 12
  ticks" is a visible game mechanic). The internal timer can be real-time, but
  the player-visible duration must match the legacy tick cadence. How do we
  reconcile Evennia timers with legacy tick-denominated durations?
- Can the Buffs contrib (`evennia.contrib.rpg.buffs`) serve as the foundation,
  or does the legacy affect system's complexity (stacking rules, object affects,
  room affects, bitvector flag manipulation) require a custom implementation?
- Should affects on objects and rooms use the same handler as character affects,
  or should they be separate systems?

---

## 6. Message Formatting: `act()` vs. `msg()`

### How the legacy system works

The `act()` function is the single most called function in the codebase. It
formats context-sensitive messages using token substitution:
- `$n` → actor's name (or "someone" if invisible to the viewer)
- `$N` → victim's name (same visibility logic)
- `$e/$E` → he/she/it pronoun for actor/victim
- `$m/$M` → him/her/it pronoun
- `$s/$S` → his/her/its pronoun
- `$p/$P` → object short description

It delivers different versions of the same message to three audiences
simultaneously: the actor, the victim, and bystanders who can see the action.
Visibility checks, snoop forwarding (admins monitoring a player), and arena
spectating are handled transparently.

For example, `act("$n hits $N with $p.", ch, weapon, victim, TO_ROOM)` produces:
- Actor sees: "You hit the goblin with a sword."
- Victim sees: "The warrior hits you with a sword."
- Bystander in the room sees: "The warrior hits the goblin with a sword."
- An invisible actor → bystanders see nothing; victim sees "Someone hits you..."

### How Evennia handles messaging

Evennia provides `obj.msg()` (send a string to a session), `obj.msg_contents()`
(send to everyone in the same location), and the `FuncParser` actor-stance system
(`$You()`, `$conj()`, `$pron()`) for perspective-aware formatting.

### The challenge

The Evennia `FuncParser` covers much of what `act()` does, but there is a
significant semantic gap:

**Visibility filtering** is built into the legacy `act()`. If the actor is
invisible and the bystander doesn't have detect-invisible, the bystander sees
nothing — the message is silently suppressed. In Evennia, this must be
implemented as a filter on `msg_contents()` or as a custom messaging layer that
checks visibility before delivering.

**Three-audience delivery** (actor, victim, bystanders) is a single `act()` call
in the legacy system. In Evennia, this typically requires two or three separate
`msg()` calls with different text. The `msg_contents()` method with mapping can
handle some of this, but the actor and victim often need completely different
message text (not just different perspective — different information).

**Snoop forwarding** (admin sees everything a snooped player sees) and **arena
spectating** (spectators see combat messages) are legacy features that inject
additional message recipients beyond the room. These need explicit recipient-list
management in Evennia.

**This matters because the agent writing specs for any player-facing feature will
encounter output messages.** Every combat action, spell effect, skill use, and
social interaction produces output through `act()`. The spec agent needs to know:
what does the player see? What does the victim see? What do bystanders see? And
the messaging layer must exist before any of those features can be implemented.

**Design questions:**

- The output text is part of the game's identity. The messaging layer must
  reproduce the exact text layout, pronoun substitution, and visibility
  filtering of `act()`. This almost certainly requires a project-specific
  messaging utility wrapping `msg_contents()`. How closely can FuncParser's
  actor-stance system serve as the foundation, and what must be built on top?
- Snoop forwarding and arena spectating must work as in the original. How
  should additional message recipients (beyond the room) be managed in Evennia?
- The messaging layer is a dependency of nearly every other system. It should
  be one of the first infrastructure pieces implemented. What is its minimal
  viable surface?

---

## 7. The Spell/Skill Catalog: 200+ Implementations

### How the legacy system works

~200 spells are implemented as individual C functions (`spell_fireball`,
`spell_cure_light`, `spell_teleport`, etc.) in a single 7,000-line file. Each
spell is registered in a static table with per-class level requirements, mana
costs, target types, and a function pointer. Casting dispatches through the table.

Skills use a similar table: each skill has a function pointer, level per class,
and proficiency tracking. Together, spells and skills constitute the largest body
of game-specific logic in the codebase.

### The challenge

**This is the volume problem.** The individual spell implementations are
straightforward to port — each is a self-contained function that checks saves,
applies damage or affects, and sends output. The challenge is doing this 200+
times without creating a giant unmaintainable module, and without losing the
data-driven properties of the original (level requirements, mana costs, target
types are data, not code).

**The spell registration table** needs a clean equivalent: a registry that maps
spell names to implementations, stores metadata (level requirements, mana costs,
target types), and supports runtime queries ("what spells can a level 10 mage
learn?"). In Evennia, this could be:
- A module-level dict of spell definition objects
- A database-backed registry (Django model or Attributes on a Global Script)
- A class-per-spell pattern with metadata as class attributes

**Object casting** (scrolls, wands, staves, potions, pills) stores spell
references on item objects. In the legacy system, this is an integer function
pointer index. In Evennia, items need to reference spells by name or registry
key, and the casting system needs to resolve that reference to the implementation.

**The remort system** allows characters to learn spells from other classes. This
means the per-class level requirement table is not just "what can you learn" but
"what can you learn now, including cross-class abilities from previous lives."

**Design questions:**

- What is the right decomposition for 200+ spell implementations? One file per
  spell category (offensive, defensive, transportation, etc.)? One class per
  spell? A data-driven approach where simple spells are table entries and only
  complex spells need custom code?
- Should the spell registry live in code (Python dicts/classes) or in the database
  (queryable, editable without code changes)? The legacy system uses code; a
  database approach enables runtime administration.
- Can the spell system be designed so that simple spells (deal X damage of type Y,
  apply affect Z for duration D) are purely data-driven, reducing the number of
  custom implementations needed?

---

## 8. NPC Behavior: Two Legacy Systems, Neither Maps Cleanly

### How the legacy system works

NPCs have two behavior systems:

1. **Special functions** (`spec_fun`): A C function pointer assigned to an NPC
   prototype. Called every mob-update tick. Examples: `spec_cast_mage` (cast
   offensive spells in combat), `spec_fido` (eat corpses), `spec_guard` (attack
   criminals), `spec_janitor` (pick up junk). 40–50 distinct spec functions cover
   the NPC behavior catalog.

2. **MobProg scripting**: A domain-specific language with triggers
   (speech/greet/fight/death/random/time) and conditional logic. Stored per-NPC
   in area files. More flexible than spec functions but limited to simple
   if/then/else logic with variable tracking.

### The challenge

Neither system maps cleanly to Evennia:

**Spec functions** are global-tick-driven (called every mob pulse for every NPC
that has one). In Evennia, the equivalent is either a per-NPC Script with
`at_repeat()`, an AI handler triggered by hooks, or a TickerHandler subscription.
The per-NPC Script approach is clean but expensive at scale (hundreds of NPCs =
hundreds of ticking Scripts). The TickerHandler approach batches tick processing
but loses per-NPC state management.

**MobProg scripting** requires a decision: port the MobProg interpreter to Python
(maintaining a DSL), or translate each MobProg script to native Python/Evennia
hook methods. Porting the interpreter preserves data-driven NPC behavior (builders
can write scripts without Python knowledge) but introduces a maintenance burden.
Translating to Python is cleaner but loses the data-driven property.

**The behavioral fidelity requirement** means legacy NPCs must act the same way:
aggro mobs attack on sight, sentinel mobs stay in place, spec functions fire
their effects on the same cadence. The player should not be able to tell the
difference.

**Design questions:**

- MobProg scripts define per-NPC behavior authored in area files. Should the
  reimplementation include a MobProg interpreter (preserving the data-driven
  authoring model) or translate each script to native Python hooks (cleaner
  but loses the data-driven property)? The player-facing behavior must match
  either way.
- How should NPC AI tick? Per-NPC Scripts, a batch processor, or hook-driven
  (only act when stimulated)? The legacy mob pulse fires every ~4 seconds for
  all active NPCs — the cadence must be reproduced.
- The legacy system has 40–50 distinct spec functions. What is the cleanest
  Evennia-native representation that preserves the exact behavior of each?
  Individual behavior classes, handler mixins, or a configurable behavior
  registry?
- How many NPCs will exist simultaneously? The legacy world has hundreds of
  active NPCs. This determines whether per-NPC Scripts are feasible or if a
  lighter-weight batch approach is needed.

---

## 9. Character Model: Unified Type vs. Account/Character Split

### How the legacy system works

`Character` is one type. A player IS their character — there is no Account
entity. Login authenticates a character name and password. There is no
multi-character support, no character selection screen, no out-of-character
identity. `IS_NPC(ch)` (checking a flag) distinguishes players from NPCs; they
share the same data structure.

### How Evennia works

Account and Character are separate. An Account (player identity) puppets a
Character (in-game avatar). Multi-character support, character selection, and
OOC commands are native. NPCs and PCs are typically separate Typeclasses.

### The challenge

**The Account/Character split is structural.** It affects where data lives
(player preferences on Account vs. character stats on Character), how login
works, how persistence works (Account persists even if Character is deleted), and
how multi-character features interact with game mechanics designed for one
character per player.

**The unified `Character` type** pervades the legacy codebase. Every system that
operates on characters uses `IS_NPC()` checks to branch between player and NPC
behavior. Porting requires either:
- A shared `LivingMixin` that provides common behavior (stats, affects, combat
  participation) to both `PlayerCharacter` and `NPC` typeclasses — clean but
  requires systematic decomposition of every `IS_NPC()` branch.
- A single Character typeclass with a flag — preserves the legacy structure but
  is a Diku antipattern that limits Evennia's flexibility.

**The position system** (`POS_STANDING`, `POS_FIGHTING`, `POS_SLEEPING`, etc.) is
deeply embedded in the legacy codebase. Nearly every command checks the
character's position before executing. In Evennia, position must be an explicit
Attribute or Tag, and every command must check it — or the position system must be
enforced at the CmdSet level (sleeping characters get a restricted CmdSet that
only includes `wake`).

**Design questions:**

- The legacy game is one-character-per-player. The reimagined game should
  preserve this model (Evennia `MULTISESSION_MODE=0` or `1`). Where do
  legacy "player preferences" (color settings, auto-loot, brief mode) live
  in the Account/Character split?
- The login process is one of the few systems where we can deliberately
  improve UX (the legacy flow is a rigid state machine with awkward prompts).
  How much freedom do we have here without breaking player expectations?
- Position enforcement (`POS_STANDING`, `POS_FIGHTING`, `POS_SLEEPING`) is
  checked on nearly every command. What is the cleanest Evennia mechanism —
  per-command checks, CmdSet swapping, or a pre-command hook — that
  reproduces the exact "You can't do that while sleeping" behavior?

---

## 10. Data Tables: Code vs. Configuration

### How the legacy system works

Race definitions (stats, abilities, size, vulnerabilities), class definitions
(stat priorities, skill groups, titles), attack types, item types, weapon types,
flag definitions — these are all **hardcoded C arrays** in `const.cc` and
`tables.cc`. They are compiled into the server binary. Changing a race's stat
bonuses requires recompiling.

### The challenge

In a Python/Evennia world, these tables can be either code (Python dicts/modules)
or configuration (database entries, YAML files, JSON). The choice affects who can
modify them and how changes are deployed.

**Code-based tables** are simple, version-controlled, testable, and performant.
They match the legacy pattern. But they require a developer to change.

**Database-backed tables** can be modified at runtime by builders or admin tools.
But they are harder to version-control, and every query is a DB hit (unless
explicitly cached).

**Hybrid approaches** (code defines defaults, database overrides take precedence)
add complexity but offer flexibility.

This is not an academic choice. The legacy game has ~15 races, ~6 classes, ~200
spells, ~100 skills, ~30 attack types, ~20 item types, and ~150 flag definitions.
The volume of data tables is large enough that the representation choice affects
development velocity and maintainability.

**Design questions:**

- The data values themselves are part of the fidelity target — a level 10 mage
  learns fireball at cost 15 mana, period. The representation (code vs. DB) is
  an engineering choice. Which tables should be code (version-controlled,
  performant) and which should be database-backed (runtime-editable)?
- Should the project use the Evennia Prototype system for entity templates, or a
  custom registry? Prototypes are familiar to Evennia developers but may not fit
  the legacy table structure (which mixes entity templates with rules metadata).

---

## 11. Dynamic Loot Generation

### How the legacy system works

A procedural item creation system using template objects (vnums 24355-24379),
random affixes (prefixes/suffixes from name tables), rarity tiers, and stat
rolls. Generates items with names like "Gleaming Sword of the Bear" with
randomized stat bonuses. The loot tables, modifier pools, and rarity weights are
defined in code and data arrays.

### The challenge

In Evennia, every generated item is a persistent database object. The legacy
system generates loot as ephemeral in-memory objects that exist until the next
area reset or until a player picks them up (and saves). In Evennia, generated
loot persists indefinitely.

**Object accumulation**: If the loot system generates items frequently and they
aren't cleaned up, the database grows without bound. Ground items from dead mobs,
uncollected loot from abandoned encounters — these persist.

**Template-based generation** maps well to Evennia Prototypes with callable values
(randomized stats). But the affix system (prefix/suffix name generation,
combinatorial stat modifiers) needs custom logic on top of the Prototype spawning
system.

**Design questions:**

- Generated items that aren't picked up must eventually vanish (matching legacy
  behavior where resets clean up ground objects). What is the decay mechanism
  for generated loot in a persistent world?
- Should loot be generated on mob death (matching legacy timing — the corpse
  immediately contains items) or lazily (generated when looted, reducing DB
  object creation for uncollected corpses)? Lazy generation changes the
  player-visible behavior slightly (you can't `look in corpse` and see items
  before looting) unless handled carefully.
- Can the Prototype system support the affix/randomization model, or does loot
  generation need a custom factory?

---

## 12. Cross-Cutting Concerns

Several challenges span multiple systems:

### State caching and performance

The legacy system caches aggressively: affect aggregates, stat lookups, and entity
lists are kept in memory. Evennia's Attribute system caches per-object in memory
but derived aggregates (effective AC, total hitroll) must be explicitly managed.
Systems that query derived stats frequently (combat, skill checks) need a caching
strategy.

### The `IS_NPC()` pervasion

Nearly every legacy function that operates on characters branches on `IS_NPC()`.
This must be systematically addressed: either decompose into Typeclass-specific
methods, use a shared mixin with polymorphic dispatch, or accept the flag-check
pattern. The choice cascades through every system.

### Equipment interaction with stats

Equipping/removing items modifies character stats through "apply" values. The
legacy system directly modifies character fields when equipment changes.
In Evennia, this should be computed on access (sum base + equipment + buffs) but
the equipment handler must participate in the stat computation pipeline. The
circular dependency (equipment handler needs to know which stat to modify; stat
computation needs to query equipment handler) requires careful interface design.

### String-to-effect mapping

Legacy objects store spell effects as integer function pointers (`value[3]` on a
potion is a `spell_sn` index). Skills store proficiency as an integer indexed by
skill number. These integer-based cross-references need a string-based or
enum-based equivalent that is robust to registry changes.

---

## 13. What This Means for the MCP Server

The doc server's information layers directly support navigating these challenges:

**V1 (Implementation)** answers "how does the legacy system actually implement
this?" — the specific code paths, function chains, global variable dependencies,
and side effects that a spec agent must understand.

**V2 (Conceptual)** answers "how does this feature fit into the broader system?"
— which subsystems it touches, what the dependency graph looks like, and what
narrative documentation exists.

**V3 (User-Facing)** will answer "what does the player expect to see?" — the
output messages, command syntax, and behavioral contracts that the reimplementation
must preserve even if the implementation changes completely.

**V4 (Builder's Guide)** will answer "what are the data-level rules?" — how area
files configure spells, mobs, objects, and resets, which constrains how the
reimagined data model must work.

A spec-creating agent working on any of the challenges described above will need
all four layers. Understanding `spell_fireball`'s implementation (V1) is not
enough — the agent also needs to know how fireball fits into the magic system
(V2), what the player sees when they cast it (V3), and how its damage dice are
configured in area files (V4).
