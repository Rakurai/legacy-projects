# User Experience Systems Component Documentation

## Overview

The User Experience Systems enhance player interactions with commands, other players, and the game world through quality-of-life improvements, social features, and specialized gameplay mechanics. These systems make gameplay more engaging, intuitive, and socially rewarding.

### System Responsibilities
- Providing command shortcuts and customization
- Supporting player-to-player social interactions
- Offering specialized gameplay activities and minigames
- Improving quality of life for players

## Core Classes and Interfaces

### Command Customization
- **Alias**: Player-defined command shortcuts
  - Custom command mapping
  - Command sequence binding
  - Variable substitution
  - Persistent preferences

### Social Interactions
- **Marriage System**: Character relationship mechanics
  - Proposal and acceptance workflow
  - Wedding ceremony management
  - Relationship status tracking
  - Special abilities for married couples

### Minigames
- **Paintball**: Specialized combat activity
  - Custom weapons and ammunition
  - Team management
  - Scoring system
  - Non-lethal competition

## Implementation Details

### Alias System Implementation
- **Command Storage**: Each player can store multiple custom aliases
- **Alias Command**: Interface for creating, listing, and removing aliases
- **Substitution**: Support for positional parameters (e.g., $1, $2) in alias definitions
- **Security**: Protection against recursive aliases and command abuse
- **Persistence**: Aliases are saved with character data between sessions

### Marriage System Implementation
- **Proposal Mechanics**: Characters can propose to others with acceptance/rejection tracking
- **Ceremony Management**: Wedding event staging with customizable elements
- **Status Effects**: Marriage provides specific bonuses to paired characters
- **Divorce Handling**: Process for dissolving character relationships
- **Social Visibility**: Commands to display relationship status

### Paintball System Implementation
- **Special Equipment**: Paintball guns and ammunition management
- **Team Organization**: Player grouping and team assignment
- **Scoring Logic**: Point tracking for individuals and teams
- **Arena Management**: Designated play areas with entry/exit controls
- **Non-lethal Combat**: Special combat rules that prevent actual character harm

## Key Files and Components

### Implementation Files
- `alias.cc` (190 LOC) - Command aliasing system implementation
- `marry.cc` (465 LOC) - Character marriage system implementation
- `paint.cc` (191 LOC) - Paintball minigame system implementation

## System Behaviors

### Core Behaviors
- **Command Customization**: Players can define shortcuts for frequently used commands
- **Social Bonding**: Characters can establish formal relationships with special benefits
- **Recreational Activities**: Special game modes provide alternative gameplay experiences

### Special Features
- **Parameter Expansion**: Aliases support dynamic command construction with variables
- **Relationship Benefits**: Married characters gain unique abilities when near each other
- **Team Dynamics**: Paintball encourages teamwork and strategic play

## Dependencies and Relationships

### Dependencies On
- **Character System**: For player state and relationship tracking
- **Command System**: For command processing and alias integration
- **World System**: For spatial awareness across rooms and areas
- **Skill System**: For success calculations
- **Information Systems**: For spatial awareness and tracking features

### Depended On By
- **Player Experience**: Directly enhances gameplay quality
- **Social Engagement**: Promotes player interaction and community
- **Character Progression**: Offers additional gameplay goals

## Open Questions and Future Improvements
- The alias system could be expanded to include conditional execution
- Marriage system could integrate with clan or guild mechanics for additional benefits
- Paintball could be expanded with additional game modes and customization options

---
