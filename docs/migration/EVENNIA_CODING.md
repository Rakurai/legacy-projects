# Evennia Programming Guide for AI Coding Agents

---

# 1. Purpose of This Guide

This document is a **framework-usage primer for AI coding agents** that will help design and implement games on top of Evennia. It is optimized for rapid internalization, implementation correctness, framework-native design, and avoiding anti-patterns. It is not a contributor guide, player manual, or Python tutorial.

**Intended use:** Paste this document (or relevant sections) into the context window of an AI coding session before implementing features for an Evennia-based game.

---

# 2. Executive Mental Model of Evennia

## Architecture in One Paragraph

Evennia is a Python MUD framework built on **Django** (database ORM, web) and **Twisted** (async networking). It runs as two cooperating processes: a **Portal** (handles network protocols—telnet, websockets, SSH) and a **Server** (runs game logic, accesses the database). The Portal and Server communicate via AMP (Asynchronous Messaging Protocol). This split allows the Server to **reload** (refreshing all Python code) without disconnecting players. All persistent game state lives in a SQL database managed by Django's ORM, but Evennia wraps this behind a **typeclass system** that lets developers work with normal Python classes instead of raw database models.

## Core Entities and Their Relationships

```
Client ──► Session ──► Account ──► Character (Object)
                                       │
                                       ▼
                                   Room (Object) ◄──── Exit (Object)
```

| Entity | What It Is | Persistent? | Has Location? |
|--------|-----------|-------------|---------------|
| **Session** | A single network connection from a client | No (lost on disconnect/reload) | No |
| **Account** | A player's OOC identity (login credentials, permissions) | Yes (typeclassed) | No |
| **Object** | Base in-game entity. Parent of Character, Room, Exit | Yes (typeclassed) | Yes (except Rooms) |
| **Character** | An Object controlled ("puppeted") by an Account+Session | Yes | Yes |
| **Room** | An Object with `location=None` that contains other objects | Yes | No (is a container) |
| **Exit** | An Object inside a Room with a `destination` property, representing a one-way link | Yes | Yes (inside source Room) |
| **Script** | An OOC entity with optional timer; used for systems, storage, periodic tasks | Yes (typeclassed) | No (but can attach to Object/Account) |
| **Channel** | A communication channel (chat) | Yes (typeclassed) | No |
| **Attribute** | Arbitrary persistent data stored on any typeclassed entity | Yes | Belongs to a parent entity |
| **Tag** | A shared label attached to entities for fast grouping/search | Yes (shared across entities) | Belongs to a parent entity |
| **Lock** | An access-control rule string evaluated at runtime | Yes (stored on entities) | Belongs to a parent entity |
| **Prototype** | A dictionary template for spawning customized Objects | Yes (db-stored or module-defined) | N/A (is a template) |
| **Command** | A Python class defining a player-invokable action | No (class, not instance) | Belongs to a CmdSet |
| **CmdSet** | A container of Commands; merged dynamically to determine available actions | No (runtime construct) | Attached to entities |

## The Typeclass System

Typeclasses are the fundamental abstraction. The inheritance hierarchy is:

```
Django Model (database table)
  └── TypedObject (Evennia's base)
        ├── ObjectDB    ◄── DefaultObject   ◄── Object/Character/Room/Exit  (game dir)
        ├── AccountDB   ◄── DefaultAccount  ◄── Account                     (game dir)
        ├── ScriptDB    ◄── DefaultScript   ◄── Script                      (game dir)
        └── ChannelDB   ◄── DefaultChannel  ◄── Channel                     (game dir)
```

**Three levels:**
1. `*DB` models — define the database schema (DO NOT MODIFY)
2. `Default*` classes — Evennia's default behavior and hooks (rarely modified; subclass from these)
3. Game-dir classes — empty templates in `mygame/typeclasses/` where game authors add customizations

**Critical rules:**
- Typeclass names must be **globally unique** across the entire server namespace.
- Never override `__init__`. Use `at_*_creation()` hooks for one-time setup and `at_init()` for per-load setup.
- Typeclasses auto-save database fields; use `.key` not `.db_key` for the wrapper that handles saving efficiently.

## Runtime and Persistence Model

- **Everything typeclassed is persistent by default.** Creating an Object, Script, or Account writes to the database immediately.
- **Attributes** (`.db.*`) persist across restarts. **NAttributes** (`.ndb.*`) are lost on reload.
- **Sessions** are ephemeral. Any data stored on a Session is lost when the player disconnects or the server reloads.
- **Server reload** restarts the Server process, refreshing all Python code. Portal stays up; players remain connected. All `ndb` data is lost; all `db` data survives.
- **Server shutdown** stops both Portal and Server. All connections are dropped.
- **Reproducible content:** Prototypes, batch-code scripts, and `at_initial_setup` provide ways to recreate world content from code. These are not "save files" but they complement the database as a source of reproducible state.

---

# 3. Core Architectural Paradigms

## 3.1 Persistent Typeclassed Entities

All game objects are Python classes backed by database rows that persist automatically. Creating an object writes to DB immediately; `.db.health = 50` persists via deferred saves. You never manage save/load cycles.

**Mistakes:** Storing state in plain Python variables (lost on reload). Creating objects without realizing they persist and must be `.delete()`d explicitly.

## 3.2 Hook-Driven Extension

Evennia calls hook methods (`at_object_creation`, `at_pre_move`, `at_post_puppet`, `at_repeat`, etc.) at specific lifecycle moments. Override these instead of modifying framework control flow.

**Mistakes:** Using `__init__` instead of `at_object_creation`. Omitting `super()` without confirming the parent hook is empty. Confusing `at_object_creation` (once ever) with `at_init` (every load from DB).

### High-Value Hooks to Know First

`at_init()` is defined on `TypedObject` and shared by all typeclassed entities (called every load from DB, including reload).

**Objects / Characters:**

| Hook | Called When |
|------|-----------|
| `at_object_creation()` | Once, when object first created |
| `at_pre_move` / `at_post_move` | Before/after movement |
| `return_appearance(looker)` | When someone looks at this object |
| `at_pre_say` / `at_say` | Before/during speech (Character) |
| `at_pre_puppet` / `at_post_puppet` | Before/after Account puppets Character |

**Accounts:**

| Hook | Called When |
|------|-----------|
| `at_account_creation()` | Once, when Account first created |
| `at_pre_login` / `at_post_login` | Before/after authentication |
| `at_disconnect` | When Session disconnects |

**Scripts:**

| Hook | Called When |
|------|-----------|
| `at_script_creation()` | Once, when Script first created |
| `at_repeat()` | Each timer interval (`interval > 0`) |
| `at_start()` / `at_stop()` | Script starts/stops |
| `is_valid()` | Checked periodically; `False` → auto-stop |

**Commands / CmdSets:**

| Hook | Called When |
|------|-----------|
| `at_pre_cmd` / `at_post_cmd` | Before/after command execution |
| `at_cmdset_creation()` | When CmdSet is initialized |

## 3.3 Command/CmdSet Composition

Commands are Python classes grouped into CmdSets, stacked and merged at runtime from Character + Account + Session + room objects + Exits + Channels. This enables context-sensitive commands (combat mode, dark rooms, object interactions).

**Mistakes:** One giant CmdSet instead of contextual distribution. Forgetting room-object CmdSets are auto-available. Ignoring merge types (Union, Replace, Intersect, Remove).

## 3.4 Account / Session / Character Separation

Account (login identity) ≠ Character (in-game avatar) ≠ Session (network connection). Account *puppets* a Character through a Session. Enables multi-character support and OOC commands.

**Mistakes:** Player prefs on Character instead of Account (lost on switch). Session-critical data on Session (lost on reconnect). `account.msg()` without session (sends to all).

## 3.5 Database-Backed State as First-Class Assumption

All important game state lives in the database automatically — no "save game" step. Prototypes, batch-code, and `at_initial_setup` can regenerate world structure from code, complementing the database.

**Mistakes:** Building custom save/load. Treating DB as secondary store. Using `.ndb` for state that must survive reload.

## 3.6 No Custom Game Loop

Evennia manages the server loop via Twisted's reactor. Use hooks, Scripts, TickerHandler, `utils.delay`, `utils.repeat` — never `while True:` or `time.sleep()` (freezes entire server).

**Mistakes:** Blocking game loops. Global "main tick" (use TickerHandler or on-demand computation). Polling instead of hook-driven events.

## 3.7 Custom Django Models (When Needed)

Attributes/Tags suffice for most data. Add custom Django models (`startapp` workflow) when you need indexed queries on structured/relational data (economy ledgers, guild tables).

**Mistakes:** Django models for simple per-object data. Forgetting `makemigrations`/`migrate`. Not using `SharedMemoryModel` for frequently-referenced models needing idmapper caching.

---

## Minimum Internal Model — If You Remember Only 10 Things

1. **Portal handles network, Server runs game logic.** Server can reload (refreshing all Python) without disconnecting players.
2. **Everything typeclassed is a database row.** Creating an Object/Script/Account writes to DB immediately. Delete explicitly with `.delete()`.
3. **`.db` persists, `.ndb` doesn't.** `utils.delay()` is non-persistent by default. Session data dies on reconnect.
4. **Never use `__init__`, `time.sleep()`, or blocking I/O.** Use `at_object_creation`/`at_init` for setup; `utils.delay`/`yield` for waiting.
5. **Account ≠ Character.** Account = player identity + permissions. Character = in-game avatar + location + stats.
6. **Hooks are the extension mechanism.** Override `at_*` methods. Call `super()` unless you have confirmed the parent hook does nothing you need.
7. **CmdSets compose dynamically.** Commands come from Character + Account + Session + room objects + Exits + Channels, merged by priority.
8. **Tags for booleans, Attributes for values, Handlers for systems.** Don't store everything in one mega-dict.
9. **Thin commands, thin typeclasses.** Game logic goes in `game/rules.py` modules and handler classes.
10. **Never modify files inside `evennia/`.** Subclass in your game directory, override settings, use hooks.

---

# 4. The Primary Extension Surfaces

## 4.1 Game Project Directory

`evennia --init mygame` creates the game directory. Key locations: `typeclasses/` for entity customization, `commands/` for commands and CmdSets, `game/` for project-owned logic (rules, handlers, subsystems), `world/` for content and build artifacts, `server/conf/settings.py` for configuration.

**Rule:** Put your game code in the game directory. Never modify files inside `evennia/` itself. Override behavior by subclassing, overriding settings, or using the provided hook modules.

## 4.2 Typeclasses

**Purpose:** Define the behavior of in-game entities.

**Customization points:**
- Override `at_object_creation()` for initial stat/attribute setup.
- Override hooks for movement (`at_pre_move`, `at_post_move`), puppeting, interaction (`at_pre_get`, `at_say`), and display (`return_appearance`, `get_display_*`).
- Use `AttributeProperty` for declarative persistent properties.
- Use `ObjectParent` mixin (in `typeclasses/objects.py`) for behavior shared by ALL Objects, Characters, Rooms, and Exits.

**Common mistakes:**
- Deep inheritance hierarchies where composition (handlers, mixins) would be cleaner.
- Putting system logic (combat engine, economy) on a typeclass instead of in a separate module or Script.
- Forgetting that `at_object_creation` only fires once — changing it does NOT update existing objects.

> **Use typeclass inheritance when:** behavior genuinely differs (Character vs Room vs Item).
> **Use handler/composition when:** you're adding a system (equipment, traits, cooldowns) that could apply to multiple typeclasses.
> **Avoid:** inheritance deeper than 2–3 levels; putting rule logic directly on typeclasses.

## 4.3 Commands

**Purpose:** Define actions players can perform.

**Customization points:**
- `key`, `aliases`, `locks`, `help_category` — class-level properties.
- `parse()` — parse `self.args` into structured data on `self`.
- `func()` — execute the command logic.
- Supports `yield` for pauses and user input within `func()`.

**Best use cases:**
- Any player-facing verb: look, get, attack, craft, cast, say.
- Use `self.caller` for the acting entity; `self.caller.search()` for finding objects.

**Common mistakes:**
- Storing mutable state on command instances (they are reused across invocations).
- Reimplementing parsing that `MuxCommand` already provides (switches, `=` splitting).
- Not returning after error messages (missing `return` after `self.caller.msg("Error")`).

## 4.4 CmdSets

**Purpose:** Group commands and control when they're available.

**Customization points:**
- `at_cmdset_creation()` to add commands.
- `mergetype` (Union/Replace/Intersect/Remove), `priority`, `no_exits`, `no_objs`, `no_channels`.
- Add CmdSets to characters in `at_object_creation` or dynamically via `obj.cmdset.add()`.

**Best use cases:**
- Object-provided commands (a button with "press", a terminal with "hack").
- Contextual command overlays (combat mode, menu mode, dark room mode).

**Common mistakes:**
- Modifying the default CmdSet in `commands/default_cmdsets.py` without understanding merge priority.
- Adding two commands with overlapping keys/aliases in the same CmdSet (later one silently replaces earlier).
- Forgetting `persistent=True` if a dynamically-added CmdSet should survive reload.

> **Use contextual CmdSets when:** commands should only be available in specific situations (combat, menu, object interaction).
> **Use character default CmdSet when:** commands should always be available to the character.
> **Avoid:** putting all commands in one CmdSet and gating with conditionals inside `func()`.

## 4.5 Scripts

**Purpose:** Persistent OOC entities for game systems, storage, and timed tasks.

**Customization points:**
- `at_script_creation()` for initial setup.
- `at_repeat()` for periodic logic (when `interval > 0`).
- `is_valid()` to auto-stop when conditions aren't met.
- Attach to objects via `obj.scripts.add()` or create globally.

**Best use cases:**
- Combat handler (tracks combatants, turn order, state).
- Weather system (ticks every N minutes, notifies rooms).
- Persistent storage for system state (economy, quest progress, faction data).
- Global singletons via `settings.GLOBAL_SCRIPTS`.

**Common mistakes:**
- Using Scripts for single-fire delays (use `utils.delay` instead — much lighter).
- Creating/deleting Scripts rapidly in hot paths (they're database objects — use TickerHandler or `utils.repeat` for lightweight periodic tasks).
- Forgetting that stopping a Script's timer does NOT delete the Script (call `.delete()` explicitly).

## 4.6 Prototypes

**Purpose:** Template dictionaries for spawning customized Object instances without needing a unique typeclass per variation.

**Customization points:**
- Define in `mygame/world/prototypes.py` (module-based, read-only from in-game) or via the OLC (database-stored, editable in-game).
- Supports inheritance via `prototype_parent`.
- Values can be static, callable, or protfunc strings (e.g., `$randint(1,10)`).

**Best use cases:**
- Variations on a type (different goblin stat blocks sharing one `Goblin` typeclass).
- Builder-facing content creation without Python access.
- Batch world population.

**Common mistakes:**
- Using prototypes when a new typeclass is more appropriate (prototypes are for data variations, typeclasses for behavioral differences).
- Forgetting to set `location` when spawning via `evennia.prototypes.spawner.spawn()` (unlike the in-game `spawn` command, the API does not auto-set location).

## 4.7 Menus (EvMenu)

Build interactive multi-node menus for chargen, NPC dialogue, shops, etc. Each node is a function returning `(text, options)`. Options have `key`, `desc`, `goto` (node name or callable). Supports free-form input, persistent menus (survive reload), and a templating language.

**Mistakes:** No exit path (player gets stuck). Using `yield` in commands for complex flows when EvMenu would be more robust.

## 4.8 Settings

**Purpose:** Configure Evennia behavior.

**Customization point:** `mygame/server/conf/settings.py` — override values from `evennia/settings_default.py`.

**Key settings for game authors:**

| Setting | Purpose |
|---------|--------|
| `BASE_*_TYPECLASS` | Default typeclass for each entity type |
| `CMDSET_CHARACTER` | Default CmdSet for characters |
| `MULTISESSION_MODE` | 0–3, controls session/puppet relationship |
| `GLOBAL_SCRIPTS` | Auto-started global Script singletons |
| `PERMISSION_HIERARCHY` | Ordered list of permission levels |
| `DEFAULT_HOME` / `START_LOCATION` | Default home/start room (#dbref) |
| `COMMAND_DEFAULT_CLASS` | Base class for all commands (default: MuxCommand) |

Other commonly overridden settings: `PROTOTYPE_MODULES`, `LOCK_FUNC_MODULES`, `INLINEFUNC_MODULES`, `INSTALLED_APPS`. See `evennia/settings_default.py` for the complete reference.

**Common mistake:** Copying large sections of `settings_default.py` into your settings file. Only override what you need — this avoids conflicts with upstream updates.

## 4.9 Contribs

**Purpose:** Optional, community-maintained modules for common game features.

**How to adopt:** Import and subclass/configure in your game directory. Do not modify the contrib source — copy it to your project if you need deep changes.

**Key contribs for game authors:**

| Contrib | Path | What It Provides |
|---------|------|-----------------|
| **Traits** | `evennia.contrib.rpg.traits` | Persistent stat/skill/resource system with TraitHandler |
| **Buffs** | `evennia.contrib.rpg.buffs` | Timed buff/debuff system with modifiers |
| **Cooldowns** | `evennia.contrib.game_systems.cooldowns` | Lightweight rate-limiting timers |
| **Crafting** | `evennia.contrib.game_systems.crafting` | Tag-based recipe crafting |
| **Turn Battle** | `evennia.contrib.game_systems.turnbattle` | Turn-based combat (progressive complexity) |
| **Extended Room** | `evennia.contrib.grid.extended_room` | Time/state-dependent room descriptions |
| **XYZGrid** | `evennia.contrib.grid.xyzgrid` | Coordinate-based grid world from ASCII maps |
| **Wilderness** | `evennia.contrib.grid.wilderness` | Procedural/on-demand room generation |
| **Components** | `evennia.contrib.base_systems.components` | ECS-lite composition alternative to inheritance |
| **EvAdventure** | `evennia.contrib.tutorials.evadventure` | Complete example game (Knave OSR rules) |

Also available: Dice (`rpg/dice`), Clothing (`game_systems/clothing`), Containers (`game_systems/containers`), Mail (`game_systems/mail`), RP System (`rpg/rpsystem`), Character Creator (`rpg/character_creator`). See `evennia/contrib/` for the full list.

---

# 5. Entity Modeling Guidance

## 5.1 Account vs Character

| Concern | Account | Character |
|---------|---------|-----------|
| Represents | The human player | An in-game avatar |
| Persist when offline? | Yes | Yes |
| Has location? | No | Yes |
| Commands | OOC commands (channel chat, who, quit) | IC commands (look, get, say, attack) |
| Permissions | Player-level permissions (Builder, Admin) | Object-level permissions (or inherits from Account) |
| How many per player? | One (usually) | One or more (depending on MULTISESSION_MODE) |

**Decision rule:** If data belongs to the *player* (preferences, play-time stats, OOC reputation), put it on the Account. If data belongs to the *character* (stats, inventory, location, name), put it on the Character. `[Framework fact]`

**Permissions rule:** Always put hierarchy permissions (Builder, Admin) on the Account, not the Character. Account permissions override Character permissions for hierarchical checks. `[Framework fact]`

> **Use Account when:** storing player preferences, OOC reputation, login-related data, cross-character state.
> **Use Character when:** storing stats, inventory, IC relationships, location-dependent data.
> **Avoid:** putting hierarchy permissions on Character; storing session-lived data on either.

## 5.2 Character vs Generic Object

Characters are Objects with puppeting support. Use Character for:
- Player-controlled avatars.
- NPCs that need the same hooks/systems as PCs (often desirable for consistent combat/interaction).

Use generic Object for:
- Items, furniture, weapons, treasure.
- Environmental objects (buttons, levers, signs).
- Things that should never be puppeted.

**Legacy migration note (DIKU):** DIKU "mobiles" map most naturally to Characters (if they need full command access and puppeting hooks) or Objects with AI Scripts (if they're simpler NPCs). This is a **project-specific design decision** — Evennia does not prescribe a canonical mapping. `[Open design choice]` The EvAdventure tutorial uses a `LivingMixin` shared between PCs and NPCs, which is a documented pattern worth considering. `[Common pattern]`

## 5.3 Object vs Custom Django Model

| Use Attribute-based storage | Use a custom Django model |
|----------------------------|--------------------------|
| Per-object data (stats, descriptions, state) | Cross-object relational data (guild memberships, economic ledger) |
| Flexible, schema-free data | Data needing indexed SQL queries |
| Small number of values per object | Tables with thousands of rows that need efficient filtering |
| Prototype or builder-editable data | Read-heavy data shared across many objects |

**Rule of thumb:** Start with Attributes. Only introduce a Django model when you need relational queries, performance at scale, or schema enforcement that Attributes cannot provide.

## 5.4 Attribute vs Tag vs Property vs Script

| Mechanism | Use For | Persistent? | Queryable? |
|-----------|---------|-------------|------------|
| **Attribute** (`.db.*`) | Arbitrary per-object data (HP, description, quest state) | Yes | Via `search_object_attribute()` |
| **AttributeProperty** | Declaring typed Attributes on a typeclass (like Django fields) | Yes | Same as Attribute |
| **Tag** | Boolean labels for grouping/search (is_undead, belongs_to_guild) | Yes (shared) | Very fast via `search_tag()` |
| **TagProperty** / **TagCategoryProperty** | Declaring Tags on a typeclass | Yes | Same as Tag |
| **NAttribute** (`.ndb.*`) | Temporary runtime data (combat target, menu state) | No (lost on reload) | No |
| **Script** | System state, timer-driven behavior, persistent handlers | Yes | Via `search_script()` |
| **Lock** | Access control rules | Yes | Checked via `obj.access()` |
| **Python property** | Computed/derived values (don't store what you can compute) | No | No |

**Decision matrix for "where should this data live?":**

- **Doesn't survive reload?** → `.ndb` or Python variable
- **Per-object arbitrary data?** → Attribute (`.db.*`)
- **Boolean label for grouping?** → Tag
- **Relational/cross-object structured data?** → Custom Django Model
- **System-level global state?** → Global Script with Attributes
- **Needs periodic timer behavior?** → Script with interval

## 5.5 Room/World Topology

Rooms are Objects with `location=None`. Exits are Objects inside Rooms with a `destination` pointing to another Room. Exits are **one-way** — to create a two-way connection, create two Exits.

**Creating rooms and exits in code:**
```python
from evennia import create_object
room1 = create_object("typeclasses.rooms.Room", key="Town Square")
room2 = create_object("typeclasses.rooms.Room", key="Market")
create_object("typeclasses.exits.Exit", key="north", location=room1, destination=room2)
create_object("typeclasses.exits.Exit", key="south", location=room2, destination=room1)
```

**Legacy migration note (DIKU):** DIKU "areas" with numbered rooms and direction-based links map naturally to Evennia Rooms and Exits. DIKU "zone resets" (respawning mobs/items) have **no direct Evennia equivalent**. You must implement reset logic yourself, typically via Scripts with timers that use prototypes to respawn content. This is an **open migration question requiring project-specific design**. For coordinate-based worlds, the `xyzgrid` contrib provides a documented approach.

## 5.6 Inventories, Equipment, and Containers

In Evennia, an object's inventory is simply the list of objects whose `location` is that object. `obj.contents` returns everything inside.

Equipment systems must be built by the game — Evennia provides no default equipment slots. Common patterns:
- **Attribute-based slots:** Store equipped items as Attributes (e.g., `.db.equipment = {"weapon": obj1, "armor": obj2}`).
- **Handler pattern:** Create an `EquipmentHandler` as a `@lazy_property` that manages slot logic (see EvAdventure's `equipment.py` for a reference implementation).
- Tags for item classification (e.g., tag `wieldable`, tag `wearable`).

## 5.7 NPCs and Autonomous Entities

NPCs can be Characters (if they need full puppet hooks) or Objects (if simpler).

**Common NPC patterns:**
- AI as a Script attached to the NPC (`npc.scripts.add(AIScript)`), with `at_repeat` driving behavior.
- A shared `LivingMixin` between PC and NPC typeclasses for combat/interaction hooks.
- TickerHandler subscriptions for periodic NPC actions.
- Tag-based NPC classification for area-wide operations (e.g., all NPCs tagged `faction_guard`).

---

# 6. Commands and Interaction Model

## How Commands Work

1. Player types input.
2. Session sends it to the command handler.
3. Handler gathers CmdSets from: Session + Account + Character + objects in room + Exits + Channels.
4. CmdSets are merged by priority (higher priority merges "on top").
5. Parser matches input against merged command pool.
6. Matched command's `at_pre_cmd()` → `parse()` → `func()` → `at_post_cmd()` are called.

## Runtime Properties Available in Commands

Inside `func()` and `parse()`, the following are available:

| Property | Value |
|----------|-------|
| `self.caller` | The entity executing the command (usually the Character) |
| `self.args` | Everything after the command name (e.g., `" at sword"` for `look at sword`) |
| `self.raw_string` | The complete raw input |
| `self.session` | The Session that triggered this command |
| `self.account` | The Account behind the caller |
| `self.obj` | The object on which this command's CmdSet is defined |
| `self.cmdstring` | The matched command name |

## Command Class Hierarchy

`Command` (base) → `MuxCommand` (adds `/switch`, `=` splitting, args stripping) → Your commands. `MuxCommand` is the default `COMMAND_DEFAULT_CLASS` and recommended starting point.

## Organizing Commands

Organize by domain: `commands/general.py`, `commands/combat.py`, `commands/social.py`, etc. Define CmdSets in `commands/default_cmdsets.py`.

**Command availability:** Character CmdSet (always while puppeting), Account CmdSet (always, even OOC), Unloggedin CmdSet (pre-auth), Objects in room (when `call` lock passes), Exits (always, priority 101), Channels (always, priority 101).

## Permissions and Access Control

Commands use `locks = "cmd:perm(Builder)"`. Check object-level access in `func()` with `target.access(self.caller, "edit")`. Always `return` after error messages. `caller.search()` handles "not found" messages automatically — just check `if not target: return`.

---

# 7. State, Persistence, and Timing

## Persistence Quick Rules

**Memorize these — they are the most common source of reload bugs:**

| What | Survives Reload? | Survives Shutdown? |
|------|-----------------|-------------------|
| `.db.foo` (Attribute) | Yes | Yes |
| `.ndb.foo` (NAttribute) | **No** | No |
| `utils.delay()` (default) | **No** | No |
| `utils.delay(persistent=True)` | Yes | Yes |
| `utils.repeat()` (ticker-backed) | Yes | Yes |
| Script with interval | Yes | Yes |
| TickerHandler subscription | Yes | Yes |
| Python class/instance variables | **No** | No |
| Session data | **No** | No |
| EvMenu state (default) | **No** → pass `persistent=True` | No |

## Attributes

The primary mechanism for storing per-object data.

**Three access patterns:**
1. **`.db` shortcut:** `obj.db.health = 100` / `val = obj.db.health` — simple, only works for `None`-category Attributes.
2. **`.attributes` handler:** `obj.attributes.add("health", 100, category="stats")` — full control, supports categories.
3. **`AttributeProperty`:** Class-level declaration — `health = AttributeProperty(100)` — best for known, typed properties.

**Serialization:** Attributes can store any picklable Python object: numbers, strings, lists, dicts, sets, and references to other typeclassed entities (stored as dbref, resolved on retrieval). Cannot store: open file handles, lambdas, unpicklable objects.

**`autocreate=False` on AttributeProperty:** The Attribute won't be created in the database until explicitly set. Until then, the default value is returned with no database access. Advantage: efficiently serves defaults without DB overhead. Disadvantage: invisible to `.db` and `examine` until set.

## Tags

Lightweight boolean flags for classification and search.

```python
obj.tags.add("undead", category="monster_type")
all_undead = evennia.search_tag("undead", category="monster_type")
```

Tags are **shared** — adding the same tag to a million objects creates only one Tag row in the database. This makes tag-based search extremely fast.

**Key distinction:** Tags have no value. They exist or they don't. If you need a value, use an Attribute.

**Special Tag uses:** Aliases (alternative object names) and Permissions are implemented as Tags with special categories internally.

## Scripts and Timing

**Timing options from lightest to heaviest:**

| Method | Overhead | Persists? | Best For |
|--------|----------|-----------|----------|
| `utils.delay(seconds, callback, *args, **kwargs)` | Very low | **No** (`persistent=False` by default; pass `persistent=True` to survive reload) | Single delayed action |
| `utils.repeat(seconds, callback, *args, **kwargs)` | Low | Yes (uses persistent ticker system) | Recurring action on many objects at same interval |
| `TICKER_HANDLER.add(interval, callback)` | Low | Yes | Subscription-based recurring actions |
| `Script` with `interval` | Medium | Yes | Complex persistent periodic logic with pause/stop/state |
| `ON_DEMAND_HANDLER` | Very low | Yes | State that only needs computing when checked |

**Decision rule:** Use `utils.delay` for one-off delays. Use `TICKER_HANDLER` or `utils.repeat` for lightweight recurring tasks. Use a Script when you need persistent state along with the timer (e.g., a combat handler tracking turns). Use `ON_DEMAND_HANDLER` when state can be lazily computed.

> **Use `utils.delay` when:** a single action should happen once after N seconds (non-persistent by default).
> **Use `utils.repeat` / `TICKER_HANDLER` when:** many objects need recurring callbacks at the same interval, and you don't need per-object persistent state.
> **Use Script with interval when:** the timer needs associated persistent state (combatants, turn order) or pause/resume capability.
> **Use on-demand when:** state is time-based but only needs evaluation when queried (crop growth, cooldowns).
> **Avoid:** `time.sleep()` (blocks server); creating/deleting Scripts for short delays; ticking when hooks or on-demand would suffice.

**Critical rule:** Never use `time.sleep()` anywhere in Evennia code. It blocks the entire server.

## TickerHandler

For subscribing objects to periodic updates:

```python
from evennia import TICKER_HANDLER
TICKER_HANDLER.add(60, obj.at_tick)    # call obj.at_tick() every 60 seconds
TICKER_HANDLER.remove(60, obj.at_tick) # stop
```

**Key insight from Evennia docs:** Don't use tickers to detect changes. If 99% of ticks do nothing, you're wasting cycles. Use hooks and on-demand computation instead. Tickers are for when something must happen to multiple objects simultaneously without external input (e.g., weather, hunger).

## OnDemandHandler

For state that changes over time but only needs to be evaluated when queried:

```python
from evennia import ON_DEMAND_HANDLER
ON_DEMAND_HANDLER.add("crop_field_#42", stages={
    0: "planted",
    300: "growing",
    900: "ready_to_harvest"
})
# Later, when someone looks at the field:
stage = ON_DEMAND_HANDLER.get_stage("crop_field_#42")  # returns current stage
```

Efficiently handles time-based states without ticking. Skips intermediate stages if nobody checks — do not rely on intermediate side effects.

## State Placement Decision Matrix

| Question | If Yes → |
|----------|----------|
| Does it need to persist across reload? | `.db` Attribute, Tag, or Script |
| Is it temporary runtime data? | `.ndb` NAttribute |
| Is it a boolean flag for grouping? | Tag |
| Is it per-object variable data? | Attribute |
| Is it cross-object structured data? | Custom Django Model |
| Is it time-based state that can be lazily computed? | OnDemandHandler |
| Does it need periodic active behavior? | Script or TickerHandler |
| Is it session-specific (e.g., menu state)? | `caller.ndb._evmenu` or Session `.ndb` |

---

# 8. Content Creation and World Representation

## Rooms, Exits, and Objects

Rooms are the spatial containers of the game world. Every in-game entity (except Rooms themselves) has a `location` — usually a Room. Exits are one-way links between Rooms.

**Creating world content in code:**
```python
from evennia import create_object
room = create_object("typeclasses.rooms.Room", key="Forest Clearing",
                     attributes=[("desc", "Sunlight filters through the canopy.")])
```

**Creating via batch processor:**
Batch-Code Processor lets you run arbitrary Python for reproducible world scripts. Place in `mygame/world/build_forest.py`, run with `batchcode world.build_forest`.

## Prototypes and Spawning

Prototypes are dictionaries defining object templates. They decouple data variation from code:

```python
# in mygame/world/prototypes.py
IRON_SWORD = {
    "prototype_key": "iron_sword",
    "key": "iron sword",
    "typeclass": "typeclasses.objects.Object",
    "tags": [("sword", "weapon_type"), ("iron", "material")],
    "damage": 8,     # shorthand for Attribute ("damage", 8)
    "weight": 5,
}
ENCHANTED_SWORD = {
    "prototype_key": "enchanted_sword",
    "prototype_parent": "iron_sword",
    "key": "enchanted sword",
    "damage": 12,
    "tags": [("magical", "properties")],  # merges with parent's tags
}
```

Spawn with: `evennia.prototypes.spawner.spawn(ENCHANTED_SWORD)` or in-game: `spawn enchanted_sword`.

**Prototype inheritance:** Children inherit all parent keys. `attrs` and `tags` merge complementarily (only matching key+category gets replaced). Other keys replace entirely.

**Callable values:** Prototype values can be callables for randomization: `"health": lambda: random.randint(20, 30)`

## Static vs Generated Content

- **Static content:** Built once via batch processors or in-game commands (or code at initial_setup). Persists in the database.
- **Generated content:** Created procedurally at runtime. The `wilderness` contrib provides on-demand room generation. Scripted resets can respawn content via prototypes.

## Legacy Migration: Importing Existing Game Data

**Documented Evennia approach:** Evennia does not provide a built-in DIKU area file importer. However:
- The `Evennia for Diku Users` doc (in docs/source/Howtos/) discusses conceptual mapping.
- Batch-Code Processor can execute arbitrary Python code to parse external data files and call `create_object()`, `create_script()`, etc.
- Prototype dictionaries can be generated programmatically from parsed area files.
- Tag-based classification replaces DIKU flag-based systems.

**Migration strategy (recommended):**
1. Parse legacy data files into intermediate Python dicts.
2. Map legacy entity types to Evennia typeclasses + prototypes.
3. Generate batch-code scripts or module-based prototypes from parsed data.
4. Use `evennia.prototypes.spawner.spawn()` to materialize the world.

**Legacy concept mapping:**

| Legacy Concept | Evennia Equivalent | Mapping Confidence |
|---------------|-------------------|-------------------|
| Room | `DefaultRoom` subclass | **Documented** |
| Exit/Direction | `DefaultExit` objects (one-way, create two for bidirectional) | **Documented** |
| Player | `Account` + `Character` (separate entities) | **Documented** |
| Mobile/MOB | `Character` subclass or `Object` with AI Script | **Open design choice** — no canonical mapping |
| Object/Item | `Object` subclass with Tags/Attributes for properties | **Documented** |
| Area | No direct equivalent; Tags to group rooms, or XYZGrid zones | **Open design choice** |
| Zone resets | Script with timer + prototype-based spawning | **Open design choice** — must be custom-built |
| VNUM | `dbref` (#id) as unique identifier; Tags for additional namespacing | **Approximate comparison** |
| Flags (mob/room/obj) | Tags + Attributes | **Code-evident framework pattern** |
| Affects/buffs | No built-in; `evennia.contrib.rpg.buffs` provides one | **Approximate comparison** (contrib-supported) |
| Heartbeat/tick | No global tick; use TickerHandler, Scripts, or on-demand | **Documented** — Evennia explicitly rejects global-tick |
| Command table | CmdSet + Command classes | **Documented** |
| Scripted mob behavior | Scripts attached to objects with `at_repeat` | **Code-evident framework pattern** |
| Global managers | Global Scripts via `GLOBAL_SCRIPTS` setting | **Documented** |

---

# 9. Implementing Game Systems on Top of Evennia

## General Architecture Pattern

For any game system (combat, crafting, quests, etc.):

1. **Rules module:** Put game logic in `mygame/game/` as plain Python modules. Keep it independent of Evennia objects where possible. Pass objects in as arguments. `[Common pattern]`
2. **Handler on typeclass:** Expose per-object system state via a `@lazy_property` handler (e.g., `self.traits`, `self.equipment`). `[Common pattern]`
3. **Script for persistent state:** Use a Script for system state that spans multiple objects (e.g., a combat encounter tracking multiple combatants). `[Documented extension surface]`
4. **Commands for player interaction:** Create CmdSets with relevant verbs, add context-appropriate. `[Documented extension surface]`
5. **Tags for classification:** Use Tags for efficient grouping and querying. `[Framework fact]`
6. **Prototypes for content:** Define system-specific content (spell definitions, recipe templates) as prototypes or module-level dicts. `[Common pattern]`

## 9.1 Combat

`CombatHandler(DefaultScript)` manages encounter state (combatants, turns). Rules in `game/rules.py`; `LivingMixin` for shared `at_damage()`/`at_defeat()` hooks. Combat CmdSet (high priority) added on start. **Ref:** `contrib.game_systems.turnbattle`, `contrib.tutorials.evadventure.combat_base`.

## 9.2 Skills / Progression / Stats

`contrib.rpg.traits` TraitHandler with `static`/`counter`/`gauge` types, exposed via `@lazy_property` on Character. `AttributeProperty` for simpler values. Rules module for checks.

## 9.3 Quests

`QuestHandler` as `@lazy_property` on Character tracking active/completed quests. Quest definitions as classes with step-methods (see EvAdventure's `quests.py`). Tags for quest state flags. Hook calls from game events to check progress.

## 9.4 Crafting

`evennia.contrib.game_systems.crafting` — recipe-based system using Tags for ingredient matching and Prototypes for output. Or custom `world/crafting.py` with recipe dicts.

## 9.5 Buffs / Debuffs

`evennia.contrib.rpg.buffs` for full buff system (duration, stacking, modifiers). For simple timed effects: set Attribute + `utils.delay(60, remove_fn, obj)`. For stat modification, use handler's `check(value, stat)` pattern.

## 9.6 AI / NPC Behavior

Script with `at_repeat` for periodic decisions. State machine in Attributes (`.db.ai_state`). Target tracking via `.db.target` (object references auto-resolve). Tag-based group behavior. Reference: `evadventure.ai` `AIHandler`.

## 9.7 Factions

Tags for membership (`category="faction"`). Custom lock functions for faction-gated actions. Global Script for faction-level state. Django model for complex relational data.

## 9.8 Communication

Built-in: Channels (OOC), `say`/`whisper`/`emote` (IC). Custom IC systems: Channel subclass with range checks, or command-based (radio command checking for radio object). `rpg.rpsystem` for emote/sdesc/recog.

## 9.9 UI / Menus

**EvMenu** for multi-step flows (chargen, shops, NPC dialogue). **EvTable** for formatted output. **EvForm** for fixed layouts. **FuncParser** for per-receiver text — actor-stance callables: `$You()`, `$you()`, `$conj()`, `$pconj()`, `$your()`, `$Your()`, `$pron()`, `$Pron()`, `$obj()`. Example: `$You() $conj(attack) the goblin.`

---

# 10. Project Organization and Codebase Hygiene

The key structural idea: `commands/` and `typeclasses/` are Evennia integration
surfaces; `game/` is the home for project-owned logic (rules, handlers, subsystems);
`world/` holds content and build artifacts.

## Separation Principles

1. **Thin typeclasses and commands.** They delegate to rules modules and handlers. A command's `func()` should read inputs → call system function → report results.
2. **Handler pattern.** Encapsulate per-object system behavior in handler classes accessed via `@lazy_property` (e.g., `self.equipment = EquipmentHandler(self)`). Handlers live with their domain in `game/` (e.g., `game/objects/equipment.py`).
3. **Rules as standalone modules.** Put calculation logic in `game/rules.py`. Functions accept objects as parameters, return results.
4. **No god objects.** Consider factoring out handlers when typeclasses grow large.

## Naming Conventions

Per Evennia's code style (PEP8-based):
- `CamelCase` for classes only: `class DragonNPC(Character):`
- `lowercase_with_underscores` for everything else: `def roll_attack(attacker, defender):`
- Commands prefixed with `Cmd`: `class CmdAttack(Command):`
- CmdSets suffixed with `CmdSet`: `class CombatCmdSet(CmdSet):`

## Testing Strategy

- Test rules modules with pure unit tests (no Evennia dependencies needed).
- Test typeclasses and commands with `EvenniaTest` / `EvenniaCommandTest` (pre-creates test objects).
- Use `--keepdb` to speed up repeated test runs.

---

# 11. Best Practices

1. **`AttributeProperty` for known persistent properties.** Provides type documentation, defaults, cleaner access than raw `.db.*`.
2. **Tags for classification, Attributes for variable data.** Tags: "is this a weapon?". Attributes: "how much damage?"
3. **Keep commands thin.** `func()` orchestrates: parse → find targets → call rules → report. No embedded game logic.
4. **Handler pattern.** `@lazy_property` handler classes for per-object systems (equipment, traits, cooldowns). Keeps typeclasses clean.
5. **Centralize rules.** Dice, skill checks, damage formulas in `game/rules.py`. Don't scatter across commands/typeclasses.
6. **Hooks over polls.** React to events via hooks, don't poll on timers.
7. **`utils.delay` over Script for one-shots.** Scripts are DB objects; `delay` is lightweight.
8. **Use `create_object`/`create_script`/etc.** Don't instantiate typeclasses directly.
9. **Use `caller.search()`.** Handles ambiguity, errors, access checks.
10. **`msg()` routing:** `self.msg()` in Command targets triggering session. `obj.msg()` for puppeted objects. `obj.msg_contents()` for room-wide (supports `$You()`/`$conj()`).
11. **Check contribs first.** Traits, buffs, cooldowns, crafting, combat, equipment, extended rooms — many already exist.
12. **Test with `quell`.** Superuser bypasses locks. `quell` tests as regular player.
13. **Batch processors for reproducible worlds.** Serve as documentation; allow rebuilding after DB reset.

---

# 12. Common Anti-Patterns (Ordered by Risk)

## 12.1 Blocking the Reactor (`time.sleep()`, game loops, sync I/O)
Creating a `while True:` loop or calling `time.sleep()` **freezes the entire server for all players.** Use hooks, `utils.delay`, `yield` in commands, TickerHandler/Scripts for periodic tasks, and Twisted deferreds for async I/O.

## 12.2 Using `__init__` for Object Setup
Django's ORM does not call `__init__` predictably. Use `at_object_creation()` (once, on first creation), `at_init()` (every load from DB), or `at_first_save()`.

## 12.3 Treating Account and Character as Interchangeable
Player data on Account, IC data on Character. Hierarchy permissions on Account. Only Characters have locations. Mixing these causes data loss on character switches and permission bugs.

## 12.4 Modifying Framework Files
Never edit files inside `evennia/`. Subclass in game dir, override settings, add hooks. Changes are overwritten on update.

## 12.5 Fighting the Persistence Model
Don't build a custom save/load system or serialize state to JSON files. The database holds live game state. Use Attributes, Tags, Scripts, and (when needed) Django models. Prototypes and batch-code create reproducible content, not a parallel persistence layer.

## 12.6 Storing Everything in Flat Attributes
`obj.db.stats = {"str": 10, "hp": 100, "inventory": [...]}` — a single mega-dict — breaks queryability, type safety, and handler logic. Use separate Attributes/`AttributeProperty` per concern, Tags for flags, handlers for systems.

## 12.7 Ignoring CmdSet / Context Patterns
Don't put all commands in one CmdSet and gate with conditionals. Use contextual CmdSets: combat commands in `CombatCmdSet`, object-specific commands on the object.

## 12.8 Deep Typeclass Inheritance
`Object → Item → Weapon → Sword → MagicSword → FireSword` is brittle. Use composition: `Object` + handlers + Tags + prototype variations. Reserve inheritance for genuinely different behavior.

## 12.9 Duplicating Framework Facilities
Use `caller.search()`, `obj.access()`, `obj.msg()`, `obj.msg_contents()`. Don't write custom search, permission, or message routing unless the built-in is genuinely insufficient.

## 12.10 Ignoring `ObjectParent` Mixin
Shared behavior for all Objects/Characters/Rooms/Exits goes in `ObjectParent` (in `typeclasses/objects.py`), not duplicated across each typeclass.

## 12.11 Creating/Deleting Scripts in Hot Paths
Scripts are database objects. Use `utils.delay()` for one-shot delays, `utils.repeat()` or TickerHandler for recurring tasks.

---

# 13. "How to Think" Checklist for an AI Agent Before Coding

Run through these before implementing any feature:

**Ownership:** What entity owns this? (Account/Character/Object/Room/Script/Command?) Individual or global system?

**Persistence:** Survives reload? → `.db` / Tag. Temporary? → `.ndb`. Time-limited? → Attribute + delay/Script. Relational? → Django model.

**Storage:** Attribute vs Tag vs Script vs prototype vs custom model? Tags for classification, Attributes for variable data. `AttributeProperty` for typed access.

**Framework:** Existing hook for this? Existing contrib? Am I re-implementing something built-in? Am I editing `evennia/` instead of subclassing?

**Commands:** Command or internal hook logic? Which CmdSet? Using `caller.search()`? Returning after errors? Locks checked?

**Architecture:** `func()` delegating to rules module? Handler for per-object state? Avoiding deep inheritance? Typeclass lean or god-object?

**Timing:** Lightest mechanism? (delay < TickerHandler < Script) On-demand vs ticked? Event-driven vs polling?

---

# 14. Source Map / Where to Look Next

**Read first:** `evennia/__init__.py` (flat API), `evennia/settings_default.py` (all settings), `Components/Typeclasses.md`, `Components/Objects.md`, `Howtos/Beginner-Tutorial/` (Parts 1–5).

**Read when working on commands:** `evennia/commands/command.py`, `commands/default/muxcommand.py`, `evennia/commands/cmdset.py`, `Components/Commands.md`, `Components/Command-Sets.md`.

**Read when working on persistence/timers:** `evennia/typeclasses/attributes.py`, `evennia/typeclasses/tags.py`, `evennia/scripts/scripts.py`, `evennia/utils/utils.py` (`delay`, `repeat`), `Components/Attributes.md`, `Components/Scripts.md`.

**Read when working on objects/world:** `evennia/objects/objects.py`, `evennia/accounts/accounts.py`, `evennia/utils/create.py`, `evennia/utils/search.py`, `Components/Prototypes.md`, `Components/Locks.md`.

**Read when working on migration/content:** `Howtos/Evennia-for-Diku-Users.md`, `evennia/prototypes/spawner.py`, `evennia/utils/evmenu.py`.

**Game template extension points:** `typeclasses/` (all entity files), `commands/default_cmdsets.py`, `server/conf/settings.py`, `world/prototypes.py`.

---

# 15. Open Questions / Ambiguous Areas

## 15.1 NPC Architecture Choice

Evennia does not prescribe whether NPCs should be Characters or Objects. `[Open design choice]` Using Characters gives NPCs full command/puppet infrastructure but may be heavier than needed. Using Objects with AI Scripts is lighter but requires more custom hookup. **Recommendation:** Consider Character-based NPCs sharing a `LivingMixin` with player Characters (as in EvAdventure), unless you have a specific reason to use Objects. `[Project recommendation]`

## 15.2 Equipment System Design

No standard equipment system exists in core Evennia. `[Open design choice]` The EvAdventure tutorial provides one reference implementation (slot-based with handler), and the clothing contrib provides another (layer-based). **Recommendation:** Use a handler-based approach. Study EvAdventure's `equipment.py` as a starting pattern. `[Project recommendation]`

## 15.3 Zone/Area Reset Systems

DIKU-style zone resets (periodic mob/item respawning) have no direct Evennia equivalent. `[Open design choice]` You must build this as a Script-based system that uses prototypes for respawning. The exact architecture is a project-specific design decision.

## 15.4 When to Use Django Models vs Scripts for Global State

The line between "use a Global Script with Attributes" and "create a custom Django model" is not precisely defined. `[Open design choice]` **Heuristic:** If you need SQL-level queries (JOIN, GROUP BY, complex WHERE) or the data has relational structure beyond flat key-value pairs, use a Django model. If it's essentially a persistent dict or simple state machine, a Global Script is simpler. `[Project recommendation]`

## 15.5 Other Ambiguities

- **Multi-Session Mode:** `MULTISESSION_MODE` 0–3 affects Session/Account/Character linkage. Start with mode 0 or 1. Test `msg()` routing in mode 2+.
- **Typeclass Swapping:** `obj.swap_typeclass("new.TypeClass")` changes class at runtime, retaining Attributes/Tags. Powerful but test carefully.
- **Performance:** Handles hundreds of concurrent players. Profile under load. Use `.ndb` for high-frequency transient data. Prefer Tags over Attributes for frequently queried flags.
- **Web Integration:** Django web server + REST API + websocket webclient. Standard Django patterns. Shares game database.

---
