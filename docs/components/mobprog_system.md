# MobProg System

## Overview
The MobProg System defines scripting mechanisms for NPC behavior using triggers such as speech, time, and combat. It supports conditional logic, event responses, and stateful behavior through a compact scripting language, enabling dynamic and complex NPC actions. This system provides the foundation for creating interactive, responsive NPCs that can react to player actions, time-based events, and environmental conditions, bringing the game world to life through automated behaviors.

## Responsibilities
- Providing comprehensive script-based behavior for NPCs (mobiles)
- Supporting diverse trigger conditions (speech, action, time, combat, room entry, etc.)
- Enabling conditional logic and variable state tracking for complex decision trees
- Managing event-based behavior activation with prioritization
- Allowing multiple independent behaviors per NPC for rich interactions
- Executing specialized commands available only to NPCs
- Coordinating NPC response timing with delayed action capabilities
- Maintaining script state across game sessions

## Core Components

### Script Engine
- **MobProg**: Script-based behavior system for NPCs
  - Trigger definitions with varied activation conditions
  - Action sequences for NPC responses
  - Conditional execution blocks (IF-THEN-ELSE structures)
  - Variable system for state tracking
  - Multi-trigger support for complex behaviors

- **MobProgActList**: Queue for pending NPC actions
  - Action scheduling with prioritization
  - Delayed execution capability
  - Safe command processing specific to NPCs
  - Action sequencing and chaining

### Special Functions
- **spec_fun**: Hardcoded C++ NPC behaviors predating the MobProg scripting system
  - Assigned to mobiles via function pointer in their prototype
  - Fire during the NPC update tick (every pulse)
  - Examples: spec_cast_mage (NPC casts offensive spells), spec_cast_cleric (NPC heals/buffs), spec_breath_fire/acid/gas/frost/lightning (dragon breath attacks), spec_executioner (attacks criminals), spec_guard (protects area), spec_thief (picks pockets), spec_fido (eats corpses), spec_janitor (picks up trash)
  - Looked up by name via a function pointer table in `special.cc`
  - Simpler than MobProgs but more performant for common behaviors

### Trigger System
- **Time Triggers**: Schedule-based activation
  - Hour/minute specific triggers
  - Day/night cycle awareness
  - Periodic execution capabilities

- **Speech Triggers**: Language-based activation
  - Keyword detection in nearby speech
  - Phrase matching with wildcards
  - Language-sensitive responses

- **Action Triggers**: Behavior-based activation
  - Movement detection (arrive, leave)
  - Combat action responses
  - Object interaction awareness
  - Special action detection

- **State Triggers**: Condition-based activation
  - Health status changes
  - Environmental condition responses
  - Random activation with probability
  - NPC state-dependent behaviors

### Execution Engine
- **Command Processor**: Action execution system
  - Command validation and security
  - Parameter substitution
  - Error handling and recovery
  - Context-aware execution

- **Variable Manager**: State tracking system
  - Local and global variable storage
  - Variable type handling
  - Scope management
  - Persistence between triggers

## Implementation Details

### Script Structure and Processing
- **Program Format**: Area file integration
  - Embedded in mobile prototypes
  - Multiple programs per NPC
  - Priority-based execution order
  - Comment and documentation support

- **Parsing System**: Script loading and validation
  - Syntax checking during load
  - Error reporting with line numbers
  - Optimization for runtime performance
  - Command validation against security rules

- **Trigger Evaluation**: Activation condition checking
  - Context-sensitive pattern matching
  - Parameter extraction from triggers
  - Environment state examination
  - Probability-based random triggers

- **Conditional Logic**: Decision tree processing
  - Nested IF-THEN-ELSE statements
  - Logical operators (AND, OR)
  - Comparison operators
  - Variable-based conditions

### Action Execution
- **Command Set**: Mobile-specific actions
  - Movement commands with pathfinding
  - Special communication capabilities
  - Object manipulation actions
  - Combat and social behaviors
  - State-changing operations

- **Action Scheduling**: Execution timing
  - Immediate vs. delayed execution
  - Action prioritization
  - Interrupt handling
  - Sequence management

- **Context Handling**: Execution environment
  - Target identification and validation
  - Room and environment awareness
  - Actor and victim parameter substitution
  - Random selection capabilities

## Key Files

### Header Files
- `MobProg.hh` (71 LOC) - NPC scripting system
  - Trigger type definitions
  - Program structure definitions
  - Condition evaluation interfaces
  - Action execution interfaces
  - Variable management

- `MobProgActList.hh` (23 LOC) - NPC action queue
  - Action scheduling structures
  - Priority definitions
  - Delayed action management
  - Queue processing interfaces

### Implementation Files
- `mob_prog.cc` (1937 LOC) - NPC scripting implementation
  - Trigger processing logic
  - Conditional evaluation
  - Command execution
  - Variable management
  - Program loading and execution

- `mob_commands.cc` (672 LOC) - NPC command handling
  - Mobile-specific command implementations
  - Command validation and security
  - Parameter processing
  - Special NPC action capabilities

## System Behaviors

### Script Activation Behaviors
- **Trigger Evaluation**: Scripts activate based on specific conditions
  - Input matching for speech and command triggers
  - Time-based scheduling for hour/minute triggers
  - State monitoring for condition triggers
  - Event detection for action triggers

- **Priority Management**: Multiple scripts can trigger simultaneously
  - Higher priority scripts execute first
  - Interruption of lower priority scripts
  - Queue management for pending actions
  - Conflict resolution for competing triggers

- **Context Sensitivity**: Triggers consider environmental context
  - Room-specific behaviors
  - Target-aware responses
  - State-dependent activation
  - Visibility and accessibility checks

### Execution Behaviors
- **Conditional Processing**: Scripts can branch based on conditions
  - State-based decision making
  - Random chance branches
  - Character attribute examination
  - Environmental condition checking

- **Command Execution**: Scripts perform actions through commands
  - Movement and navigation
  - Speech and communication
  - Combat initiation and tactics
  - Object manipulation
  - State changes and affects

- **Action Timing**: Scripts control execution timing
  - Immediate vs. delayed execution
  - Sequential action chains
  - Conditional delays
  - Interrupt handling and recovery

### State Management Behaviors
- **Variable Tracking**: Scripts maintain state through variables
  - Numeric and string variable support
  - Increment/decrement operations
  - Comparison and testing
  - Persistence between trigger activations

- **Global State**: Some state can be shared between NPCs
  - Global variables for world events
  - Shared behavior coordination
  - Cross-NPC communication
  - Environment-wide state tracking

## Dependencies and Relationships

### Dependencies On
- **Character System**: For NPC entity access and manipulation
  - Mobile prototype integration
  - Character state access
  - Attribute checking and modification
  - NPC instantiation hooks

- **World System**: For environmental context and placement
  - Room awareness and navigation
  - Environmental condition checking
  - Location-based triggers
  - Area reset integration

- **Event System**: For event-based trigger activation
  - Combat event hooks
  - Movement detection
  - Speech and communication events
  - Time and schedule events

- **Command System**: For action execution
  - Command validation and permissions
  - Parameter processing
  - Execution contexts
  - Command result handling

### Depended On By
- **NPC AI**: For behavior implementation
  - Shopkeeper behaviors
  - Guard and sentinel actions
  - Quest-giving NPC interactions
  - Environmental storytelling

- **Quest System**: For interactive quest behaviors
  - Quest-giving NPC scripts
  - Progress tracking interactions
  - Reward distribution
  - Dynamic quest adjustments

- **Dynamic World Features**: For responsive environment
  - Weather-responsive behaviors
  - Time-sensitive events
  - Special holiday events
  - World-changing event reactions
