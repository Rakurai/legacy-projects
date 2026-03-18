# EVENNIA_MODEL.md — Conceptual Architecture of an Evennia Game

> **Purpose:** Describe what an Evennia game project IS, in established software engineering
> terms, without game-specific jargon. This document gives engineers and AI agents the
> vocabulary to reason about, discuss, and implement game systems without ambiguity.

---

## The One-Paragraph Summary

An Evennia game is a **persistent object domain model** where every significant entity
in the world is a **domain object** that lives in a database and exposes behavior through
methods. Domain objects compose specialized behavior by delegating to **handler objects**
attached via lazy properties. Players interact with the domain exclusively through a
**text command pipeline** — a chain of processing steps that resolves raw input into a
named **command object**, which parses its arguments, delegates work to domain objects
or pure-logic modules, and emits output back through the domain object's messaging
interface. The framework provides the persistence layer, the networking layer, and the
command dispatch infrastructure; the game developer's job is to define domain objects
(by subclassing framework base classes), compose handlers onto them, write commands that
orchestrate interactions, and isolate game rules into standalone modules.

---

## The Architecture in Detail

### 1. Persistent Domain Objects (Typeclasses)

The central organizing concept. Every entity that matters in the game world — a character,
a room, an item, an NPC, a background process — is represented by a **persistent domain
object**.

**What they are, in engineering terms:**

- They follow the **Active Record** pattern: the object IS the database record. It
  contains both data (persisted to the database) and behavior (methods that operate on
  that data). There is no separate "data access object" or "repository" layer — the
  domain object handles its own persistence.
- They use **class inheritance** as the primary extension mechanism. The framework
  provides base classes (`DefaultCharacter`, `DefaultRoom`, `DefaultObject`, etc.).
  The game developer creates subclasses that add game-specific data and behavior.
  The framework calls this "the typeclass system."
- They have **transparent persistence**. Fields declared on the object (via
  `AttributeProperty` or the `.db` accessor) are automatically stored in and loaded
  from the database. The developer does not write SQL, manage ORM queries for
  individual attribute access, or call `.save()` for attribute changes.
- They have **identity**. Every domain object has a unique database ID (`dbref`),
  a primary name (`key`), and can be found by search. They are not throwaway value
  objects — they are long-lived entities with lifecycle hooks.

**What they are NOT:**

- NOT plain data containers. They have methods. They can act.
- NOT raw database models. The framework handles persistence transparently;
  developers work with typeclass subclasses, not with the underlying ORM layer.
- NOT stateless. They hold mutable state (Attributes, Tags, location) across server
  restarts.

**The lifecycle hooks** are the **Template Method** pattern. The framework defines the
skeleton of operations (object creation, object movement, receiving a message, being
looked at) and calls hook methods at defined extension points (`at_object_creation`,
`at_pre_move`, `at_msg_receive`, `return_appearance`, etc.). The game developer
overrides hooks to inject game-specific behavior without replacing framework logic.

### 2. Behavioral Composition (Handlers)

Domain objects gain focused capabilities through **handler objects** — small,
single-responsibility classes that manage one aspect of the domain object's state.

**What they are, in engineering terms:**

- They are the **Delegate** pattern (or **Strategy** pattern, depending on usage).
  The domain object does not implement equipment management, quest tracking, or AI
  logic directly. It delegates to a handler that encapsulates that concern.
- They are instantiated via `@lazy_property` on the owning domain object. This means
  they are created on first access and cached for the lifetime of the object in memory.
- They store all persistent data through the owning object's Attribute system
  (`self.obj.attributes`). They do not have their own database tables.
- They expose an **API surface** — a set of methods that commands, hooks, and other
  handlers call. The handler IS the interface to a subsystem.

**Example in abstract terms:**

```
DomainObject
  ├── @lazy_property → EquipmentDelegate   (manages slot-based inventory)
  ├── @lazy_property → QuestDelegate       (manages quest state machine)
  ├── @lazy_property → BuffDelegate        (manages timed stat modifiers)
  └── @lazy_property → CombatDelegate      (manages combat state, or is a Script)
```

The handler pattern replaces what other architectures might call "services,"
"components," or "managers." In Evennia, handlers are:
- **Owned by** a specific domain object (not global singletons)
- **Co-located with** their domain concern (not in a separate `services/` layer)
- **Stateless in memory** — all persistent state lives in the owning object's Attributes

### 3. The Command Pipeline (Input Processing)

Players do not call methods on domain objects directly. All interaction flows through a
**command pipeline** — a fixed sequence of processing steps that the framework executes
on every line of player input.

**The pipeline, in engineering terms:**

```
Raw Text Input
  │
  ▼
1. Gather Command Sets ─── Collect available commands from the caller,
  │                        their location, objects present, and account.
  ▼                        (This is capability/context resolution.)
2. Merge Command Sets ──── Combine sets using priority and merge rules.
  │                        (Union, intersection, or replacement.)
  ▼
3. Parse & Match ────────── Find the Command object whose key/aliases
  │                         match the input. (Pattern matching.)
  ▼
4. Instantiate & Prime ─── Clone the Command prototype, attach caller,
  │                        session, and raw input as instance state.
  ▼
5. Execute Hooks ────────── Call at_pre_cmd() → parse() → func() → at_post_cmd()
  │                         in sequence. parse() breaks input into arguments.
  ▼                         func() performs the action.
6. Output ────────────────── Results are sent back via domain object msg().
```

**What commands are, in engineering terms:**

- Each command is an instance of the **Command pattern** (GoF). It encapsulates a user
  action as an object with `parse()` and `func()` methods.
- Commands are **thin integration points**. They should parse input, delegate to domain
  objects or rule modules for actual logic, and format output. They should NOT contain
  business logic. The rule of thumb: if a command's `func()` method contains math,
  conditionals about game state, or database mutations beyond simple delegation, the
  logic belongs in a handler or rules module instead.
- Commands are **stateless between invocations**. The framework reuses command class
  instances — do not store mutable state on `self` that persists across calls.
- **Command Sets** are the **capability system**. They determine what a player CAN DO
  in a given context. Entering a shop can add shop commands; entering combat can add
  combat commands and remove movement commands. CmdSets are merged dynamically using
  set-theoretic operations (union, intersection, replacement).

### 4. Pure Logic Modules (Rules)

Game rules — dice rolling, hit resolution, saving throws, experience calculation — live
in **standalone Python modules** that are decoupled from the framework.

**What they are, in engineering terms:**

- They are **pure functions or stateless utility classes**. They take input values
  (numbers, enum values, domain objects) and return results. They do not persist
  data, they do not send messages, they do not know about the command pipeline.
- They represent the "rulebook" — the authoritative source of game mechanics.
- They are the most testable part of the codebase: no database, no framework, just
  input → output.
- The recommended form is a **class that groups related functions**, instantiated as a
  **module-level singleton** for convenient import (e.g., `dice = RollEngine()`).

### 5. Autonomous Processes (Scripts)

Some game behavior is not triggered by player input — weather cycles, NPC wandering,
timed effects, combat rounds. These are handled by **scripts**: persistent domain
objects that have a timer and execute code on a schedule.

**What they are, in engineering terms:**

- They are **scheduled tasks with persistent state**. They survive server restarts.
- They can be attached to a domain object (an NPC's AI tick, a room's weather cycle)
  or run globally (a server-wide economy tick).
- When used as a handler (e.g., `CombatHandler`), they are domain objects that
  coordinate multi-actor interactions over time. This makes them both a handler
  AND a persistent timer — a unique Evennia pattern.
- They follow the same typeclass inheritance model as all other domain objects.

### 6. Persistent Key-Value Storage (Attributes)

All domain-object state that isn't a core database field (key, location, typeclass_path)
is stored through the **Attribute system** — a key-value store attached to every domain
object.

**What it is, in engineering terms:**

- It is a **schema-free persistence layer**. Any Python-picklable value can be stored
  under any string key, on any domain object, without migration or schema changes.
- `AttributeProperty` provides a **descriptor-based** (declarative) interface that
  makes Attributes look like regular class fields, with defaults and type information.
- The `.db` accessor provides a **dynamic** (imperative) interface: `obj.db.health = 100`.
- Handlers use this system internally — their data IS Attribute data on the owning object.

### 7. Identity, Search, and References (Tags)

Domain objects are found and grouped using **Tags** (lightweight string labels) and
**search functions** (query by key, tag, typeclass, or location).

**What they are, in engineering terms:**

- Tags are a **labeling/classification system** — like database indexes you can
  query. They have a key, an optional category, and are very fast to filter on.
- There are no foreign-key references between game objects in the traditional ORM
  sense for game-specific relationships. Instead, objects reference each other by
  storing `dbref` or using tags/search. The Attribute system can also store direct
  object references.

### 8. Rendering & Output

Presentation is a significant concern in an Evennia game. Formatting text,
constructing descriptions, and producing perspective-appropriate messages all
involve real logic. Evennia distributes this as a **responsibility of domain
objects and commands** rather than isolating it in a separate architectural tier.

The pattern is **server-side rendering with self-describing domain objects.**

**The rendering toolkit:**

| Function / Pattern | What it does | Web analog |
|---|---|---|
| `msg_contents()` + actor-stance parser | Renders a perspective-aware template with object data. Caller sees "You attack the goblin," bystander sees "The warrior attacks the goblin." | Server-side template engine (Jinja, Django templates) |
| `return_appearance()` and `get_display_*()` hooks | Domain objects render their own visual representation for a given viewer. | A view/partial that serializes a model for display |
| `EvTable`, `EvForm` | Construct formatted tabular/form text output. | HTML helper / UI component library |
| ANSI markup (`|r`, `|b`, etc.) | Inline styling of output text. | CSS / inline styles |
| `msg()` | Delivers rendered output to the client's session. | Writing to the HTTP response body |
| The MUD client (terminal, web client) | Interprets ANSI codes, MXP, GMCP directives. | The browser rendering engine |

**How it works:**

- **Domain objects own their own presentation.** `return_appearance()`,
  `get_display_name()`, `get_display_desc()`, and similar hooks mean the object
  itself is the authority on how it looks to a given viewer.
- **Commands format their results.** The command's `func()` builds output strings
  — often by calling rendering methods on domain objects or using formatting
  utilities — and sends them via `msg()`.
- **`msg_contents()` is a template renderer.** It takes a template string with
  placeholders, fills in data from domain objects, and produces different output
  per observer based on perspective (e.g., caller sees "You attack the goblin,"
  bystander sees "The warrior attacks the goblin").
- **The client is a rendering terminal.** It interprets markup (ANSI color codes,
  MXP tags, GMCP data) but does not generate content. Advanced clients can accept
  processing directives that manipulate the presentation.

**Where presentation logic lives:**

1. **On domain objects** — hooks like `return_appearance()` and `get_display_name()`.
2. **In commands** — `func()` methods that format and send output.
3. **In shared rendering utilities** — `EvTable`, `EvForm`, ANSI helpers, and any
   game-specific formatting functions.

Presentation code should be **identifiable and separable** even though it does not
live in a dedicated directory. A `return_appearance()` override that performs
business-logic queries is mixing concerns. A command `func()` with extensive
string formatting should extract that rendering into a method on the domain object
or a utility function.

For the Django **web interface** (`web/`), standard MVC applies: Django views read
from the database and render HTML templates. This is a secondary access path for
out-of-game browsing, not the primary game interaction.

---

## What This Is NOT

To prevent false mappings from other paradigms:

| Paradigm | Why it does not apply cleanly |
|----------|------------------------------|
| **MVC** | Presentation logic exists (see §8) but is distributed across domain objects and commands, not isolated in a separate tier. Domain objects render themselves via hooks; commands format their own output; `msg_contents()` provides template rendering. Commands are thin use-case objects that delegate to domain objects, not controllers. The Django web interface (`web/`) IS MVC, but it is a secondary access path. |
| **Entity-Component-System (ECS)** | Evennia uses **class inheritance**, not data-oriented component composition. Handlers add behavior via delegation, but they are not "components" in the ECS sense — they are not interchangeable, not data-driven, and not processed by external "systems." |
| **Microservices** | The game runs as a single server process, with a separate I/O proxy (Portal). This is a two-process deployment model, not a service mesh. |
| **Event-Driven Architecture** | Hooks exist, but the primary flow is synchronous: input → pipeline → output, all in one call chain. There is no event bus, no pub/sub, no eventual consistency. Django signals exist for limited cross-cutting concerns. |
| **Repository Pattern** | There are no repositories. Domain objects ARE their own persistence (Active Record). You don't "fetch" an object through a repository — you search for it, and the returned object includes both state and behavior. |
| **Service Layer** | There is no separate "service" layer between commands and domain objects. Handlers on domain objects serve the role that services play in layered architectures, but they are owned by and attached to specific domain objects, not injected or global. |

---

## The Dependency Direction

The healthy dependency flow in an Evennia game:

```
   ┌──────────────────────────────────────────────────────────────┐
   │  Constants / Enums   (depends on nothing)                    │
   └──────────────┬───────────────────────────────────────────────┘
                  │
   ┌──────────────▼───────────────────────────────────────────────┐
   │  Rules Module         (depends on: enums)                    │
   └──────────────┬───────────────────────────────────────────────┘
                  │
   ┌──────────────▼───────────────────────────────────────────────┐
   │  Domain Objects       (depends on: enums, rules, framework)  │
   │  (Typeclasses +       typeclasses, handlers, mixins          │
   │   Handlers)                                                  │
   └──────────────┬───────────────────────────────────────────────┘
                  │
   ┌──────────────▼───────────────────────────────────────────────┐
   │  Commands             (depends on: domain objects, rules,    │
   │  (Input processing)    enums)                                │
   └──────────────┬───────────────────────────────────────────────┘
                  │
   ┌──────────────▼───────────────────────────────────────────────┐
   │  Command Sets         (depends on: commands)                 │
   │  (Capability groups)                                         │
   └──────────────────────────────────────────────────────────────┘
```

**The arrow points DOWN.** Commands depend on domain objects; domain objects do NOT depend
on commands. Rules depend on nothing game-specific. Enums depend on nothing at all.

Violating this direction (e.g., a handler that imports a command, or a rules module that
calls `msg()`) is a design error.
