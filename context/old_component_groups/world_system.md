# World System Component Documentation

## Overview

The World System forms the core spatial environment of the game, providing the physical structure where gameplay occurs. It's organized as a hierarchy of areas containing rooms, with navigation enabled through exits. The system employs a prototype pattern where areas load definitions for rooms, objects, and mobiles that are instantiated as needed during gameplay.

### System Responsibilities
- Creating and managing the physical game world
- Handling room creation and interconnections
- Managing environmental conditions and time
- Supporting navigation and world mapping
- Providing area reset mechanics for content respawning

The World Structure system defines the physical environment of the game world, organized into areas containing rooms that are connected by exits. Areas are loaded from text files and contain the prototype definitions for rooms, objects, and mobiles. The World Environment system manages the game's time, weather, and physical environment, providing immersion through time progression, day/night cycles, and changing weather conditions that affect gameplay.

## Core Classes and Interfaces

### Areas
- **Area**: Represents a distinct geographical region containing multiple rooms, objects, and mobiles
  - Manages loading from area files
  - Handles regular updates and resets
  - Tracks player and immortal presence

### Rooms
- **Room**: Represents a specific location in the game world
  - Contains characters and objects
  - Connects to other rooms via exits
  - Can have specialized properties (safe, private, etc.)
  
- **RoomPrototype**: Template for creating room instances
  - Defines base properties (descriptions, flags, etc.)
  - Can be instantiated multiple times
  - Manages room attributes, flags, and behaviors
  - Provides prototype data to room instances
  
- **RoomID**: Unique identifier for room instances
  - Combines virtual number with instance number
  - Enables multiple instances of the same room template
  - Provides serialization and parsing utilities
  - Supports comparison and reference operations

- **Exit/ExitPrototype**: Defines connections between rooms
  - Contains direction, destination, and properties
  - Supports locks, hidden exits, etc.
  - Manages visibility and access controls
  - Tracks door states (open/closed/locked)
  - Supports one-way and bidirectional connections

### Location System
- **Location**: Represents a specific position in the game world
  - Combines room reference with position within room
  - Supports character/object positioning
  - Handles relative location calculations
  - Provides consistent location interface across systems

### Environmental Systems
- **GameTime**: Tracks in-game time (hours, days, months, years)
- **Weather**: Environmental conditions that affect gameplay
  - Dynamic weather patterns with seasonal variations
  - Atmospheric pressure simulation system
  - Sky condition tracking (sunny, cloudy, rainy, etc.)
  - Room-specific weather effects
  - Weather forecasting capabilities
- **World**: Central coordinator for the game environment
  - Area management and organization
  - Global state tracking
  - World-wide updates and coordination
  - Area reset scheduling and management
  - World initialization and shutdown sequence
  - Instance management for rooms and areas

### Area Management
- **Reset**: Defines area respawn instructions
  - Controls mobile and object placement
  - Manages equipment for mobiles
  - Handles door states (open/closed/locked)
  - Supports various reset types and conditions
  - Enables periodic world refreshing

- **Vnum**: Virtual number identifier system
  - Uniquely identifies prototypes and areas
  - Maps to specific instances in the world
  - Provides type-safe alternative to raw integers
  - Supports range operations and comparisons

### Terrain System
- **Sector**: Defines terrain types for rooms
  - Determines movement costs and limitations
  - Affects specific skills and abilities
  - Influences weather and environmental effects

## Implementation Details

### Area Implementation
- **Construction and Loading**: Areas are built from text files (.are)
- **Section Types**: Areas load different sections for rooms, objects, mobiles, etc.
- **Update and Reset**: Areas respawn monsters and objects based on timers and player presence
- **Player Tracking**: Areas monitor character presence for update decisions

### Room Implementation
- **Instance Creation**: Rooms are created from prototypes when needed
- **Character Movement**: Rooms handle character entry and exit with `add_char` and `remove_char`
- **Property Delegation**: Many room properties are delegated to their prototypes
- **Environmental State**: Rooms track conditions like light levels

### Region Management
- **Region Implementation**: Area geographical association with mapping between regions and world coordinates (worldmap/Region.cc, 157 LOC)
  - Region boundary detection
  - Point-in-polygon testing
  - Region property management
  - Named region lookup and retrieval
- **Coordinate Operations**: Distance calculations, translations, and coordinate validation (worldmap/Coordinate.cc, 18 LOC)
  - Vector mathematics
  - Path calculations
  - Distance metrics
  - Coordinate normalization

### World Environment Implementation
- **Time System**: Custom game calendar with hours, days, months, and years
- **Day/Night Cycle**: Sunlight conditions that affect visibility and certain gameplay mechanics
- **Weather Simulation**: Dynamic weather system with seasonal variations and atmospheric effects
- **Atmospheric Pressure**: Complex weather simulation with pressure changes and atmospheric patterns

### Design Patterns
- **Prototype Pattern**: Templates for rooms, exits, objects, and mobiles
- **Delegation**: Room instances delegate property queries to prototypes
- **Reference Counting**: Tracking character presence for game mechanics
- **Spatial Partitioning**: Quadtree for efficient area lookups

## Key Files and Components

### Header Files
- `Area.hh` - Area class definition
- `Room.hh` - Room class definition
- `RoomPrototype.hh` - Room prototype definition
- `Exit.hh` (51 LOC) - Exit class definition
- `ExitPrototype.hh` (23 LOC) - Exit prototype definition
- `Location.hh` (114 LOC) - Location system definition
- `GameTime.hh` (39 LOC) - Game time system
- `worldmap/Coordinate.hh` (86 LOC) - World coordinate system
- `worldmap/Region.hh` (43 LOC) - Geographical region management
- `worldmap/Quadtree.hh` (100 LOC) - Spatial partitioning
- `RoomID.hh` (49 LOC) - Room identification system
- `RoomPrototype.hh` (44 LOC) - Room template definition
- `Reset.hh` (37 LOC) - Area reset instruction system
- `Sector.hh` (25 LOC) - Terrain type definition
- `Vnum.hh` (28 LOC) - Virtual number management
- `Weather.hh` (32 LOC) - Weather system definition
- `World.hh` (81 LOC) - World management interface

### Implementation Files
- `Area.cc` - Area implementation with loading and reset logic
- `Room.cc` - Room implementation with character management
- `GameTime.cc` (134 LOC) - Game time tracking and calendar system
- `World.cc` (307 LOC) - World management and coordination
- `Weather.cc` (147 LOC) - Dynamic weather system
- `RoomID.cc` (79 LOC) - Room identification system
- `RoomPrototype.cc` (132 LOC) - Room template system
- `worldmap/Coordinate.cc` (18 LOC) - Coordinate system implementation
- `worldmap/Region.cc` (157 LOC) - Region management implementation

## System Behaviors

### Core Behaviors
- **Room Identity**: Rooms have both a vnum (from prototype) and a unique location ID
- **Light Management**: Careful tracking of light sources as characters move
- **Area Reset Logic**: Areas reset based on age and presence of players (but not immortals)
- **Region System**: Areas map to geographic regions in the world
- **Time Cycle**: In-game time progresses with day/night cycles affecting gameplay
- **Weather System**: Dynamic weather with seasonal variations

### Special Features
- **Plague Spreading**: Disease effects can spread between characters in the same room
- **Environmental Effects**: Room conditions can affect character stats and abilities
- **Instance Management**: Multiple instances of the same room prototype can exist

## Dependencies and Relationships

### Dependencies On
- **Character System**: For tracking character presence and movement
- **Object System**: For managing items in rooms and areas
- **Affect System**: For applying status effects to rooms
- **Event System**: For firing events on room entry/exit
- **Information Systems**: For world visualization and mapping

### Depended On By
- **Movement System**: For handling character navigation
- **Combat System**: For battlefield properties and effects
- **Quest System**: For location-based objectives
- **Mobile System**: For NPC placement and behavior

## Open Questions and Future Improvements
- The room instance system suggests support for instanced dungeons - is this fully implemented?
- Area reset mechanics appear to consider player presence but not immortal presence - is this intentional?
- The region system could be enhanced with more geographic features
- Weather effects could be expanded to have more gameplay impact

---
