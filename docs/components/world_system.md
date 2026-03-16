---
id: world_system
name: World System
kind: system
layer: data_model
parent: null
depends_on: [character_data, object_system, utilities]
depended_on_by: [combat, magic, quests, mobprog_npc_ai, persistence, admin_tools, builder_tools, networking]
---

## Overview
<!-- section: overview | grounding: mixed -->
The World System forms the core spatial environment of the game, providing the physical structure where gameplay occurs. It's organized as a hierarchy of areas containing rooms, with navigation enabled through exits. The system employs a prototype pattern where areas load definitions for rooms, objects, and mobiles that are instantiated as needed during gameplay. It also manages environmental conditions, time, and world mapping to create an immersive and dynamic environment where player actions take place.

## Responsibilities
<!-- section: responsibilities | grounding: mixed -->

- Creating and managing the physical game world structure
- Handling room creation, properties, and interconnections
- Managing environmental conditions, time, and weather
- Supporting navigation, exploration, and world mapping
- Providing area reset mechanics for content respawning
- Maintaining spatial organization through regions and coordinates
- Simulating time progression and environmental changes

## Areas & Rooms
<!-- section: key_components | grounding: grounded -->

- `Area`: Represents a distinct geographical region
  - Manages loading from area files
  - Handles regular updates and resets
  - Tracks player and immortal presence
  - Contains collections of rooms, objects, and mobiles

- `Room`: Represents a specific location in the game world
  - Contains characters and objects
  - Connects to other rooms via exits
  - Can have specialized properties (safe, private, etc.)
  - Handles character entry and exit
  - Manages environmental conditions
  
- `RoomPrototype`: Template for creating room instances
  - Defines base properties (descriptions, flags, etc.)
  - Can be instantiated multiple times
  - Manages room attributes, flags, and behaviors
  - Provides prototype data to room instances
  
- `RoomID`: Unique identifier for room instances
  - Combines virtual number with instance number
  - Enables multiple instances of the same room template
  - Provides serialization and parsing utilities
  - Supports comparison and reference operations

- `Exit`/`ExitPrototype`: Defines connections between rooms
  - Contains direction, destination, and properties
  - Supports locks, hidden exits, etc.
  - Manages visibility and access controls
  - Tracks door states (open/closed/locked)
  - Supports one-way and bidirectional connections

## Environmental Systems
<!-- section: key_components | grounding: mixed -->

- `Location`: Represents a specific position in the game world
  - Combines room reference with position within room
  - Supports character/object positioning
  - Handles relative location calculations

- `GameTime`: Tracks in-game time
  - Hours, days, months, years tracking
  - Time-based event triggering
  - Day/night cycle calculations
  - Sunlight effects on gameplay
  - Custom game calendar system

- `Weather`: Environmental conditions simulator
  - Dynamic weather patterns with seasonal variations
  - Atmospheric pressure simulation system
  - Sky condition tracking (sunny, cloudy, rainy, etc.)
  - Room-specific weather effects
  - Weather forecasting capabilities

- `World`: Central coordinator for the game environment
  - Area management and organization
  - Global state tracking
  - World-wide updates and coordination
  - Area reset scheduling and management
  - World initialization and shutdown sequence
  - Instance management for rooms and areas

## Resets & Vnums
<!-- section: key_components | grounding: grounded -->

### World Organization
- `Reset`: Defines area respawn instructions
  - Controls mobile and object placement
  - Manages equipment for mobiles
  - Handles door states (open/closed/locked)
  - Supports various reset types and conditions

- `Vnum`: Virtual number identifier system
  - Uniquely identifies prototypes and areas
  - Maps to specific instances in the world
  - Provides type-safe alternative to raw integers
  - Supports range operations and comparisons

- `Sector`: Defines terrain types for rooms
  - Determines movement costs and limitations
  - Affects specific skills and abilities
  - Influences weather and environmental effects
  - Defines visual representation on maps

## Mapping & Coordinates
<!-- section: key_components | grounding: grounded -->

### Mapping Systems
- `Worldmap`: Core world map interface
  - Manages spatial organization
  - Supports terrain representation
  - Enables map generation and visualization

- `Coordinate`: Defines coordinate system for positions
  - Supports translation and validation
  - Enables distance calculations
  - Provides 2D/3D spatial representation

- `Region`: Defines geographical regions
  - Manages boundary detection
  - Handles property management
  - Organizes world into named areas

- `Quadtree`: Implements spatial partitioning
  - Optimizes spatial searches
  - Enables efficient area queries
  - Supports neighbor finding

### Map Visualization
- **MapColor**: Color management for terrain and feature representation
- **Map Generation**: ASCII-based world representation using symbols and colors
  - Character-based terrain and feature representation
  - Color coding for different terrain types and features
  - Dynamic generation based on game world state
  - Terminal color and symbol-based terrain display
  - Player position marking and view centering

## Navigation & Awareness
<!-- section: key_components | grounding: mixed -->
- **Scan**: Multi-directional room scanning
  - Shows characters and features in adjacent rooms up to several rooms away
  - Distance-based detail degradation (closer rooms show more info)
  - Skill-based range modifiers
  - Respects visibility rules (hidden, invisible, dark rooms)
- **Hunt/Track**: BFS pathfinding for locating targets
  - Breadth-first search across room exits to find shortest path
  - Skill-based success checks with environmental modifiers (terrain, weather)
  - Returns directional guidance toward the target
  - Used by both player `track` command and NPC hunting behavior
- **Movement**: Directional navigation between rooms
  - Movement point cost based on sector type (terrain)
  - Door opening, swim checks, fly requirements
  - Movement-triggered events (greet progs, aggression checks)
  - Position requirements (must be standing)

### Room Perception (Look/Examine)
- `do_look()` — Primary room examination command: displays room name, description, exits, contents (characters and objects), with visibility filtering based on light, hidden status, and perception
- `do_examine()` — Extended object/character inspection: combines look with additional detail (container contents, weapon stats, etc.)
- **Direction Scouting** — Looking in a direction shows brief info about adjacent room
- **Hidden Entity Handling** — Visibility mechanics determining what characters and objects are shown (affected by invis, hidden, detect, light levels)
- **Key File**: `act_info.cc` (5493 LOC) — Primary home for look/examine; cross-ref `character_data.md` for do_score/do_inventory

## Implementation Details
<!-- section: implementation | grounding: mixed -->

### Area Implementation
- **Construction and Loading**: Areas are built from text files (.are)
- **Section Types**: Areas load different sections for rooms, objects, mobiles, etc.
- **Update and Reset**: Areas respawn monsters and objects based on timers and player presence
- **Player Tracking**: Areas monitor character presence for update decisions (ignoring immortals for reset purposes)

### Room Implementation
- **Instance Creation**: Rooms are created from prototypes when needed
- **Character Movement**: Rooms handle character entry and exit with tracking mechanisms
- **Property Delegation**: Many room properties are delegated to their prototypes
- **Environmental State**: Rooms track conditions like light levels

### Environment Implementation
- **Time System**: Custom game calendar with hours, days, months, and years
- **Day/Night Cycle**: Sunlight conditions that affect visibility and certain gameplay mechanics
- **Weather Simulation**: Dynamic weather system with seasonal variations and atmospheric effects
- **Atmospheric Pressure**: Complex weather simulation with pressure changes and atmospheric patterns

### Region Management
- **Region Implementation**: Area geographical association with mapping between regions and world coordinates
- **Coordinate Operations**: Distance calculations, translations, and coordinate validation

## Key Files
<!-- section: key_components | grounding: grounded -->

### Header Files
- `/src/include/Area.hh` - Area class definition
- `/src/include/Room.hh` - Room class definition
- `/src/include/RoomPrototype.hh` - Room prototype definition (44 LOC)
- `/src/include/Exit.hh` - Exit class definition (51 LOC)
- `/src/include/ExitPrototype.hh` - Exit prototype definition (23 LOC)
- `/src/include/Location.hh` - Location system definition (114 LOC)
- `/src/include/GameTime.hh` - Game time system (39 LOC)
- `/src/include/Weather.hh` - Weather system definition (32 LOC)
- `/src/include/World.hh` - World management interface (81 LOC)
- `/src/include/RoomID.hh` - Room identification system (49 LOC)
- `/src/include/Reset.hh` - Area reset instruction system (37 LOC)
- `/src/include/Sector.hh` - Terrain type definition (25 LOC)
- `/src/include/Vnum.hh` - Virtual number management (28 LOC)
- `/src/include/worldmap/Worldmap.hh` - World map interface
- `/src/include/worldmap/Coordinate.hh` - Coordinate system (86 LOC)
- `/src/include/worldmap/Region.hh` - Geographical region management (43 LOC)
- `/src/include/worldmap/Quadtree.hh` - Spatial partitioning (100 LOC)

### Implementation Files
- `/src/Area.cc` - Area loading, initialization, and reset mechanics
- `/src/Room.cc` - Room instance creation and character movement tracking
- `/src/RoomPrototype.cc` - Room template loading and instance creation (132 LOC)
- `/src/Weather.cc` - Dynamic weather system with seasonal variations (147 LOC)
- `/src/World.cc` - Central world management for areas and updates (307 LOC)
- `/src/GameTime.cc` - In-game time with hour/day/month/year tracking (134 LOC)
- `/src/RoomID.cc` - Room identification functionality (79 LOC)
- `/src/worldmap/Region.cc` - Geographical region management (157 LOC)
- `/src/worldmap/Coordinate.cc` - Coordinate system operations (18 LOC)
- `/src/worldmap/Worldmap.cc` - Visual world map with terrain representation

### Spatial Awareness Files
- `/src/scan.cc` (223 LOC) — Multi-directional awareness implementation
- `/src/hunt.cc` (358 LOC) — Hunting/tracking system with BFS pathfinding
- `/src/worldmap/MapColor.hh` (48 LOC) — Map visualization colors

## System Behaviors
<!-- section: behaviors | grounding: mixed -->

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
- **Door States**: Exits can have doors with open/closed/locked states
- **Room Affects**: Rooms can have temporary or permanent status effects

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): For tracking character presence and movement
- **Object System** (`object_system`): For managing items in rooms and areas
- **Utilities** (`utilities`): For string formatting and support functions

### Depended On By
- **Combat** (`combat`): For battlefield properties and terrain effects
- **Magic** (`magic`): For spell targeting in rooms
- **Quests** (`quests`): For location-based objectives and triggers
- **MobProg & NPC AI** (`mobprog_npc_ai`): For NPC placement, behavior, and navigation
- **Persistence** (`persistence`): For area and room data storage
- **Admin Tools** (`admin_tools`): For environment manipulation
- **Builder Tools** (`builder_tools`): For area and room creation
- **Networking** (`networking`): For connection state during room display
