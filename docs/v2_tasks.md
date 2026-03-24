# V2 Stage 0 Task Checklist

> **Completed (2026-03-24):** All tasks below are done. V2 database ingestion
> was superseded by serving component docs as MCP resources.

Derived from [v2_proposal.md](v2_proposal.md). Work each file top-to-bottom. Cross-cutting tasks apply to every file touched.

---

## Cross-cutting (apply to every file)

- [x] Remove `# H1` title line (title comes from frontmatter `name`)
- [x] Add YAML frontmatter block per proposal
- [x] Add `<!-- section: ... | grounding: ... -->` tag after every `## ` heading
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`
- [x] Drop all "Depended On By" entries that list human roles or vague categories; keep only system-to-system edges using V2 IDs
- [x] Promote `### H3` sub-headings under `## Core Components` to `## H2` where they represent distinct chunkable topics
- [x] Retain `###` only for internal structure within a single `##` chunk

---

## Renames

- [x] `admin_controls.md` → `admin_tools.md`
- [x] `builder_commands.md` → `builder_tools.md`
- [x] `in_game_editor.md` → `notes_editor.md`
- [x] `memory_and_gc.md` → `memory_gc.md`
- [x] `mobprog_system.md` → `mobprog_npc_ai.md`
- [x] `organizations_and_pvp.md` → `clans_pvp.md`
- [x] `social_and_communication.md` → `social_communication.md`

---

## New files to create

- [x] `character_data.md` — from dissolved `character_system.md`
- [x] `combat.md` — from dissolved `character_system.md` + `status_and_look_commands.md`
- [x] `magic.md` — from dissolved `character_system.md`
- [x] `affect_system.md` — from dissolved `character_system.md`
- [x] `skills_progression.md` — from dissolved `character_system.md`
- [x] `loot_generation.md` — extracted from `object_system.md`

---

## Files to dissolve (delete after redistribution)

- [x] `character_system.md` — redistribute content to character_data, combat, magic, affect_system, skills_progression, mobprog_npc_ai
- [x] `status_and_look_commands.md` — redistribute to world_system, character_data, combat, skills_progression, affect_system
- [x] `user_experience_enhancers.md` — redistribute aliases → command_interpreter, marriage → social_communication, paintball → clans_pvp
- [x] `logging_and_monitoring.md` — redistribute to utilities, admin_tools
- [x] `world_visualization.md` — redistribute to world_system

---

## Per-file edits

### `admin_tools.md` (renamed from admin_controls.md)

- [x] Add frontmatter (id: admin_tools, kind: system, layer: operations)
- [x] Split `## Core Components` into `## Admin Command Architecture`, `## WIZnet & Monitoring`, `## Punishment & Moderation`, `## Disabled Commands`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop human-role edges
- [x] Keep WIZnet content here as canonical owner

### `builder_tools.md` (renamed from builder_commands.md)

- [x] Add frontmatter (id: builder_tools, kind: system, layer: operations)
- [x] Split `## Core Components` into `## World Building Tools`, `## Entity Creation Tools`, `## Prototype Management`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop human-role edges

### `character_data.md` (new)

- [x] Create file with frontmatter (id: character_data, kind: system, layer: data_model)
- [x] Pull Character/Player/MobilePrototype/DepartedPlayer entity docs from character_system.md
- [x] Pull Character Implementation + Player Implementation from character_system.md
- [x] Pull race_table, guild_table from character_system.md Data Tables
- [x] Pull do_score(), do_inventory() and status display content from status_and_look_commands.md
- [x] Pull Character.hh/cc, Player.hh/cc, MobilePrototype.hh, DepartedPlayer.hh, RollStatsState.cc, ReadNewMOTDState.cc file entries
- [x] Pull const.cc/tables.hh/merc.hh as primary home; add cross-references to object_system, combat, skills_progression
- [x] Create heading structure per proposal; tag all `##` headings

### `combat.md` (new)

- [x] Create file with frontmatter (id: combat, kind: system, layer: game_mechanic)
- [x] Pull Combat System subsection from character_system.md
- [x] Pull Combat Implementation subsection from character_system.md
- [x] Pull attack_table from character_system.md Data Tables
- [x] Pull Combat Readiness content from status_and_look_commands.md
- [x] Pull fight.cc, effects.cc, dispel.cc, Battle.hh file entries
- [x] Create heading structure per proposal; tag all `##` headings

### `magic.md` (new)

- [x] Create file with frontmatter (id: magic, kind: system, layer: game_mechanic)
- [x] Pull Magic System subsection from character_system.md
- [x] Pull magic.cc, rmagic.cc, magic.hh file entries
- [x] Create heading structure per proposal; tag all `##` headings

### `affect_system.md` (new)

- [x] Create file with frontmatter (id: affect_system, kind: system, layer: game_mechanic)
- [x] Pull Affect System subsection from character_system.md
- [x] Pull all affect/*.cc/hh file entries
- [x] Pull Condition Monitoring content from status_and_look_commands.md
- [x] Create heading structure per proposal; tag all `##` headings

### `skills_progression.md` (new)

- [x] Create file with frontmatter (id: skills_progression, kind: system, layer: game_mechanic)
- [x] Pull Skills and Progression subsection from character_system.md
- [x] Pull skill/spell tables, skill group tables from character_system.md Data Tables
- [x] Pull skills.cc, set-stat.cc, remort.cc file entries
- [x] Pull Experience and Progression content from status_and_look_commands.md
- [x] Create heading structure per proposal; tag all `##` headings

### `loot_generation.md` (new)

- [x] Create file with frontmatter (id: loot_generation, kind: system, layer: game_mechanic)
- [x] Extract Loot System V2 content from object_system.md
- [x] Extract loot_tables.cc, lootv2.cc file entries from object_system.md
- [x] Create heading structure per proposal; tag all `##` headings

### `command_interpreter.md` (keep)

- [x] Add frontmatter (id: command_interpreter, kind: system, layer: infrastructure)
- [x] Absorb alias system content from user_experience_enhancers.md; add `## Alias System` section
- [x] Relocate Connection System subsection (conn::State) to networking.md or replace with cross-reference
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; replace vague edges with V2 IDs

### `economy.md` (keep)

- [x] Add frontmatter (id: economy, kind: system, layer: player_feature)
- [x] Split `## Core Components` into `## Auction System`, `## Banking System`, `## Currency System`, `## Shop System`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop role-based edges
- [x] Establish this file as canonical owner of Shop System; add cross-reference note for object_system.md

### `event_dispatcher.md` (keep)

- [x] Add frontmatter (id: event_dispatcher, kind: support, layer: infrastructure)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop role-based edges

### `game_engine.md` (keep)

- [x] Add frontmatter (id: game_engine, kind: system, layer: infrastructure)
- [x] Split `## Core Components` into `## State Management`, `## Game Loop`, `## Entity Lifecycle`, `## Message Dispatch`, `## Boot & Shutdown`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; replace role-based edges with V2 IDs

### `help_system.md` (keep)

- [x] Add frontmatter (id: help_system, kind: system, layer: content_system)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop role-based edges
- [x] Update "Editor System" dependency reference → cross-reference to notes_editor.md

### `notes_editor.md` (renamed from in_game_editor.md)

- [x] Add frontmatter (id: notes_editor, kind: system, layer: content_system)
- [x] Promote Editor Core → `## Line Editor`
- [x] Split Content Type Handlers: Note boards → `## Note Boards`; Description Editor / Help File Editor → cross-references
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop non-system edges, keep help_system

### `memory_gc.md` (renamed from memory_and_gc.md)

- [x] Add frontmatter (id: memory_gc, kind: support, layer: infrastructure)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop role-based edges

### `mobprog_npc_ai.md` (renamed from mobprog_system.md)

- [x] Add frontmatter (id: mobprog_npc_ai, kind: system, layer: content_system)
- [x] Absorb NPC AI/MobProg content from character_system.md (MobProg subsection, MobProgActList, NPC Implementation AI parts, mob_prog.cc, mob_commands.cc)
- [x] Promote Script Engine, Special Functions, Trigger System, Execution Engine to `## ` headings
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop self-referential and non-system edges

### `networking.md` (keep)

- [x] Add frontmatter (id: networking, kind: system, layer: infrastructure)
- [x] Split `## Core Components` into `## Connection Management`, `## Protocol Implementation`, `## Connection State Machine`, `## Copyover`
- [x] Absorb conn::State / login-state content from command_interpreter.md
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`

### `object_system.md` (keep)

- [x] Add frontmatter (id: object_system, kind: system, layer: data_model)
- [x] Split `## Core Components` into `## Object Entities`, `## Item Enhancement`, `## Data Tables`
- [x] Extract Loot System V2 content → loot_generation.md
- [x] Reduce Shop System to cross-reference → economy.md
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`

### `clans_pvp.md` (renamed from organizations_and_pvp.md)

- [x] Add frontmatter (id: clans_pvp, kind: system, layer: player_feature)
- [x] Absorb paintball content from user_experience_enhancers.md
- [x] Promote Clan System, War System, PvP Systems to `##` headings
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`
- [x] Clarify Guild subsection — relocate to skills_progression.md if it describes training guilds

### `persistence.md` (keep)

- [x] Add frontmatter (id: persistence, kind: system, layer: operations)
- [x] Split `## Core Components` into `## Database Management`, `## File-Based Persistence`, `## Configuration System`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`
- [x] Add cross-reference to notes_editor.md for note file storage

### `quests.md` (keep)

- [x] Add frontmatter (id: quests, kind: system, layer: player_feature)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`; drop role-based edges

### `social_communication.md` (renamed from social_and_communication.md)

- [x] Add frontmatter (id: social_communication, kind: system, layer: player_feature)
- [x] Absorb marriage system content from user_experience_enhancers.md
- [x] Promote Channel System, Social Actions, Ignore & Filtering, Music & Jukebox, Marriage System, Pose System to `##` headings
- [x] Replace Message Formatting subsection with cross-reference to game_engine.md (act() system)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`

### `utilities.md` (keep)

- [x] Add frontmatter (id: utilities, kind: support, layer: infrastructure)
- [x] Absorb logging content from logging_and_monitoring.md; deduplicate against existing Logging & Diagnostics
- [x] Split `## Core Components` into `## Custom String Class`, `## String Processing`, `## Argument Processing`, `## Flag Management`, `## Entity Lookup`, `## Randomization`, `## Logging & Diagnostics`, `## Runtime Type Information`, `## Visualization Tools`
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`
- [x] Note canonical ownership split for const.cc/tables.hh/tables.cc across character_data, object_system, utilities

### `world_system.md` (keep, absorbs world_visualization.md)

- [x] Add frontmatter (id: world_system, kind: system, layer: data_model)
- [x] Absorb world_visualization.md content (Worldmap, MapColor, Coordinate, Region, Quadtree, Scan, Hunt); deduplicate
- [x] Absorb look/room perception content from status_and_look_commands.md (do_look, do_examine, direction scouting, hidden entity handling)
- [x] Split `## Core Components` into `## Areas & Rooms`, `## Environmental Systems`, `## Resets & Vnums`, `## Mapping & Coordinates`, `## Navigation & Awareness`
- [x] Merge file lists from world_visualization.md (scan.cc, hunt.cc, worldmap/*.cc)
- [x] Tag all `##` headings
- [x] Rename `## Dependencies and Relationships` → `## Dependencies`

---

## Cleanup

- [x] Delete `character_system.md`
- [x] Delete `status_and_look_commands.md`
- [x] Delete `user_experience_enhancers.md`
- [x] Delete `logging_and_monitoring.md`
- [x] Delete `world_visualization.md`
- [x] Verify no remaining references to deleted filenames across surviving docs
- [x] Verify every surviving file has frontmatter + tagged headings
- [x] Verify every `## Dependencies` section uses only V2 system IDs
