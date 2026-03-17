---
id: admin_tools
name: Admin Tools
kind: system
layer: operations
parent: null
depends_on: [character_data, object_system, world_system, persistence, command_interpreter]
depended_on_by: [quests]
---

## Overview
<!-- section: overview | grounding: mixed -->
The Admin Controls subsystem provides comprehensive command sets for server management, player moderation, permission handling, and debugging. It includes security controls, logging toggles, and player account tools, supporting daily operations and system integrity. These tools form the backbone of game administration, enabling privileged users to maintain, troubleshoot, and manage the game environment with minimal disruption to the player experience.

## Responsibilities
<!-- section: responsibilities | grounding: mixed -->

- Managing server configuration, operation, and maintenance
- Moderating player accounts, behavior, and conflict resolution
- Handling security permissions, access control, and privilege management
- Providing extensive debugging and system inspection tools
- Tracking and logging administrative actions for accountability
- Supporting server stability and performance monitoring
- Enabling emergency interventions and system recovery
- Facilitating quest and event management by administrators

## Admin Command Architecture
<!-- section: key_components | grounding: mixed -->

### Command Categories
- **Admin Commands**: Highest level system operations
  - Server control and configuration
  - System maintenance functions
  - Critical resource management
  - Global game state manipulation

- **Coder Commands**: Technical debugging and development tools
  - Runtime code inspection
  - Memory and performance analysis
  - Test function execution
  - Technical debugging utilities
  - Core systems monitoring

- **General Commands**: Common administrative utilities
  - Character and object manipulation
  - Environment modification
  - Information gathering tools
  - Day-to-day administrative functions
  - Status reporting and monitoring

- **Quest Commands**: Mission and event management
  - Quest creation and editing
  - Event triggering and monitoring
  - Reward distribution controls
  - Quest status modification
  - Special event management

- **Security Commands**: User management and permissions
  - Account creation and modification
  - Password and authentication management
  - Access level control
  - Ban and restriction implementation
  - Security audit and verification

## WIZnet & Monitoring
<!-- section: key_components | grounding: mixed -->

### Administrative Systems
- **WIZnet System**: Admin communication and notification
  - Specialized admin-only communication channels
  - Tiered notification categories
  - Permission-based message filtering
  - Administrative alerts and warnings

## Disabled Commands
<!-- section: key_components | grounding: mixed -->

- **Disabled Commands**: Runtime command management
  - Command activation and deactivation
  - Conditional command disabling
  - Temporary and permanent restrictions
  - Command access auditing

## Punishment & Moderation
<!-- section: key_components | grounding: mixed -->

- **Punishment System**: Player moderation tools
  - Warning and notification mechanisms
  - Temporary and permanent restrictions
  - Behavior tracking and history
  - Graduated response system
  - Appeal and review processes

- **Permission Management**: Access control implementation
  - Level-based permission hierarchy
  - Feature-specific access flags
  - Special privilege management
  - Temporary privilege granting
  - Permission verification systems

## Implementation Details
<!-- section: implementation | grounding: mixed -->

### Command Implementation
- **Permission Levels**: Tiered access to administrative functions
  - Level-based command availability
  - Function-specific permission flags
  - Command category restrictions
  - Special exception handling

- **WIZnet Flag System**: Specialized notification system
  - WIZ_ON - Basic wizard command access
  - WIZ_SECURE - High-level security operations
  - WIZ_LOAD - Object/mobile creation monitoring
  - WIZ_QUEST - Quest operation monitoring
  - Various specialized flags for operation categories

- **Command Security**: Protection for privileged operations
  - Confirmation for destructive actions
  - Logging of sensitive operations
  - IP-based security measures
  - Session validation for critical commands
  - Access attempt monitoring

- **Game Management**: Server control features
  - Shutdown management with announcements
  - Database backup triggering
  - Configuration parameter adjustment
  - Memory and resource management
  - Player connection management

### Administrative Tools Implementation
- **Player Administration**: Account management
  - Creation of new accounts with validation
  - Modification of account parameters
  - Access level adjustment
  - Account suspension and deletion
  - Password reset and security features

- **Command Toggling**: Feature control system
  - Real-time enabling and disabling
  - Group-based command management
  - Emergency lockdown capabilities
  - Feature testing with limited exposure
  - Gradual feature rollout support

- **Logging Controls**: Monitoring system
  - Verbosity level adjustment
  - Target-specific logging
  - Log rotation and management
  - Priority-based filtering
  - Real-time log monitoring

- **Security Auditing**: Access tracking system
  - Command usage recording
  - Login and access attempts
  - Privilege escalation tracking
  - Administrative action review
  - Anomaly detection and alerting

## Key Files
<!-- section: key_components | grounding: grounded -->

### Implementation Files
- `wiz_admin.cc` (17 LOC) - Administrative commands
  - Server control operations
  - System configuration commands
  - Core service management
  - Global parameter setting

- `wiz_coder.cc` (676 LOC) - Debugging and coding tools
  - Memory inspection commands
  - Performance analysis tools
  - Technical debugging utilities
  - System internals examination
  - Runtime testing capabilities

- `wiz_gen.cc` (4220 LOC) - General immortal commands
  - Character manipulation
  - Object creation and modification
  - Environment control
  - Information gathering
  - Game state adjustment
  - Common administrative utilities

- `wiz_quest.cc` (1001 LOC) - Quest management
  - Quest creation and editing
  - Event management tools
  - Reward system controls
  - Quest tracking and monitoring
  - Special event implementation

- `wiz_secure.cc` (1165 LOC) - Security and account commands
  - Account management
  - Password and authentication tools
  - Access control implementation
  - Ban and restriction commands
  - Security verification utilities

- `Disabled.cc` - Command disabling functionality
  - Command activation/deactivation
  - Permission checking
  - Command status tracking
  - Access control implementation

- `Logging.cc` - Logging system implementation
  - Log message routing
  - Verbosity control
  - Target management
  - Format standardization
  - Log storage and rotation

### Resource Directories
- `misc/` - Administrative resources
  - `bugs.txt` - Bug reports from players
  - `typos.txt` - Typo reports for correction
  - `punishment.txt` - Records of administrative actions
  - Configuration files for various systems
  - Administrative tracking documents

## System Behaviors
<!-- section: behaviors | grounding: mixed -->

### Command Access Behaviors
- **Permission Hierarchy**: Tiered command access
  - Layer-based permission system
  - Command-specific access control
  - Context-sensitive availability
  - Dynamic permission adjustment
  - Security monitoring for sensitive commands

- **Command Groups**: Functional organization
  - Category-based command sets
  - Progressive access to functionality
  - Task-oriented command grouping
  - Consistent naming conventions
  - Command aliasing for convenience

- **Security Validation**: Access verification
  - Multi-factor checks for critical commands
  - IP and session validation
  - Command rate limiting
  - Pattern detection for abuse
  - Automatic lockout for suspicious activity

### Administration Behaviors
- **Player Management**: Account administration
  - Creation and onboarding processes
  - Privilege level adjustment
  - Punishment and restriction application
  - Account recovery and assistance
  - Profile and preference management

- **System Control**: Server management
  - Startup and shutdown procedures
  - Performance monitoring and tuning
  - Resource allocation and limitation
  - Backup and recovery operations
  - Configuration and parameter adjustment

- **Crisis Management**: Emergency tools
  - Lockdown and restriction capabilities
  - Mass communication to players
  - Rapid response to exploits
  - Service interruption handling
  - Data protection and recovery

### Tool Behaviors
- **Command Control**: Feature management
  - Targeted enabling and disabling
  - Context-sensitive restrictions
  - Temporary and permanent toggling
  - Command variants and alternatives
  - Permission-based visibility

- **Logging Control**: Monitoring system
  - Detail level adjustment
  - Category-specific tracking
  - Real-time observation
  - Historical analysis
  - Pattern recognition for issues

- **Moderation**: Problem management
  - Behavior tracking and documentation
  - Progressive intervention system
  - Communication with affected players
  - Resolution and follow-up procedures
  - Appeal and review processes

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): For player and NPC management
- **Object System** (`object_system`): For item manipulation
- **World System** (`world_system`): For environment manipulation
- **Persistence** (`persistence`): For database and file access
- **Command Interpreter** (`command_interpreter`): For command routing and permissions

### Depended On By
- **Quests** (`quests`): Administrative quest management tools
  - Community moderators
  - Technical support teams

- **Content Creators**: For world development
  - Area builders
  - Quest designers
  - Event coordinators
  - Story writers
  - Game balance specialists

- **Players**: For indirect benefits
  - Technical issue resolution
  - Community standards enforcement
  - Game balance maintenance
  - Content updates and fixes
  - Special event experiences

- **Quest Systems**: For event management
  - Event triggering mechanisms
  - Reward distribution
  - Special condition creation
  - Unique experience implementation
  - Limited-time feature management
