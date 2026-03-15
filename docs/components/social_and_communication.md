# Social Actions and Channels

## Overview
The Social Actions and Channels subsystem manages social interactions between players, including emotes, chat channels, ignore lists, and customizable social commands. It supports color formatting, targeted messaging, and permission-controlled communications, forming the backbone of in-game communication and expression. This system is critical for player engagement, community building, and roleplaying by providing rich tools for player-to-player interaction beyond basic gameplay mechanics.

## Responsibilities
- Managing global and group communication channels
- Supporting social/emote commands with multiple targets
- Handling direct and broadcast messaging
- Providing ignore/filtering systems for communication
- Enabling online editing of social actions
- Supporting roleplaying through expressive communication
- Facilitating community formation and management
- Enforcing communication standards and policies

## Core Components

### Channel System
- `Channels`: Global and group chat systems
  - Themed broadcast channels (gossip, auction, etc.)
  - Organization-specific channels (clan, group)
  - Administrative channels for staff
  - Chat history tracking
  - Toggle functionality for enabling/disabling
  - Permission-based channel access
  - User preference management

### Social Action System
- `Social`: Class representing pre-defined emotive commands
  - Multiple target support (to character, to room)
  - Customized messages for different perspectives
  - Online editing capabilities for administrators
  - Context-aware message formatting
  - Rich emotion expression
  - Support for no-target, character-target, and object-target
  - Visibility rules based on perception

### Communication Filtering
- `Ignore System`: Multi-level player communication filtering
  - Targeted blocking of specific players
  - Different ignore levels for various communication types (tells, channels, etc.)
  - Durable ignore lists saved with character data
  - Commands for adding, removing, and listing ignored players
  - Context-aware filtering based on ignore settings

### Message Formatting
- `act.hh`/`act.cc`: Core message formatting system
  - Token substitution for different perspectives
  - Multiple audience handling (actor, target, observers)
  - Visibility filtering based on context
  - Format standardization across action types
  - Color code support for rich text
  - Dynamic content insertion

### Music System
- **Music/Jukebox**: In-game song playback
  - Music files containing song lyrics/text
  - Jukebox objects in rooms that can be interacted with
  - Play command to start song playback
  - Tick-based lyric broadcast to the room (songs play line by line over time)
  - Song listing and selection

### Marriage System
- **Marriage**: Character relationship mechanics
  - Proposal and acceptance protocol
  - Wedding ceremony process
  - Partner status tracking (visible in score/who)
  - Divorce mechanics
  - Special partner commands and social status effects

### Pose System
- **Pose**: Custom character descriptors
  - Class-specific pose options
  - Custom title/description appearing in room descriptions and who lists
  - Per-character configuration

## Implementation Details

### Channel Implementation
- **Channel Management**: Functions for joining/leaving channels
- **Message Distribution**: Routing messages to appropriate recipients
- **Access Control**: Permission checking for channel usage
- **Channel Toggles**: Individual channel enabling/disabling
- **Chat History**: Some channels maintain recent history

### Social Action Implementation
- **Social Definition**: Pre-defined emotes with formatted messages
- **Message Construction**: Dynamic assembly based on targets
- **Perspective Handling**: Different text for actor, target, and observers
- **Online Editing**: Tools for administrators to modify socials
- **Social Database**: Persistent storage of social definitions

### Communication Filter Implementation
- **Ignore List**: Player-defined list of ignored characters
- **Filter Rules**: Logic for determining when to block messages
- **Persistence**: Saving ignore preferences with character data
- **Interface**: Commands for managing ignore settings

### Direct Communication
- **Tells**: Private messages between players
- **Reply System**: Quick responses to last received tell
- **Group Chat**: Communication within formed groups
- **Clan Chat**: Organization-specific messaging
- **Whispers**: Location-based quiet messaging

## Key Files

### Header Files
- `/src/include/channels.hh` (13 LOC) - Communication channel system
- `/src/include/Social.hh` (31 LOC) - Social action system
- `/src/include/act.hh` (39 LOC) - Message formatting system interface

### Implementation Files
- `/src/channels.cc` - Channel system implementation
- `/src/social.cc` (453 LOC) - Social action system implementation
- `/src/act_comm.cc` - Communication command implementation
- `/src/act.cc` (484 LOC) - Core action message formatting
- `/src/ignore.cc` (182 LOC) - Player-to-player communication filtering

## System Behaviors

### Core Behaviors
- **Channel Communication**: Broadcasting messages to subscribers of a channel
- **Direct Messaging**: Person-to-person private communication
- **Emotive Expression**: Rich social actions for roleplaying
- **Message Filtering**: Blocking unwanted communication
- **Perspective-Aware Output**: Messages customized based on observer's relationship to action

### Special Features
- **Color Formatting**: Support for colored text in messages
- **Targeted Actions**: Socials can target specific characters or objects
- **Multi-Audience Messaging**: Different observers see contextually appropriate messages
- **Editor Interface**: Administrative tools for modifying socials
- **Channel History**: Some channels maintain recent message history
- **Message Visibility**: Rules for who can see which messages based on state and position

## Dependencies and Relationships

### Dependencies On
- **Character System**: For actor state, visibility rules, and relationships
- **Command Interpreter**: For routing communication commands
- **World System**: For location-based messaging and visibility
- **Information System**: For displaying communication output

### Depended On By
- **Player Experience**: Critical for social engagement and community
- **Clan System**: Uses channels for organization communication
- **Group System**: Relies on special communication channels
- **Admin Controls**: Uses special channels for staff communication
- **Event System**: Events may trigger special messages or channels
