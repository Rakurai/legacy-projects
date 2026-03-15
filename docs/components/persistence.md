# Persistence

## Overview
The Persistence system handles the saving and loading of all game data, ensuring that player progress, world state, and configuration settings persist across server restarts. It implements multiple storage mechanisms including SQLite database access, structured file I/O for character and world data, and JSON-based configuration management. This component is essential for maintaining game continuity, supporting player progression, and enabling administrative data management in the long-running MUD environment.

## Responsibilities
- Storing and retrieving player character data
- Managing object persistence across server sessions
- Saving and loading world state information
- Handling configuration file parsing and application
- Providing transaction safety for critical data operations
- Supporting data format versioning and migrations
- Implementing backup and recovery mechanisms
- Offering both SQL and file-based storage options
- Ensuring data integrity through validation and error handling
- Managing note and message board persistence

## Core Components

### Database Management
- **SQL Interface**: SQLite integration layer
  - Connection pooling and management
  - Transaction handling with commit/rollback
  - Prepared statement support
  - Result set processing
  - Error handling and reporting
  - Query optimization
  - Schema management
  - Migration support

- **Data Models**: Structured storage schemas
  - Character data models
  - Object persistence layouts
  - World state representations
  - Configuration structures
  - Audit and logging schemas
  - Index optimization
  - Relation management

### File-Based Persistence
- **Character Files**: Player data storage
  - Attribute persistence
  - Inventory management
  - Quest and progress tracking
  - Preference and setting storage
  - Equipment tracking
  - Skill and spell mappings
  - Player metadata handling

- **World Files**: Area and room persistence
  - Area file loading and processing
  - Room state persistence
  - Door and exit state tracking
  - Reset instruction storage
  - Instance management
  - World event recording

- **Configuration System**: Game settings management
  - JSON configuration parsing
  - Dynamic setting adjustment
  - Default value handling
  - Configuration validation
  - Override mechanisms
  - Hierarchical configuration support
  - Environment-specific settings

### Persistence Utilities
- **Serialization Tools**: Data conversion utilities
  - Entity serialization helpers
  - Binary data handling
  - Text formatting for storage
  - Version tagging for migrations
  - Cross-format conversion tools
  - Compression support

- **I/O Management**: File handling utilities
  - Buffered I/O operations
  - Error recovery mechanisms
  - Atomic file operations
  - Directory management
  - File locking for concurrent access
  - Permissions and security handling

## Implementation Details

### Database Implementation
- **SQLite Integration**: Core database functionality
  - Connection lifecycle management
  - Statement preparation and execution
  - Result set navigation and extraction
  - Transaction boundary control
  - Error code interpretation
  - Connection pooling for performance
  - Thread safety considerations

- **Schema Design**: Database structure
  - Table relationships and foreign keys
  - Index optimization for common queries
  - Data type selection for efficiency
  - Normalization for data integrity
  - Denormalization for performance
  - Versioning and migration support

### File System Implementation
- **File Format**: Data storage structure
  - Header formats and magic numbers
  - Record delimitation
  - Field separation strategies
  - Type encoding mechanisms
  - Versioning information
  - Checksumming for integrity
  - Backward compatibility support

- **I/O Operations**: File handling
  - Safe file writing patterns
  - Temporary file usage
  - Backup creation before writes
  - Read buffering for performance
  - Error detection and recovery
  - Path resolution and normalization

### Configuration Management
- **JSON Parsing**: Configuration loading
  - Schema validation
  - Type checking
  - Default value application
  - Environment variable substitution
  - Includes and references
  - Comment handling
  - Error reporting

- **Configuration API**: Settings access
  - Typed accessors for settings
  - Caching mechanisms
  - Change notification
  - Dynamic reloading
  - Validation rules
  - Scope management

## Key Files
- **sql.hh/sqlite.cc**: Core SQLite database interface
  - 750 lines
  - Database connection management
  - Statement preparation and execution
  - Result set handling
  - Transaction control
  - Error reporting and handling

- **file.hh/file.cc**: File I/O utilities
  - 520 lines
  - Safe file reading and writing
  - Format-specific I/O operations
  - Path management and resolution
  - Error handling for file operations

- **load_config.cc**: Configuration loading
  - 380 lines
  - JSON parsing and validation
  - Configuration application
  - Default handling
  - Error reporting

- **objstate.cc**: Object persistence
  - 410 lines
  - Item state preservation
  - Container contents tracking
  - Special item handling
  - Version compatibility

- **storage.cc**: Item storage system
  - 280 lines
  - Player storage management
  - Capacity tracking and limits
  - Storage location handling
  - Access control validation

- **Player.cc** (relevant portions): Player data persistence
  - Character serialization and deserialization
  - Player-specific data handling
  - Equipment and inventory persistence
  - Setting and preference storage

- **Note.cc** (relevant portions): Note system persistence
  - 220 lines (persistence-related)
  - Board content storage
  - Message persistence
  - Read status tracking

- **World.cc** (relevant portions): World state persistence
  - 180 lines (persistence-related)
  - Area file loading
  - World state saving
  - Reset state management

## System Behaviors
1. **Player Data Lifecycle**:
   - Character creation stores initial state
   - Periodic automatic saving during gameplay
   - Manual saving with 'save' command
   - Complete saving on logout
   - Loading on login with fallback mechanisms
   - Data migration for format changes

2. **Object Persistence Flow**:
   - Creation from templates
   - State tracking during gameplay
   - Special handling for containers and contents
   - Saving on server shutdown
   - Restoration on server startup
   - Special case handling for quest items

3. **Configuration Management**:
   - Initial loading at server startup
   - Dynamic reconfiguration support
   - Validation against schema
   - Default application for missing values
   - Scope-based overrides
   - Persistence of changes when required

4. **Database Operations**:
   - Connection establishment
   - Transaction boundary management
   - Statement preparation and execution
   - Result processing
   - Error handling and recovery
   - Resource cleanup

## Dependencies and Relationships
- **Character System**: For player data structures
- **Object System**: For item persistence
- **World System**: For area and room data
- **Game Engine**: For lifecycle management
- **Memory & GC**: For efficient resource usage
- **Utilities**: For support functions
