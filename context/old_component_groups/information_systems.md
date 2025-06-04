# Information Systems Component Documentation

## Overview

The Information Systems component manages how game information is gathered, organized, presented, and discovered. These systems focus on providing players and administrators with access to data about the game world, game mechanics, other players, and system status - enhancing understanding and supporting decision-making.

### System Responsibilities
- Providing in-game documentation and knowledge management
- Delivering environmental and character information to players
- Supporting asynchronous communication through message boards
- Enabling world visualization and spatial awareness
- Facilitating content creation through editing tools
- Supporting debugging and system diagnostics

## Core Classes and Interfaces

### Help System
- **help_struct**: Core structure for help entries
  - Level requirements for viewing
  - Keywords for searching
  - Help text content

- **Help Categories**: Organized topic collections
  - Player Information (HELP_INFO)
  - Clan Information (HELP_CLAN)
  - Skills Documentation (HELP_SKILL)
  - Spells Documentation (HELP_SPELL)
  - Race Information (HELP_RACE)
  - Class Information (HELP_CLASS)
  - Movement Commands (HELP_MOVE)
  - Object Interaction (HELP_OBJECT)
  - Communication (HELP_COMM)
  - Combat System (HELP_COMBAT)
  - Miscellaneous Help (HELP_MISC)
  - Administrative Commands (HELP_WIZ*)

### Information Commands
- **Look**: Environmental perception commands
  - Room examination
  - Object inspection
  - Character observation
  - Direction scouting

- **Status**: Character status display
  - Attributes and statistics
  - Equipment and inventory
  - Skill and spell status
  - Combat readiness
  - Experience and progression

- **World Information**: Environmental data
  - Time and weather
  - Area information
  - World news and events
  - Game statistics

### Message Board System
- **Note**: Asynchronous communication framework
  - Multiple themed boards for different topics
  - Permissions-based read/write access
  - Note creation, editing, and removal
  - Read status tracking for unread messages
  - Searchable content with keywords and metadata

### Editor System
- **Edit**: In-game text editor for various content types
  - Line-based editing with command syntax
  - Support for notes, descriptions, and other text content
  - Copy, paste, and formatting capabilities
  - String replacement and modification functions

### World Visualization
- **Worldmap**: ASCII-based map display
  - Color-coded terrain representation
  - Feature highlighting for points of interest
  - View customization options
  - Coordinate system integration

### Spatial Awareness
- **Scan**: Extended room visibility system
  - Multi-directional awareness
  - Character detection beyond current room
  - Distance-based information filtering
  
- **Hunt**: Character tracking mechanics
  - Trail following functionality
  - Target location detection
  - Skill-based success rates
  - Environmental impact on tracking

### Debug Information
- **Debug Commands**: System inspection tools
  - Memory usage monitoring
  - System performance commands
  - Test functionality
  - State inspection tools

## Implementation Details

### Help System Implementation
- **Database Structure**: SQLite table for help entries
  - Fields for level, group, keywords, and text
  - Efficient querying and retrieval
  - Transaction handling for updates
- **Help File Loading**: Dynamic loading from help directory
  - Help file parsing and validation
  - Category-based organization
  - Level-based access control 
- **Categorization**: Topic organization by system or function
- **Search Algorithm**: Keyword matching for help topics
  - Character-specific help search
  - Comprehensive indexing
- **Help Display**: Formatted presentation of help content
- **Help Writing**: Tools for creating and editing help files

### Information Commands Implementation
- **Look Command**: Multi-target environmental perception
  - Room descriptions with exit information
  - Object examination with special properties
  - Character inspection with equipment visibility
  - Special handling for hidden/invisible entities
- **Status Commands**: Character information display
  - Core stats and derived attributes
  - Equipment status and properties
  - Skill proficiency and spell knowledge
  - Quest tracking and achievements
- **World Commands**: Environmental information
  - Time system integration
  - Weather condition reporting
  - Area-specific information
  - Game world statistics

### Message Board Implementation
- **Board Management**: Creating and organizing boards
- **Note System**: Comprehensive bulletin board system 
  - Thread-based organization
  - Read/unread tracking
  - Permission-based access control
  - Forwarding and reply capabilities

### Editor Implementation
- **Command Structure**: Line-based editing commands
- **Buffer Management**: Text storage and manipulation
- **Format Control**: Basic text formatting capabilities
- **Integration**: Support for various editable content

### World Visualization Implementation
- **Map Generation**: ASCII-based world representation
- **Coordinate System**: Mapping game locations to coordinates
- **Rendering**: Color and symbol-based terrain display
- **Player Positioning**: Showing current location on map

### Spatial Awareness Implementation
- **Scan System**: Multi-direction room visibility
  - Distance calculation algorithms
  - Entity detection based on visibility rules
  - Information filtering by distance
- **Hunt System**: Character tracking
  - Trail detection with skill checks
  - Direction determination
  - Environmental modifiers

### Debug Information Implementation
- **Memory Tracking**: Resource usage monitoring
- **Performance Metrics**: System efficiency measurement
- **State Inspection**: Runtime game state examination
- **Test Commands**: Functionality verification tools

## Key Files and Components

### Header Files
- `help.hh` - Help system interface
- `Edit.hh` (28 LOC) - In-game text editor
- `Note.hh` (51 LOC) - Message board system
- `worldmap/Worldmap.hh` (30 LOC) - World map functionality
- `worldmap/MapColor.hh` (48 LOC) - Map visualization colors

### Implementation Files
- `help.cc` (718 LOC) - Help system implementation
- `act_info.cc` (5493 LOC) - Information command implementation
- `Note.cc` (1985 LOC) - Message board implementation
- `scan.cc` (223 LOC) - Area scanning functionality
- `hunt.cc` (358 LOC) - Hunting/tracking system
- `worldmap/Worldmap.cc` (109 LOC) - World map visualization
- `debug.cc` - Debugging utilities

## System Behaviors

### Help System Behaviors
- **Topic Organization**: Hierarchical arrangement of help topics
- **Keyword Searching**: Finding topics by relevant keywords
- **Context Sensitivity**: Some help responds to context
- **Dynamic Updates**: Help content can be modified at runtime
- **Targeted Help**: Different information for different user types

### Information Command Behaviors
- **Context Awareness**: Information tailored to situation
- **Detail Levels**: Varying information depth based on skills
- **Hidden Information**: Some details require special perception
- **Format Consistency**: Standardized information presentation

### Message Board Behaviors
- **Persistence**: Notes remain available across sessions
- **Organization**: Themed boards for different topics
- **Notifications**: Indication of unread messages
- **Access Control**: Different boards for different audiences

### Editor Behaviors
- **Command Mode**: Line-oriented editing commands
- **Context Awareness**: Different modes for different content
- **Persistence**: Content saved across editing sessions
- **Format Support**: Basic text formatting capabilities

### Visualization Behaviors
- **Map Accuracy**: Representation matches game world
- **Scale Options**: Different zoom levels for maps
- **Feature Highlighting**: Important locations marked
- **Player Context**: "You are here" positioning

### Spatial Awareness Behaviors
- **Range Effects**: Information detail varies with distance
- **Skill Impact**: Character abilities affect information quality
- **Environmental Factors**: Weather and light affect perception
- **Stealth Interaction**: Hidden entities may avoid detection

## Dependencies and Relationships

### Dependencies On
- **Character System**: For perception abilities and skills
- **World System**: For spatial relationships and environment
- **Object System**: For item information and properties
- **Command System**: For command processing and execution

### Depended On By
- **Players**: For learning and understanding the game
- **Combat System**: For tactical awareness and targeting
- **Quest System**: For objective information and tracking
- **Social Systems**: For player communication and coordination

## Open Questions and Future Improvements
- The help system search could be improved with more advanced algorithms
- World visualization could be enhanced with more detailed maps
- Information commands could provide more context-sensitive details
- Message boards could support more advanced formatting and organization
- Spatial awareness systems could incorporate more environmental factors
- Debug information could be expanded for more comprehensive monitoring

---
