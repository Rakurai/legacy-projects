# Legacy MUD — System Architecture Reference

A consolidated reference for the original C++ MUD codebase (~90 KLOC), combining
architectural overview, subsystem boundaries, dependency chains, and key
implementation details. Intended as the primary context document for migration
planning discussions — a reader should be able to reason about migration ordering
and integration surfaces without needing the raw component docs or MCP server.

> **Sources:** `og-legacy-overview.md` (C++ repo CLAUDE.md), `docs/subsystems.md`
> (subsystem boundary definitions), `artifacts/components/*.md` (24 curated
> component docs with AI-generated implementation analysis).

---

## Build & Runtime

| Item | Detail |
|------|--------|
| Language | C++14 (`-std=c++14`) |
| Build | `cd src && make legacy` |
| Tests | `cd test && make run` (Boost.Test) |
| Run | `./startup [port]` (default 3000, auto-restart, logs to `log/`) |
| Dependencies | SQLite3, libpng16, Boost.Test |
| Defines | `-Dunix -DSQL -DDEBUG -DIPV6` |

---

## Architectural Patterns

These patterns pervade the codebase and affect nearly every migration decision.

### Single-threaded global tick loop

The server runs one thread. `game_loop_unix()` in `comm.cc` cycles:
sleep → read input → dispatch commands → violence_update → healing/regen →
area/room updates → object/character updates → weather → time → write output.
Every subsystem is called at its own pulse interval within this loop. There is no
concurrency, no async I/O, and no event queue driving execution — ordering is
implicit in code position.

### Prototype→Instance entity model

All world content uses a two-tier pattern: `MobilePrototype` → `Character`,
`ObjectPrototype` → `Object`, `RoomPrototype` → `Room`. Prototypes are loaded
from area files at boot; instances are created on area resets. Instances carry
mutable state; prototypes hold the static template. This maps roughly to
Evennia's typeclass + prototype system but with fundamentally different lifecycle
semantics (ephemeral instances vs. persistent DB objects).

### Ephemeral world with area resets

NPCs, objects, and door states are recreated on a timer. When an area's age
exceeds its reset interval (and no players are present, ignoring immortals), it
repopulates from reset instructions. Ground items vanish. The world has no
persistent spatial state beyond what resets recreate. This is the sharpest
divergence from Evennia's persistent-DB model.

### Custom string type and flag system

`String` — a copy-on-write class where `nullptr ≠ ""` — is the string type
everywhere. `Flags` uses bitfield positions (A-Z, a-z, 0-9) for all boolean
state: act flags, affect flags, room flags, item flags. Both must be mapped to
Python equivalents early in migration.

### Static lookup tables as configuration

Races, classes, skills, spells, attack types, item types, weapon types, flag
definitions, loot tables, and name syllables are all defined in `const.cc`,
`tables.cc`, and `merc.hh` as C arrays. In Evennia these become data files,
database records, or Python dictionaries — but they parameterize *everything*.

### Pooled memory with deferred deletion

`Pooled<T>` provides object pooling for hot types (Character, Descriptor,
Object). `Garbage` base class + `GarbageCollectingList<T>` enable deferred
deletion so entities can be safely removed during iteration. Not needed in
Python, but the *reason* it exists (mid-iteration removal) still needs handling.

### `act()` message dispatch

The universal output function. Takes a format string with context-sensitive
tokens (`$n`, `$N`, `$e`, `$m`, `$s`, `$p`), a recipient class (actor / victim /
bystanders / room / world), and performs visibility checks, pronoun substitution,
snoop forwarding, and arena spectating. Every piece of player-visible text flows
through this. Evennia's `msg()` plus `$funcparser` and `FuncParser` offer
analogous capability but with different recipient routing.

---

## System Inventory

Organized by architectural layer, from foundation to operations. Each entry
includes dependencies, key implementation details, and files that concentrate
complexity.

### Layer 1 — Infrastructure

#### Game Engine
> *kind: system / depends on: networking, utilities, memory_gc, persistence*
> *depended on by: combat, magic, affect_system, world_system, character_data, command_interpreter*

Coordinates the global game state and update cycle. Runs the main loop,
orchestrates subsystem updates in a fixed priority order each tick, manages
entity lifecycle, and implements the `act()` messaging system.

**Implementation details:**
- Pulse-based main loop with fixed-order subsystem calls per tick.
- Entity creation uses prototype pattern; extraction (destruction) uses the
  `Garbage` system for safe mid-iteration removal.
- Boot sequence: command table → area files → DB connection → socials/help/notes/shops → special systems, with data validation.
- Copyover-aware: state persistence before exit, restart preparation, crash recovery.

#### Networking
> *kind: system / depends on: utilities, memory_gc*
> *depended on by: command_interpreter, game_engine*

Manages all player connections — sockets, telnet negotiation, buffering, the
login/character-creation state machine, and copyover (hot-restart).

**Implementation details:**
- Polymorphic `conn::State` interface for the connection lifecycle (login → char
  select → playing → disconnect), with reentrant state processing.
- Full telnet WILL/WONT/DO/DONT negotiation, subnegotiation for NAWS/TTYPE/MCCP/MXP.
- Copyover serializes file descriptors + connection state, `exec()`s the new
  binary — players see a brief pause, not a disconnect.
- Non-blocking I/O with read/write buffers, command throttling, idle/AFK detection.
- **Key files:** `comm.cc` (940 LOC — socket/descriptor/main loop integration),
  `telnet.hh` (220 LOC), `vt100.hh` (180 LOC).

#### Command Interpreter
> *kind: system / depends on: character_data, networking*
> *depended on by: combat, magic, social_communication, economy, quests, admin_tools, builder_tools, mobprog_npc_ai*

Parses player input and routes to command handlers. Central interface between
players and the game world.

**Implementation details:**
- `cmd_table`: hundreds of `cmd_type` structs mapping names → `DO_FUN` function
  pointers, with position requirements and permission levels.
- Shortest-unique-prefix matching for command abbreviation.
- Alias system with `$1`..`$9` positional parameters and `$*` expansion
  (`alias.cc`, 190 LOC). Recursion protection.
- Runtime `Disabled` system toggles commands with reason tracking, persisted across restarts.
- Quote-aware tokenization, `number.name` format parsing, context-sensitive entity
  references in `argument.cc`.

#### Event Dispatcher
> *kind: support / depends on: (none) / depended on by: game_engine, combat*

Global publish-subscribe event system. Registration of typed handlers, dispatch
with contextual data, safe iteration during dispatch, priority ordering.
Lightweight — most inter-system communication still happens through direct
function calls in the tick loop rather than through events.

#### Utilities
> *kind: support / depends on: (none) / depended on by: everything*

Logging, `String` (copy-on-write, null-aware), `Flags` (bitfield A-Z/a-z/0-9),
`Format` (printf-style), argument parsing, entity lookup (name-based search with
visibility rules, partial matching, `2.sword` numbered targets), dice/RNG,
type info, file tail, ASCII/PNG image rendering.

#### Memory & GC
> *kind: support / depends on: (none) / depended on by: game_engine, character_data, object_system*

`Pooled<T>` for hot types, `Garbage` base class for mark-for-deletion, and
`GarbageCollectingList<T>` for safe iteration with deferred deletion. Not needed
in Python but the patterns it enables (mid-loop entity removal) still require
attention.

---

### Layer 2 — Data Model

#### Character Data
> *kind: system / depends on: world_system, object_system, affect_system*
> *depended on by: combat, magic, skills_progression, command_interpreter, quests, social_communication, persistence, admin_tools, builder_tools*

Foundation for all acting entities (PCs and NPCs). Defines core data structures,
attribute systems, and lifecycle management.

**Implementation details:**
- **Class hierarchy:** `Character` (unified PC/NPC base) → `Player` (persistent
  auth, preferences) + `MobilePrototype` (NPC template with descriptions, stats,
  shop capabilities, behavior programs) + `DepartedPlayer`.
- **Attribute system:** 6 core stats (STR/INT/WIS/DEX/CON/CHA), derived stats
  (HP/mana/move/hitroll/damroll/AC), capped per race+class. Temporary and
  permanent modification via affects, equipment, and admin commands.
- **Static data tables:** `race_table` (stats, size, vuln/res/imm, body form),
  `guild_table` (stat priorities, primary attribute, skill groups, titles by
  level+gender), random name syllables — all in `const.cc`/`tables.cc`/`merc.hh`.
- Equipment slots with layered items, group system for cooperative play,
  position state machine (standing/sitting/fighting/sleeping/stunned).
- **Key files:** `Character.cc` (285 LOC), `Player.cc`, `set-stat.cc` (2197 LOC),
  `act_info.cc` (5493 LOC — score, inventory, look).

#### Object System
> *kind: system / depends on: world_system, affect_system*
> *depended on by: combat, magic, economy, quests, character_data, persistence, admin_tools, builder_tools*

Manages all tangible items — weapons, armor, containers, furniture, keys, etc.
Prototype→Instance separation, with type-polymorphic value unions.

**Implementation details:**
- **Core entities:** `Object` (instance — weight, cost, condition, location,
  affects), `ObjectPrototype` (template — static properties), `ObjectValue`
  (type-polymorphic: weapon damage, container capacity, food poison status, etc.).
- **Enhancement systems:** `EQSocket` gem socketing with quality/type fields;
  Loot System V2 with template objects (vnums 24355–24379), weighted probability
  tables, random prefixes/suffixes.
- **Static data tables:** `attack_table`, `type_table`, `weapon_table` (weapon
  classes → skills/damage), flag definitions — all in `const.cc`.
- Object state persistence: `objstate.cc` (184 LOC) for ground objects surviving
  restarts; `storage.cc` (157 LOC) for bank-like player item storage.
- **Key files:** `Object.cc` (396 LOC), `act_obj.cc` (5383 LOC), `loot_tables.cc`
  (1317 LOC), `lootv2.cc` (556 LOC).

#### World System
> *kind: system / depends on: character_data, object_system, utilities*
> *depended on by: combat, magic, quests, mobprog_npc_ai, persistence, admin_tools, builder_tools, networking*

Core spatial environment — `Area` → `Room` (via `RoomPrototype`) with
`Exit`/`ExitPrototype` connections. Environmental conditions, time, weather,
world mapping, area resets, and coordinate systems.

**Implementation details:**
- **Spatial model:** `Area` (region with reset timers), `Room`/`RoomPrototype`
  (locations with characters, objects, exits, properties), `RoomID` (vnum +
  instance number), `Exit`/`ExitPrototype` (directional with locks/hidden/one-way).
- **Environmental:** `GameTime` (accelerated calendar, day/night/seasons),
  `Weather` (dynamic atmospheric pressure, seasonal variations, room-specific
  effects), `Sector` (terrain types → movement costs, skill modifiers).
- **Mapping:** `Worldmap` + `Coordinate` + `Region` + `Quadtree` spatial
  partitioning. ASCII map visualization with color-coded terrain.
- **Navigation:** BFS pathfinding for hunt/track, directional scan with distance
  degradation, movement cost by sector, door/swim/fly checks.
- **Area resets:** Timer-based respawning of mobiles/objects/doors,
  player-presence tracking (ignoring immortals) for reset decisions.

#### Data Tables
> *kind: pure data / depends on: utilities / depended on by: combat, magic, progression, object_system, admin*

All the static arrays that parameterize game mechanics: race definitions (stats,
size, vuln/res/imm), guild/class definitions (stat priorities, skill groups,
titles), skill & spell tables (level requirements per class, mana costs, target
types, function pointers), skill group tables, attack type tables, item type
tables, weapon type tables, flag definition tables, loot generation tables,
random name syllables.

In a rewrite these become externalized configuration — data files, DB records, or
Python dictionaries. They must be migrated early because nearly every system
reads from them.

---

### Layer 3 — Game Mechanics

#### Affect System
> *kind: system / depends on: character_data, object_system*
> *depended on by: combat, magic, skills_progression, world_system*

Status effects modifying characters, objects, and rooms. The primary mechanism
through which spells, skills, and environmental conditions alter game entities.

**Implementation details:**
- **Affect structure:** Type, duration, modifier value, modifier target
  (stat/skill/AC/hitroll/damroll/saves), bitvector flags (invisible, detect
  hidden, flying, etc.), apply/remove callbacks.
- **Three target types:** Character affects (temp stat mods, poison DOT,
  blindness, haste), Object affects (enchantments modifying wielder stats),
  Room affects (darkness, silence, with notifications).
- **Stacking rules:** Same-affect-twice → replace, extend duration, increase
  modifier, or reject (per affect type).
- **Performance caching:** Aggregate modifier values cached to avoid recomputing
  on every stat check (`affect_cache_array.cc`).
- **Modular layout:** `affect.cc` (core), `affect_char.cc`, `affect_obj.cc`,
  `affect_room.cc`, `affect_list.cc`, `affect_cache_array.cc`, `affect_table.cc`.

#### Combat
> *kind: system / depends on: character_data, affect_system, object_system, world_system*
> *depended on by: quests, clans_pvp, mobprog_npc_ai*

Resolves all violent conflict. Per-round attack cycle via
`violence_update()` → `multi_hit()` → `one_hit()` for primary/secondary/dual-wield
attacks. The highest-complexity system in the codebase.

**Implementation details:**
- **Hit pipeline:** `one_hit()` — weapon skill check → dexterity/level modifiers →
  dodge/parry/shield block defensive rolls → damage type vs. vuln/res.
- **Damage pipeline:** `damage()` — base weapon dice + damroll + skill proficiency +
  enhanced damage + crits → sanctuary halving → damage type modifiers → equipment
  degradation from elemental effects → death threshold → XP distribution.
- **Elemental cascading:** Fire/cold/acid/shock damage cascades to equipment and
  room contents via `effects.cc`. Items can be destroyed or degraded.
- **Death processing:** `raw_kill()` → corpse creation with victim inventory,
  ghost state for players, NPC loot generation, auto-loot/auto-gold/group split.
- **Escape:** Flee (directional), wimpy (auto-flee threshold), recall (temple).
- **Arena/Battle mode:** Special rules for organized combat events.
- **Key files:** `fight.cc` (core attack loop, hit/damage, death), `effects.cc`
  (elemental), `dispel.cc` (spell removal), `Battle.hh` (arena mode).

#### Magic
> *kind: system / depends on: character_data, affect_system, object_system, skills_progression*
> *depended on by: combat, mobprog_npc_ai*

Spell casting and the complete ~200-spell library. The largest single-file
system.

**Implementation details:**
- **~200 spells** across 8 categories: offensive, defensive, healing, enhancement,
  transportation, detection, affliction, utility.
- **Casting pipeline:** Mana cost → skill check → interruption from damage →
  position requirements → target parsing (self/character/object/room/direction).
- **Object casting:** Wands, staves, scrolls, potions, pills — items with spell
  charges that trigger spell effects on use.
- **Remort spells:** High-tier abilities (sheen, focus, paralyze) available only
  after prestige reincarnation.
- **Spell saves:** Level-based saving throw system for offensive spells.
- **Verbal components:** Spoken incantation display with garbled text for
  observers who don't know the spell.
- **Key files:** `magic.cc` (~7,000 LOC — all ~200 spells), `rmagic.cc`
  (remort spells).

#### Skills & Progression
> *kind: system / depends on: character_data, affect_system*
> *depended on by: combat, magic, quests*

Character advancement — skill practice at guild trainers, level advancement with
stat/HP/mana gains, remort prestige system with permanent bonuses, and the
skill/spell table registry.

**Implementation details:**
- Practice sessions at guild trainers; `gain` command for acquiring skill groups
  (bundled packages with per-class cost ratings).
- XP-based leveling with stat gains, HP/mana/move increases, practice/train
  awards, title changes per class.
- **Remort system:** Prestige reincarnation — restart with permanent stat
  modifiers (`raffects`) and extra-class skill slots for cross-class abilities.
- **Static tables:** `skill_table` (every skill/spell with level requirements per
  class, mana costs, target types, minimum positions, damage nouns, function
  pointers); `group_table` (skill bundles with per-class costs).
- **Key files:** `skills.cc` (1783 LOC), `remort.cc`, `set-stat.cc` (2197 LOC).

#### Loot Generation
> *kind: system / depends on: object_system, character_data*
> *depended on by: combat*

Procedural treasure generation using probability distributions, context-sensitive
item creation, tiered rarity system, and template objects (vnums 24355–24379)
with random prefixes/suffixes. Generates unique items like "Gleaming Sword of
the Bear."

---

### Layer 4 — Content Systems

#### MobProg & NPC AI
> *kind: system / depends on: character_data, world_system, command_interpreter*
> *depended on by: quests*

Scripting mechanisms for NPC behavior. Two distinct systems coexist.

**Implementation details:**
- **MobProg scripting:** Trigger-based programs embedded in mobile prototypes.
  Compact scripting language with IF-THEN-ELSE conditionals, variable
  substitution, comparison operators, and string matching.
- **Trigger types:** SPEECH (keyword/wildcard), GREET (room entry), FIGHT (combat
  round), DEATH, HITPRCNT (health threshold), ENTRY (NPC moves), BRIBE (gold
  given), GIVE (object given), RAND (random per tick), TIME (in-game hour), ACT
  (`act()` message seen).
- **`spec_fun` hardcoded behaviors:** C++ function pointer per prototype, fires
  each pulse — `spec_cast_mage`, `spec_breath_fire`, `spec_executioner`,
  `spec_thief`, `spec_guard`, `spec_fido`, `spec_janitor`, etc. Predates MobProg;
  both systems coexist on the same NPCs.
- **Mob commands:** NPC-only actions — mpecho, mptransfer, mpforce, mpjunk,
  mppurge, mpgoto, mpat, mpoload, mpmload, mpkill, mpasound
  (`mob_commands.cc`, 672 LOC).
- **Key files:** `mob_prog.cc` (1937 LOC — trigger processing, conditional eval),
  `special.cc` (spec_fun table lookup).

#### Help System
> *kind: system / depends on: command_interpreter, persistence*
> *depended on by: (terminal consumer)*

Searchable in-game documentation — keyword lookup with partial matching,
level-gated entries, categorized by topic, dynamic in-game editing.

#### Notes & Editor
> *kind: system / depends on: command_interpreter, character_data, persistence*
> *depended on by: help_system*

Line-based in-game text editor (`ed`-style) for descriptions, notes, and help
entries. Multiple themed note boards (general/ideas/changes/news/immortal/penalties)
with per-character read tracking, file-based persistence, level-gated access.

---

### Layer 5 — Player Features

#### Social & Communication
> *kind: system / depends on: character_data, command_interpreter, world_system*
> *depended on by: economy, clans_pvp*

All player-to-player and player-to-world communication.

- **Chat channels:** gossip, auction, music, Q&A, grats, flame, immtalk, wiznet,
  clantalk, grouptalk — each with toggle, color coding, history recall.
- **Direct messaging:** tell, reply, say, whisper, yell (area-wide).
- **~200 social actions:** predefined emotes (bow, grin, slap, hug) with
  contextual messages for no-target/self/character-target, usable in channels.
- **Ignore system:** per-player block lists, DB-persisted, applies to tells and
  channels.
- **Other:** music/jukebox system, marriage ceremony system, pose (custom title
  in room descriptions and who lists).

#### Economy
> *kind: system / depends on: character_data, object_system, command_interpreter, social_communication*
> *depended on by: quests*

Item exchange via auction, banking, shops, and dual currency.

- **Auction:** Multi-stage countdown with notifications, minimum bid increments,
  last-minute extensions, item/bid validation, dedicated auction channel.
- **Banking:** Deposit/withdraw/balance at banker NPCs, clan banking for
  organizational funds.
- **Dual currency:** Gold and silver with exchange rates; automatic handling in
  shops/auctions.
- **Shop system:** NPC merchants with buy/sell pricing (profit margins), item type
  restrictions, open/close hours, charisma-based haggling, inventory restocked
  via area resets.

#### Quests
> *kind: system / depends on: character_data, world_system, object_system, command_interpreter, mobprog_npc_ai*
> *depended on by: (terminal consumer)*

Automated and structured player objectives. Dynamic quest generation with varied
objectives (kill/retrieve/explore), difficulty scaling, quest points as
alternative currency, `QuestArea` regions, timed challenges with cooldowns.
Core implementation: `quest.cc` (1897 LOC), admin tools: `wiz_quest.cc`.

#### Clans & PvP
> *kind: system / depends on: character_data, world_system, combat, command_interpreter*
> *depended on by: (terminal consumer)*

Structured competition — clans (hierarchical organizations with ranks, territory,
resources), wars (`War.cc`, 1478 LOC — formal inter-clan warfare with kill
tracking, scoring, victory conditions), duels (challenge/accept protocol, arena
teleportation, wagering, spectators), PvP safeguards (safe rooms, level ranges,
consent).

---

### Layer 6 — Operations

#### Persistence
> *kind: system / depends on: character_data, object_system, world_system, utilities*
> *depended on by: game_engine, admin_tools*

Saves and loads all game data across server restarts via multiple storage
mechanisms.

**Implementation details:**
- **Dual storage:** SQLite (connection pooling, transactions, prepared statements,
  schema migration) alongside custom file-based formats (magic numbers, record
  delimitation, versioning, checksumming).
- **Character persistence:** Stats, equipment, inventory, quest progress,
  preferences, skill/spell mappings, metadata — serialized to/from player files.
- **World persistence:** Area file loading/processing, room state, door/exit
  states, reset instructions, instance management.
- **Object persistence:** `objstate.cc` (410 LOC) — ground items across restarts,
  container contents, quest item protection; `storage.cc` (280 LOC) — bank-like
  player item storage.
- **Configuration:** JSON parsing with schema validation, defaults, environment
  variable substitution, dynamic reloading (`load_config.cc`, 380 LOC).

#### Admin & Builder Tools
> *kind: system / depends on: character_data, object_system, world_system, persistence, command_interpreter*
> *depended on by: (terminal consumer)*

Comprehensive privileged command sets.

- **Admin commands:** freeze, noemote, noshout, ban, permit, stat (entity
  inspection), set (property modification), transfer/goto/at, restore/slay/purge,
  reboot/shutdown/copyover, wizlock, wiznet.
- **Builder tools (OLC):** oload (spawn objects), mload (spawn NPCs), addapply
  (add enchantments), exit auditing, area creation, prototype editing — all
  real-time without server restarts.
- **Security:** Site/character-based bans, permit exceptions, log monitoring with
  tail, trust delegation.
- Multi-tiered command architecture: Admin → Coder → Implementor levels.

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│                    Infrastructure                        │
│  Utilities    Memory & GC    Event Dispatcher            │
│       ↑           ↑               ↑                      │
│   Game Engine ← Networking ← Command Interpreter         │
│       ↑                                                  │
│   Data Tables                                            │
└──────┬───────────────────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────────────────┐
│                    Data Model                             │
│  Character Data ←→ Object System                          │
│       ↑                  ↑                                │
│  World System    Affect System                            │
└──────┬───────────────────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────────────────┐
│                  Game Mechanics                            │
│  Combat ←→ Magic                                          │
│    ↑          ↑                                           │
│  Skills & Progression    Loot Generation                  │
│    ↑                                                      │
│  MobProg & NPC AI                                         │
└──────┬───────────────────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────────────────┐
│                 Player Features                           │
│  Social & Communication    Economy    Quests              │
│  Clans & PvP               Help System                    │
│  Notes & Editor                                           │
└──────┬───────────────────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────────────────┐
│                    Operations                             │
│  Persistence              Admin & Builder Tools           │
└───────────────────────────────────────────────────────────┘
```

### Migration-critical dependency chains

These chains constrain migration ordering — each system requires its
dependencies to exist (at least as stubs) before it can be implemented.

1. **Utilities → Data Tables → Character Data → Combat → Death/Loot**
   The longest chain. You cannot test combat without character data, and
   character data needs the static tables for stat caps, race definitions, and
   class definitions.

2. **Affect System → Magic → Object Casting → Loot Enhancement**
   Spells are the primary *producer* of affects. Object casting (wands, scrolls)
   wraps spell effects. Loot uses enchantment affects for stat bonuses.

3. **World System → Area Resets → MobProg triggers**
   NPC behavior depends on the world existing. MobProg triggers fire on world
   events (room entry, time, speech). Area resets populate the world MobProgs
   operate in.

4. **Command Interpreter → Every player-facing system**
   All commands route through the interpreter. In Evennia this maps to `CmdSet` +
   `Command` classes — the *first* system that needs to work.

---

## Complexity Hotspots

Files and systems that concentrate the most behavioral complexity, and therefore
represent the highest migration risk.

| File | LOC | System | Why it's hard |
|------|-----|--------|---------------|
| `magic.cc` | ~7,000 | Magic | ~200 individually-coded spells with unique targeting, effects, and edge cases |
| `act_info.cc` | 5,493 | Character Data | score, inventory, look, who — complex display formatting with stat calculations |
| `act_obj.cc` | 5,383 | Object System | All object interaction commands (get, put, wear, remove, eat, drink, etc.) |
| `set-stat.cc` | 2,197 | Character Data | `set` admin command — touches *every* modifiable field on characters, objects, rooms |
| `mob_prog.cc` | 1,937 | MobProg | Trigger processing engine, conditional evaluator, script execution |
| `quest.cc` | 1,897 | Quests | Quest generation, tracking, completion — integrates combat, world, objects |
| `skills.cc` | 1,783 | Progression | Skill use resolution, practice, gain — touches combat, magic, and data tables |
| `War.cc` | 1,478 | Clans & PvP | Inter-clan warfare — scoring, kill tracking, victory conditions, event history |
| `loot_tables.cc` | 1,317 | Loot | Probability tables, affix generation, template objects — complex data-driven logic |
| `fight.cc` | ~1,200 | Combat | Core attack loop, hit/damage resolution, death processing |

---

## Cross-cutting Concerns for Migration

### The `act()` problem

Every piece of player-visible output uses `act()`. It combines message formatting,
recipient routing, visibility filtering, pronoun substitution, snoop forwarding,
and arena spectating in a single function. Evennia's `msg()` handles delivery but
not token substitution; `$funcparser` handles inline functions but not recipient
classes. A faithful reproduction likely needs a custom `act()`-equivalent that
wraps Evennia's messaging, implemented as shared infrastructure before any
system that produces output.

### The tick timing problem

Legacy uses pulse-based timing (typically 4 pulses/second, combat round = 3
seconds, area reset = minutes). Systems are called in a specific order each
pulse. Evennia is event-driven — there is no central tick. The migration must
decide: (a) implement a single ticker that calls subsystems in order (faithful
but fights Evennia's design), or (b) convert each subsystem to independent
`TickerHandler`/`delay()` callbacks (idiomatic but risks subtle timing
differences). Combat round timing and area reset timing are the most
player-visible aspects.

### The persistence inversion

Legacy: world is ephemeral, characters are persistent (saved to files).
Evennia: everything is persistent (saved to DB). The migration must either:
(a) replicate ephemeral semantics on top of persistence (create/destroy DB
objects on resets — wasteful but faithful), or (b) make resets modify existing
DB objects (efficient but changes the model). NPC death + respawn and object
decay + respawn are the core cases.

### The unified Character type

Legacy uses one `Character` class for both PCs and NPCs, distinguished by flags
and the presence/absence of a `Player` sub-object. Evennia typically uses
separate `PlayerCharacter` and `NPC` typeclasses. The mapping must decide whether
to preserve the unified type (simpler migration, matches original patterns) or
split (cleaner Evennia code, harder to verify fidelity).

### The 200-spell catalog

Each spell in `magic.cc` is individually coded with unique targeting logic,
damage formulas, affect application, and special effects. There is no
spell-effect framework — each `spell_*` function is bespoke. Migrating these
requires either: (a) faithful per-spell translation (~200 Python functions), or
(b) abstracting common patterns into a framework and data-driving the catalog.
The MCP server's behavior-slice tools can analyze individual spells to support
either approach.

### The dual NPC behavior systems

`spec_fun` (hardcoded C++ functions) and MobProg (scripted triggers) coexist on
the same NPCs. Some NPCs have both. In Evennia these likely become
`Script`-based behaviors, but the migration must handle both systems and their
interaction. `spec_fun` behaviors are called once per pulse for every NPC that
has one — a performance consideration for large NPC populations.

---

## File Organization

The C++ source uses a mostly flat structure in `src/` with subdirectories for
specialized systems:

| Directory | Contents |
|-----------|----------|
| `src/` | Core files — `comm.cc` (entry), `Game.cc`, `fight.cc`, `magic.cc`, `interp.cc`, `act_*.cc`, `wiz_*.cc` |
| `src/affect/` | Affect/buff system modules |
| `src/conn/` | Connection state machine (login, char creation) |
| `src/event/` | Event dispatcher |
| `src/skill/` | Skill definitions and tables |
| `src/util/` | Utility classes (String, Flags, Format) |
| `src/worldmap/` | Overworld mapping with quadtree |
| `src/gem/` | Gem/item enhancement system |
| `src/JSON/` | JSON utilities (cJSON) |
| `src/include/` | Headers with matching subdirectories |
| `area/` | Area data files (custom text format) |
| `player/` | Per-character save files |
| `log/` | Server logs |
| `test/` | Boost.Test unit tests |
