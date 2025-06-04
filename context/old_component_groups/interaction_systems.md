# Interaction Systems Component Documentation

## Overview

The Interaction Systems form the core interface between players and the game world, handling command processing, communication channels, and player actions. These interconnected systems interpret text input, route commands to appropriate handlers, facilitate player communication, and translate player intent into game actions.

### System Responsibilities
- Processing and interpreting player commands
- Managing communication between players
- Handling movement and navigation
- Supporting object manipulation
- Enabling social interactions

## Core Classes and Interfaces

### Command System
- **cmd_type**: Structure that defines a command with its handler function
- **DO_FUN**: Function pointer type for command handlers
- **Disabled**: System to disable specific commands
- **interp**: Core command interpretation functionality

### Connection System
- **conn::State**: State machine for connection handling
  - Various state implementations for login sequence
  - PlayingState for active gameplay
  - Other states for character creation and configuration

### Communication System
- **Channels**: Global and group communication channels
- **Socials**: Emotive actions between players
  - Pre-defined emotive commands
  - Multiple target support (to character, to room)
  - Customized messages for different perspectives
  - Online editing capabilities for immortals
  - Context-aware message formatting

### Interaction Interfaces
- **Actable**: Interface for entities that can perform actions
  - Provides a common base for action-capable entities
  - Abstracts the action execution mechanism
  - Enables consistent action handling across different entity types

### Trading Systems
- **Auction**: Player-to-player item sale mechanism
  - Manages bidding and timing for item auctions
  - Handles transaction processing for sold items
  - Provides notifications for auction participants
  - Supports auction cancellation with proper rules

### Action Implementation
- **act_***: Groups of command implementations:
  - Movement commands
  - Object manipulation
  - Combat actions
- **Message Formatting**: Core system for context-aware messages
  - Token substitution for different perspectives
  - Multiple audience handling (actor, target, observers)
  - Visibility filtering based on context
  - Format standardization across action types

## Implementation Details

### Command Implementation
- **Command Table**: Registry of all available commands
- **Command Lookup**: Efficient partial command name matching
- **Privilege Checking**: Validation of character permissions
- **Command Disabling**: Runtime disabling of problematic commands
- **Argument Parsing**: Extraction of arguments from command strings

### Connection Implementation
- **State Pattern**: Each connection state handles specific input
- **State Transitions**: Moving between states based on input
- **Input Validation**: Ensuring proper input at each state
- **Character Association**: Binding connections to characters

### Communication Implementation
- **Channel Management**: Adding/removing characters from channels
- **Message Distribution**: Routing messages to appropriate recipients
- **Social Actions**: Extensive social action system with predefined emotive commands, multiple target support, and online social editing tools (social.cc, 453 LOC)
- **Chat Channels**: Multiple themed broadcast channels (gossip, auction, etc.)
- **Direct Communication**: Person-to-person messaging with tells and whispers
- **Text Formatting**: Rich text output with color codes and dynamic content
- **Access Controls**: Permission management for different communication types
- **Ignore System**: Multi-level player communication filtering mechanism
  - Targeted blocking of specific players
  - Different ignore levels for various communication types (tells, channels, etc.)
  - Durable ignore lists saved with character data
  - Commands for adding, removing, and listing ignored players
  - Context-aware filtering based on ignore settings

### Player Actions Implementation
- **Action Formatting**: Sophisticated message system that formats action descriptions differently based on the observer's perspective
  - Token substitution for pronouns, names, and descriptors
  - Visibility filtering based on perception abilities  
  - Snooping support for immortal monitoring
  - Varied perspectives for actor, target, and observers
- **Movement**: Direction-based and special movement commands with various restrictions and costs
  - Cardinal directions with terrain-based movement costs
  - Special movement types (enter, leave, climb)
  - Movement barriers (doors, locks, room flags)
  - Tracking and following mechanics
- **Object Interaction**: Commands for inventory management, equipment handling, and item usage
  - Container operations with capacity limits
  - Equipment management with location restrictions
  - Object usage with specialized behaviors by type
  - Shop interactions for commerce
- **Auction System**: Player-to-player item sale mechanism with bidding and timing rules
  - Multi-stage countdown with notifications
  - Bidding mechanics with validation
  - Transaction processing for funds and items
  - Cancellation handling with proper rules

## Key Files and Components

### Header Files
- `interp.hh` - Command system interface
- `Disabled.hh` - Command disabling functionality
- `conn/State.hh` (79 LOC) - Connection state machine
- `Actable.hh` (7 LOC) - Interface for action-capable entities
- `Auction.hh` (31 LOC) - Auction system interface
- `channels.hh` (13 LOC) - Communication channel system
- `comm.hh` (16 LOC) - Network communication core
- `Social.hh` (31 LOC) - Social action system
- `act.hh` (39 LOC) - Message formatting system interface

### Implementation Files
- `interp.cc` - Command interpretation implementation
- `channels.cc` - Channel system implementation
- `act_comm.cc` - Communication command implementation
- `act_move.cc` (3306 LOC) - Movement command implementation
- `act_obj.cc` (5383 LOC) - Object interaction command implementation
- `social.cc` (453 LOC) - Social action system implementation
- `act.cc` (484 LOC) - Core action message formatting
- `ignore.cc` (182 LOC) - Player-to-player communication filtering
- `conn/*.cc` - Connection state implementations

## System Behaviors

### Core Behaviors
- **Command Processing**: Parsing input and routing to handlers
- **Command Hierarchy**: Commands organized by permission level
- **State-Based Input**: Input processing depends on connection state
- **Dynamic Command Availability**: Commands available based on character state
- **Channel Management**: Join/leave/talk operations on communication channels

### Special Features
- **Command Abbreviation**: Commands can be abbreviated to shortest unique prefix
- **Targeted Actions**: Actions can target characters or objects with specificity
- **Command Throttling**: Prevention of command spam
- **Multi-Language Support**: Some support for localized messages
- **Social Expansion**: Customizable social actions with variable targets

## Dependencies and Relationships

### Dependencies On
- **Character System**: For actor state and permissions
- **World System**: For movement between rooms
- **Object System**: For item manipulation
- **Affect System**: For ability to use commands under effects
- **Information Systems**: For gathering and displaying information

### Depended On By
- **All Gameplay Systems**: Most game interactions flow through commands
- **Scripting**: NPC behaviors use command mechanism
- **Combat System**: Combat actions use command framework
- **Quest System**: Quest interactions use commands

## Open Questions and Future Improvements
- The command table structure could be modernized for easier maintenance
- Additional commands could be added for new gameplay features
- The state machine could be expanded for more nuanced connection handling
- More sophisticated command suggestion for typos could be implemented
- Command throttling could be refined for better spam prevention

---
