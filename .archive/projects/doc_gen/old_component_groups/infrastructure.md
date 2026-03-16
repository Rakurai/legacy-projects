# Infrastructure Systems Component Documentation

## Overview

The Infrastructure Systems provide the technical foundation upon which the game operates, including the core game engine, network connectivity, memory management, persistence, and utility functions. These systems are not directly visible to players but are essential for the game's operation, performance, and reliability.

### System Responsibilities
- Managing the game loop and update cycle
- Handling network connections and descriptor management
- Providing memory management and garbage collection
- Supporting persistence and data storage
- Offering debugging and logging facilities
- Implementing utility functions for common operations

## Core Classes and Interfaces

### Game Engine
- **Game**: Singleton manager for the global game state
  - World instance and global state access
  - Shutdown control and coordination
  - Central access point for game components
  - Manages game initialization sequence
  - Controls shutdown procedures
  - Provides access to global subsystems
  - Maintains critical game state variables

- **GameTime**: In-game time tracking and calendar system
  - Hour, day, month, year management
  - Time-based event triggering

### Connection Management
- **Descriptor**: Network connection wrapper
  - Input/output buffer management
  - Connection state tracking
  - Character association for active players
  - Buffer overflow protection
  - Telnet option negotiation
  - Idle timeout handling

- **conn::State**: State machine for connection handling
  - Various state implementations for login sequence
  - PlayingState for active gameplay

### Memory Management
- **Garbage**: Base class for garbage-collected objects
  - Provides foundation for reference counting
  - Implements safe deletion mechanics
  - Supports object lifecycle management
  
- **GarbageCollectingList**: Container for managing lists of objects
  - Automatic cleanup of deleted objects
  - Safe iteration during processing
  - Deferred deletion during traversal
  - Reference counting integration
  - Iterator safety during modifications
  - Complex object relationship management
  
- **Pooled**: Memory pooling for frequent allocations
  - Pre-allocated memory blocks 
  - Fast allocation for common object types
  - Reduced memory fragmentation
  - Efficient recycling of released memory
  - Type-safe wrapper for allocation patterns
  - Performance optimization for high-frequency allocations
  - Support for object reuse in critical paths

### Core Definitions
- **Merc Core**: Foundational game structures and constants
  - Core data structure definitions
  - Historical system compatibility
  - Global reference tables
  - Legacy macros and utilities

### Persistence
- **SQLite Interface**: Database connectivity and operations
  - Connection pooling and management
  - Transaction handling
  - Prepared statement support
  - Result set processing
  - Error handling and recovery

### Network Systems
- **Telnet Protocol**: Implementation of telnet specifications
  - Option negotiation (WILL/WONT/DO/DONT)
  - Suboption processing
  - Command codes and control sequences
  - Protocol state tracking

- **VT100 Terminal**: Terminal control sequences
  - Cursor movement and positioning
  - Screen clearing and formatting
  - Color and attribute control
  - Special character display

### Utilities
- **Logging**: Error reporting and debug output
  - Multiple severity levels
  - Configurable output targets
  - Context-enriched logging
  - Error tracing and reporting
- **String**: String manipulation and parsing utilities
- **Flags**: Bitflag management utilities
  - Efficient bit manipulation
  - Type-safe flag operations
  - Named flag constants
  - Composite flag sets
  - Flag serialization and parsing
  - Multi-purpose flag system for various entities
  - Flag testing and modification utilities

- **Format**: Type-safe formatting helpers
  - String composition utilities
  - Type-aware formatting
  - Safe parameter substitution
  - Format pattern support
  - Localization compatibility
  - Performance-optimized implementations
  - Consistent text representation across systems

- **Tail**: File monitoring utility
  - Real-time file display functionality
  - Last-n-lines buffer management
  - Dynamic file tracking for logs
  - Administrative monitoring tool

- **Entity Lookup**: Central system for finding game entities
  - Character, object, and room lookup
  - Name-based and ID-based search capabilities
  - Scoped search with visibility rules
  - Fuzzy matching for partial names

- **Forward Declarations**: Comprehensive header organization
  - Class and struct forward declarations
  - Global variable references
  - Function prototypes
  - Type definitions and aliases

- **Utility Macros**: Standardized code shortcuts
  - Debug and logging macros
  - Memory management helpers
  - Common function patterns
  - Safety wrappers
  - Platform-specific adaptations

- **Random Number Generation**: Pseudorandom number utilities
  - Dice-style random rolls (NdS format)
  - Range-based random selection
  - Percentage chance calculations
  - Distribution utilities

- **Image Processing**: ASCII art and visualization tools
  - Character-based drawing primitives
  - Box and line drawing
  - Screen buffer management
  - Multi-color text support

## Implementation Details

### Game Engine Implementation
- **Game Loop**: Central update cycle with pulse-based timing
- **Subsystem Updates**: Regular updates to various game systems
  - Character and object updates
  - World time and weather
  - Combat and violence
  - Quest and event timers
  - System maintenance
- **Time Management**: Real-time to game-time conversion
- **Initialization**: Ordered startup of game subsystems
- **Boot Process**: Core system initialization and validation
- **Shutdown**: Clean termination of all systems
- **Auto-reboot**: Managed system restarts

### Connection Implementation
- **Descriptor Management**: Socket handling and connection tracking
- **Input Processing**: Reading and buffering player input
- **Output Management**: Message formatting and transmission
- **State Pattern**: Each connection state handles specific input
- **Exception Handling**: Managing network errors gracefully

### Memory Management Implementation
- **Reference Counting**: Tracking object references
- **Garbage Collection**: Cleaning up unreferenced objects
- **Safe Iteration**: Handling list modifications during traversal
- **Memory Pooling**: Optimizing frequent allocations

### Persistence Implementation
- **Player Saving**: Character data persistence
- **World State**: Saving and loading world state
- **Database Operations**: CRUD operations for game data using SQLite
- **Configuration**: JSON-based configuration management
- **Database Layer**: SQLite interface for structured data storage and queries
- **File I/O**: Utilities for reading and writing various file formats for game data
- **JSON Processing**: Configuration management through JSON file format
- **Game Configuration**: Runtime settings and server parameter management (config.cc, 807 LOC)
- **Config Loading**: Dynamic configuration file parsing and validation (load_config.cc, 37 LOC)

### Utilities Implementation
- **Logging Levels**: Different severity levels for messages
  - Bug reporting system
  - Error logging with formatting
  - Debug output control
  - Administrative notifications
- **String Utilities**: Common string operations and parsing
  - Case-insensitive comparisons
  - Prefix/infix/suffix checking
  - Numeric validation
  - String transformations
- **Argument Parsing**: Sophisticated command argument extraction and processing
  - Number argument parsing (format: "5.sword")
  - Quote-aware tokenization for complex arguments
  - Multiple argument parsing (format: "5*sword")
  - Entity reference extraction (format: "p.5.name")
- **Type Management**: Runtime type information and manipulation
  - Type name resolution and storage
  - Type comparison and conversion utilities
  - Object type identification
  - Type registration system
  - Pretty-printing of type names
- **Entity Lookup**: Central system for finding game entities
  - Character, object, and room lookup
  - Name-based and ID-based search capabilities
  - Scoped search with visibility rules
  - Fuzzy matching for partial names
- **Image Processing**: Utilities for ASCII art and visualization
  - Image generation and manipulation
  - Map and diagram creation
  - Visual representation helpers

## Key Files and Components

### Header Files
- `Game.hh` (32 LOC) - Central game manager
- `Garbage.hh` (11 LOC) - Base class for garbage collection
- `GarbageCollectingList.hh` (77 LOC) - Memory management container
- `Flags.hh` (108 LOC) - Flag management utilities
- `Format.hh` (83 LOC) - Type-safe formatting
- `Pooled.hh` (84 LOC) - Memory pooling
- `Tail.hh` (29 LOC) - File tail monitoring utility
- `declare.hh` (341 LOC) - Forward declarations and common includes
- `file.hh` (18 LOC) - File operations interface
- `lookup.hh` (25 LOC) - Entity lookup utilities
- `macros.hh` (129 LOC) - Utility macro definitions
- `memory.hh` (31 LOC) - Memory management utilities
- `merc.hh` (241 LOC) - Core game definitions
- `random.hh` (12 LOC) - Random number generation
- `sql.hh` (39 LOC) - Database interface
- `telnet.hh` (83 LOC) - Telnet protocol implementation
- `typename.hh` (34 LOC) - Type information system
- `util/Image.hh` (32 LOC) - ASCII art utilities
- `vt100.hh` (16 LOC) - Terminal control codes

### Implementation Files
- `Game.cc` (139 LOC) - Game state management
- `update.cc` (1570 LOC) - Central game update system
- `Logging.cc` - Logging system implementation
- `sqlite.cc` (155 LOC) - Database interface
- `file.cc` (270 LOC) - File I/O utilities
- `GameTime.cc` (134 LOC) - Game time tracking
- `constants.cc` - Core game constants and tables
- `argument.cc` (193 LOC) - Command argument parsing utilities
- `lookup.cc` (226 LOC) - Entity lookup and reference resolution
- `typename.cc` (328 LOC) - Type name management utilities
- `util/Image.cc` (181 LOC) - Image processing and visualization
- `load_config.cc` (37 LOC) - Configuration loading
- `memory.cc` (17 LOC) - Memory management implementation

## System Behaviors

### Core Engine Behaviors
- **Pulse System**: Regular update ticks for different subsystems
- **Time Tracking**: Game time advances at configured rate
- **Event Scheduling**: Actions scheduled for future pulses
- **System Integration**: Coordination between subsystems

### Connection Behaviors
- **Connection Lifecycle**: Connect, authenticate, play, disconnect
- **Input Handling**: Command buffering and processing
- **Output Formatting**: Message coloring and pagination
- **Idle Detection**: Tracking inactive connections

### Memory Management Behaviors
- **Object Lifecycle**: Creation, use, collection
- **Safe Cleanup**: Proper ordering of object destruction
- **Optimization**: Memory pooling for common objects
- **Leak Prevention**: Tracking of allocated resources

### Persistence Behaviors
- **Regular Saves**: Periodic saving of player data
- **Safe Loading**: Recovery from corrupted data
- **Efficient Storage**: Optimized data formats
- **Configuration**: Dynamic settings via configuration files

### Utility Behaviors
- **Logging Levels**: Different verbosity for various situations
- **Flag Operations**: Efficient bit manipulation
- **String Processing**: Common text handling needs

## Dependencies and Relationships

### Dependencies On
- **Standard Libraries**: C/C++ standard library functions
- **SQLite**: For database operations
- **Network Libraries**: For socket connections

### Depended On By
- **All Game Systems**: Every system uses the infrastructure
- **Administration Tools**: For monitoring and management
- **Player Experience**: Affects performance and stability
- **Information Systems**: For debugging and monitoring tools

## Open Questions and Future Improvements
- The update cycle could be optimized for more consistent timing
- Database operations could be expanded for more game state storage
- Memory management could be modernized with newer C++ techniques
- Logging could be enhanced with more structured formats
- Configuration system could be extended for more dynamic settings

---
