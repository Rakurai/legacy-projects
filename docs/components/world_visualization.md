# World Visualization

## Overview
The World Visualization subsystem provides ASCII-based mapping and spatial awareness tools such as world maps, scan, and hunt commands. It enables environmental perception and exploration with skill-based modifiers and visibility constraints, helping players understand and navigate the game world. This component delivers critical spatial information to players, enhancing immersion and supporting effective navigation and tracking within the complex game environment.

## Responsibilities
- Displaying detailed world and area maps with terrain representation
- Providing spatial awareness through scan and hunt commands
- Visualizing terrain, features, points of interest, and player position
- Supporting coordinate and region-based queries and navigation
- Facilitating player orientation and world discovery
- Enhancing immersion through visual representation of the game world

## Core Components

### World Map System
- **Worldmap**: ASCII-based map display and rendering system
  - Color-coded terrain representation
  - Feature highlighting for points of interest
  - View customization options
  - Coordinate system integration
- **MapColor**: Color management for terrain and feature representation
- **Coordinate System**: Position tracking and spatial calculations
- **Region Management**: Geographical area organization and mapping

### Spatial Awareness Tools
- **Scan**: Extended room visibility system
  - Multi-directional awareness beyond current room
  - Character and feature detection at a distance
  - Information filtering based on distance and skills
  - Environmental factor integration (light, weather)

- **Hunt**: Character tracking mechanics
  - Trail following functionality
  - Target location detection and direction finding
  - Skill-based success rates and checks
  - Environmental impact on tracking effectiveness

## Implementation Details

### World Map Implementation
- **Map Generation**: ASCII-based world representation using symbols and colors
  - Character-based terrain and feature representation
  - Color coding for different terrain types and features
  - Dynamic generation based on game world state
  - Scale and zoom level management

- **Coordinate System**: Mapping game locations to coordinates
  - X/Y/Z coordinate tracking
  - Distance calculation algorithms
  - Position translation between map and game world
  - Region boundary definitions and checks

- **Rendering**: Visual display of map data
  - Terminal color and symbol-based terrain display
  - Feature highlighting with special characters or colors
  - View framing and map window management
  - Map legend and orientation indicators

- **Player Positioning**: Showing current location
  - "You are here" positioning on maps
  - Orientation indicators (north arrow)
  - Path highlighting to destinations
  - View centering options

### Spatial Awareness Implementation
- **Scan System**: Multi-direction room visibility
  - Distance calculation algorithms for multi-room awareness
  - Entity detection based on visibility rules and skills
  - Information filtering by distance and relevance
  - Integration with perception skills and abilities

- **Hunt System**: Character tracking mechanics
  - Trail detection algorithms with skill-based checks
  - Direction determination to target
  - Environmental modifiers (terrain, weather)
  - Pursuit assistance with directional guidance

## Key Files

### Header Files
- `worldmap/Worldmap.hh` (30 LOC) - World map functionality
  - Map generation and display interfaces
  - Character-to-symbol mapping
  - Viewport management
  
- `worldmap/MapColor.hh` (48 LOC) - Map visualization colors
  - Color definitions for different terrain types
  - Feature highlighting color schemes
  - Color management utilities
  
- `worldmap/Coordinate.hh` (86 LOC) - World coordinate system
  - Position tracking structures
  - Coordinate manipulation functions
  - Distance and direction calculations
  
- `worldmap/Region.hh` (43 LOC) - Geographical region management
  - Region definition structures
  - Region boundary checking
  - Region relationship mapping
  
- `worldmap/Quadtree.hh` (100 LOC) - Spatial partitioning
  - Efficient spatial lookup structures
  - Quadrant-based entity tracking
  - Spatial query optimization

### Implementation Files
- `worldmap/Worldmap.cc` (109 LOC) - World map visualization
  - Map rendering implementation
  - Symbol mapping for terrain features
  - View management and scrolling
  
- `worldmap/Coordinate.cc` (18 LOC) - Coordinate system implementation
  - Coordinate manipulation functions
  - Distance calculations
  - Spatial translations
  
- `worldmap/Region.cc` (157 LOC) - Region management implementation
  - Area geographical association
  - Mapping between regions and world coordinates
  - Region boundary definitions
  
- `scan.cc` (223 LOC) - Area scanning functionality
  - Multi-directional awareness implementation
  - Distance-based entity detection
  - Skill and perception integration
  
- `hunt.cc` (358 LOC) - Hunting/tracking system
  - Trail detection algorithms
  - Direction calculation to targets
  - Skill check implementation
  - Environmental factor processing

## System Behaviors

### Map Display Behaviors
- **Map Accuracy**: Representation faithfully matches the actual game world
  - Terrain features match room descriptions
  - Paths and exits align with room connections
  - Special locations properly highlighted
  - Updated dynamically as world changes

- **Scale Options**: Different zoom levels for maps
  - World overview maps for broad navigation
  - Area maps for local detail
  - Room-level detail for immediate surroundings
  - Adjustable scale based on player preferences

- **Feature Highlighting**: Important locations marked
  - Cities and settlements with distinct symbols
  - Quest locations with special highlights
  - Points of interest marked clearly
  - Dangerous areas with warning indicators

- **Player Context**: Situational awareness
  - Current position clearly marked
  - Directional indicators for orientation
  - Distance scale indicators
  - Visible path highlighting

### Spatial Awareness Behaviors
- **Range Effects**: Information detail varies with distance
  - Close entities described in more detail
  - Distant entities with limited information
  - Progressive information degradation with distance
  - Skill-based maximum detection ranges

- **Skill Impact**: Character abilities affect information quality
  - Higher perception skills increase detection range
  - Tracking skills improve hunt accuracy
  - Class-specific bonuses to certain detection types
  - Special abilities for enhanced awareness

- **Environmental Factors**: External conditions affect perception
  - Weather reduces visibility ranges
  - Terrain affects movement and tracking
  - Light conditions modify detection chances
  - Time of day influences awareness systems

- **Stealth Interaction**: Hidden entities may avoid detection
  - Stealth vs. perception skill contests
  - Concealment modifiers from equipment
  - Environmental bonuses to hiding
  - Special abilities for enhanced concealment

## Dependencies and Relationships

### Dependencies On
- **World System**: For spatial data, room connections, and environment
  - Area definitions and room relationships
  - Terrain type information
  - Exit and path data
  - Environmental conditions

- **Character System**: For perception abilities and skills
  - Character perception attributes
  - Skill levels affecting awareness
  - Special abilities modifying detection
  - Movement capabilities

- **Information Systems**: For display and formatting
  - Output formatting and color support
  - Information presentation standards
  - Terminal capabilities handling
  - User interface conventions

### Depended On By
- **Players**: For navigation and orientation
  - World exploration assistance
  - Target location discovery
  - Path finding through complex areas
  - Situational awareness in combat

- **Quest System**: For objective location
  - Target finding assistance
  - Area discovery indicators
  - Journey progress visualization
  - Objective proximity awareness

- **Event System**: For location-based triggers
  - Event proximity awareness
  - Special location identification
  - Area-based event tracking
  - Geographic milestone recording
