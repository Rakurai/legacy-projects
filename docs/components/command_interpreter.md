# Command Interpreter

## Overview
The Command Interpreter subsystem parses player input and routes it to appropriate command handlers. It forms the core interface between players and the game world, translating text input into game actions. The system includes command registration, privilege checking, command abbreviation, state-aware command availability, and runtime command toggling. All player interactions with the game are processed through this central system, making it critical for the entire gameplay experience.

## Responsibilities
- Processing and interpreting player commands
- Managing command registration and lookup
- Handling privilege and permission checks
- Supporting command abbreviation and dynamic availability
- Disabling/enabling commands at runtime
- Parsing and extracting command arguments
- Routing commands to appropriate handlers
- Throttling commands to prevent spam

## Core Components

### Command System
- `cmd_type`: Command structure with handler function
  - Stores command name, function pointer, position requirements
  - Tracks required permissions and level requirements
  - Contains function pointer to handler code
  - May include usage hints and help information

- `DO_FUN`: Function pointer type for command handlers
  - Standard interface for all command implementations
  - Ensures consistent parameter passing

- `Disabled`: System to disable specific commands
  - Tracks disabled commands with reasons
  - Persists disabled status between server restarts
  - Provides administrative controls for toggling

- `interp`: Core command interpretation functionality
  - Command lookup with abbreviation support
  - Parameter parsing and token extraction
  - Permission and state validation
  - Command dispatching to handler functions

- **Command Table**: Extensive registry of all game commands
  - Organized by function and permission level
  - Hundreds of commands with specialized handlers

### Connection System
- `conn::State`: State machine for connection handling
  - Various state implementations for login sequence
  - PlayingState for active gameplay
  - Other states for character creation and configuration

### Argument Parsing
- **Sophisticated parsing functions**: Extract structured information from text input
  - Number-name format parsing
  - Quote-aware tokenization
  - Quantity parsing
  - Complex entity references
  - Context-sensitive interpretation

## Implementation Details

### Command Implementation
- **Command Lookup**: Partial name matching through prefix matching
  - Finds shortest unique prefix for commands
  - Handles ambiguity and suggestions

- **Privilege Checking**: Multi-level validation system
  - Character permission level checks
  - Position requirements (standing, fighting, etc.)
  - Status effect restrictions

- **Command Disabling**: Administrative control over available commands
  - Runtime toggling with reason tracking
  - Persistence of disabled commands

- **Argument Parsing**: Sophisticated text processing
  - Breaking commands into components
  - Handling quoted strings
  - Managing numeric prefixes
  - Supporting complex targeting syntax

### Command Routing
- **Input Processing**: Clean and normalize user input
- **Command Recognition**: Match input to defined commands
- **Handler Dispatch**: Call appropriate handler function
- **Error Handling**: Provide feedback for invalid commands
- **Throttling**: Prevent command flooding and spam

## Key Files

### Header Files
- `/src/include/interp.hh` - Command system interface and definitions
- `/src/include/Disabled.hh` - Command disabling functionality
- `/src/include/conn/State.hh` (79 LOC) - Connection state machine
- `/src/include/Actable.hh` (7 LOC) - Interface for action-capable entities

### Implementation Files
- `/src/interp.cc` - Core command interpretation implementation
  - Contains the extensive command table
  - Implements the central `interpret()` function
  - Manages command lookup and dispatching

- `/src/Disabled.cc` - Command disabling implementation
- `/src/argument.cc` - Sophisticated command argument parsing utilities
- `/src/conn/*.cc` - Connection state implementations
- `/src/act_*.cc` files - Various command implementation groups:
  - `/src/act_comm.cc` - Communication commands
  - `/src/act_move.cc` (3306 LOC) - Movement commands
  - `/src/act_obj.cc` (5383 LOC) - Object interaction commands
  - `/src/act_info.cc` - Information gathering commands

## System Behaviors

### Core Behaviors
- **Command Processing**: Parse text and route to appropriate handlers
- **Command Hierarchy**: Commands organized by permission level
- **Command Abbreviation**: Commands can be abbreviated to shortest unique prefix
- **Permission Management**: Multi-level access control system
- **State-Based Availability**: Commands available based on character state
- **Dynamic Command Listing**: Commands shown based on character access level

### Special Features
- **Command Throttling**: Prevention of command spam
- **Disabled Command Management**: Runtime control of available commands
- **Context-Sensitive Help**: Command-specific help and usage information
- **Position Requirements**: Commands require specific character positions
- **Command Logging**: Tracking of command usage for administrative purposes
- **Command Aliasing**: Support for custom command shortcuts (via alias system)

## Dependencies and Relationships

### Dependencies On
- **Character System**: For actor state, permissions, and position requirements
- **World System**: For movement between rooms and location context
- **Object System**: For item manipulation and object targeting
- **Affect System**: For ability to use commands under status effects
- **Information Systems**: For gathering and displaying command results

### Depended On By
- **All Gameplay Systems**: Most game interactions flow through commands
- **Scripting**: NPC behaviors use the command mechanism
- **Combat System**: Combat actions use command framework
- **Quest System**: Quest interactions use commands
- **Admin Tools**: Administrative functions leverage command structure
