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

### Combat and Skills
- `Battle`: Manages structured combat scenarios (arenas, duels)
- `magic.hh`/`magic.cc`: Spell system interface and implementation
- `skills.cc`: Skill system implementation
- `set-stat.cc`: Attribute modification system

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
- **Combat Rounds**: Initiative and turn-based action resolution
- **Damage Calculation**: Based on weapon type, skills, attributes
- **Status Effects**: Application and removal during combat
- **Death Processing**: Corpse creation, XP distribution, death messages

## Key Files

### Header Files
- `/src/include/Character.hh` - Core character class definition
- `/src/include/Player.hh` - Player-specific functionality (138 LOC)
- `/src/include/MobilePrototype.hh` - NPC template system (65 LOC)
- `/src/include/MobProg.hh` - NPC scripting system (71 LOC)
- `/src/include/MobProgActList.hh` - NPC action queue (23 LOC)
- `/src/include/Battle.hh` - Structured combat system
- `/src/include/DepartedPlayer.hh` - Departed player tracking

### Implementation Files
- `/src/Character.cc` - Character class implementation (285 LOC)
- `/src/Player.cc` - Player management and persistence
- `/src/fight.cc` - Core combat resolution
- `/src/skills.cc` - Skill system implementation (1783 LOC)
- `/src/magic.cc` - Spell system implementation (~7,000 LOC)
- `/src/mob_prog.cc` - NPC scripting implementation (1937 LOC)
- `/src/mob_commands.cc` - NPC command handling (672 LOC)
- `/src/set-stat.cc` - Character attribute modification system (2197 LOC)
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

## Future Improvements
- The MobProg system could be extended with more sophisticated AI behaviors
- Character balance across different classes and races may need ongoing tuning
- The remort system could be expanded with more advancement paths
- Enhanced NPC conversational and interaction capabilities
- More sophisticated group-based mechanics and rewards
