---
id: notes_editor
name: Notes & Editor
kind: system
layer: content_system
parent: null
depends_on: [command_interpreter, character_data, persistence]
depended_on_by: [help_system]
---

## Overview
<!-- section: overview | grounding: mixed -->
The In-Game Editor subsystem offers a line-based text editor for editing descriptions, notes, and help entries within the game environment. It supports formatting commands and persistence, enabling players and administrators to create and modify content dynamically. This system is essential for content creation and modification without requiring server restarts or external tools, supporting both administrative functions and player-generated content.

## Responsibilities
<!-- section: responsibilities | grounding: mixed -->

- Providing comprehensive in-game text editing for descriptions, notes, help files, and other text content
- Supporting line-based editing commands with syntax similar to basic Unix editors
- Managing text buffers and temporary storage during editing sessions
- Implementing formatting options and text manipulation functions
- Ensuring content persistence and proper integration with relevant game systems
- Supporting different editing contexts with appropriate behavior modifications
- Providing user feedback and command assistance during editing

## Line Editor
<!-- section: key_components | grounding: mixed | role: mechanism -->

### Editor Core
- **Edit Class**: Primary in-game text editor implementation
  - Line-based editing interface
  - Command parsing and execution
  - Buffer management for text content
  - Session persistence between commands

- **Command Structure**: Comprehensive editing command set
  - Line insertion, deletion, and modification
  - Text block operations (copy, cut, paste)
  - Search and replace functionality
  - Format control commands
  - Navigation within the buffer

- **Buffer Management**: Text storage and manipulation
  - Line-oriented text storage
  - Undo/redo capability
  - Clipboard functionality
  - Temporary storage during editing

- **Format Control**: Text appearance manipulation
  - Basic text formatting capabilities
  - Color code insertion and handling
  - Paragraph and line formatting
  - Special character handling

## Note Boards
<!-- section: key_components | grounding: mixed | role: mechanism -->

### Content Type Handlers
- **Note Editor**: Bulletin board post editing
  - Subject line handling
  - Post formatting conventions
  - Reply and forward functionality
  - Board-specific formatting rules

- **Note Boards**: Multiple themed message boards
  - Board types: general notes, ideas, changes, news, immortal quests, penalties
  - Each board has its own file-based storage
  - Level-gated access (board visibility and posting permissions based on character level/role)
  - Multi-recipient addressing with "to" field parsing

- **Note Reading**: Browsing and reading posted notes
  - Unread tracking per character
  - Spool browsing with next/previous navigation
  - Catchup command to mark all notes as read
  - Note expiration with configurable expiry dates
  - Timestamp and sender/recipient display

- **Description Editor**: Room, object, and character description editing
  > **Note:** Description editing for rooms/objects uses the Line Editor but is owned by the respective systems (`world_system`, `object_system`, `builder_tools`). Cross-reference only.

- **Help File Editor**: Help content management
  > **Note:** Help editing is owned by `help_system`. Cross-reference only.

- **Miscellaneous Content**: Other text content types
  - Player biographies and backgrounds
  - Mail message composition
  - Area notes and documentation
  - Custom content types

## Implementation Details
<!-- section: implementation | grounding: mixed -->

### Editor Implementation
- **Command Processing**: Editor command execution flow
  - Command prefix identification
  - Argument parsing and validation
  - Command execution with error handling
  - State management between commands

- **Buffer Operations**: Text content manipulation
  - Line addition, insertion, and deletion
  - Block operations for efficient editing
  - Search algorithms for text location
  - Replace functionality with confirmation options

- **Session Management**: Editing state persistence
  - Interrupted session recovery
  - Timeout handling for idle sessions
  - Multi-part editing support
  - Abort and save conflict resolution

- **Integration Points**: Connection with other systems
  - Content delivery to appropriate systems
  - Validation based on destination requirements
  - Format conversion for storage
  - Permission checking for edit operations

## Key Files
<!-- section: key_components | grounding: mixed -->

### Header Files
- `Edit.hh` (28 LOC) - In-game text editor interface
  - Editor class definition
  - Command constants and structures
  - Buffer management interfaces
  - Integration point declarations

### Implementation Files
- While no dedicated implementation file was found, the editor functionality is likely integrated within:
  - Note system implementation
  - Help system implementation
  - Description editing commands
  - Admin tools for content management

### Key Classes and Structures
- **Edit Class**: Core editor implementation
  - Buffer storage and management
  - Command processing logic
  - State tracking between commands
  - Integration with destination systems

- **EditorState**: Session persistence structure
  - Current buffer contents
  - Cursor position and selection
  - Command history
  - Context information

## System Behaviors
<!-- section: behaviors | grounding: mixed -->

### Command Mode Behaviors
- **Line-Oriented Editing**: Text manipulation by line numbers
  - Adding lines with automatic numbering
  - Replacing specific line contents
  - Deleting single or ranges of lines
  - Inserting lines between existing content

- **Block Operations**: Multi-line text manipulation
  - Copying blocks to clipboard
  - Cutting content with preservation
  - Pasting from clipboard
  - Moving blocks within the buffer

- **Search and Navigation**: Content location and movement
  - Finding text patterns within buffer
  - Jumping to specific lines
  - Navigating by page or section
  - Position tracking and display

- **Formatting Commands**: Text appearance modification
  - Color code insertion and management
  - Paragraph formatting for readability
  - Indentation and alignment control
  - Special character insertion

### Context Awareness Behaviors
- **Content Type Adaptation**: Behavior changes based on edited content
  - Different validation rules for different destinations
  - Format suggestions based on content type
  - Command availability based on editing context
  - Help and guidance specific to content purpose

- **Permission-Based Features**: Access control for editing capabilities
  - Admin-only formatting options
  - Content type restrictions based on privileges
  - Size and complexity limitations based on user level
  - Special command access for authorized users

- **Feedback Systems**: User guidance during editing
  - Command help and suggestions
  - Error messages with correction hints
  - Status updates on buffer state
  - Completion confirmations

### Persistence Behaviors
- **Session Continuity**: Edit state preservation
  - Buffer preservation between commands
  - Interrupted session recovery
  - Timeout handling with content preservation
  - Conflict resolution for simultaneous edits

- **Content Integration**: Proper storage of edited content
  - Destination-specific formatting and validation
  - Version control for important content
  - Backup creation before major changes
  - Atomic transaction handling for saves

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Command Interpreter** (`command_interpreter`): For processing editor commands
- **Character Data** (`character_data`): For editor user state and permissions
- **Persistence** (`persistence`): For saving edited content

### Depended On By
- **Help System** (`help_system`): For help file creation and modification
