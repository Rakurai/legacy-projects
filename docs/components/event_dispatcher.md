# Event Dispatcher

## Overview
The Event Dispatcher subsystem implements a global publish-subscribe event system for inter-system communication. It allows registration of event handlers and dispatch of typed events with contextual data, supporting safe iteration and system extensibility. This component enables loosely coupled interactions between game systems, allowing for modular development and flexible response to game state changes across the codebase.

## Responsibilities
- Distributing events to all registered handlers based on event type
- Managing comprehensive event types and priorities across the entire game
- Passing contextual data with events for rich information exchange
- Supporting safe handler registration/removal during dispatch operations
- Providing the core communication backbone for inter-system coordination
- Ensuring delivery order based on priority for critical game events
- Supporting both targeted and broadcast event patterns
- Maintaining system extensibility through loose coupling

## Core Components

### Dispatcher Architecture
- **event::Dispatcher**: Core event distribution component
  - Central singleton for game-wide event management
  - Registration interface for handlers
  - Event dispatch mechanism with safe iteration
  - Handler lookup and notification
  - Priority-based dispatch ordering

- **event::Handler**: Interface for event recipients
  - Standard notification method for receiving events
  - Context data extraction capabilities
  - Implementation in subscribing systems
  - Type-specific event handling

- **event::Type**: Fine-grained event type enumeration
  - System-specific event categories
  - Priority classification for ordering
  - Hierarchical organization of events
  - Event metadata support

### Subscription Management
- **Handler Registration**: System for adding event listeners
  - Type-specific subscriptions
  - Multiple handlers per event type
  - Dynamic registration during runtime
  - Access control for registration

- **Handler Removal**: Clean unsubscription mechanism
  - Safe removal during dispatch
  - Bulk unsubscription support
  - Automatic cleanup for deleted handlers
  - Reference management

- **Lifecycle Management**: Handler validity tracking
  - Detection of stale handlers
  - Garbage collection of invalid references
  - Resource management for subscriptions
  - Performance optimization for lookups

### Event Processing
- **Dispatch Logic**: Core event distribution
  - Type-based handler lookup
  - Priority-ordered execution
  - Context data distribution
  - Exception safety during notification

- **Context Handling**: Rich data passing
  - Type-safe context objects
  - Data encapsulation for events
  - Efficient data sharing mechanisms
  - Immutable event data pattern

## Implementation Details

### Dispatcher Implementation
- **Handler Storage**: Efficient lookup structures
  - Type-indexed handler collections
  - Priority queues for ordered dispatch
  - Fast iteration for notification
  - Memory-efficient storage

- **Safe Iteration**: Robust dispatch mechanism
  - Copy-on-write during dispatch
  - Deferred modification for handler lists
  - Thread-safety considerations
  - Preventing recursion issues

- **Subscription Management**: Registration tracking
  - Handler validity checking
  - Reference counting for handlers
  - Registration audit trail
  - Performance monitoring

### Event Type System
- **Type Hierarchy**: Organized event classification
  - System-specific event groups
  - Sub-categorization of related events
  - Extensible type system
  - Metadata support for events

- **Priority System**: Execution order control
  - Critical vs. normal vs. background events
  - Deterministic ordering within priority levels
  - System-specific priority rules
  - Default prioritization scheme

### Event Context
- **Data Packaging**: Information bundling
  - Source and target entities
  - Event-specific parameters
  - Result and feedback channels
  - Timestamp and sequence information

- **Context Lifetime**: Data availability management
  - Scope-bound context objects
  - Copy semantics for persistence
  - Memory management for large contexts
  - Lazy evaluation for expensive data

## Key Files and Components

### Header Files
- `event/Dispatcher.hh` - Core dispatcher interface
  - Event distribution API
  - Subscription management
  - Handler lookup system
  - Safe iteration guarantees

- `event/Handler.hh` - Event recipient interface
  - Handler base class definition
  - Notification method contracts
  - Context handling interfaces
  - Handler lifecycle hooks

- `event/event.hh` - Event type definitions
  - Comprehensive type enumeration
  - Priority classification
  - Event metadata structures
  - Type relationship definitions

### Implementation Files
- `event/Dispatcher.cc` - Dispatcher implementation
  - Handler storage and lookup
  - Event distribution algorithms
  - Subscription management
  - Safe iteration mechanisms

## System Behaviors

### Event Distribution Behaviors
- **Type Filtering**: Events are routed only to relevant handlers
  - Exact type matching
  - Optional wildcard or category subscriptions
  - Hierarchical event distribution
  - Targeted vs. broadcast events

- **Priority Ordering**: Critical events processed first
  - Multiple priority levels for different use cases
  - Consistent ordering within priority classes
  - System-specific priority rules
  - Starvation prevention for low-priority events

- **Synchronous Processing**: Events processed immediately
  - Depth-first event chain execution
  - Complete processing before return
  - Causal ordering preservation
  - Immediate feedback for event originators

- **Safe Modification**: Handlers can modify subscriptions
  - Deferred list modification during dispatch
  - Safe unsubscription from within handlers
  - New subscription registration during dispatch
  - Structural preservation during iteration

### Handler Management Behaviors
- **Dynamic Registration**: Systems can subscribe at runtime
  - On-demand subscription for efficiency
  - Context-sensitive handler activation
  - Temporary subscriptions for specific scenarios
  - Bulk registration for system initialization

- **Reference Safety**: Protection against invalid handlers
  - Weak reference patterns
  - Automatic cleanup for destroyed handlers
  - Validity checking before dispatch
  - Resource leak prevention

- **Subscription Auditing**: Tracking active handlers
  - Diagnostic tools for subscription analysis
  - Performance monitoring for handlers
  - Subscription lifespan tracking
  - System-wide event flow visualization

### Context Passing Behaviors
- **Rich Information Exchange**: Detailed context objects
  - Event-specific data structures
  - Source and target entity references
  - Parameter passing for flexible handling
  - Result collection from handlers

- **Immutable Context**: Protected event information
  - Read-only access to core event data
  - Consistent view for all handlers
  - Copy semantics for persistence needs
  - Type safety for context access

## Dependencies and Relationships

### Dependencies On
- **Game Rules**: For event type definitions
  - Event categorization
  - Priority classification
  - System-specific event types
  - Event semantics and contracts

- **Character/Object/World Systems**: For event sources/targets
  - Entity references in events
  - State information for context
  - Event origination points
  - Feedback targets for results

### Depended On By
- **All Gameplay Systems**: For state change notification
  - Combat system for hit/damage events
  - Movement system for location changes
  - Interaction system for command events
  - State system for condition changes

- **Scripting Systems**: For event-driven behaviors
  - MobProg trigger integration
  - Script event hooks
  - Custom event handlers
  - Event-based automation

- **AI Systems**: For responsive behaviors
  - NPC reaction to events
  - Environmental awareness
  - Behavioral triggers
  - State machine transitions

- **Quest/Achievement Systems**: For progress tracking
  - Completion trigger events
  - Progress milestone events
  - Fail condition detection
  - Reward distribution events

## Future Improvements

### Event System Expansion
- Implement hierarchical event types with inheritance
- Add pattern-based subscription for broader event matching
- Support event batching for performance optimization
- Create event metadata for improved filtering and routing

### Performance Optimizations
- Implement more efficient handler lookup structures
- Add handler prioritization within event types
- Create specialized fast paths for high-frequency events
- Optimize memory usage for large numbers of subscriptions

### Monitoring and Debugging
- Add comprehensive event logging and tracing
- Create visualization tools for event flow analysis
- Implement subscription auditing and leak detection
- Add performance metrics for dispatcher and handlers

### Advanced Features
- Implement event queuing for deferred processing
- Add conditional event suppression mechanisms
- Create event correlation for complex pattern detection
- Support distributed events across server instances
