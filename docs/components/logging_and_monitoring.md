# Logging & Monitoring

## Overview
The Logging & Monitoring subsystem provides comprehensive support for system logging, debug tracing, and administrative event tracking throughout the MUD codebase. It implements adjustable verbosity levels, targeted output channels, and persistent storage of audit logs and game errors, ensuring system reliability, accountability, and effective troubleshooting capabilities. This system serves as the foundation for server maintenance, performance optimization, and administrative oversight.

## Responsibilities
- Logging system events, errors, warnings and informational messages
- Recording and auditing administrator actions for accountability
- Providing detailed debug tracing and inspection tools for troubleshooting
- Storing and managing persistent audit logs with rotation and archiving
- Supporting comprehensive monitoring of server health and performance metrics
- Enabling real-time observation of system behavior and player activity
- Facilitating post-incident analysis and problem resolution
- Providing configurable verbosity levels for different subsystems
- Supporting development and testing with diagnostic information

## Core Components

### Logging Infrastructure
- **Logging System**: Core logging implementation
  - Multiple severity levels (ERROR, WARNING, INFO, DEBUG)
  - Configurable output targets (console, file, database)
  - Context-enriched logging with metadata
  - Error tracing and reporting with call stacks
  - Category-based message routing
  - Rotation and archiving of log files

- **Debug Output**: Development and troubleshooting tools
  - Debug mode controls and toggles
  - Conditional logging based on verbosity
  - Performance impact tracking
  - Memory allocation tracking
  - Special debugging commands for administrators
  - Test mode logging enhancements

- **Audit Logging**: Administrative action recording
  - Command usage tracking for privileged users
  - Security event recording
  - Changes to critical game data
  - Player modification audit trail
  - System configuration change tracking
  - Login and authentication records

### Monitoring Tools
- **Tail Utility**: Real-time file monitoring
  - Dynamic log file observation
  - Last-n-lines buffer management
  - Pattern-based filtering
  - Administrative monitoring interface
  - Alert generation for specific patterns

- **Performance Tracking**: System health monitoring
  - Memory usage observation
  - CPU utilization metrics
  - Network traffic analysis
  - Database performance tracking
  - Resource leak detection
  - Threshold-based alerts

- **State Inspection**: Game state examination
  - World state snapshots
  - Player activity monitoring
  - System load analysis
  - Resource utilization stats
  - Object count and distribution
  - Memory allocation patterns

### Control Interfaces
- **Verbosity Management**: Output control system
  - Category-specific verbosity settings
  - Runtime adjustable logging levels
  - Custom filtering rules
  - Priority-based message handling
  - Temporary diagnostic modes

- **WIZnet Monitoring**: Admin notification system
  - Special event monitoring flags
  - WIZ_ON - Basic wizard visibility
  - WIZ_LOAD - Object/mobile creation alerts
  - WIZ_QUEST - Quest operation monitoring
  - Category-specific notification channels
  - Priority-based alert routing

## Implementation Details

### Logging Implementation
- **Severity Levels**: Message categorization system
  - Critical errors requiring immediate attention
  - Warnings indicating potential issues
  - Informational messages for normal operation
  - Debug information for development
  - Audit records for administrative review
  - Trace data for detailed analysis

- **Output Routing**: Message destination control
  - Console output for immediate visibility
  - File logging for persistence
  - Database storage for structured queries
  - Remote logging capability
  - Multiple simultaneous outputs
  - Conditional routing based on message properties

- **Format Control**: Message structure and presentation
  - Timestamp and source inclusion
  - Consistent formatting across subsystems
  - Machine-parseable log formats
  - Context data enrichment
  - Sanitization of sensitive information
  - Standardized error codes and categories

### Monitoring Implementation
- **Real-Time Observation**: Live system tracking
  - Active session monitoring
  - Traffic and command analysis
  - Resource utilization tracking
  - Connection status observation
  - Event frequency analysis
  - Pattern detection in system behavior

- **Historical Analysis**: Trend tracking and reporting
  - Log aggregation and summarization
  - Statistical analysis of system behavior
  - Performance trend identification
  - Anomaly detection through baselines
  - Correlation between events and issues
  - Capacity planning support

- **Alert Generation**: Notification system
  - Threshold-based warnings
  - Pattern matching triggers
  - Escalation based on severity
  - Administrator notification
  - Automatic response capabilities
  - Alert tracking and resolution

## Key Files

### Implementation Files
- `Logging.cc` - Core logging system implementation
  - Message formatting and routing
  - Severity level handling
  - Output target management
  - Log file rotation and archiving
  - Context enrichment logic

- `Game.cc` - Global logging controls
  - `log_all` variable for global logging toggle
  - System-wide logging initialization
  - Default verbosity configuration
  - Global log state management

- `Tail.hh` (29 LOC) - File monitoring utility
  - Real-time log file display
  - Buffer management for display
  - Pattern matching for filtering
  - Administrative interface definition

- `macros.hh` - Logging utility macros
  - Debug helper functions
  - Logging shortcuts for consistent usage
  - Conditional compilation controls
  - Context capture utilities
  - Platform-specific adaptations

### Resource Locations
- `log/` directory - Primary storage for log files
  - System logs with rotation
  - Error logs with extended details
  - Administrative action records
  - Security and access logs
  - Connection and player logs

- `misc/` directory - Administrative resources
  - `bugs.txt` - Player-reported issues
  - `typos.txt` - Content correction reports
  - `punishment.txt` - Administrative actions log
  - Configuration files for monitoring systems

## System Behaviors

### Logging Behaviors
- **Severity-Based Filtering**: Messages filtered by importance
  - Critical errors always logged
  - Warnings conditionally logged based on verbosity
  - Informational messages for normal operation tracking
  - Debug messages only in development or diagnostic modes
  - Audit records for sensitive operations

- **Context Enrichment**: Metadata added to log messages
  - Source location (file, line, function)
  - Timestamp with millisecond precision
  - Actor information (player, admin, system)
  - Category and subsystem tags
  - Session and connection identifiers
  - Related entity references

- **Output Management**: Log destination control
  - Dynamic file selection based on message type
  - Automatic log rotation by size or time
  - Console echoing for immediate visibility
  - Silent operation modes for performance
  - Emergency logging for critical failures

### Monitoring Behaviors
- **Active Observation**: Real-time system tracking
  - Command execution monitoring
  - Resource utilization tracking
  - Player activity observation
  - Connection status monitoring
  - Error rate analysis
  - Performance metrics collection

- **Historical Tracking**: Long-term data collection
  - Trend analysis over time
  - Capacity planning support
  - Problem pattern identification
  - Usage statistics compilation
  - System health trending
  - Baseline establishment for anomaly detection

- **Alert Processing**: Notification system
  - Threshold violation detection
  - Pattern-based triggers
  - Administrator notification routing
  - Escalation based on severity
  - Resolution tracking
  - Recurring problem identification

### Administrative Behaviors
- **Audit Trail**: Action accountability
  - Command usage recording by admins
  - Object and character modifications
  - System configuration changes
  - Security-relevant actions
  - Player account manipulations
  - Server operation changes

- **Security Monitoring**: Protection mechanisms
  - Login attempt tracking
  - Privilege escalation logging
  - Resource abuse detection
  - Exploit attempt identification
  - Unusual pattern recognition
  - Account activity anomalies

## Dependencies and Relationships

### Dependencies On
- **Infrastructure**: For core file and system operations
  - File system access for log storage
  - Time services for timestamps
  - Output stream management
  - Process information access
  - System resource metrics

- **Admin Controls**: For monitoring configuration
  - Permission checking for log access
  - Verbosity setting commands
  - Monitoring tool control
  - Alert configuration management
  - Audit level determination

- **World/Character/Object Systems**: For event sources
  - Game entity state changes
  - Player and NPC actions
  - World modifications
  - Object creation and destruction
  - Game rules execution

### Depended On By
- **Game Administrators**: For system management
  - Problem diagnosis and troubleshooting
  - Performance monitoring and optimization
  - Security oversight and auditing
  - Player activity tracking
  - Server health assessment

- **Server Maintenance**: For technical operations
  - Crash analysis and prevention
  - Resource planning and allocation
  - Database integrity verification
  - System upgrade planning
  - Backup and recovery operations

- **Audit/Review Processes**: For accountability
  - Administrative action review
  - Security incident investigation
  - Player complaint resolution
  - Policy enforcement verification
  - Historical record maintenance

- **Development**: For code improvement
  - Bug identification and resolution
  - Performance bottleneck detection
  - Feature usage analysis
  - Test validation and verification
  - Integration testing support
