# Networking

## Overview
The Networking system manages all player connections to the MUD, implementing socket management, telnet protocol handling, connection state machines, and terminal control sequences. This component serves as the foundational communication layer between players and the game server, handling everything from initial connections through the entire player session lifecycle. It supports both traditional telnet clients and modern MUD clients with enhanced protocol features, ensuring reliable bi-directional communication with proper buffering, timeout handling, and terminal negotiations.

## Responsibilities
- Managing TCP/IP socket connections for player sessions
- Implementing the telnet protocol with option negotiation
- Providing VT100 terminal control for text formatting and display
- Processing input buffers with command history and editing
- Formatting and queuing output with color and pagination
- Handling connection states from login through gameplay
- Detecting and managing idle connections and timeouts
- Supporting graceful disconnection and reconnection
- Managing bandwidth with throttling and compression techniques
- Implementing terminal type detection and capability negotiation
- Providing protocol extensions for modern MUD clients
- Logging connection statistics and error conditions

## Core Components

### Connection Management
- **Socket Handling**: Network communication foundation
  - Socket creation and binding
  - Connection acceptance and tracking
  - Non-blocking I/O operations
  - Signal handling for network events
  - Host resolution and validation
  - Connection statistics tracking
  - Multi-platform socket interfaces
  - Polling and event notification

- **Descriptor Management**: Connection representation
  - Player session tracking
  - Input and output buffer management
  - Connected state tracking
  - Client capability records
  - Host information storage
  - Security and authentication state
  - Connected time tracking
  - Command history management

### Protocol Implementation
- **Telnet Protocol**: Core communication protocol
  - Command parsing and interpretation
  - Option negotiation (WILL/WONT/DO/DONT)
  - Subnegotiation for extended features
  - Special character handling
  - Escape sequence processing
  - Protocol state tracking
  - Client capability detection
  - IAC doubling for binary data

- **Terminal Control**: Display formatting
  - ANSI color code processing
  - VT100 control sequence generation
  - Cursor positioning and screen control
  - Text attributes (bold, underline, etc.)
  - Client capability-aware formatting
  - Fallback rendering for limited clients
  - Color configuration and customization
  - Dynamic width adjustment

### Connection State Machine
- **State System**: Connection lifecycle management
  - State definition and transition rules
  - Abstract state interface
  - Login sequence handling
  - Character selection and creation
  - Game entry and exit processing
  - Error recovery states
  - Connection interruption handling
  - Reconnection support

- **Login Process**: Authentication and entry
  - Username and password processing
  - New character creation workflow
  - Account validation and security
  - MOTD and news presentation
  - Character selection interfaces
  - Welcome sequence coordination
  - Login attempt limiting
  - Ban checking and enforcement

### Server Continuity
- **Copyover**: Hot-restart capability preserving player connections
  - Serializes active connection state (file descriptors, character references)
  - Passes file descriptors to newly-exec'd server process
  - Restores connections and characters in the new process
  - Players experience a brief pause rather than disconnection
  - Triggered by admin `copyover` command

## Implementation Details

### Socket Implementation
- **Connection Processing**: Socket lifecycle
  - Socket initialization and setup
  - Non-blocking configuration
  - Accept loop management
  - Connection rate limiting
  - Error condition detection
  - Graceful shutdown handling
  - OS-specific optimizations
  - Buffer size tuning

- **I/O Handling**: Data transfer
  - Read buffer management
  - Write queue processing
  - Partial read/write handling
  - Error detection and recovery
  - Bandwidth management
  - Idle detection
  - Prompt handling
  - Line editing support

### Protocol Processing
- **Telnet Negotiation**: Option management
  - Request and response tracking
  - Feature discovery
  - Option state machine
  - Capability announcement
  - Default settings application
  - Renegotiation handling
  - Timeout management
  - Extended option support

- **Terminal Features**: Display capabilities
  - Terminal type detection
  - Window size negotiation
  - Color support detection
  - Client feature tracking
  - Rendering adaptation
  - Special character handling
  - Unicode support
  - Layout optimization

### State Machine Implementation
- **State Framework**: Transition management
  - Polymorphic state interface
  - State transition mechanics
  - Reentrant state processing
  - Input processing delegation
  - Context preservation
  - Timeout handling
  - Error state recovery
  - State factory implementation

- **Player Session**: Active connection management
  - Character binding
  - Input processing pipeline
  - Output formatting and queuing
  - Session variables tracking
  - Command throttling
  - AFK detection
  - Disconnection handling
  - Reconnection matching

## Key Files
- **comm.hh/comm.cc**: Core network communication
  - 940 lines
  - Socket initialization and management
  - Descriptor list handling
  - Input/output processing
  - Main game loop integration
  - Connection acceptance
  - Write queue processing
  - Signal handling for network events

- **telnet.hh**: Telnet protocol definitions
  - 220 lines
  - Protocol command constants
  - Option code definitions
  - Subnegotiation formats
  - Helper function declarations
  - Protocol state tracking
  - Command parsing utilities

- **vt100.hh**: Terminal control sequences
  - 180 lines
  - ANSI color code definitions
  - Screen control sequences
  - Cursor positioning helpers
  - Text attribute constants
  - Terminal control utilities
  - Color mapping functions

- **conn/State.hh/State.cc**: Connection state machine
  - 310 lines
  - Abstract state interface
  - State transition framework
  - State instance registry
  - Context passing mechanism
  - Default implementations

- **conn/ReadNewMOTDState.cc**: Character welcome sequence
  - 240 lines
  - New player processing
  - Message of the day display
  - Character setup completion
  - Welcome sequence coordination
  - Game entry preparation

- **conn/RollStatsState.cc**: Character creation
  - 290 lines
  - Attribute generation logic
  - User input validation
  - Character customization
  - Stat adjustment implementation
  - Race and class modifiers

## System Behaviors
1. **Connection Lifecycle**:
   - Socket creation and binding at startup
   - Connection acceptance in main loop
   - Descriptor creation for new connections
   - State machine initialization
   - Authentication and character selection
   - Gameplay state transition
   - Idle detection and timeout management
   - Graceful or error disconnection
   - Socket and resource cleanup

2. **Input Processing Flow**:
   - Socket read operations
   - Raw input buffering
   - Telnet command filtering
   - Line editing and history management
   - Command completion processing
   - State-specific input handling
   - Command interpretation dispatch
   - Input throttling for security

3. **Output Processing Flow**:
   - Message formatting and colorization
   - Output buffer queuing
   - Pagination for large outputs
   - Prompt generation and positioning
   - Buffer flushing to socket
   - Partial write handling
   - Flow control for large volumes
   - Error detection and recovery

4. **Protocol Negotiation**:
   - Initial option announcements
   - Client capability detection
   - Feature negotiation sequence
   - Terminal type and window size detection
   - Color support verification
   - Extended protocol support detection
   - Dynamic feature adaptation
   - Renegotiation on capability changes

## Dependencies and Relationships
- **Command Interpreter**: For processing player input
- **Game Engine**: For integration with main loop
- **Utilities**: For string processing and logging
- **Character System**: For binding connections to players
- **Memory & GC**: For resource management
