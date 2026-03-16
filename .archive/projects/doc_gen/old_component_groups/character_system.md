# Character System Component Documentation

## Overview

The Character System forms the foundation for all entities capable of taking actions in the game, including both player characters (PCs) and non-player characters (NPCs). It handles character attributes, states, combat capabilities, progression, and lifecycle management from creation to deletion.

### System Responsibilities
- Managing character creation and customization
- Tracking character attributes, stats, and states
- Processing character actions and combat
- Handling character progression through skills and levels
- Supporting NPC behavior through scripting

## Core Classes and Interfaces

### Character Entities
- **Character**: Base class for all characters (players and NPCs)
  - Contains core attributes, stats, and state
  - Handles combat data and action processing
  - Manages affects (status effects) on the character

- **DepartedPlayer**: Tracks data for players who have left the game

- **MobilePrototype**: Template for NPC creation
  - Stores base data for NPCs (descriptions, stats, behaviors)
  - Used to instantiate NPC characters in areas
  - Defines mobile behavior programs
  - Manages shop capabilities for merchant NPCs
  - Controls NPC equipment and inventory
  - Sets mobile special attributes and flags
  - Governs the parameters for mobile behavior

- **Player**: Extends Character for player-specific functionality
  - Manages persistent player data
  - Tracks player preferences and configurations
  - Handles player progression and advancement
  - Stores authentication information
  - Maintains player history and records
  - Manages player-specific states and flags
  - Tracks relationships with other players
  - Handles player resource management
  - Supports advanced player customization

### Scripting and Behavior (NPC AI System)
- **MobProg**: Script-based behavior for NPCs
  - Trigger conditions (time, speech, greet, etc.)
  - Actions to execute when triggered
  - Flexible scripting for defining NPC behaviors and responses
  - Event-based behavior activation with trigger system
  - Conditional execution with variables
  - Complex behavioral sequences with state tracking
  - Multiple independent behaviors per mobile

- **MobProgActList**: Queue of pending NPC actions
  - Specialized commands available only to NPCs for unique actions
  - Action scheduling and prioritization
  - Delayed execution capability
  - Safe command processing for NPCs

- **Entity Management**: Core functions for managing character states and transitions

### Combat and Skills
- **Battle**: Manages structured combat scenarios (arenas, duels)
- **Magic/Spells**: System for magical abilities
- **Skills**: Non-magical abilities and techniques

## Implementation Details

### Character Implementation
- **Creation and Initialization**: Characters are created either from player data or from mobile prototypes
- **State Management**: Characters track position, fighting status, and various flags
- **Attribute System**: Core stats affect derived attributes (strength → hit/damage)
- **Equipment**: Characters have equipment slots with layered items

### Player Implementation
- **Creation Process**: Comprehensive character creation process
  - Attribute generation with rolling system (conn/RollStatsState.cc, 62 LOC)
  - New player welcome sequence (conn/ReadNewMOTDState.cc, 171 LOC)
  - Race, class, and attribute selection
  - Customization with starting skills and equipment
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
  - Program flow with IF-THEN-ELSE conditional execution
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

## Key Files and Components

### Header Files
- `Character.hh` - Core character class definition
- `Player.hh` (138 LOC) - Player-specific functionality
- `MobilePrototype.hh` (65 LOC) - NPC template system
- `MobProg.hh` (71 LOC) - NPC scripting system
- `MobProgActList.hh` (23 LOC) - NPC action queue
- `Battle.hh` - Structured combat system
- `DepartedPlayer.hh` - Departed player tracking
- `magic.hh` - Spell system interface

### Implementation Files
- `Character.cc` (285 LOC) - Character class implementation
- `Player.cc` - Player management and persistence
- `fight.cc` - Core combat resolution
- `skills.cc` (1783 LOC) - Skill system implementation
- `magic.cc` (~7,000 LOC) - Spell system implementation
- `mob_prog.cc` (1937 LOC) - NPC scripting implementation
- `mob_commands.cc` (672 LOC) - NPC command handling
- `set-stat.cc` (2197 LOC) - Character attribute modification system
- `stored_src/Customize.cc` - Character customization
- `conn/RollStatsState.cc` (62 LOC) - Character creation stats

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
- **World System**: For character placement and movement
- **Object System**: For equipment, inventory, and carried items
- **Affect System**: For status effects on characters
- **Event System**: For firing character-related events

### Depended On By
- **Command System**: Character state affects available commands
- **Combat System**: Characters are the primary actors in combat
- **Quest System**: Characters track quest progress
- **Communication System**: Characters send and receive messages

## Open Questions and Future Improvements
- The MobProg system could be extended with more sophisticated AI behaviors
- Character balance across different classes and races may need ongoing tuning
- The remort system could be expanded with more advancement paths
- NPC interactions could be enhanced with more dynamic conversational capabilities

---
