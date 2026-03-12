# Game Rules

## Overview
The Game Rules subsystem implements the core logic and mechanics that govern gameplay, including combat, skill resolution, spell effects, status conditions, and the event system. It coordinates with character and object systems to resolve gameplay actions according to consistent rules and statistical outcomes. These interconnected systems provide the foundational mechanics that make the game world operate according to consistent rules, creating a balanced and engaging player experience.

## Responsibilities
- Managing status effects (affects) on characters, objects, and rooms
- Handling combat mechanics, calculations, and resolution
- Processing events and notifying interested components
- Implementing skill and magic systems
- Supporting specialized gameplay features (quests, duels, clans, wars)
- Providing target selection and validation mechanisms
- Managing effect removal and dispel mechanics

## Core Components

### Affect System
- `Affect`: Represents a status effect with type, duration, and modifier values
  - Can be applied to characters, objects, or rooms
  - Contains modifier information for stats, resistances, etc.
  - Includes duration and timing management
  - Supports stacking rules for combining effects

- `AffectTable`: Registry of all available affect types with properties

### Combat System
- `Combat Functions`: Core battle resolution and damage calculations
  - Attack resolution based on skills and stats
  - Damage calculation with weapon type, skill, attributes
  - Death processing with appropriate consequences
  - Position requirements for different actions

- `Magic System`: Spell effects and magical combat support
  - Offensive combat spells with elemental damage types
  - Healing and restoration spells of various potencies
  - Utility and information-gathering magic
  - Environmental manipulation spells
  - Movement and transportation magic
  - Creation and summoning spells
  - Spell scaling based on character level

- `Skill System`: Non-magical abilities and techniques
  - Combat skills improving attack and defense
  - Utility skills for various gameplay advantages
  - Profession-specific abilities 
  - Passive and active skill effects

- `Type Enumerations`: Comprehensive system of types
  - Damage types (slash, pierce, magic, etc.)
  - Attack types (punch, kick, weapon, etc.)
  - Weapon types (sword, axe, mace, etc.)
  - Elemental types for damage and resistance

### Event System
- `event::Dispatcher`: Core event distribution component
  - Routing events to registered handlers
  - Subscription management
  - Safe iteration during dispatch

- `event::Handler`: Interface for event recipients
  - Notification mechanism through the notify method
  - Base class for components that respond to events

- `event::Type`: Enumeration of different event types
  - Fine-grained event categorization
  - System-specific event definitions
  - Event priority classification

### Special Systems
- `Dispel Mechanics`: System for removing magical effects
  - Level-based dispel success calculations
  - Effect type categorization for dispel targeting
  - Different dispel variants (dispel magic, cancel, etc.)

- `Find System`: Sophisticated target acquisition for spells and effects
  - Target validity checking
  - Range and line-of-sight validation
  - Multiple targeting strategies
  - Context-aware target selection

- `Music System`: Bardic performance mechanics
  - Song effects and benefits
  - Instrument quality and types
  - Performance skill integration
  - Area-based effect application

- Organizational systems:
  - `Duel`: Formal combat between players with rules
  - `Clan`: Player organization with ranks and resources
  - `War`: Structured conflict between clans with scoring
  - `Shop`: In-game merchant system
  - `QuestArea`: Specialized areas with quest-specific properties

## Implementation Details

### Affect Implementation
- **Stacking**: Rules for combining multiple affects of same type
- **Timed Effects**: Auto-expiring affects with remaining duration
- **Caching**: Performance optimizations for affect lookups
- **Visibility**: Some affects change how entities are perceived

### Combat Implementation
- **Round-Based**: Combat occurs in rounds with initiative
- **Position Requirements**: Different positions enable different actions
- **Attack Types**: Various attack forms with different calculations
- **Skill Influence**: Skills modify success chance and damage
- **Magic Integration**: Spells have various combat effects
- **Elemental System**: Different damage types and resistances

### Event Implementation
- **Type-Based Distribution**: Events are sent to handlers based on type
- **Data Passing**: Events can include contextual data
- **Multiple Handlers**: Multiple systems can respond to same event
- **Safe Dispatching**: Changes to handler list during dispatch are handled safely

### Special System Implementation
- **Remort System**: Character advancement beyond maximum level
- **Clan Management**: Player organization with ranks and resources
- **War System**: Structured conflict between clans with scoring
- **Shop System**: In-game merchant system with hours and specialized merchandise

## Key Files

### Header Files
- `/src/include/affect/Affect.hh` - Affect class and related structures (181 LOC)
- `/src/include/magic.hh` - Magic system interfaces
- `/src/include/skill/Type.hh` - Skill type enumerations (245 LOC)
- `/src/include/skill/skill.hh` - Skill system interfaces (39 LOC)
- `/src/include/event/Dispatcher.hh` - Event distribution system
- `/src/include/event/Handler.hh` - Event handler interface
- `/src/include/event/event.hh` - Event type definitions (17 LOC)
- `/src/include/Duel.hh` - Dueling system interface (55 LOC)
- `/src/include/Clan.hh` - Clan organization interface (43 LOC)
- `/src/include/Guild.hh` - Guild system interface (16 LOC)
- `/src/include/QuestArea.hh` - Quest area management (27 LOC)
- `/src/include/Shop.hh` - Shop system interface (25 LOC)
- `/src/include/War.hh` - Clan war management (61 LOC)
- `/src/include/dispel.hh` - Effect removal interface (12 LOC)
- `/src/include/find.hh` - Target acquisition interface (24 LOC)
- `/src/include/music.hh` - Bardic music system interface (21 LOC)

### Implementation Files
- `/src/fight.cc` - Core combat resolution
- `/src/magic.cc` - Spell system implementation (~7,000 LOC)
- `/src/skills.cc` - Skill system implementation (1783 LOC)
- `/src/dispel.cc` - Effect removal system (249 LOC)
- `/src/effects.cc` - Special effects system (855 LOC)
- `/src/event/Dispatcher.cc` - Event distribution implementation (89 LOC)
- `/src/War.cc` - Clan war system (1478 LOC)
- `/src/remort.cc` - Character advancement beyond maximum level (580 LOC)
- `/src/quest.cc` - Quest system implementation (1897 LOC)

## System Behaviors

### Core Behaviors
- **Status Effects**: Characters, objects, and rooms can have affects applied
- **Combat Resolution**: Turn-based combat with multiple factors influencing outcomes
- **Spell Casting**: Magic system with various spell types and effects
- **Skill Usage**: Non-magical abilities with success rates and effects
- **Event Processing**: System-wide event notification and handling

### Special Features
- **Remort System**: Character advancement beyond maximum level
- **Clan Organizations**: Hierarchical player groups with shared resources
- **War Mechanics**: Structured PvP with scoring and resolution
- **Duel System**: Formal combat between players with special rules
- **Shop System**: Merchants with buying/selling mechanics and specialized goods

## Dependencies and Relationships

### Dependencies On
- **Character System**: For applying effects to characters and managing combatants
- **Object System**: For applying effects to objects and using items in combat
- **World System**: For applying effects to rooms and handling environment effects
- **Command System**: For triggering mechanics through player commands

### Depended On By
- **All Gameplay Systems**: Most game systems utilize affects, combat, or events
- **NPC System**: AI behaviors depend on combat mechanics
- **Player Experience**: Core gameplay revolves around these mechanics
- **Quest System**: Mission objectives often involve combat or special mechanics

## Future Improvements
- Optimize affect caching for performance in high-volume scenarios
- Ongoing combat and skill balance adjustments for different character types
- Expand event system to support more event types and complex event chains
- Enhance quest and special systems with more varied objectives and rewards
- Refine combat mechanics to improve tactical depth and character differentiation
- Integrate magic and physical combat systems more seamlessly
