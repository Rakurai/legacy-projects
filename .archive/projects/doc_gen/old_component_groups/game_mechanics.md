# Game Mechanics Component Documentation

## Overview

The Game Mechanics systems implement the core rules and effects that govern gameplay, including status effects, combat resolution, event handling, and specialized gameplay features. These interconnected systems provide the foundational mechanics that make the game world operate according to consistent rules.

### System Responsibilities
- Managing status effects (affects) on characters, objects, and rooms
- Handling combat mechanics, calculations, and resolution
- Processing events and notifying interested components
- Supporting specialized gameplay features (quests, duels, clans)
- Implementing skill and magic systems

## Core Classes and Interfaces

### Affect System
- **Affect**: Represents a status effect with type, duration, and modifier values
  - Can be applied to characters, objects, or rooms
  - Contains modifier information for stats, resistances, etc.
  - Includes duration and timing management

- **AffectTable**: Registry of all available affect types with properties

### Combat System
- **Combat Functions**: Core battle resolution and damage calculations
- **Magic System**: Spell effects and magical combat support
- **Skill System**: Non-magical abilities and techniques
- **Type Enumerations**: Damage types, attack types, weapon types

### Event System
- **event::Dispatcher**: Core event distribution component
- **event::Handler**: Interface for event recipients
- **event::Type**: Enumeration of different event types
  - Fine-grained event categorization
  - System-specific event definitions
  - Event priority classification

### Combat System
- **Attack Resolution**: Determining hit success based on skills and stats
- **Damage Calculation**: Computing damage with weapon type, skill, attributes
- **Death Processing**: Handling character death with appropriate consequences
- **Magic Effects**: Implementing spell damage, healing, and special effects
- **Skill Usage**: Non-magical combat abilities and techniques

### Event Implementation
- **Event Distribution**: Routing events to registered handlers
- **Subscription Management**: Adding and removing event handlers
- **Event Data**: Passing context information with events
- **Safe Iteration**: Maintaining handler list integrity during dispatch

### Magic System Implementation
- **Spell Framework**: Core infrastructure for spell definition and execution
- **Varied Spell Types**:
  - Offensive combat spells with elemental damage types
  - Healing and restoration spells of various potencies
  - Utility and information-gathering magic
  - Environmental manipulation spells
  - Movement and transportation magic
  - Creation and summoning spells
- **Targeting System**: Mechanism for targeting spells at characters, objects, or rooms
- **Spell Scaling**: Level-based effectiveness scaling
- **Elemental System**: Different damage types and resistances
- **Remort Magic**: Enhanced magic system for high-level characters
- **Dispel Mechanics**: System for removing magical effects
  - Level-based dispel success calculations
  - Effect type categorization for dispel targeting
  - Different dispel variants (dispel magic, cancel, etc.)

### Target Finding
- **Find System**: Sophisticated target acquisition for spells and effects
  - Target validity checking
  - Range and line-of-sight validation
  - Multiple targeting strategies
  - Context-aware target selection

### Special System Implementation
- **Quest Generation**: Creating, tracking, and rewarding missions
  - Automated quest system with mission generation (quest.cc, 1897 LOC)
  - Token system for tracking progress
  - Time-limited challenges with scaling rewards
- **Remort System**: Character advancement beyond maximum level (remort.cc, 580 LOC) allowing high-level characters to restart with enhanced abilities
- **Music System**: Bardic performance mechanics
  - Song effects and benefits
  - Instrument quality and types
  - Performance skill integration
  - Area-based effect application
  - Duration and maintenance mechanics
  - Profession-specific abilities
- **Clan Management**: Player organization with ranks and resources
- **War System**: Structured conflict between clans with scoring
- **Duel System**: Formal combat between players with rules
- **Clan Territory**: Association of areas with specific clans
- **Shop System**: In-game merchant system
  - Shop hour restrictions and opening times
  - Item buying and selling with profit margins
  - Specialized merchandise by shop type
  - Shopkeeper behavior and interaction
  - Price negotiation and haggling

## Key Files and Components

### Header Files
- `affect/Affect.hh` (181 LOC) - Affect class and related structures
- `magic.hh` - Magic system interfaces
- `skill/Type.hh` (245 LOC) - Skill type enumerations
- `skill/skill.hh` (39 LOC) - Skill system interfaces
- `event/Dispatcher.hh` - Event distribution system
- `event/Handler.hh` - Event handler interface
- `event/event.hh` (17 LOC) - Event type definitions
- `Duel.hh` (55 LOC) - Dueling system interface
- `Clan.hh` (43 LOC) - Clan organization interface
- `Guild.hh` (16 LOC) - Guild system interface
- `QuestArea.hh` (27 LOC) - Quest area management
- `Shop.hh` (25 LOC) - Shop system interface
- `War.hh` (61 LOC) - Clan war management
- `dispel.hh` (12 LOC) - Effect removal interface
- `find.hh` (24 LOC) - Target acquisition interface
- `music.hh` (21 LOC) - Bardic music system interface

### Implementation Files
- `affect/*.cc` - Affect system implementations
- `fight.cc` - Core combat resolution
- `magic.cc` (~7,000 LOC) - Spell system implementation
- `skills.cc` (1783 LOC) - Skill system implementation
- `dispel.cc` (249 LOC) - Effect removal system
- `effects.cc` (855 LOC) - Special effects system
- `event/Dispatcher.cc` (89 LOC) - Event distribution implementation
- `War.cc` (1478 LOC) - Clan war system
- `quest.cc` (1897 LOC) - Quest system

## System Behaviors

### Affect Behaviors
- **Stacking**: Rules for combining multiple affects of same type
- **Timed Effects**: Auto-expiring affects with remaining duration
- **Caching**: Performance optimizations for affect lookups
- **Visibility**: Some affects change how entities are perceived

### Combat Behaviors
- **Round-Based**: Combat occurs in rounds with initiative
- **Position Requirements**: Different positions enable different actions
- **Attack Types**: Various attack forms with different calculations
- **Skill Influence**: Skills modify success chance and damage
- **Magic Integration**: Spells have various combat effects

### Event Behaviors
- **Type-Based Distribution**: Events are sent to handlers based on type
- **Data Passing**: Events can include contextual data
- **Multiple Handlers**: Multiple systems can respond to same event
- **Safe Dispatching**: Changes to handler list during dispatch are handled safely

### Special System Behaviors
- **Quest Generation**: Random and fixed quests with objectives
- **Clan Organizations**: Hierarchical player groups with shared resources
- **War Mechanics**: Structured PvP with scoring and resolution
- **Remort System**: Character advancement beyond maximum level

## Dependencies and Relationships

### Dependencies On
- **Character System**: For applying effects to characters
- **Object System**: For applying effects to objects
- **World System**: For applying effects to rooms and areas
- **Command System**: For triggering mechanics through commands

### Depended On By
- **All Gameplay Systems**: Most game systems utilize affects, combat, or events
- **NPC System**: AI behaviors depend on combat mechanics
- **Player Experience**: Core gameplay revolves around these mechanics

## Open Questions and Future Improvements
- The affect caching system could be optimized further for performance
- Combat balance may need ongoing adjustment for different character types
- The event system could be expanded to support more event types
- Special systems like quests could be enhanced with more varied objectives

---
