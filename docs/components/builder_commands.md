# Builder Commands

## Overview
The Builder Commands subsystem provides comprehensive tools for content creators to build and modify game areas, rooms, objects, and NPCs from within the game. It includes commands for object spawning, area creation, and prototype editing, supporting dynamic world development without requiring server restarts or external file editing. This system serves as the foundation for all content creation in the MUD, enabling administrators to create rich, interactive environments directly through the game interface.

## Responsibilities
- Creating and editing comprehensive game areas, rooms, objects, and NPCs
- Spawning and modifying game entities with real-time updates
- Managing complex world structures and interconnections
- Supporting builder permissions and tiered access control
- Providing tools for prototype creation and instance management
- Facilitating world testing and validation
- Enabling content duplication and mass creation
- Supporting area reset configuration and behavior definition

## Core Components

### World Building Tools
- **Area Management**: Area creation and configuration
  - Area initialization and property setting
  - Reset behavior configuration
  - Area connection and relationship management
  - Area flags and special properties

- **Room Creation**: Environmental space development
  - Room description and property editing
  - Exit creation and linking
  - Room flag configuration
  - Special room feature implementation
  - Room coordinate assignment

- **Exit Management**: Connection between rooms
  - Bidirectional exit creation
  - Door implementation and lock configuration
  - Special exit types (portals, hidden paths)
  - Exit flag management
  - Direction and orientation control

### Entity Creation Tools
- **Object Creation**: Item development
  - Object prototype creation and editing
  - Instance spawning with customization
  - Container and content management
  - Special object property configuration
  - Object reset behavior configuration

- **Mobile Creation**: NPC development
  - Mobile prototype definition
  - Instance creation with customization
  - Shop and vendor configuration
  - Special behavior assignment
  - Combat properties and equipment
  - AI script attachment

### Prototype Management
- **Template Control**: Base entity management
  - Prototype creation and modification
  - Prototype listing and searching
  - Inheritance and extension mechanics
  - Default property configuration

- **Instance Management**: Entity instantiation
  - Creating instances from prototypes
  - Instance customization and modification
  - Mass production capabilities
  - Instance tracking and cleanup

### Builder Support Tools
- **Examination Commands**: Entity inspection
  - Detailed property viewing
  - Statistical analysis
  - Relationship visualization
  - Internal structure examination

- **Copy and Duplication**: Content replication
  - Template copying with modifications
  - Recursive duplication of complex structures
  - Mass production with variations
  - Cross-area copying

## Implementation Details

### Command Structure
- **Command Hierarchy**: Organized by function
  - Creation commands (create, dig, open)
  - Modification commands (set, edit)
  - Examination commands (stat, rlist, olist, mlist)
  - Management commands (purge, reset)
  - Utility commands (clone, copy)

- **Permission System**: Tiered access control
  - Level-based command availability
  - Area ownership and permissions
  - Edit restrictions and locks
  - Builder-specific flags and privileges

- **Parameter Handling**: Command argument processing
  - Target specification and resolution
  - Property value parsing and validation
  - Flag manipulation syntax
  - Wildcard and pattern support

### Entity Management
- **Prototype System**: Template-based creation
  - Reusable entity definitions
  - Default property configurations
  - Inheritance between prototypes
  - Versioning and reference tracking

- **Property Manipulation**: Entity customization
  - Type-specific property editors
  - Flag manipulation commands
  - Description and text editing
  - Numerical value configuration

- **Reset Configuration**: World state management
  - Object placement and respawning
  - Mobile positioning and behavior
  - Reset timing and conditions
  - Special reset instructions

## Key Files

### Implementation Files
- `wiz_build.cc` (348 LOC) - Core world building tools
  - Room and area creation commands
  - Object prototype management
  - Mobile creation and configuration
  - Reset behavior implementation

### Key Commands
- **Area Tools**: `aset`, `astat`, `alist`, `areset`
  - Area property management
  - Area overview and statistics
  - Area listing and searching
  - Reset configuration

- **Room Tools**: `dig`, `rset`, `rstat`, `rlist`
  - Room creation and connection
  - Room property configuration
  - Room examination
  - Room listing and searching

- **Object Tools**: `create`, `oset`, `ostat`, `olist`
  - Object creation and instantiation
  - Object property configuration
  - Object examination
  - Object listing and filtering

- **Mobile Tools**: `mset`, `mstat`, `mlist`, `mload`
  - Mobile property configuration
  - Mobile examination
  - Mobile listing and filtering
  - Mobile instantiation and placement

- **General Tools**: `purge`, `reset`, `redit`, `oedit`, `medit`
  - Entity removal and cleanup
  - Area reset forcing
  - Advanced editors for rooms, objects, and mobiles

## System Behaviors

### Creation Behaviors
- **Template-Based Creation**: Entities created from prototypes
  - Default values from templates
  - Inheritance of properties
  - Instance customization
  - Template versioning

- **Incremental Building**: Progressive world development
  - Room-by-room creation
  - Exit linking and connection
  - Object placement and attachment
  - Mobile positioning and behavior setting

- **Mass Production**: Efficient content creation
  - Bulk entity creation
  - Template duplication with variations
  - Recursive copying of structures
  - Pattern-based generation

### Management Behaviors
- **Property Control**: Detailed entity configuration
  - Typed property editors
  - Flag and bit manipulation
  - Numerical value constraints
  - Text and description formatting

- **Examination Tools**: Content inspection and validation
  - Detailed property views
  - Relationship visualization
  - Structural validation
  - Statistical analysis

- **Reset Management**: World state control
  - Configurable reset behavior
  - Manual reset triggering
  - Reset validation and debugging
  - Special reset instructions

### Access Control Behaviors
- **Permission Hierarchy**: Tiered building rights
  - Level-based command access
  - Area ownership restrictions
  - Editor access permissions
  - Special builder flags

- **Safety Measures**: Protection against errors
  - Confirmation for destructive actions
  - Validation of critical changes
  - Rollback capabilities
  - Change logging and tracking

## Dependencies and Relationships

### Dependencies On
- **World System**: For area and room structure
  - Room connections and relationships
  - Area organization and properties
  - Geographic coordinates and mapping
  - Environmental features

- **Object System**: For item creation and management
  - Object prototypes and instances
  - Object property definitions
  - Container relationships
  - Special object behaviors

- **Character System**: For NPC development
  - Mobile prototypes and instances
  - AI and behavior scripting
  - Combat statistics and abilities
  - Equipment and inventory

- **Admin Controls**: For permissions and security
  - Access level verification
  - Command availability checking
  - Audit logging of changes
  - Builder privilege management

### Depended On By
- **Content Creators**: World builders and designers
  - Area developers
  - Quest designers
  - Special event creators
  - World maintainers

- **Game Administrators**: For world management
  - Content modification
  - Bug fixing in the world
  - Special event setup
  - World state restoration

- **Quest System**: For interactive content
  - Quest-related object creation
  - Special NPC setup
  - Event trigger placement
  - Dynamic content management
