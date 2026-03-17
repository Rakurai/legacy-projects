# Quests and Objectives

## Overview
The Quests and Objectives subsystem provides systems for generating, tracking, and rewarding player objectives. It supports both fixed and dynamic quests, time-limited challenges, and reward systems, and is closely tied to character progression and world regions. This system creates structured goals for players to pursue, enhancing engagement and providing direction for gameplay beyond simple exploration and combat.

## Responsibilities
- Generating and managing quests and missions
- Tracking player progress on objectives
- Rewarding players for quest completion
- Supporting time-limited and dynamic challenges
- Integrating quest tokens and mission management
- Creating meaningful gameplay objectives across the world
- Managing quest points as an alternative currency
- Providing character advancement opportunities

## Core Components

### Quest System
- `quest.cc`: Comprehensive automated quest system (1897 LOC)
  - Dynamic mission generation with varied objectives
  - Quest state management and tracking
  - Time-based quest availability and expiration
  - Reward calculation and distribution logic
  - Multiple difficulty levels and challenge scaling
  - Token-based progress tracking

- `QuestArea`: Specialized areas with quest-specific properties
  - Start room tracking for quest areas
  - Quest-related object handling
  - Mission state management
  - Environmental context for objectives

- `wiz_quest.cc`: Administrative quest management tools
  - Quest creation and modification tools
  - Quest monitoring and debugging utilities
  - Event-based quest triggers
  - Quest reward adjustment tools

### Player Quest Tracking
- Quest point system for rewards and purchases
- Next quest timer tracking
- Quest giver and target tracking
- Quest location management
- Quest object tracking
- Special quest flags for character status

### Quest Objects
- Quest tokens for objective validation
- Special identification for quest items
- Protection mechanisms for quest objects
- Special handling during server restarts

## Implementation Details

### Quest Mechanics
- **Quest Generation**: Both automated random quests and fixed predefined missions
- **Timer System**: Characters must wait between quests based on points earned
- **Quest Types**:
  - Item retrieval quests
  - Mobile hunting quests
  - Location-based objectives
  - Special event quests
  - Time-limited challenges

### Quest State Management
- **Progress Tracking**: System monitors objective completion status
- **Time Limits**: Some quests have expiration timers
- **Multiple Objectives**: Support for multi-stage quests
- **Quest Points**: Special currency earned from completing objectives
  - Can be spent on special items or benefits
  - Tracked persistently with character data
  - Used as a measure of character accomplishment

### Quest Integration
- **World Integration**: Quests span across different game areas and regions
- **Character System**: Tracks quest status and progress in player character data
- **Object System**: Special handling for quest items and tokens
- **NPC Integration**: Special behaviors for quest givers and targets

## Key Files

### Header Files
- `/src/include/QuestArea.hh` - Quest area management (27 LOC)
- Player character quest-related fields in Player.hh:
  - `questmob` - Target mobile for quest
  - `questobj` - Target object for quest
  - `questpoints` - Accumulated quest points
  - `quest_giver` - NPC that assigned the quest
  - `questloc` - Location for quest objective
  - `nextquest` - Timer until next quest is available

### Implementation Files
- `/src/quest.cc` - Core quest system implementation (1897 LOC)
- `/src/wiz_quest.cc` - Administrative quest management (1001 LOC)
- Quest-related methods in player character implementation files

## System Behaviors

### Core Behaviors
- **Quest Assignment**: Characters can seek out quests from specific NPCs
- **Objective Tracking**: System tracks various types of objectives
- **Time Limits**: Quests may have expiration timers for urgency
- **Reward Scaling**: Rewards scale based on difficulty and level
- **Quest Points**: Special currency earned for completing objectives

### Special Features
- **Random Generation**: Dynamic quest creation for replayability
- **Quest Point Economy**: Alternative reward system beyond experience
- **Quest Items**: Special items with quest-specific properties
- **Quest Areas**: Regions designed specifically for quest activities
- **Automated Messaging**: Quest progress and completion notifications

## Dependencies and Relationships

### Dependencies On
- **Character System**: For player progress tracking and quest status storage
- **World System**: For quest locations, areas, and spatial objectives
- **Object System**: For quest items, tokens, and objective validation
- **Game Rules**: For quest objective logic and completion validation
- **Command System**: For quest-related commands and interactions

### Depended On By
- **Player Progression**: Quests provide alternative advancement paths
- **Economy System**: Quest points serve as alternate currency
- **Event System**: Quests trigger various in-game events
- **NPC AI**: Special behaviors for quest givers and targets

## Future Improvements
- Expand quest variety and objective types beyond current patterns
- Add more dynamic and branching quest lines with multiple outcomes
- Enhance integration with world events and player actions
- Implement narrative-driven quest chains with story progression
- Create more complex multi-stage quests with interdependent objectives
- Develop guild or group quests requiring team coordination
- Improve quest rewards to include more unique and specialized items
