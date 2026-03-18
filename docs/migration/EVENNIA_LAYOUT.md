# Legacy Repository Layout

## 1. Purpose

This document defines the intended repository structure for the reimagined Legacy project.

Its purpose is not only to describe where files go, but also to explain why the layout is shaped this way.

The repository structure is part of the project’s architecture and documentation. A good layout should:

* work naturally with Evennia’s programming model
* support clear boundaries between framework integration and project-owned logic
* reduce pressure toward catch-all directories
* remain workable for a small project
* stay understandable for both human contributors and AI-assisted development

This document should be treated as the default structure and reasoning for the repository. It may evolve later if migration experience reveals a better arrangement.

## 2. Guiding Principles

### 2.1 Follow Evennia’s natural workflow

The top-level game code should preserve the main Evennia integration concepts rather than hiding them behind an unfamiliar layout.

In practice, this means keeping the framework-facing anchors recognizable:

* `commands/`
* `typeclasses/`
* `server/conf/`
* `web/`

These are the places Evennia users expect to find the main integration surfaces.

### 2.2 Keep framework integration separate from project logic

Evennia-facing code should not become the main home of gameplay rules.

The repository should make it easy to distinguish:

* command entry points and player interaction glue
* typeclass and hook integration
* project-owned gameplay logic
* world/content/build artifacts
* documentation, specs, scripts, and deployment support

### 2.3 Separate game logic from world content

The project should distinguish between:

* **game logic**: rules, subsystem behavior, policies, and reusable gameplay code
* **world content**: prototypes, help entries, area/build data, import files, batch scripts, and world-population artifacts

This is why the layout uses both `game/` and `world/`.

### 2.4 Prefer shallow, discoverable structure

The repository should remain easy to scan.

It should not become so flat that dozens of unrelated files accumulate in one directory, and it should not become so deeply nested that contributors must memorize long paths to find routine code.

### 2.5 Let structure encourage good habits

A contributor or coding agent should be nudged toward the intended architecture by the directory layout itself.

The structure should make it easier to:

* keep commands thin
* keep typeclasses thin
* keep rules in project-owned modules
* keep content artifacts separate from subsystem logic
* know where to add documentation and specs

## 3. High-Level Repository Shape

A full repository is expected to contain more than the core Evennia game package.

At a high level, the repository should look approximately like this:

```text
repo/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile
│
├── docs/
│   ├── architecture/
│   ├── best-practices/
│   ├── migration/
│   ├── plans/
│   ├── subsystem/
│   └── ...
│
├── specs/
│   └── ...
│
├── scripts/
│   ├── dev/
│   ├── build/
│   ├── import/
│   └── ...
│
├── deployment/
│   ├── docker/
│   ├── nginx/
│   └── ...
│
└── legacy/
    ├── commands/
    ├── typeclasses/
    ├── game/
    ├── world/
    ├── server/
    ├── web/
    └── tests/
```

The exact auxiliary files may evolve, but the central idea should remain stable:

* repository-level concerns live at the repository root
* the Evennia game directory lives in a dedicated project folder
* the game directory remains recognizable to Evennia contributors

## 4. Repository-Level Directories

## 4.1 `docs/`

Project documentation lives here.

This should include:

* Project Vision
* Coding Guide
* Workflow and Spec Process
* Evennia Programming Guide
* Architecture Map
* subsystem architecture documents
* migration notes
* future AI-oriented guidance

Recommended substructure:

```text
docs/
├── architecture/
├── best-practices/
├── migration/
├── plans/
├── subsystem/
└── ...
```

The `docs/best-practices/` area is the right place for style and working-guideline documents.

The `docs/plans/` area holds planning documents and roadmaps.

## 4.2 `specs/`

Feature specs created through spec-driven development live here.

This directory is for feature-level planning artifacts, not for subsystem architecture documents or broad design essays.

Use this for nontrivial feature additions and behavior changes where a spec is warranted.

## 4.3 `scripts/`

Repository utility scripts live here.

These are project and developer utilities, not gameplay code.

Typical uses:

* local development helpers
* build and packaging scripts
* import/export helpers
* migration support tooling
* convenience wrappers around uv, Docker, or deployment tasks

Recommended substructure:

```text
scripts/
├── dev/
├── build/
├── import/
└── ...
```

Do not put core game logic here.

## 4.4 `data/`

Stored flat-file content and migration artifacts live here.

This may include:

* import source files from Legacy or related tools
* exported data snapshots
* intermediate transformation artifacts
* reference content used during migration

Recommended substructure:

```text
data/
├── import/
├── exports/
└── source/
```

This directory is for data artifacts, not for runtime game logic.

## 4.5 `deployment/`

Deployment-related assets that are broader than a single `docker-compose.yml` or `Dockerfile` can live here.

Examples:

* container configuration
* reverse-proxy configuration
* production-specific support files

If deployment remains simple, some of these files may stay at the repository root instead.

## 4.6 Root files

The repository root is the right place for project-level tooling and metadata such as:

* `pyproject.toml`
* `uv.lock`
* `.python-version`
* `.env.example`
* `README.md`
* `docker-compose.yml`
* `Dockerfile`

These belong at the top level because they describe the repository as a whole rather than the game package alone.

## 5. The Evennia Game Directory

The Evennia project itself lives in a dedicated directory, here shown as `legacy/`.

This is the main game directory and should remain recognizable as an Evennia project.

Its high-level structure should look like this:

```text
legacy/
├── commands/
├── typeclasses/
├── game/
├── world/
├── server/
├── web/
└── tests/
```

This structure deliberately keeps the major Evennia-facing anchors visible while separating project-owned logic from world/content artifacts.

## 6. Core Game Directory Structure

## 6.1 `commands/`

This directory contains command entry points and cmdset wiring.

Responsibilities:

* player input entry points
* command parsing and routing
* command availability organization
* account, character, and unlogged-in cmdset definitions
* player-facing integration glue at the command layer

Typical contents:

```text
commands/
├── command.py
├── default_cmdsets.py
├── general.py
├── combat.py
├── social.py
├── crafting.py
└── admin.py
```

Commands should usually be thin.

They should parse input, resolve context, call project-owned logic in `game/`, and present results.
They should not become the primary home of subsystem rules.

## 6.2 `typeclasses/`

This directory contains Evennia entity integration.

Responsibilities:

* Accounts, Characters, Rooms, Exits, Objects, Scripts, Channels
* framework hooks
* attaching domain helpers or subsystem capabilities
* entity-level integration surfaces
* state access points where appropriate

Typical contents:

```text
typeclasses/
├── accounts.py
├── channels.py
├── characters.py
├── exits.py
├── objects.py
├── rooms.py
└── scripts.py
```

Typeclasses should remain relatively thin.

They are allowed to contain real entity behavior where that behavior genuinely belongs to the entity, but they should not become dumping grounds for broad subsystem logic.

## 6.3 `game/`

This directory contains the project-owned gameplay code.

This is the main home for:

* subsystem logic
* rules
* policies
* calculations
* helper objects that belong to a specific domain
* reusable gameplay modules

This is where the project’s internal architecture should be most visible.

Recommended shape:

```text
game/
├── __init__.py
├── enums.py
├── rules.py
├── utils.py
├── characters/
├── objects/
├── combat/
├── effects/
├── progression/
├── quests/
├── economy/
├── social/
└── content/
```

This directory is intentionally distinct from `world/`.

`game/` is for code and subsystem logic.
`world/` is for content/build/world artifacts.

### Why `game/` exists

Without `game/`, there is pressure to bury gameplay logic in:

* `commands/`
* `typeclasses/`
* a broad and ambiguous `world/`

`game/` provides a clear home for project-owned logic while still allowing the top-level Evennia structure to remain recognizable.

## 6.4 `world/`

This directory contains world/content/build artifacts rather than the main body of gameplay logic.

Use it for:

* prototypes
* help entries
* build scripts
* area/world population files
* import-adjacent content artifacts
* reproducible world-building assets

Recommended shape:

```text
world/
├── prototypes.py
├── help_entries.py
├── build.ev
├── build.py
├── areas/
└── import/
```

This directory should not become a miscellaneous bucket for arbitrary subsystem code.

The guiding distinction is:

* if it is primarily **game logic**, it belongs in `game/`
* if it is primarily **world content or build artifact**, it belongs in `world/`

## 6.5 `server/`

This directory contains Evennia server configuration and server-level hooks.

This should remain in the location Evennia expects.

Typical contents:

```text
server/
└── conf/
    ├── settings.py
    ├── lockfuncs.py
    ├── at_initial_setup.py
    └── at_server_startstop.py
```

This directory is framework-critical and should not be relocated.

## 6.6 `web/`

This directory contains web-facing customizations.

Use it for:

* Django template overrides
* static assets where appropriate
* web-specific project code that belongs to the Evennia web layer

It should mirror the needs of the Evennia web structure rather than forcing a separate parallel architecture.

## 6.7 `tests/`

This directory contains project tests.

Recommended shape:

```text
tests/
├── test_rules.py
├── test_characters.py
├── test_combat.py
├── test_commands.py
└── ...
```

Tests should cover:

* project-owned rules and subsystem behavior
* boundary integration where Evennia interaction matters

This directory may later grow internal structure if the test suite becomes large enough to justify it.

## 7. Recommended `game/` Substructure

The `game/` package should be shallow and domain-oriented.

The exact domains may evolve, but a typical shape might look like this:

```text
game/
├── __init__.py
├── enums.py
├── rules.py
├── utils.py
│
├── characters/
│   ├── __init__.py
│   ├── identity.py
│   ├── chargen.py
│   ├── races.py
│   ├── classes.py
│   └── npcs.py
│
├── objects/
│   ├── __init__.py
│   ├── equipment.py
│   ├── containers.py
│   └── items.py
│
├── combat/
│   ├── __init__.py
│   ├── handler.py
│   ├── actions.py
│   └── skills.py
│
├── effects/
│   ├── __init__.py
│   ├── buffs.py
│   ├── conditions.py
│   └── timers.py
│
├── progression/
│   ├── __init__.py
│   ├── stats.py
│   ├── skills.py
│   └── advancement.py
│
├── quests/
│   ├── __init__.py
│   ├── tracker.py
│   └── definitions.py
│
├── economy/
│   ├── __init__.py
│   ├── currency.py
│   ├── shops.py
│   └── crafting.py
│
├── social/
│   ├── __init__.py
│   ├── channels.py
│   ├── organizations.py
│   └── reputation.py
│
└── content/
    ├── __init__.py
    ├── importers.py
    ├── translators.py
    └── factories.py
```

This is an example, not a locked final package map.

The important rules are:

* keep it shallow
* organize by domain concern
* keep helper/handler objects with their domain
* avoid a generic `handlers/` bucket
* avoid deeply nested trees

## 8. Why There Is No Top-Level `handlers/` Directory

This layout intentionally does not include a top-level `handlers/` directory.

Reasoning:

* In Evennia practice, helper/handler-style objects are common.
* But they are most useful when attached to and understood within a domain.
* A generic `handlers/` directory encourages a grab-bag of weakly related helper objects.

Instead:

* an equipment helper belongs in `game/objects/equipment.py`
* a quest tracker belongs in `game/quests/tracker.py`
* an AI helper belongs in the domain that owns NPC behavior

The pattern is valid.
The bucket is not.

## 9. Dependency and Responsibility Flow

The intended direction of responsibility is:

* `commands/` receives player input and routes intent
* `typeclasses/` provides framework-bound entities and hooks
* `game/` owns rules, policies, and subsystem logic
* `world/` provides content/build artifacts consumed by the system
* `server/` and `web/` provide framework integration surfaces

A healthy dependency flow usually looks like:

* commands call into `game/`
* typeclasses mount or call into `game/`
* `game/` may use Evennia abstractions where necessary, but should remain as project-owned as practical
* `world/` supplies data, prototypes, and build material rather than acting as the main gameplay logic layer

## 10. Practical Placement Rules

When adding a new file or module, use these rules.

### Put it in `commands/` if:

* it is primarily a player command
* it defines cmdsets or command availability
* it exists to parse input and route to other code

### Put it in `typeclasses/` if:

* it defines an Evennia entity typeclass
* it exists mainly to provide hooks or entity behavior at the framework boundary
* it mounts subsystem capabilities or exposes entity-local behavior

### Put it in `game/` if:

* it defines subsystem logic
* it implements calculations, rules, or policies
* it is a helper object tightly tied to a domain
* it should be reusable across commands and typeclasses

### Put it in `world/` if:

* it is a prototype or content definition
* it is a build or population script
* it is a help entry file
* it is a content import or world artifact rather than a runtime subsystem module

### Put it in `scripts/` at repository root if:

* it is a developer utility or repository task script
* it is not part of runtime gameplay behavior

### Put it in `docs/` if:

* it is explanatory or policy documentation
* it is not runtime code or build data

## 11. What to Avoid

Avoid the following structural failure modes.

### 11.1 Treating `world/` as a dump-everything bucket

`world/` should not become the default home for all code that does not obviously fit elsewhere.

### 11.2 Burying subsystem logic inside commands or typeclasses

These are integration surfaces, not the ideal home for large rulesets.

### 11.3 Creating generic utility buckets

Avoid directories such as `handlers/`, `helpers/`, or `misc/` unless they represent a truly coherent and stable concept.

### 11.4 Deep nesting

Do not build a tree that requires contributors to navigate multiple nested levels for ordinary work.

### 11.5 Mixing repository tooling with game runtime code

Developer utilities, deployment helpers, migration data, and gameplay modules should not be intermixed casually.

## 12. Naming Guidance

### Repository and package names

The Evennia game directory is shown here as `legacy/`, but the final package name should be chosen carefully.

It should be:

* short
* unambiguous
* appropriate for import paths
* unlikely to collide with unrelated packages

### Module naming

Prefer names that reflect domain responsibility clearly.

Good examples:

* `equipment.py`
* `advancement.py`
* `currency.py`
* `tracker.py`
* `identity.py`

Avoid overly generic names such as:

* `common.py`
* `misc.py`
* `helpers.py`
* `stuff.py`

unless the module genuinely has a narrowly defined shared purpose.

## 13. Evolution Rules

The layout is allowed to evolve, but it should evolve deliberately.

A new package or directory is justified when:

* a domain has grown large enough that its responsibilities are no longer clear in one module
* a coherent subsystem has emerged that deserves its own boundary
* a content/build area needs its own organization
* test structure has grown large enough to require subdivision

Do not introduce new structure solely to satisfy abstract architectural neatness.

## 14. Summary

The intended repository layout is built around a simple idea:

* keep Evennia integration surfaces recognizable
* keep project-owned gameplay logic in a clear home
* separate game logic from world/content artifacts
* keep repository-level tooling and documentation outside the game package

That leads to a structure where:

* `commands/` handles command entry points
* `typeclasses/` handles Evennia entity integration
* `game/` holds subsystem logic and project-owned code
* `world/` holds content/build/world artifacts
* `server/` and `web/` remain where Evennia expects them
* repository-level concerns live outside the game package

This is the default layout for the reimagined Legacy repository unless later project experience reveals a better fit.
