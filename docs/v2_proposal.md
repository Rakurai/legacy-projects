# V2 Stage 0 Proposal: Document Cleanup

Reference: [DESIGN_v2.md §5.2–§5.3](../.ai/mcp/doc_server/DESIGN_v2.md), [v2_indexing.md §5.6](../.ai/mcp/doc_server/v2_indexing.md)

All changes below are architectural: file layout, YAML frontmatter, heading tags, and content ownership reassignment. No prose rewriting.

---

## `admin_controls.md` → RENAME to `admin_tools.md`

- Add frontmatter:
  ```yaml
  ---
  id: admin_tools
  name: Admin Tools
  kind: system
  layer: operations
  parent: null
  depends_on: [character_data, object_system, world_system, persistence, command_interpreter]
  depended_on_by: [quests]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` (Command Categories, Administrative Systems) → split into multiple tagged ##:
    - `## Admin Command Architecture` `<!-- section: key_components | grounding: mixed -->` — command categories, permission tiers
    - `## WIZnet & Monitoring` `<!-- section: key_components | grounding: mixed -->` — WIZnet flags, admin notification
    - `## Punishment & Moderation` `<!-- section: key_components | grounding: mixed -->`
    - `## Disabled Commands` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->` — wiz_admin.cc, wiz_coder.cc, wiz_gen.cc, wiz_quest.cc, wiz_secure.cc, Disabled.cc, Logging.cc
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- WIZnet content currently in admin_controls.md overlaps with logging_and_monitoring.md's WIZnet Monitoring section — keep WIZnet in this file as it's admin-facing; logging_and_monitoring.md's copy goes to utilities.md as a reference note only.
- The "Depended On By" subsections listing human roles ("Game Administrators", "Content Creators", "Players") are not V2-relevant dependency edges — drop them from the Dependencies section. Only retain system-to-system edges.

---

## `builder_commands.md` → RENAME to `builder_tools.md`

- Add frontmatter:
  ```yaml
  ---
  id: builder_tools
  name: Builder Tools
  kind: system
  layer: operations
  parent: null
  depends_on: [character_data, object_system, world_system, admin_tools, command_interpreter]
  depended_on_by: []
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## World Building Tools` `<!-- section: key_components | grounding: mixed -->` — area/room/exit creation
    - `## Entity Creation Tools` `<!-- section: key_components | grounding: mixed -->` — object/mobile creation
    - `## Prototype Management` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->` — wiz_build.cc
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- The "Depended On By" subsections listing human roles ("Content Creators", "Game Administrators") are not V2-relevant dependency edges — drop them.

---

## `character_system.md` → DISSOLVE

- **Delete** after redistribution.
- Content redistribution map (section → target file):
  - `## Overview`, `## Responsibilities` → portions to each target based on topic
  - `### Character Entities` (Character, Player, MobilePrototype, DepartedPlayer) → `character_data.md`
  - `### Scripting and Behavior (NPC AI System)` (MobProg, MobProgActList) → `mobprog_npc_ai.md`
  - `### Combat System` (entire subsection) → `combat.md`
  - `### Magic System` (entire subsection) → `magic.md`
  - `### Affect System` (entire subsection) → `affect_system.md`
  - `### Data Tables (Character-Related)` → split: race/guild tables → `character_data.md`, skill/spell tables → `skills_progression.md`, attack type tables → `combat.md`
  - `### Skills and Progression` → `skills_progression.md`
  - `## Implementation Details > Character Implementation` → `character_data.md`
  - `## Implementation Details > Player Implementation` → `character_data.md`
  - `## Implementation Details > NPC Implementation` → `mobprog_npc_ai.md` (AI/MobProg parts) + `character_data.md` (prototype/respawn parts)
  - `## Implementation Details > Combat Implementation` → `combat.md`
  - `## Key Files` — redistribute per file relevance:
    - Character.hh/cc, Player.hh/cc, MobilePrototype.hh, DepartedPlayer.hh, RollStatsState.cc, ReadNewMOTDState.cc → `character_data.md`
    - fight.cc, effects.cc, dispel.cc, Battle.hh → `combat.md`
    - magic.cc, rmagic.cc, magic.hh → `magic.md`
    - affect/*.cc/hh → `affect_system.md`
    - mob_prog.cc, mob_commands.cc, MobProg.hh, MobProgActList.hh → `mobprog_npc_ai.md`
    - skills.cc, set-stat.cc, remort.cc → `skills_progression.md`
    - const.cc, tables.hh/cc, merc.hh → shared reference; primary home in `character_data.md`, cross-referenced from `object_system.md`, `combat.md`, `skills_progression.md`
  - `## System Behaviors` → redistribute per topic
  - `## Dependencies and Relationships` → rebuild per target file

---

## `character_data.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: character_data
  name: Character Data
  kind: system
  layer: data_model
  parent: null
  depends_on: [world_system, object_system, affect_system]
  depended_on_by: [combat, magic, skills_progression, command_interpreter, quests, social_communication, persistence, admin_tools, builder_tools]
  ---
  ```
- Receives: Character/Player/MobilePrototype entity docs, character implementation details, creation flow, stat system, race/guild data tables from dissolved `character_system.md`.
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Character Entities` `<!-- section: key_components | grounding: grounded -->` — Character, Player, MobilePrototype, DepartedPlayer
  - `## Attribute & Stat System` `<!-- section: key_components | grounding: mixed -->` — core stats, derived stats, stat modification
  - `## Character Creation` `<!-- section: implementation | grounding: mixed -->` — creation flow, rolling, race/class selection
  - `## Data Tables` `<!-- section: key_components | grounding: grounded -->` — race_table, guild_table references
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `combat.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: combat
  name: Combat
  kind: system
  layer: game_mechanic
  parent: null
  depends_on: [character_data, affect_system, object_system, world_system]
  depended_on_by: [quests, clans_pvp, mobprog_npc_ai]
  ---
  ```
- Receives: Combat System subsection, Combat Implementation subsection, fight.cc/effects.cc/dispel.cc file entries, attack_table from dissolved `character_system.md`.
- Receives: combat-related content from dissolved `status_and_look_commands.md` (Combat Readiness subsection).
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Attack Resolution` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Damage Pipeline` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Death & Corpse Processing` `<!-- section: key_components | grounding: mixed | role: edge_case -->`
  - `## Defensive Mechanics` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Group Combat` `<!-- section: behaviors | grounding: mixed -->`
  - `## Flee & Recall` `<!-- section: behaviors | grounding: mixed -->`
  - `## Battle/Arena Mode` `<!-- section: behaviors | grounding: mixed | role: edge_case -->`
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `magic.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: magic
  name: Magic
  kind: system
  layer: game_mechanic
  parent: null
  depends_on: [character_data, affect_system, object_system, skills_progression]
  depended_on_by: [combat, mobprog_npc_ai]
  ---
  ```
- Receives: Magic System subsection, magic.cc/rmagic.cc file entries from dissolved `character_system.md`.
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Spell Casting` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Spell Library` `<!-- section: key_components | grounding: mixed -->`
  - `## Remort Spells` `<!-- section: key_components | grounding: mixed -->`
  - `## Object Casting` `<!-- section: key_components | grounding: mixed | role: mechanism -->` — wands, staves, scrolls, potions
  - `## Saves & Verbal Components` `<!-- section: behaviors | grounding: mixed -->`
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `affect_system.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: affect_system
  name: Affect System
  kind: system
  layer: game_mechanic
  parent: null
  depends_on: [character_data, object_system]
  depended_on_by: [combat, magic, skills_progression, world_system]
  ---
  ```
- Receives: Affect System subsection, all affect/*.cc/hh file entries from dissolved `character_system.md`.
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Affect Application & Removal` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Character Affects` `<!-- section: key_components | grounding: mixed -->`
  - `## Object Affects` `<!-- section: key_components | grounding: mixed -->`
  - `## Room Affects` `<!-- section: key_components | grounding: mixed -->`
  - `## Stacking & Caching` `<!-- section: implementation | grounding: mixed | role: mechanism -->`
  - `## Affect Table` `<!-- section: key_components | grounding: grounded -->`
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `skills_progression.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: skills_progression
  name: Skills & Progression
  kind: system
  layer: game_mechanic
  parent: null
  depends_on: [character_data, affect_system]
  depended_on_by: [combat, magic, quests]
  ---
  ```
- Receives: Skills and Progression subsection, skills.cc/set-stat.cc/remort.cc, skill/spell tables, skill group tables from dissolved `character_system.md`.
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Practice & Gain` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Level Advancement` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Remort System` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Skill & Spell Tables` `<!-- section: key_components | grounding: grounded -->`
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `command_interpreter.md` → KEEP (rename not needed, id matches)

- Add frontmatter:
  ```yaml
  ---
  id: command_interpreter
  name: Command Interpreter
  kind: system
  layer: infrastructure
  parent: null
  depends_on: [character_data, networking]
  depended_on_by: [combat, magic, social_communication, economy, quests, admin_tools, builder_tools, mobprog_npc_ai]
  ---
  ```
- Absorbs: alias system content from dissolved `user_experience_enhancers.md` (alias.cc, alias definition, parameter substitution).
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Add new `## Alias System` `<!-- section: key_components | grounding: grounded -->` section with alias content.
- Drop "Depended On By > All Gameplay Systems" — replace with V2 system ID edges.
- The Connection System subsection under Core Components (conn::State, login states) is Networking content — flag for relocation to `networking.md` or cross-reference.

---

## `economy.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: economy
  name: Economy
  kind: system
  layer: player_feature
  parent: null
  depends_on: [character_data, object_system, command_interpreter, social_communication]
  depended_on_by: [quests]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Auction System` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Banking System` `<!-- section: key_components | grounding: mixed -->`
    - `## Currency System` `<!-- section: key_components | grounding: mixed -->`
    - `## Shop System` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Shop System content here duplicates content in `object_system.md` — establish `economy.md` as canonical owner for shop mechanics; `object_system.md` should cross-reference.
- Drop role-based "Depended On By" entries (Player Economy, Item Distribution, etc.) — not V2 system edges.

---

## `event_dispatcher.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: event_dispatcher
  name: Event Dispatcher
  kind: support
  layer: infrastructure
  parent: null
  depends_on: []
  depended_on_by: []
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: mixed -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: mixed -->`
- Drop role-based "Depended On By" entries — not V2 system edges.

---

## `game_engine.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: game_engine
  name: Game Engine
  kind: system
  layer: infrastructure
  parent: null
  depends_on: [networking, utilities, memory_gc, persistence]
  depended_on_by: [combat, magic, affect_system, world_system, character_data, command_interpreter]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## State Management` `<!-- section: key_components | grounding: mixed -->`
    - `## Game Loop` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Entity Lifecycle` `<!-- section: key_components | grounding: grounded | role: mechanism -->`
    - `## Message Dispatch` `<!-- section: key_components | grounding: grounded | role: mechanism -->` — act() system
    - `## Boot & Shutdown` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Drop role-based "Depended On By" entries — replace with V2 system edges.

---

## `help_system.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: help_system
  name: Help System
  kind: system
  layer: content_system
  parent: null
  depends_on: [command_interpreter, persistence]
  depended_on_by: []
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- The "Dependencies On > Editor System" reference should become a cross-reference to `notes_editor.md`.
- Drop role-based "Depended On By" entries.

---

## `in_game_editor.md` → RENAME to `notes_editor.md`

- Add frontmatter:
  ```yaml
  ---
  id: notes_editor
  name: Notes & Editor
  kind: system
  layer: content_system
  parent: null
  depends_on: [command_interpreter, character_data, persistence]
  depended_on_by: [help_system]
  ---
  ```
- The current file conflates the line editor (Edit class) with Note boards. Both belong here per the V2 system list ("Notes & Editor").
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components > Editor Core` → `## Line Editor` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Core Components > Content Type Handlers` → split:
    - Note boards content → `## Note Boards` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - Description Editor, Help File Editor → cross-reference to owning systems
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: mixed -->` — note: the current text admits "no dedicated implementation file was found", tag accordingly
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Drop "Depended On By > World Building" and "Player Expression" — not V2 system edges. Keep Help System and convert to V2 ID.

---

## `logging_and_monitoring.md` → DISSOLVE into `utilities.md`

- **Delete** after redistribution.
- Content redistribution:
  - Logging Infrastructure (Logging.cc, macros.hh, severity levels) → `utilities.md` Logging & Diagnostics section
  - Tail utility → `utilities.md` (already present as File Monitoring)
  - WIZnet Monitoring subsection → `admin_tools.md` (WIZnet is admin-facing)
  - Performance Tracking, State Inspection → `utilities.md`
  - Resource Locations (log/, misc/ directories) → `utilities.md`
- Deduplicate against existing Logging and Diagnostics section already in `utilities.md`.

---

## `memory_and_gc.md` → RENAME to `memory_gc.md`

- Add frontmatter:
  ```yaml
  ---
  id: memory_gc
  name: Memory & GC
  kind: support
  layer: infrastructure
  parent: null
  depends_on: []
  depended_on_by: []
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: mixed -->`
- Drop role-based "Depended On By" — not V2 edges. The `depends_on`/`depended_on_by` arrays in frontmatter are empty for support entries (edges managed via other systems' frontmatter).

---

## `mobprog_system.md` → RENAME to `mobprog_npc_ai.md`

- Add frontmatter:
  ```yaml
  ---
  id: mobprog_npc_ai
  name: MobProg & NPC AI
  kind: system
  layer: content_system
  parent: null
  depends_on: [character_data, world_system, command_interpreter]
  depended_on_by: [quests]
  ---
  ```
- Absorbs: NPC AI/Scripting/MobProg content from dissolved `character_system.md` (MobProg subsection, MobProgActList, NPC Implementation > AI parts, mob_prog.cc, mob_commands.cc file entries).
- Absorbs: Special Functions content (spec_fun) — already present in current file, good.
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components > Script Engine` → `## Script Engine` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Core Components > Special Functions` → `## Special Functions` `<!-- section: key_components | grounding: grounded -->`
  - `## Core Components > Trigger System` → `## Trigger System` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Core Components > Execution Engine` → `## Execution Engine` `<!-- section: implementation | grounding: mixed | role: mechanism -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Drop "Depended On By > NPC AI" (self-referential) and "Dynamic World Features" — not V2 system edges.

---

## `networking.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: networking
  name: Networking
  kind: system
  layer: infrastructure
  parent: null
  depends_on: [utilities, memory_gc]
  depended_on_by: [command_interpreter, game_engine]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Connection Management` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Protocol Implementation` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Connection State Machine` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Copyover` `<!-- section: key_components | grounding: grounded | role: mechanism -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Absorbs: the `conn::State` / login-state content currently mentioned under `command_interpreter.md`'s Core Components > Connection System — that content belongs here.

---

## `object_system.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: object_system
  name: Object System
  kind: system
  layer: data_model
  parent: null
  depends_on: [world_system, affect_system]
  depended_on_by: [combat, magic, economy, quests, character_data, persistence, admin_tools, builder_tools]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Object Entities` `<!-- section: key_components | grounding: grounded -->` — Object, ObjectPrototype, ObjectValue, ExtraDescr
    - `## Item Enhancement` `<!-- section: key_components | grounding: mixed -->` — EQSocket, Gem System
    - `## Shop System` → cross-reference to `economy.md` as canonical owner; keep brief mention here
    - `## Data Tables` `<!-- section: key_components | grounding: grounded -->` — attack_table, type_table, weapon_table, flag tables
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Loot System V2 content and loot_tables.cc/lootv2.cc file entries extract to `loot_generation.md`.
- Shop System content — `economy.md` is canonical owner. Reduce to a cross-reference here.

---

## `loot_generation.md` → CREATE

- Add frontmatter:
  ```yaml
  ---
  id: loot_generation
  name: Loot Generation
  kind: system
  layer: game_mechanic
  parent: null
  depends_on: [object_system, character_data]
  depended_on_by: [combat]
  ---
  ```
- Receives: Loot System V2 content and loot table content from `object_system.md`.
- Heading structure:
  - `## Overview` `<!-- section: overview | grounding: mixed -->`
  - `## Loot Tables & Probability` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Template Item Generation` `<!-- section: implementation | grounding: mixed | role: mechanism -->`
  - `## Key Files` `<!-- section: key_components | grounding: grounded -->`
  - `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `organizations_and_pvp.md` → RENAME to `clans_pvp.md`

- Add frontmatter:
  ```yaml
  ---
  id: clans_pvp
  name: Clans & PvP
  kind: system
  layer: player_feature
  parent: null
  depends_on: [character_data, world_system, combat, command_interpreter]
  depended_on_by: []
  ---
  ```
- Absorbs: paintball minigame content from dissolved `user_experience_enhancers.md` (paint.cc, team mechanics, arena).
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components > Clan System` → `## Clan System` `<!-- section: key_components | grounding: mixed -->`
  - `## Core Components > War System` → `## War System` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Core Components > PvP Systems` → `## PvP & Duels` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- The "Guild" subsection under Clan System describes class guilds, not player organizations — clarify or relocate to `skills_progression.md` if it refers to training guilds.

---

## `persistence.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: persistence
  name: Persistence
  kind: system
  layer: operations
  parent: null
  depends_on: [character_data, object_system, world_system, utilities]
  depended_on_by: [game_engine, admin_tools]
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Database Management` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## File-Based Persistence` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
    - `## Configuration System` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Note persistence is also relevant to `notes_editor.md` (note file storage) — cross-reference, don't duplicate.

---

## `quests.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: quests
  name: Quests
  kind: system
  layer: player_feature
  parent: null
  depends_on: [character_data, world_system, object_system, command_interpreter, mobprog_npc_ai]
  depended_on_by: []
  ---
  ```
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- Drop role-based "Depended On By" entries.

---

## `social_and_communication.md` → RENAME to `social_communication.md`

- Add frontmatter:
  ```yaml
  ---
  id: social_communication
  name: Social & Communication
  kind: system
  layer: player_feature
  parent: null
  depends_on: [character_data, command_interpreter, world_system]
  depended_on_by: [economy, clans_pvp]
  ---
  ```
- Absorbs: marriage system content from dissolved `user_experience_enhancers.md` (marry.cc, proposal/ceremony/divorce mechanics).
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components > Channel System` → `## Channel System` `<!-- section: key_components | grounding: mixed | role: mechanism -->`
  - `## Core Components > Social Action System` → `## Social Actions` `<!-- section: key_components | grounding: mixed -->`
  - `## Core Components > Communication Filtering` → `## Ignore & Filtering` `<!-- section: key_components | grounding: grounded -->`
  - `## Core Components > Message Formatting` → cross-reference to `game_engine.md` (act() is game engine infrastructure); keep brief mention
  - `## Core Components > Music System` → `## Music & Jukebox` `<!-- section: key_components | grounding: mixed -->`
  - `## Core Components > Marriage System` → `## Marriage System` `<!-- section: key_components | grounding: mixed -->`
  - `## Core Components > Pose System` → `## Pose System` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `status_and_look_commands.md` → DISSOLVE

- **Delete** after redistribution.
- Content redistribution:
  - Look Command System (room examination, object inspection) → `world_system.md` (room perception is spatial awareness)
  - Character Observation, Direction Scouting → `world_system.md`
  - Status Command System (attribute display, equipment status, skill status) → `character_data.md`
  - Combat Readiness subsection → `combat.md`
  - Experience and Progression → `skills_progression.md`
  - `## Key Files > act_info.cc` reference → shared; primary home `character_data.md` with cross-references from `world_system.md`
  - `do_look()`, `do_examine()` → `world_system.md`
  - `do_score()`, `do_inventory()` → `character_data.md`
  - Hidden Entity Handling (visibility mechanics) → `world_system.md`
  - Condition Monitoring (active affects display) → `affect_system.md`

---

## `user_experience_enhancers.md` → DISSOLVE

- **Delete** after redistribution.
- Content redistribution:
  - Alias system (alias.cc, Command Customization) → `command_interpreter.md`
  - Marriage system (marry.cc, Social Interactions) → `social_communication.md`
  - Paintball (paint.cc, Minigames) → `clans_pvp.md` (as a PvP minigame)

---

## `utilities.md` → KEEP

- Add frontmatter:
  ```yaml
  ---
  id: utilities
  name: Utilities
  kind: support
  layer: infrastructure
  parent: null
  depends_on: []
  depended_on_by: []
  ---
  ```
- Absorbs: logging infrastructure content from dissolved `logging_and_monitoring.md` (Logging.cc, macros.hh, Tail utility, resource locations). Deduplicate against existing Logging and Diagnostics section.
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Custom String Class` `<!-- section: key_components | grounding: grounded -->`
    - `## String Processing` `<!-- section: key_components | grounding: mixed -->`
    - `## Argument Processing` `<!-- section: key_components | grounding: mixed -->`
    - `## Flag Management` `<!-- section: key_components | grounding: grounded -->`
    - `## Entity Lookup` `<!-- section: key_components | grounding: mixed -->`
    - `## Randomization` `<!-- section: key_components | grounding: mixed -->`
    - `## Logging & Diagnostics` `<!-- section: key_components | grounding: mixed -->`
    - `## Runtime Type Information` `<!-- section: key_components | grounding: mixed -->`
    - `## Visualization Tools` `<!-- section: key_components | grounding: mixed -->`
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->`
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`
- const.cc and tables.hh/tables.cc are listed here but also belong to `character_data.md` and `object_system.md` — keep the reference here but note canonical ownership is split (character/race/guild/skill tables → `character_data.md`; object/weapon/flag tables → `object_system.md`; lookup/flag utilities → `utilities.md`).

---

## `world_system.md` → KEEP (absorbs `world_visualization.md`)

- Add frontmatter:
  ```yaml
  ---
  id: world_system
  name: World System
  kind: system
  layer: data_model
  parent: null
  depends_on: [character_data, object_system, utilities]
  depended_on_by: [combat, magic, quests, mobprog_npc_ai, persistence, admin_tools, builder_tools, networking]
  ---
  ```
- Absorbs: all content from dissolved `world_visualization.md`:
  - World Map System (Worldmap, MapColor, Coordinate, Region, Quadtree) — already partially present, deduplicate
  - Spatial Awareness Tools (Scan, Hunt) — scan.cc, hunt.cc file entries
  - Map display behaviors
- Absorbs: look/room perception content from dissolved `status_and_look_commands.md` (do_look, room examination, direction scouting, hidden entity handling).
- Tag existing headings:
  - `## Overview` → `<!-- section: overview | grounding: mixed -->`
  - `## Responsibilities` → `<!-- section: responsibilities | grounding: mixed -->`
  - `## Core Components` → split into multiple tagged ##:
    - `## Areas & Rooms` `<!-- section: key_components | grounding: grounded -->`
    - `## Environmental Systems` `<!-- section: key_components | grounding: mixed -->`
    - `## Resets & Vnums` `<!-- section: key_components | grounding: grounded -->`
    - `## Mapping & Coordinates` `<!-- section: key_components | grounding: grounded -->` — absorbs worldmap content from world_visualization.md
    - `## Navigation & Awareness` `<!-- section: key_components | grounding: mixed -->` — scan, hunt, movement; absorbs from world_visualization.md and status_and_look_commands.md
  - `## Implementation Details` → `<!-- section: implementation | grounding: mixed -->`
  - `## Key Files` → `<!-- section: key_components | grounding: grounded -->` — merge file lists from world_visualization.md (scan.cc, hunt.cc, worldmap/*.cc)
  - `## System Behaviors` → `<!-- section: behaviors | grounding: mixed -->`
  - `## Dependencies and Relationships` → rename to `## Dependencies` `<!-- section: dependencies | grounding: grounded -->`

---

## `world_visualization.md` → DISSOLVE into `world_system.md`

- **Delete** after redistribution.
- All content moves to `world_system.md` — see that file's entry above.

---

## Cross-cutting notes

- **`## Responsibilities` sections**: Present in nearly every file. V2 allows `section: responsibilities` as a valid section_kind. Keep them but tag consistently as `grounding: mixed`.
- **`## Dependencies and Relationships`**: Rename to `## Dependencies` everywhere. Current "Depended On By" subsections listing human roles or vague categories ("Players", "Game Administrators", "All Gameplay Systems") are not V2 subsystem edges — drop them all. Only retain system-to-system edges expressed as V2 IDs.
- **`# H1` title**: Remove from all files. The file title is derived from frontmatter `name` field. H1 headings are not chunks and only add noise.
- **Nested `### H3` under `## Core Components`**: The current pattern of a single `## Core Components` with many `###` sub-sections produces one enormous chunk. Per §5.2, each substantial topic should be its own `##` heading (which becomes its own chunk). Promote major `###` sub-headings to `##` where they represent distinct topics. Keep `###` only for internal structure within a single chunk.
