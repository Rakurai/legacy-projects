# Status & Look Commands

## Overview
The Status & Look Commands subsystem implements character self-inspection and environmental perception, enabling players to see their stats, surroundings, and interactable elements in a room. It supports context-sensitive display and hidden entity handling, providing essential feedback for player awareness and decision-making. This system forms the core of how players experience and interact with both their character's condition and the game environment, serving as the primary sensory interface to the game world.

## Responsibilities
- Displaying comprehensive character status, attributes, and equipment
- Showing detailed room descriptions and visible entities with appropriate filtering
- Supporting examination of objects, characters, and environments at multiple detail levels
- Handling context-sensitive and hidden information based on character abilities
- Providing feedback on character condition, effects, and progression
- Formatting and organizing complex information for readability
- Supporting special perception abilities and detection mechanics

## Core Components

### Look Command System
- **Room Examination**: Environmental perception commands
  - Room descriptions with dynamic elements
  - Object and character visibility in locations
  - Exit information with status indicators
  - Special feature detection

- **Object Inspection**: Item examination functionality
  - Detailed item properties and descriptions
  - Equipment and container contents
  - Special object characteristics
  - Hidden features and triggers

- **Character Observation**: NPC and player examination
  - Visual appearance and equipment visibility
  - Status and condition indicators
  - Relative strength assessment
  - Relationship and faction indicators

- **Direction Scouting**: Extended perception beyond current room
  - Peek functionality for adjacent rooms
  - Path characteristics and difficulty
  - Danger detection and warnings
  - Terrain information for movement planning

### Status Command System
- **Attribute Display**: Character statistics visualization
  - Core attributes and derived statistics
  - Current vs. maximum values (HP/Mana/Move)
  - Temporary modifiers and effects
  - Progress indicators and milestones

- **Equipment Status**: Character gear management
  - Equipped items by slot
  - Item condition and properties
  - Special equipment effects
  - Set bonuses and combinations

- **Skill and Spell Status**: Ability information
  - Known skills and spells
  - Proficiency levels and cooldowns
  - Practice and training status
  - Skill dependencies and requirements

- **Combat Readiness**: Battle preparation information
  - Weapon and armor statistics
  - Combat modifiers and bonuses
  - Status effects relevant to combat
  - Tactical information and recommendations

- **Experience and Progression**: Character development tracking
  - Experience points and level information
  - Training points and options
  - Quest completion status
  - Achievement tracking and milestones

### Information Handling
- **Context-Sensitive Display**: Adaptive information presentation
  - Information filtering based on character knowledge
  - Detail level adjustment for different commands
  - Progressive revelation of complex information
  - Situational awareness enhancement

- **Hidden Entity Handling**: Detection and visibility systems
  - Invisibility and hiding mechanics
  - Perception skill checks and contests
  - Environmental factors affecting visibility
  - Special detection abilities and limitations

## Implementation Details

### Look Command Implementation
- **Room Description System**: Environmental information delivery
  - Base room descriptions with dynamic elements
  - Time and light-dependent description modifiers
  - Weather and season effects on descriptions
  - Special handling for underwater, flying, or unusual positions

- **Object Examination Logic**: Item information presentation
  - Multi-level detail for different examination commands
  - Special object type handling (containers, portals, etc.)
  - Magical and hidden property detection
  - Value and quality assessment information

- **Character Inspection**: NPC/player examination system
  - Equipment visibility based on positioning
  - Health and status indication through descriptions
  - Special characteristics and notable features
  - Disguise and illusion handling

- **Special Perception**: Enhanced awareness mechanics
  - Detection systems for hidden objects and characters
  - Secret door and trap discovery
  - Special vision types (darkvision, truesight, etc.)
  - Perception skill integration with look commands

### Status Command Implementation
- **Core Stats Display**: Character information organization
  - Formatted presentations of diverse attributes
  - Comparative statistics for self-assessment
  - Alignment and faction standing information
  - Currency, wealth and resource tracking

- **Equipment Status Organization**: Gear management views
  - Inventory categorization and sorting
  - Equipment slot utilization and options
  - Item enhancement and enchantment display
  - Weight, value, and condition tracking

- **Ability Status Tracking**: Skill and spell management
  - Comprehensive ability listings with details
  - Training and practice status information
  - Cooldown and availability tracking
  - Prerequisite and advancement paths

- **Condition Monitoring**: Character state visualization
  - Current effects and their durations
  - Beneficial and harmful condition tracking
  - Recovery rates and estimated durations
  - Status effect stacking and interaction display

## Key Files

### Implementation Files
- `act_info.cc` (5493 LOC) - Primary information command implementation
  - Look command and all variants
  - Status display commands (score, affects, etc.)
  - Equipment and inventory commands
  - Examination and inspection functionality

### Key Functions
- `do_look()` - Primary environmental perception function
  - Direction-based looking
  - Target-specific examination
  - Visibility checks and filtering
  - Description formatting and delivery

- `do_examine()` - Detailed object inspection
  - Container contents checking
  - Hidden feature detection
  - Extended object information
  - Special object type handling

- `do_score()` - Character status overview
  - Core attribute display
  - Derived statistics calculation
  - Formatting and presentation
  - Character goals and achievements

- `do_inventory()` - Item possession management
  - Carried item listing
  - Weight calculation
  - Item categorization
  - Special item flagging

## System Behaviors

### Environmental Perception Behaviors
- **Detail Levels**: Information depth varies by command and context
  - Quick glance vs detailed examination
  - Automatic vs requested information
  - Skill-based information revelation
  - Experience-based knowledge display

- **Visibility Mechanics**: Complex sight and detection systems
  - Light level effects on visibility
  - Concealment and hiding mechanics
  - Distance-based detail degradation
  - Special vision modes and limitations

- **Dynamic Descriptions**: Adaptive environmental information
  - Time-sensitive description elements
  - Weather and condition effects
  - Character state influence on perception
  - Special ability modifications to standard views

- **Information Prioritization**: Relevant data highlighting
  - Threat and danger emphasis
  - Value and usefulness indicators
  - Changed state notifications
  - Important interaction opportunity flagging

### Character Information Behaviors
- **Comprehensive Self-Assessment**: Complete character status
  - Full attribute and status display
  - Progress tracking and milestones
  - Comparative strength indicators
  - Goal and achievement tracking

- **Equipment Management**: Gear information organization
  - Slot optimization suggestions
  - Comparison between equipped and carried items
  - Set completion tracking
  - Special equipment interaction hints

- **Status Effect Tracking**: Active modification monitoring
  - Remaining duration of temporary effects
  - Stacking effect visualization
  - Conflicting effect warnings
  - Beneficial vs harmful effect distinction

- **Progression Guidance**: Development path information
  - Available training options
  - Skill and spell advancement paths
  - Level-up requirements and benefits
  - Quest and achievement opportunities

## Dependencies and Relationships

### Dependencies On
- **Character System**: For character attributes, stats, and progression data
  - Character structure access
  - Skill and ability information
  - Status effect tracking
  - Perception and detection abilities

- **Object System**: For item properties and interaction
  - Item data structures
  - Container content management
  - Equipment slot handling
  - Special item behaviors

- **World System**: For room data and environmental information
  - Room descriptions and properties
  - Exit and connection information
  - Environmental conditions
  - Special location features

- **Information Systems**: For display formatting and organization
  - Output formatting and pagination
  - Color and emphasis conventions
  - Information categorization
  - User interface standards

### Depended On By
- **Players**: For primary game world interaction
  - Situational awareness
  - Character status monitoring
  - Environmental navigation
  - Interaction opportunity discovery

- **Quest System**: For objective tracking and completion
  - Goal visibility and progress
  - Target identification
  - Collection tracking
  - Achievement recognition

- **Combat System**: For tactical decision making
  - Opponent assessment
  - Environment evaluation
  - Equipment status awareness
  - Condition and effect monitoring
