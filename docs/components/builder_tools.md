---
id: builder_tools
name: Builder Tools
kind: system
layer: operations
parent: null
depends_on: [character_data, object_system, world_system, admin_tools, command_interpreter]
depended_on_by: []
---

## Overview
<!-- section: overview | grounding: mixed -->
The Builder Commands subsystem provides comprehensive tools for content creators to build and modify game areas, rooms, objects, and NPCs from within the game. It includes commands for object spawning, area creation, and prototype editing, supporting dynamic world development without requiring server restarts or external file editing. This system serves as the foundation for all content creation in the MUD, enabling administrators to create rich, interactive environments directly through the game interface.

## Responsibilities
<!-- section: responsibilities | grounding: mixed -->

- Creating and editing comprehensive game areas, rooms, objects, and NPCs
- Spawning and modifying game entities with real-time updates
- Managing complex world structures and interconnections
- Supporting builder permissions and tiered access control
- Providing tools for prototype creation and instance management
- Facilitating world testing and validation
- Enabling content duplication and mass creation
- Supporting area reset configuration and behavior definition

## World Building Tools
<!-- section: key_components | grounding: mixed -->

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

## Entity Creation Tools
<!-- section: key_components | grounding: mixed -->

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

## Prototype Management
<!-- section: key_components | grounding: mixed -->

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
<!-- section: implementation | grounding: mixed -->

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
<!-- section: key_components | grounding: grounded -->

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
<!-- section: behaviors | grounding: mixed -->

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

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **World System** (`world_system`): For area and room structure
- **Object System** (`object_system`): For item creation and management
- **Character Data** (`character_data`): For NPC development and mobile prototypes
- **Admin Tools** (`admin_tools`): For permissions and security
- **Command Interpreter** (`command_interpreter`): For command routing
