# Character System

## Overview
The Character System forms the foundation for all entities capable of taking actions in the game, including both player characters (PCs) and non-player characters (NPCs). It handles character attributes, states, combat capabilities, progression, and lifecycle management from creation to deletion. The system employs a prototype pattern for NPC instantiation and scripting via MobProgs, and integrates closely with combat, object, quest, and command systems to enable diverse gameplay through skills, spells, AI behavior, and customization features.

## Responsibilities
- Character creation and customization (PCs and NPCs)
- Tracking and updating character attributes, stats, and states
- Processing character actions, movement, and combat
- Managing character progression, skills, and level advancement
- Supporting NPC behavior and scripting (AI)
- Handling player persistence and data storage
- Managing group mechanics, remort, and clan membership
- Processing death, resurrection, and associated penalties

## Core Components

### Character Entities
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

### Scripting and Behavior (NPC AI System)
- `MobProg`: Script-based behavior for NPCs
  - Trigger conditions (time, speech, greet, etc.)
  - Actions to execute when triggered
  - Flexible scripting for defining NPC behaviors and responses
  - Event-based behavior activation with trigger system
  - Conditional execution with variables (IF-THEN-ELSE)
  - Complex behavioral sequences with state tracking
  - Multiple independent behaviors per mobile

- `MobProgActList`: Queue of pending NPC actions
  - Specialized commands available only to NPCs for unique actions
  - Action scheduling and prioritization
  - Delayed execution capability
  - Safe command processing for NPCs

### Combat System
All mechanics for resolving violent conflict between characters.
- **Attack Resolution**: Per-round hit calculation considering weapon skill, dexterity, level difference, and situational modifiers. Dual-wielding and secondary attack chances.
- **Damage Calculation**: Base weapon damage modified by damroll, skill proficiency, enhanced damage, and critical hits. Damage types (slash, bash, pierce, etc.) interact with vulnerabilities and resistances.
- **Defensive Checks**: Dodge, parry, and shield block rolls with skill-based chances. Special defenses like sanctuary (halves damage) and protective shield.
- **Elemental Effects**: Fire, cold, acid, and shock damage cascading to equipment and room contents. Items can be destroyed or degraded by elemental exposure.
- **Dispel Mechanics**: Spell and ability removal with level-based saving throws. Dispel magic, cancellation, and specific effect counterspells.
- **Death & Corpse**: Death processing with XP loss, corpse creation containing victim's inventory, ghost state for players, and NPC loot generation. Auto-looting and auto-gold splitting for groups.
- **Group Combat**: Group experience splitting, group assist mechanics, and group-wide combat coordination.
- **Battle State**: Global battle/arena mode with special rules for organized combat events.
- **Position Effects**: Combat effectiveness varies by position (standing vs. sleeping vs. stunned). Position recovery after being bashed or tripped.
- **Flee & Recall**: Escape mechanics with directional flee, wimpy auto-flee threshold, and recall-to-temple as emergency escape.

### Magic System
Spell casting, spell effects, and the complete spell library.
- **Spell Casting**: Mana-cost casting with skill checks, interruption from damage, and position requirements. Cast command with target parsing (self, character, object, room, direction).
- **Spell Library**: ~200 individual spell implementations covering:
  - *Offensive*: Magic missile, fireball, lightning bolt, chain lightning, etc.
  - *Defensive*: Armor, shield, sanctuary, stone skin, protection evil/good
  - *Healing*: Cure light/serious/critical, heal, refresh, restoration
  - *Enhancement*: Giant strength, haste, bless, frenzy, holy word
  - *Transportation*: Teleport, gate, word of recall, summon, portal
  - *Detection*: Detect magic/evil/hidden/invis, identify, locate object
  - *Affliction*: Curse, poison, plague, blind, sleep, charm
  - *Utility*: Enchant weapon/armor, recharge, create food/water, continual light
- **Remort Spells**: High-tier spells available only after remort — sheen, focus, paralyze, and other prestige abilities.
- **Object Casting**: Items with spell charges (wands, staves, scrolls, potions, pills) that trigger spell effects on use.
- **Spell Saves**: Level-based saving throw system determining full/partial/no effect for offensive spells.
- **Verbal Components**: Spoken incantation display with garbled text for observers who don't know the spell.

### Affect System
Status effects that modify characters, objects, and rooms.
- **Affect Application**: Applying effects with type, duration, modifier value, modifier target (stat, skill, AC, hitroll, damroll, saves, etc.), and associated bitvector flags (invisible, detect hidden, flying, etc.).
- **Character Affects**: Temporary modifications to character stats, skills, and flags. Examples: strength buff, poison DOT, blindness, haste, sanctuary. Handles affect-on-apply and affect-on-removal callbacks.
- **Object Affects**: Enchantments on items that modify wielder stats when equipped. Permanent or temporary. Supports stacking rules.
- **Room Affects**: Environmental effects on rooms — darkness, silence, etc. Applied and removed with proper notification.
- **Affect Stacking**: Rules for what happens when the same affect is applied twice — replace, extend duration, increase modifier, or reject.
- **Affect Caching**: Performance-optimized stat recalculation that caches aggregate modifier values to avoid recomputing on every stat check.
- **Affect Table**: Registry of all affect types with display names, durations, and behavior flags.
- **Affect List Management**: Container for managing ordered sets of affects with add/remove/search operations.

### Data Tables (Character-Related)
Static lookup tables in `const.cc`, `tables.cc`, and `merc.hh` that parameterize character mechanics.
- **Race Definitions** (`race_table`): Stats, size, abilities, vulnerabilities, resistances, immunities, body form, and special flags for each playable and NPC race.
- **Guild/Class Definitions** (`guild_table`): Base stat priorities, primary attribute, skill groups, titles by level and gender, weapon vnum, and class-specific behaviors for each character class.
- **Skill & Spell Tables** (`skill_table`): Complete registry of every skill and spell with level requirements per class, mana costs, target types, minimum positions, damage nouns, and function pointers to implementations.
- **Skill Group Tables** (`group_table`): Bundles of skills that can be learned together, with per-class cost ratings.
- **Random Name Syllables**: Syllable tables for procedural NPC name generation.

### Skills and Progression
- `skills.cc`: Skill system implementation — practice sessions at guild trainers, gain command for acquiring skill groups, proficiency tracking
- `set-stat.cc`: Attribute modification system
- **Level Advancement**: XP-based leveling with stat gains, HP/mana/move increases, practice/train awards, and title changes per class
- **Remort System**: Prestige reincarnation allowing high-level characters to restart with permanent bonuses. Remort affects (raffects) provide persistent stat modifiers. Extra-class skill slots let characters learn abilities from other classes.
- **Skill Groups**: Bundled skill packages that can be learned as units, with per-class cost ratings

## Implementation Details

### Character Implementation
- **Creation and Initialization**: Characters are created either from player data or from mobile prototypes
- **State Management**: Characters track position, fighting status, and various flags
- **Attribute System**: Core stats affect derived attributes (strength → hit/damage)
- **Equipment**: Characters have equipment slots with layered items

### Player Implementation
- **Creation Process**: Comprehensive character creation process
  - Attribute generation with rolling system
  - Race, class, and attribute selection
  - Customization with starting skills and equipment
  - New player welcome sequence
- **Persistence**: Player data is saved to/loaded from files
- **Customization**: Interface for modifying attributes, skills, and appearance
- **Progression**: XP gain, level advancement, and skill learning
- **Character Statistics**: Comprehensive system for managing character attributes
  - Core attributes (strength, intelligence, wisdom, etc.)
  - Derived statistics (hit points, mana, combat values)
  - Stat modification system for temporary and permanent changes
  - Attribute balance and cap management
  - Command-based stat manipulation for administrators
- **Death and Resurrection**: Handling death penalties and revival

### NPC Implementation
- **Prototype Pattern**: NPCs are instantiated from templates
- **AI**: Basic reaction behaviors via MobProgs
  - Script-based behavior system with trigger conditions
  - Various trigger types (speech, action, time, combat, etc.)
  - Program flow with conditional execution
  - Variable system for basic state tracking
  - Event-based behavior activation
- **Special Commands**: Unique NPC behaviors available only to mobiles
  - Specialized movement with pathfinding
  - NPC-specific communication capabilities
  - Quest-related interaction commands
  - Special combat behaviors
  - Object manipulation specific to NPCs
- **Special Functions**: Unique NPC behaviors (shopkeepers, trainers, etc.)
- **Respawning**: NPCs are recreated during area resets

### Combat Implementation
- **Combat Loop**: Per-round resolution via `violence_update()` — iterates fighting characters, calls `multi_hit()` for primary attacks, secondary attacks, and dual-wield
- **Hit Resolution**: `one_hit()` performs the core attack — weapon skill check, dexterity/level modifiers, dodge/parry/shield block defensive rolls, damage type interaction with vulnerabilities/resistances
- **Damage Pipeline**: `damage()` applies final damage — sanctuary halving, damage type modifiers, equipment degradation from elemental effects, death threshold check, XP distribution
- **Death Processing**: `raw_kill()` handles corpse creation with victim inventory, ghost state for players, NPC loot generation, group auto-loot/auto-gold splitting
- **Effects Processing**: `effects.cc` handles elemental cascading (fire/cold/acid/shock) to equipment and room contents
- **Dispel Processing**: `dispel.cc` handles spell/affect removal with level-based saving throws

## Key Files

### Header Files
- `/src/include/Character.hh` - Core character class definition
- `/src/include/Player.hh` - Player-specific functionality (138 LOC)
- `/src/include/MobilePrototype.hh` - NPC template system (65 LOC)
- `/src/include/MobProg.hh` - NPC scripting system (71 LOC)
- `/src/include/MobProgActList.hh` - NPC action queue (23 LOC)
- `/src/include/Battle.hh` - Structured combat system
- `/src/include/DepartedPlayer.hh` - Departed player tracking
- `/src/include/magic.hh` - Spell system interface
- `/src/include/affect/Affect.hh` - Affect class definition
- `/src/include/affect/Type.hh` - Affect type enum
- `/src/include/affect/affect_list.hh` - Affect list interface

### Implementation Files
- `/src/Character.cc` - Character class implementation (285 LOC)
- `/src/Player.cc` - Player management and persistence
- `/src/fight.cc` - Core combat resolution (attack loop, hit/damage, death processing)
- `/src/effects.cc` - Elemental damage effects (fire, cold, acid, shock)
- `/src/dispel.cc` - Spell/affect removal mechanics
- `/src/skills.cc` - Skill system implementation (1783 LOC)
- `/src/magic.cc` - Spell system implementation (~7,000 LOC, ~200 spells)
- `/src/rmagic.cc` - Remort-tier spell implementations
- `/src/affect/affect.cc` - Core affect application and removal
- `/src/affect/affect_char.cc` - Character-specific affect handling
- `/src/affect/affect_obj.cc` - Object-specific affect handling
- `/src/affect/affect_room.cc` - Room-specific affect handling
- `/src/affect/affect_list.cc` - Affect container operations
- `/src/affect/affect_cache_array.cc` - Stat modifier caching
- `/src/affect/affect_table.cc` - Affect type registry
- `/src/mob_prog.cc` - NPC scripting implementation (1937 LOC)
- `/src/mob_commands.cc` - NPC command handling (672 LOC)
- `/src/set-stat.cc` - Character attribute modification system (2197 LOC)
- `/src/remort.cc` - Remort system, raffects, extra-class skill slots
- `/src/const.cc` - Race, guild, skill, skill group, and attack type table definitions
- `/src/include/tables.hh` - Table structure declarations
- `/src/tables.cc` - Table serialization and lookup helpers
- `/src/include/merc.hh` - Race, guild, and skill struct definitions
- `/src/conn/RollStatsState.cc` - Character creation stats (62 LOC)
- `/src/conn/ReadNewMOTDState.cc` - New player welcome sequence (171 LOC)

## System Behaviors

### Core Behaviors
- **Character States**: Characters exist in various states (standing, sitting, fighting, etc.)
- **Movement**: Characters navigate between rooms with position requirements
- **Visibility**: Characters can be invisible, hidden, or detectable
- **Health System**: Characters have hit points, mana, and movement points
- **Group System**: Characters can form groups for cooperative play

### Special Features
- **Remort System**: High-level characters can "remort" for enhanced abilities
- **Clan System**: Character organizational structures with shared resources
- **PvP System**: Player versus player combat with special rules
- **Skill Learning**: Characters can learn new abilities from trainers or practice
- **Plague Effects**: Disease can spread between characters in proximity

## Dependencies and Relationships

### Dependencies On
- **World System**: For character placement and movement between rooms
- **Object System**: For equipment, inventory, and carried items
- **Affect System**: For status effects on characters
- **Event System**: For firing character-related events

### Depended On By
- **Command System**: Character state affects available commands
- **Combat System**: Characters are the primary actors in combat
- **Quest System**: Characters track quest progress
- **Communication System**: Characters send and receive messages
