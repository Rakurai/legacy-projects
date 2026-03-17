---
id: character_data
name: Character Data
kind: system
layer: data_model
parent: null
depends_on: [world_system, object_system, affect_system]
depended_on_by: [combat, magic, skills_progression, command_interpreter, quests, social_communication, persistence, admin_tools, builder_tools]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Character Data system forms the foundation for all entities capable of taking actions in the game, including both player characters (PCs) and non-player characters (NPCs). It defines the core data structures, attribute systems, and lifecycle management for characters from creation to deletion. The system employs a prototype pattern for NPC instantiation and maintains the persistent data model that all other gameplay systems depend on.

## Character Entities
<!-- section: key_components | grounding: grounded -->

- `Character`: Base class for all characters (players and NPCs)
  - Contains core attributes, stats, and state
  - Handles combat data and action processing
  - Manages affects (status effects) on the character
  - Tracks position, fighting status, and various flags

- `Player`: Extends Character for player-specific functionality
  - Manages persistent player data
  - Tracks player preferences and configurations
  - Handles player progression and advancement
  - Stores authentication information
  - Maintains player history and records
  - Manages player-specific states and flags
  - Tracks relationships with other players
  - Handles player resource management
  - Supports advanced player customization

- `MobilePrototype`: Template for NPC creation
  - Stores base data for NPCs (descriptions, stats, behaviors)
  - Used to instantiate NPC characters in areas
  - Defines mobile behavior programs
  - Manages shop capabilities for merchant NPCs
  - Controls NPC equipment and inventory
  - Sets mobile special attributes and flags
  - Governs the parameters for mobile behavior

- `DepartedPlayer`: Tracks data for players who have left the game

## Attribute & Stat System
<!-- section: key_components | grounding: mixed -->

- **Core Attributes**: Strength, intelligence, wisdom, dexterity, constitution, charisma
- **Derived Statistics**: Hit points, mana, movement points, combat values (hitroll, damroll, AC)
- **Stat Modification**: Temporary and permanent changes via affects, equipment, and admin commands
- **Attribute Balance**: Cap management and balance constraints per race/class
- **Character States**: Characters exist in various states (standing, sitting, fighting, sleeping, stunned, etc.)
- **Health System**: Characters have hit points, mana, and movement points with regeneration
- **Visibility**: Characters can be invisible, hidden, or detectable
- **Group System**: Characters can form groups for cooperative play

### Status Display
- `do_score()` — Character status overview with core attributes, derived statistics, formatting and presentation
- `do_inventory()` — Carried item listing with weight calculation, categorization, and special item flagging
- Attribute display with current vs. maximum values (HP/Mana/Move), temporary modifiers and effects
- Equipment status showing equipped items by slot, condition, and properties

## Character Creation
<!-- section: implementation | grounding: mixed -->

- **Creation and Initialization**: Characters are created either from player data or from mobile prototypes
- **Player Creation Process**:
  - Attribute generation with rolling system
  - Race, class, and attribute selection
  - Customization with starting skills and equipment
  - New player welcome sequence
- **NPC Instantiation**: NPCs are instantiated from MobilePrototype templates during area resets
- **State Management**: Characters track position, fighting status, and various flags
- **Equipment**: Characters have equipment slots with layered items
- **Persistence**: Player data is saved to/loaded from files
- **Death and Resurrection**: Handling death penalties and revival

## Data Tables
<!-- section: key_components | grounding: grounded -->

Static lookup tables in `const.cc`, `tables.cc`, and `merc.hh` that parameterize character mechanics.
- **Race Definitions** (`race_table`): Stats, size, abilities, vulnerabilities, resistances, immunities, body form, and special flags for each playable and NPC race.
- **Guild/Class Definitions** (`guild_table`): Base stat priorities, primary attribute, skill groups, titles by level and gender, weapon vnum, and class-specific behaviors for each character class.
- **Random Name Syllables**: Syllable tables for procedural NPC name generation.

Cross-referenced from: `object_system.md` (attack/weapon/item tables), `combat.md` (attack_table), `skills_progression.md` (skill/spell tables).

## Key Files
<!-- section: key_components | grounding: grounded -->

### Header Files
- `/src/include/Character.hh` — Core character class definition
- `/src/include/Player.hh` — Player-specific functionality (138 LOC)
- `/src/include/MobilePrototype.hh` — NPC template system (65 LOC)
- `/src/include/DepartedPlayer.hh` — Departed player tracking

### Implementation Files
- `/src/Character.cc` — Character class implementation (285 LOC)
- `/src/Player.cc` — Player management and persistence
- `/src/set-stat.cc` — Character attribute modification system (2197 LOC)
- `/src/const.cc` — Race, guild, and attack type table definitions (primary home; cross-ref object_system, combat, skills_progression)
- `/src/include/tables.hh` — Table structure declarations
- `/src/tables.cc` — Table serialization and lookup helpers
- `/src/include/merc.hh` — Race, guild, and skill struct definitions
- `/src/conn/RollStatsState.cc` — Character creation stats (62 LOC)
- `/src/conn/ReadNewMOTDState.cc` — New player welcome sequence (171 LOC)
- `act_info.cc` (5493 LOC) — Primary home for status display commands (do_score, do_inventory, etc.); cross-ref world_system.md for do_look/do_examine

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **World System** (`world_system`): For character placement and movement between rooms
- **Object System** (`object_system`): For equipment, inventory, and carried items
- **Affect System** (`affect_system`): For status effects on characters

### Depended On By
- **Combat** (`combat`): Characters are the primary actors in combat
- **Magic** (`magic`): Spell targets and casters
- **Skills & Progression** (`skills_progression`): Character advancement
- **Command Interpreter** (`command_interpreter`): Character state affects available commands
- **Quests** (`quests`): Characters track quest progress
- **Social & Communication** (`social_communication`): Characters send and receive messages
- **Persistence** (`persistence`): Player data storage
- **Admin Tools** (`admin_tools`): Character manipulation commands
- **Builder Tools** (`builder_tools`): NPC creation and editing
