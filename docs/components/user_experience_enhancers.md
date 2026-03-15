# User Experience Enhancers

## Overview
The User Experience Enhancers subsystem includes quality-of-life systems such as aliases for custom command macros, marriage mechanics for social bonds, and minigames like paintball. These features enhance engagement, personalization, and social interaction for players by providing convenience, social depth, and recreational activities beyond the core gameplay. While not essential to the game's primary mechanics, these systems significantly improve player satisfaction and retention.

## Responsibilities
- Providing command shortcuts and customization (aliases)
- Supporting player-to-player social interactions (marriage)
- Offering specialized gameplay activities and minigames (paintball)
- Improving overall quality of life for players
- Creating alternative gameplay experiences
- Enhancing player socialization and bonding
- Supporting personalization of the game experience

## Core Components

### Command Customization
- `Alias`: Player-defined command shortcuts
  - Custom command mapping
  - Command sequence binding
  - Variable substitution with positional parameters
  - Persistent preferences across sessions
  - Security protections against recursive aliases
  - Command history access

### Social Interactions
- `Marriage System`: Character relationship mechanics
  - Proposal and acceptance workflow
  - Wedding ceremony management
  - Relationship status tracking
  - Special abilities for married couples
  - Divorce handling and procedures
  - Social visibility of relationships

### Minigames
- `Paintball`: Specialized combat activity
  - Custom weapons and ammunition
  - Team management and assignment
  - Scoring system for competitive play
  - Non-lethal competition mechanics
  - Arena management with entry/exit controls
  - Special combat rules to prevent character harm

## Implementation Details

### Alias System Implementation
- **Command Storage**: Players can create multiple named aliases
- **Usage Interface**: Commands for creating, listing, and removing aliases
- **Parameter Substitution**: Support for variables like $1, $2 in definitions
- **Security Measures**: Prevention of recursive and harmful aliases
- **Persistence**: Aliases saved with character data between sessions
- **Variable Expansion**: Dynamic insertion of command arguments

### Marriage System Implementation
- **Proposal Process**: Character-to-character proposal with acceptance options
- **Wedding Ceremony**: Event mechanics with witness participation
- **Status Benefits**: Special abilities granted to married characters
- **Relationship Tracking**: Persistent status tracking in character data
- **Partner Commands**: Special commands available to married pairs
- **Divorce Handling**: Process and consequences for ending relationships

### Paintball System Implementation
- **Equipment Management**: Special weapons with paintball ammunition
- **Team Structure**: Random or selected team assignments
- **Point System**: Scoring for hits, team victories, and competitions
- **Safe Combat**: Special rules ensuring no permanent character damage
- **Game Modes**: Different types of paintball competitions
- **Arena Control**: Designated play areas with special rules

## Key Files

### Implementation Files
- `/src/alias.cc` (190 LOC) - Command aliasing system implementation
  - Alias creation, deletion, and substitution
  - Parameter handling and validation
  - Recursive detection and security

- `/src/marry.cc` (465 LOC) - Character marriage system implementation
  - Proposal and acceptance mechanics
  - Wedding ceremony progression
  - Relationship benefits implementation
  - Divorce processing

- `/src/paint.cc` (191 LOC) - Paintball minigame system implementation
  - Team and scoring management
  - Paintball weapon mechanics
  - Arena control and game rules

## System Behaviors

### Core Behaviors
- **Command Aliases**: Creation and use of custom command shortcuts
  - Simple substitution (e.g., "k" for "kill")
  - Complex commands with parameters
  - Command sequences bound to a single alias

- **Character Relationships**: Formal bonding between player characters
  - Proposal and acceptance process
  - Ceremonial wedding with witnesses
  - Special abilities when partners are near each other
  - Publicly visible relationship status

- **Alternative Gameplay**: Recreational activities beyond standard gameplay
  - Team-based paintball competitions
  - Non-lethal combat with scoring
  - Specialized equipment and rules

### Special Features
- **Alias Parameter Expansion**: Dynamic command construction with variables
  - Position-based substitution ($1, $2, etc.)
  - All-parameter inclusion ($*)
  - Protection against command injection

- **Relationship Benefits**: Mechanical advantages for married characters
  - Special commands only available to partners
  - Enhanced abilities when together
  - Social status indicators

- **Team Dynamics**: Structured team play in paintball
  - Team scoring and competition
  - Strategic cooperation incentives
  - Safe practice for combat tactics

## Dependencies and Relationships

### Dependencies On
- **Character System**: For player state, relationships, and persistent data
- **Command System**: For command processing, interpretation, and execution
- **World System**: For location awareness and room-based interactions
- **Skill System**: For success calculations in specialized activities
- **Information Systems**: For status display and tracking features

### Depended On By
- **Player Experience**: Directly enhances gameplay satisfaction
- **Social Engagement**: Promotes community interaction and bonding
- **Character Development**: Provides additional goals and achievements
- **Player Retention**: Creates long-term social connections and gameplay variety
