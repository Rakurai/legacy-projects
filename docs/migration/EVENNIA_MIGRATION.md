# EVENNIA_MIGRATION.md — Adapting Diku/ROM Concepts to Evennia

> **Purpose:** Guide developers and AI agents in translating Diku/ROM-derived MUD
> concepts, architecture, and implementation patterns into Evennia's philosophy,
> architecture, patterns, and provided interfaces.

---

## The Fundamental Shift

The single most important difference between Diku and Evennia is the **persistence
model**, and everything else flows from it.

**Diku resets the world. Evennia persists it.**

In a Diku MUD, the world is defined in area files. On boot, the server reads those
files and populates memory with mobs, objects, and rooms. When mobs are killed and
items are looted, the world degrades. A periodic **zone reset** timer recreates mobs
and objects from the area-file definitions, restoring the world to its baseline state.
The area file is the source of truth; the runtime world is ephemeral.

In Evennia, every object created exists in the database permanently until explicitly
deleted. There is no reset cycle that recreates the world from files. If an NPC is
killed, it stays dead unless game logic explicitly respawns it. If a player drops a
sword in a room, that sword remains in that room across server restarts, across
reboots, indefinitely.

**What this changes:**

| Diku assumption | Evennia reality |
|----------------|-----------------|
| Mobs respawn automatically from zone files | NPCs must be explicitly respawned by game logic (a Script timer + Prototype spawning) |
| Items dropped by mobs are ephemeral — they vanish on reset | Items are persistent. Cleanup requires explicit game logic. |
| World state is ephemeral and resets to a known good state | World state is persistent. There is no automatic "reset to baseline." |
| Area files define the world | Prototypes define templates; build scripts create instances. The database is the world. |
| Editing an area file changes the world on next reboot/reset | Editing a Prototype does not change existing objects — only newly spawned ones. Use `evennia spawn/update` or write migration logic for existing objects. |

**The adaptation:** Any Diku system that relies on periodic reset must be reimplemented
as explicit game logic. Mob respawning becomes a Script with `at_repeat()` that checks
whether a mob exists and spawns from a Prototype if not. Item cleanup becomes a Script
that periodically scans for orphaned items. Zone management becomes a handler or Script
attached to rooms or a global controller.

---

## Concept Mapping

### Entities

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| `CHAR_DATA *ch` (character struct) | Typeclass instance — `self.caller` in commands, Character object in handlers | A rich domain object, not a C struct pointer |
| Mobile (mob) | NPC typeclass inheriting from `DefaultCharacter` | Same base class as player characters. Differentiated by typeclass, not by a separate data type. |
| Object (item) | Typeclass inheriting from `DefaultObject` | Item types (weapon, armor, potion) are distinguished by typeclass inheritance or Tags, not by an `item_type` integer field |
| Room | Typeclass inheriting from `DefaultRoom` | A Room is an Object with `location=None`. It contains other objects. |
| Exit | Typeclass inheriting from `DefaultExit` | An Exit is an Object inside a Room with a `destination` property. One-way by default; create two Exits for bidirectional travel. |
| Area / Zone | A group of Rooms connected by Exits, identified by Tags | There is no formal "area" container. Use Tags (e.g., `("midgaard", "area")`) on Rooms to group them. |
| VNUM (mob/obj/room ID) | `dbref` (auto-assigned integer #ID) + Tags (developer-assigned labels) | Do not emulate VNUMs. Use Tags for categorization and search. Use Prototypes for templated spawning. |

### State and Data

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| Mob/obj/room flags (`ACT_SENTINEL`, `ROOM_DARK`, `ITEM_GLOW`) | Tags and/or Attributes | Tags for boolean flags (fast to query). Attributes for values. Do not use bitfields. |
| Affects / `affected_type` struct | Handler (custom or Buffs contrib) | Timed stat modifiers are managed by a handler attached to the character via `@lazy_property`. The Buffs contrib provides a ready-made implementation. |
| Character stats (str, dex, con) | Attributes via `AttributeProperty` or Traits contrib handler | Use `AttributeProperty` for simple flat stats. Use the Traits contrib for complex stat systems with base/bonus/modifier tracking. |
| Equipment slots (`WEAR_HEAD`, `WEAR_BODY`) | Equipment handler (EvAdventure pattern) | Define slots as an Enum. Build an EquipmentHandler that maps slots to worn objects. See `evadventure/equipment.py`. |
| Item `item_type` + type-specific fields | Typeclass inheritance or Tags | Create `Weapon(Object)`, `Armor(Object)`, `Potion(Object)` typeclasses, or use a single Object typeclass with Tags for classification |
| Position state (`POS_SLEEPING`, `POS_FIGHTING`) | Tags + CmdSet manipulation, or Attributes | Add/remove CmdSets to change available commands when state changes. E.g., entering combat adds a combat CmdSet; sleeping removes movement commands. |
| Carry weight / inventory slots | Handler | Evennia has no built-in carry system. Implement as a handler that checks on `at_pre_get()` / `at_pre_drop()` hooks. |

### World Building

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| Area file (`.are`/`.wld`/`.mob`/`.obj`/`.zon`) | Prototypes + Build scripts | Prototypes define object templates as Python dicts. Build scripts (`.ev` batch commands or `.py` batch code) instantiate the world by spawning from prototypes and linking rooms. |
| Zone reset (periodic mob/obj repopulation) | Script with `at_repeat()` + Prototype spawning | Create a "zone controller" Script that periodically checks for missing mobs/objects and spawns replacements from Prototypes. This is explicit game logic, not a framework feature. |
| OLC (Online Creation) | Prototype OLC (`spawn/olc` command) or custom EvMenu builders | Evennia provides a basic Prototype editor. For full builder tools, build custom EvMenu interfaces. |
| Room sector types (`SECT_CITY`, `SECT_FOREST`) | Tags on rooms + custom movement hooks | Tag rooms with sector type. Override `at_pre_move` or `at_post_move` to apply movement costs per sector. |
| Room extra descriptions | Attributes or `detail` system on room typeclass | Store extra descriptions as a dict Attribute. Override the `look` command or `return_appearance()` to display them when a keyword is examined. |

### Behavior and Logic

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| Spec procs (`special_procedures`) | Hook method overrides on typeclasses | A spec proc is a function pointer on a mob. In Evennia, override `at_*` hooks on the NPC's typeclass. For per-instance behavior variation, use Attributes checked within hooks or attach different handler instances. |
| MobProgs / TriggerProgs | Hook methods, or Ingame Python contrib | Map MobProg triggers to Evennia hooks: `greet_prog` → `at_object_receive`, `act_prog` → `at_msg_receive`, `rand_prog` → Script `at_repeat()`, `fight_prog` → combat handler hooks. |
| Global tick / heartbeat | TickerHandler (subscription) or Script timer | Evennia has no single global tick. Use `TICKER_HANDLER.add(interval, callback)` for subscription-based ticking, or create a Script with `at_repeat()` for periodic tasks. |
| Mob AI (aggression, memory, hate lists) | AI handler + Attributes | Build an AIHandler (see `evadventure/ai.py` for the pattern). Store aggression state, memory/hate lists as Attributes on the NPC. Process AI decisions in `at_repeat()` of an attached Script or TickerHandler callback. |
| Mob morale / flee behavior | Rules module + AI handler | Calculate morale checks in the rules module. Trigger flee behavior from the AI handler or combat handler based on the result. |
| Socials (bow, laugh, wave) | Command classes | Define each social as a Command subclass. Use `msg_contents()` with actor-stance parsing for perspective-appropriate output. |

### Combat

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| Auto-attack loop (rounds on a global tick) | CombatHandler Script with `at_repeat()` | Diku combat runs on the global heartbeat. In Evennia, create a CombatHandler Script that ticks at the desired round interval. See `evadventure/combat_twitch.py` (real-time) or `evadventure/combat_turnbased.py`. |
| `hit_dice` / `dam_dice` (`NdN+M` format) | Rules module functions | Parse or define damage as tuples `(num_dice, die_size, modifier)`. Implement roll functions in the rules module. |
| Hitroll / damroll modifiers | Rules module + Attributes or Traits | Store base values as Attributes. Calculate effective values in the rules module, applying equipment bonuses and buff modifiers. |
| Saving throws (`SAVING_PARA`, `SAVING_SPELL`) | Rules module | Define saving throw categories as Enums. Implement saving throw resolution as a rules module function. |
| `THAC0` / armor class | Rules module | Whether you preserve THAC0 or modernize to a different hit formula, implement it as a rules module function that accepts attacker stats, defender stats, and returns hit/miss. |
| Death / defeat handling | Hook on Character or combat handler | Override `at_defeat()` or equivalent custom hook. Diku instant-death can be preserved or softened. Remember: in Evennia, deleting a Character is permanent (no reset brings it back). |

### Infrastructure

| Diku/ROM | Evennia | Notes |
|----------|---------|-------|
| Permission levels (Implementor, God, Immortal, Builder) | Permission hierarchy: Developer > Admin > Builder > Helper > Player > Guest | Map Diku levels to Evennia's permission strings. Use Locks for fine-grained access control. |
| Channels | DefaultChannel typeclass | Evennia provides channels natively. Customize by subclassing DefaultChannel. |
| Mail system | Msg objects or contrib | Evennia's `Msg` model stores messages. The `mail` contrib provides a ready-made in-game mail system. |
| Who list / player listing | Command that queries connected sessions | Use `evennia.SESSION_HANDLER.all()` to get connected sessions. |
| Flat-file data storage | SQL database via Django ORM | All persistent state is in the database. Prototypes and build scripts are the code-side definition; the database is the runtime truth. |
| `MULTISESSION_MODE` | Setting in `settings.py` | `MULTISESSION_MODE=0` mimics Diku's one-connection-per-account model. Higher modes allow multiple simultaneous connections. |
| Shops / merchants | EvMenu-driven shop handler | Build NPC shops using EvMenu for the interaction flow and a handler for shop inventory. See `evadventure/shops.py`. |
| Experience / leveling | Rules module + handler or Attributes | Track XP as an Attribute. Implement level-up logic in the rules module. Apply stat changes via the rules module or a progression handler. |
| Skills / spells (large catalogs) | Classes + data dictionaries, or Prototype-like dicts | For small catalogs: define each as a class. For large catalogs (hundreds of spells): define a base class and store individual spell/skill data in dictionaries or database-stored definitions. |

---

## How to Decompose a Diku System for Evennia

When adapting a Diku subsystem (combat, equipment, magic, crafting, etc.), work through
these steps in order:

### Step 1: Identify the game entities

What kinds of things exist in this system? Each distinct kind is a candidate for a
typeclass.

- Diku "mob types" differing only in stats → one NPC typeclass + different Prototypes
- Diku "item types" differing in behavior → separate typeclasses (`Weapon`, `Armor`, `Potion`)
- Diku "room types" differing only in flags → one Room typeclass + Tags for flags

The threshold: if two things need **different code** (different methods, different hooks),
they are different typeclasses. If they need only **different data** (different stats,
different descriptions), they are the same typeclass with different Attributes/Prototypes.

### Step 2: Identify the state they carry

What data does each entity need? Map it to Evennia's storage:

- Simple values (health, mana, level) → `AttributeProperty` on the typeclass
- Complex managed state (equipped items, buff stack, quest progress) → Handler
- Classification labels (mob type, area membership, flags) → Tags
- Computed or derived values → Methods on the typeclass or handler (do not persist derived values)

### Step 3: Identify the rules

What calculations operate on this state? Factor them into the rules module:

- Damage formulas, hit checks, saving throws → `rules.py`
- XP calculations, level-up thresholds → `rules.py`
- Anything you would look up in a rulebook → `rules.py`

Rules modules take data in, return results. They do not call `msg()`, do not modify
objects directly, do not import Commands.

### Step 4: Identify the player-facing commands

What does the player type to interact with this system?

- Each distinct player action → one Command class
- Commands parse input, call handler/rules methods, format and send output
- Group related commands in one commands module file (e.g., `commands/combat.py`)
- Add commands to the appropriate CmdSet

### Step 5: Identify time-driven behavior

What happens without player input? Each periodic or delayed process needs a Script:

- Mob respawning → Script on a room or zone controller
- Combat rounds → CombatHandler Script
- Buff expiration → Handler with internal timer or TickerHandler subscription
- Weather changes → Global Script
- NPC AI decision loop → Script attached to NPC, or TickerHandler subscription

### Step 6: Place files per LAYOUT rules

See EVENNIA_LAYOUT.md. Each domain gets a sub-package containing its typeclasses,
handlers, and data structures. Commands go in the commands sub-package. Rules and
enums stay at the game package root.

---

## Antipatterns from Diku Thinking

### Emulating VNUMs

**Diku habit:** Assign integer IDs to every mob, object, and room template. Reference
everything by VNUM.

**Why it fails in Evennia:** VNUMs are a flat-file indexing system. Evennia assigns
`dbref` numbers automatically. Building a parallel VNUM registry adds complexity
without benefit.

**Instead:** Use Prototypes for templates (they have string keys). Use Tags for
classification and search. Use `evennia.search_object(tag="guard", tagcategory="mob_type")`
to find objects.

### Global Reset Scripts

**Diku habit:** Periodically destroy and recreate all mobs and objects from area files.

**Why it fails in Evennia:** Destroying and recreating objects is expensive (database
writes). It also destroys any runtime state those objects accumulated — custom
Attributes set by player interaction, modified descriptions, handler state.

**Instead:** Respawn only what is missing. Check if a mob exists before spawning. Use
Prototypes as templates and tracked Tags to know what should exist. If items need
cleanup, write targeted cleanup logic rather than wholesale destruction.

### Game Logic in Commands

**Diku habit:** In C Diku, the `do_attack()` function contains the entire attack
resolution because there is no natural place to put reusable logic.

**Why it fails in Evennia:** Commands are instantiated per-invocation and should not
carry state. Logic in commands cannot be reused by NPCs, Scripts, or other systems.

**Instead:** Commands delegate to handlers and rules. The combat handler resolves
attacks. The rules module calculates hit/damage. The command just calls
`combat_handler.submit_action(caller, "attack", target)` and sends the result to the
player.

### Bitfield Flags

**Diku habit:** Store mob/room/object properties as bits in an integer field.
`MOB_FLAGS(mob) = ACT_SENTINEL | ACT_AGGRESSIVE | ACT_STAY_ZONE`.

**Why it fails in Evennia:** Bitfields are opaque, hard to query, and foreign to Python.

**Instead:** Use Tags for boolean flags: `mob.tags.add("sentinel", category="act_flag")`.
Query with `evennia.search_object(tag="aggressive", tagcategory="act_flag")`. Use
Attributes for non-boolean values.

### Separate Data Files for Mobs/Objects

**Diku habit:** Define every mob and object in a structured text file (`.mob`, `.obj`).

**Why it fails in Evennia:** Evennia does not parse area files. Prototypes and build
scripts fill this role.

**Instead:** Define Prototypes as Python dicts. Use build scripts to instantiate the
world. For large amounts of content, generate Prototypes programmatically from
structured data (Python dicts, JSON, YAML) using a build script.

### Thinking in Global Ticks

**Diku habit:** Everything runs on a global heartbeat — combat, regen, hunger,
weather, mob AI.

**Why it fails in Evennia:** A single global tick creates unnecessary coupling and makes
it hard to run subsystems at different rates.

**Instead:** Use independent timers. Combat gets its own Script or TickerHandler at
combat speed. NPC AI ticks at AI speed. Weather ticks at weather speed. Regen ticks
per-character. Each concern controls its own timing.

### Storing Derived State

**Diku habit:** Store computed values like effective AC, total hitroll, speed
in struct fields, recalculate and update when equipment or buffs change.

**Why it fails in Evennia:** Stored derived values go stale. Every code path that
changes a contributing factor must remember to recalculate.

**Instead:** Compute derived values on access. Write a method on the handler or
typeclass:

```python
@property
def effective_armor(self):
    base = self.db.base_armor
    equipment_bonus = self.equipment.armor_bonus()
    buff_bonus = self.buffs.modifier("armor")
    return base + equipment_bonus + buff_bonus
```

---

## Contrib Quick Reference

Contribs are optional packages in Evennia that provide ready-made implementations of
common game systems. Import and extend them rather than building from scratch.

| Diku system | Evennia contrib | Import path |
|-------------|----------------|-------------|
| Character stats (str, dex, etc.) | Traits | `evennia.contrib.rpg.traits` |
| Buffs / affects | Buffs | `evennia.contrib.rpg.buffs` |
| Cooldowns / skill timers | Cooldowns | `evennia.contrib.game_systems.cooldowns` |
| Dice rolling | Dice | `evennia.contrib.rpg.dice` |
| Equipment / wear slots | EquipmentHandler pattern (EvAdventure) | `evennia.contrib.tutorials.evadventure.equipment` |
| Crafting | Crafting | `evennia.contrib.game_systems.crafting` |
| Turn-based combat | Turn Battle | `evennia.contrib.game_systems.turnbattle` |
| Character creation | Character Creator | `evennia.contrib.rpg.character_creator` |
| Room features / details | Extended Room | `evennia.contrib.grid.extended_room` |
| Map display | Ingame Map Display | `evennia.contrib.grid.ingame_map_display` |
| Large/dynamic maps | Wilderness | `evennia.contrib.grid.wilderness` |
| Coordinate grid | XYZGrid | `evennia.contrib.grid.xyzgrid` |
| MobProg-like scripting | Ingame Python | `evennia.contrib.base_systems.ingame_python` |
| Mail system | Mail | `evennia.contrib.game_systems.mail` |

Contribs stay in Evennia's tree. Do not copy contrib code into your game package
unless you need to fork it. Import and subclass to customize behavior.
