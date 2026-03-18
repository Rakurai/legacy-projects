# EVENNIA_GLOSSARY.md — Term Definitions for Game Development on Evennia

> **Purpose:** Canonical definitions of terms as used in this project. When a term appears
> in code review, planning discussions, commit messages, or AI agent prompts, it means
> exactly what is defined here — nothing more, nothing less.
>
> **Audience:** Human developers, AI planning agents, code reviewers.

---

## How to Use This Glossary

- **Bold term** = the canonical name to use in all project communication.
- **"Also called"** = synonyms you may encounter in Evennia docs or community. Use the
  canonical name in our project.
- **Engineering analog** = the closest established software pattern, for bridging
  understanding. It is an approximation, not an identity.

---

## Core Framework Concepts

### Typeclass

A Python class that the game developer writes, inheriting from one of Evennia's
`Default*` base classes. It defines a kind of persistent domain object — its data,
behavior, hooks, and handlers.

- **Engineering analog:** Active Record. The typeclass is both the business entity and
  its persistence mechanism.
- **Also called:** "type class," "typed object" (in Evennia internals).
- **Key property:** Every typeclass instance is backed by a database row. Creating a
  typeclass instance creates a database record. Deleting the database record destroys
  the object.
- **What it is NOT:** A plain Python class. You cannot instantiate a typeclass with
  `MyCharacter()` — you must use `evennia.create_object(MyCharacter, ...)` or the
  framework's spawning system.
- **Base classes provided by the framework:**

  | Base Class | Represents |
  |-----------|------------|
  | `DefaultObject` | Any in-world entity (items, furniture, generic things) |
  | `DefaultCharacter` | Player characters and significant NPCs |
  | `DefaultRoom` | A location in the game world |
  | `DefaultExit` | A traversable link between rooms |
  | `DefaultAccount` | A player's out-of-character identity (login, sessions) |
  | `DefaultScript` | A background process, timer, or state container |
  | `DefaultChannel` | A communication channel |

### Attribute

A named, persistent key-value pair attached to any typeclass instance. Stores
game-specific state (health, inventory list, quest progress) without database
schema changes.

- **Engineering analog:** Schema-free property bag / key-value store per entity.
- **Access patterns:**
  - **Imperative:** `obj.db.health = 100` / `val = obj.db.health`
  - **Declarative:** `health = AttributeProperty(100)` on the typeclass class body,
    then `obj.health = 100` / `val = obj.health`
- **Persistence:** Survives server restarts. The framework manages storage
  transparently.
- **What it is NOT:** A Django model field. Attributes do not require migrations.
  They are not column-level indexed (though you can manually query them). For
  high-performance queries, use Tags instead.

### AttributeProperty

A Python descriptor declared on a typeclass class body that provides a clean,
typed interface to an underlying Attribute.

- **Engineering analog:** Declarative field descriptor / property with default.
- **Advantage over `.db`:** IDE-discoverable, self-documenting, supports defaults,
  visible in class definition.

### Tag

A lightweight string label attached to any typeclass instance. Used for
classification, grouping, and fast querying.

- **Engineering analog:** Label / index tag / categorical marker.
- **Has:** A `key` (string) and optional `category` (string namespace).
- **Fast to query:** Tags are indexed in the database. Searching by tag is
  significantly faster than searching by Attribute value.
- **Common uses:** Object typing ("weapon", "armor"), zone membership ("midgaard"),
  quest flags ("quest_goblin_started"), system markers ("no_combat").

### Handler

A Python class that manages one behavioral concern for a typeclass instance.
Attached to the typeclass via `@lazy_property`. Stores its data through the
owning object's Attribute system.

- **Engineering analog:** Delegate / Strategy object (owned, not injected).
- **Also called:** Sometimes confused with "service" or "manager" in other paradigms.
  In Evennia, handlers are **owned by** a specific object instance, not global.
- **Key properties:**
  - One handler instance per owning object instance (not shared, not global).
  - All data stored via `self.obj.attributes` — the handler has no database table.
  - The handler provides the **API** for its concern. External code (commands, other
    handlers) calls handler methods, not raw Attribute access.
- **Examples:** EquipmentHandler, QuestHandler, AIHandler, TraitHandler, BuffHandler.
- **Built-in handlers provided by framework:** `.locks`, `.tags`, `.attributes`,
  `.cmdset`, `.scripts`, `.nicks`, `.sessions`.

### Command

A Python class that encapsulates one player-invocable action. It parses text
input and executes game logic (by delegating to domain objects and rules).

- **Engineering analog:** Command pattern (GoF) / Application-layer use case.
- **Also called:** "cmd" in code.
- **Key rule:** Commands should be **thin**. They parse, delegate, and format
  output. Business logic belongs in handlers or rules modules.
- **Stateless between invocations.** Do not store mutable state on `self` that
  must persist across calls.

### CmdSet (Command Set)

A collection of Command classes that are available together in a given context.
CmdSets can be added to, removed from, or merged with other CmdSets dynamically.

- **Engineering analog:** Capability set / available-operations context.
- **Key property:** CmdSets are attached to domain objects and merged at runtime
  using set-theoretic operations (union, intersection, replacement). This is how
  context-sensitive commands work.
- **What it is NOT:** A routing table or URL dispatcher. CmdSets are merged
  dynamically based on game state, not statically configured.

### Script

A typeclass (persistent domain object) that has an optional timer and can execute
code on a schedule or in response to events.

- **Engineering analog:** Persistent scheduled task / state machine with timer.
- **Also called:** "global script" (when not attached to an object), "combat handler"
  (when used as a multi-actor coordinator).
- **Key property:** Can function as both a timer AND a handler simultaneously
  (e.g., `CombatHandler` is a Script that manages combat state and ticks rounds).

### Hook (Hook Method)

A method on a typeclass that the framework calls at a defined point in a
lifecycle or operation. The game developer overrides hooks to inject custom behavior.

- **Engineering analog:** Template Method pattern / extension point / lifecycle callback.
- **Naming convention:** `at_<event>` (e.g., `at_object_creation`, `at_pre_move`,
  `at_post_puppet`, `at_msg_receive`).
- **Key rule:** Always call `super()` unless you explicitly intend to replace the
  framework's default behavior for that hook.

### Mixin

A plain Python class (not a typeclass) that provides shared methods to multiple
typeclasses via multiple inheritance.

- **Engineering analog:** Mixin / trait (in the language-feature sense, not Evennia's
  `TraitHandler`).
- **Key rule:** Mixins must not inherit from Django models or typeclass base classes.
  They are behavior-only. Listed BEFORE the framework base class in the MRO.
- **Examples:** `ObjectParent` (shared by all location-having objects), `LivingMixin`
  (shared by PCs and NPCs).

### Lock

An access-control rule string evaluated at runtime. Locks are stored on typeclass
instances and checked via `obj.access(caller, access_type)`.

- **Engineering analog:** ACL entry / permission predicate.
- **Syntax:** `"access_type:lockfunc(args)"` — e.g., `"edit:perm(Builder)"`.
- **Key property:** Evaluated dynamically — a lock can check permissions, object
  state, or custom functions. Multiple lock types can coexist on one object.

### dbref

The unique database reference identifier for any typeclass instance, in the format
`#<integer>` (e.g., `#42`).

- **Engineering analog:** Primary key / object ID.
- **Key properties:**
  - Auto-assigned by the framework on object creation. Not developer-controlled.
  - Stable across server restarts.
  - Used by `evennia.search_object("#42")` and in-game commands for unambiguous
    targeting.
  - NOT a substitute for Tags or Prototypes for categorization. Do not build
    VNUM-like registries on top of dbrefs.

---

## Game Logic Concepts

### Rules Module

A Python module containing game mechanics (dice rolling, hit resolution, saving
throws, experience calculation) as pure functions or stateless utility classes.

- **Engineering analog:** Pure function module / stateless domain service.
- **Key properties:**
  - Imported by typeclasses, handlers, and commands.
  - Does NOT import from commands or send output via `msg()`.
  - Should be testable without a database or running server.
  - Often exposes a module-level singleton: `dice = RollEngine()`.
- **Canonical location:** In the game logic package (e.g., `legacy/game/rules.py`).

### Enums Module

A Python module defining all game constants as `enum.Enum` subclasses.

- **Engineering analog:** Constants / enumeration types.
- **Purpose:** Eliminates magic strings and magic numbers. Provides IDE-discoverable,
  typo-proof constants.
- **Key rule:** Depends on nothing. Imported by everything.
- **Canonical location:** In the game logic package (e.g., `legacy/game/enums.py`).

### Prototype

A Python dictionary that defines a template for spawning domain objects with
preconfigured Attributes, Tags, Locks, and other properties.

- **Engineering analog:** Factory configuration / blueprint / data-driven template.
- **Also called:** "object prototype" in Evennia docs.
- **Key property:** Prototypes are DATA, not code. They describe WHAT to create,
  not HOW it behaves. Behavior comes from the typeclass.
- **Prototypes can inherit** from other prototypes via `"prototype_parent"`.

---

## Structural Concepts

### Game Package

The top-level Python package that contains all game-specific code (typeclasses,
handlers, commands, rules, enums). Distinguished from framework code (which lives
in the `evennia` package) and from configuration (which lives in `server/`).

- **Engineering analog:** Application module / bounded context.
- **What it contains:** Everything a developer writes to make THIS game different
  from an empty Evennia installation.
- **What it does NOT contain:** Framework code, server configuration, Django
  template overrides, batch build data files.

### Domain (Sub-Package)

A sub-package within the game logic package that groups all code related to one game
concern: its handlers, data structures, and internal utilities.

- **Engineering analog:** Module / bounded context / feature package.
- **Key rule:** A domain sub-package should be cohesive. If everything in the
  sub-package changes for the same reason, it's the right size. If unrelated
  things are grouped, it's too broad.
- **Examples:** `game/characters/`, `game/combat/`, `game/objects/`, `game/economy/`.

### Build Script

A batch file (`.ev` for commands, `.py` for Python) that creates world content
(rooms, exits, NPCs, items) by issuing creation commands or calling `create_*`
functions.

- **Engineering analog:** Database seed script / migration data.
- **Lives in:** `world/` directory. NOT in the game package.

---

## Relationship Concepts

### Session

A network connection from a player's client to the server. A player may have
multiple sessions (connections) simultaneously depending on server configuration.

- **Engineering analog:** Connection / client session.
- **NOT the same as:** Account or Character. The relationship is:
  `Session → Account → Character` (a session authenticates an account, which
  puppets a character).

### Account

A player's out-of-character identity. Handles authentication, session management,
and character selection.

- **Engineering analog:** User account / identity.
- **NOT the same as:** Character. One account can own multiple characters.

### Puppet / Puppeting

The act of an Account taking control of a Character object. While puppeted, the
player's input is processed as commands on the Character, and output from the
Character is routed to the player's session(s).

- **Engineering analog:** Binding a controller to an entity / session-entity
  association.

### Location / Contents

Every in-world domain object has a `location` (the object it is inside of) and
`contents` (the list of objects inside it). Rooms typically have no location and
contain characters, items, and exits.

- **Engineering analog:** Spatial containment hierarchy / parent-child tree.

---

## Anti-Glossary: Terms to Avoid

These terms carry baggage from other paradigms that does not map cleanly to Evennia.
Using them causes confusion.

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| "Model" (as in MVC) | Typeclasses are not passive data containers. They have behavior. | "Typeclass" or "domain object" |
| "Controller" (as in MVC) | Commands are not controllers. They're thin integration points. | "Command" |
| "Service" | Handlers are not injected global services. They're owned by specific objects. | "Handler" |
| "Component" (as in ECS) | Handlers are not data-only, interchangeable components processed by systems. | "Handler" |
| "System" (as in ECS) | There is no external "system" that processes components. Logic lives on/near the objects. | "Handler" or "rules module" |
| "Entity" (as in ECS) | Evennia objects are not ID-only entities with external components. They are rich objects. | "Domain object" or "typeclass" |
| "Repository" | There is no data access layer. Typeclasses are Active Record. | "Search" (use `evennia.search_*`) |
| "DAO" | Same reason as Repository. | Direct Attribute access or handler methods |
| "Event" (pub/sub sense) | Hooks are synchronous callbacks, not queued events. | "Hook" |
| "Middleware" | There is no middleware stack. Pre/post processing uses hooks on typeclasses or commands. | "Hook" or "at_pre_*/at_post_*" |
| "Store" / "State store" | Attributes are not a separate store — they ARE the object's state. | "Attributes" |
| "Area file" / "Zone file" | This is Diku terminology for flat-file world definitions. Evennia uses prototypes and build scripts. | "Build script" or "prototype" |
| "VNUM" | Diku-era integer ID system. Evennia uses dbref (auto-assigned) and tags (developer-assigned). | "dbref" or "tag" |
| "Spec" / "Special" | Diku term for trigger code on objects. Evennia uses hooks on typeclasses. | "Hook" |
