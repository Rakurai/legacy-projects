# Help System

## Overview
The Help System delivers structured documentation to players, including searchable help topics and categorized entries. It supports level-gated access and in-game editing tools for dynamic help updates, providing essential knowledge and guidance for players and administrators. This system forms a critical part of the game's information delivery infrastructure, helping both new and experienced players understand game mechanics, commands, and features.

## Responsibilities
- Providing comprehensive in-game documentation and knowledge management
- Organizing help topics by category and access level for intuitive navigation
- Supporting keyword search with context-sensitive help delivery
- Enabling dynamic updates and in-game editing of help content
- Restricting access to certain help topics based on player level or role
- Facilitating self-service learning and game mastery for players

## Core Components

### Help Data Structures
- `help_struct`: Core structure for help entries containing:
  - Level requirements for viewing (access control)
  - Keywords for searching and indexing
  - Help text content
  - Category classification

### Help Categories
Organized topic collections providing logical grouping:
- Player Information (`HELP_INFO`) - Basic game concepts and getting started
- Clan Information (`HELP_CLAN`) - Clan mechanics and organization
- Skills Documentation (`HELP_SKILL`) - Skills system and individual skill details
- Spells Documentation (`HELP_SPELL`) - Magic system and specific spell information
- Race Information (`HELP_RACE`) - Different playable races and characteristics
- Class Information (`HELP_CLASS`) - Character classes and specializations
- Movement Commands (`HELP_MOVE`) - Navigation and travel information
- Object Interaction (`HELP_OBJECT`) - Item usage and manipulation guidance
- Communication (`HELP_COMM`) - Chat channels and social interaction
- Combat System (`HELP_COMBAT`) - Fighting mechanics and tactics
- Miscellaneous Help (`HELP_MISC`) - Various topics not fitting other categories
- Administrative Commands (`HELP_WIZ*`) - Staff-only commands and tools

### Help System Infrastructure
- **Database Integration**: SQLite table structure for help entries storage
- **Help File Loading**: Dynamic parsing and loading from help directory
- **Search and Indexing**: Keyword matching algorithms for topic retrieval
- **Help Editor**: Tools for creating and modifying help entries in-game
- **Access Control**: Level-based restrictions for viewing specific content

## Implementation Details

### Database Structure
- SQLite table for help entries with fields for:
  - Level requirements
  - Group/category classification
  - Keywords for searching
  - Full help text content
- Transaction handling for updates and modifications

### Help File Management
- Dynamic loading from dedicated help directory
- File parsing and validation during server initialization
- Category-based organization and indexing
- Level-based access control for restricted topics

### Search Implementation
- Keyword matching algorithm for finding relevant topics
- Character-level specific help content delivery
- Comprehensive indexing of all help entries
- Context-sensitive help based on current player state

### Help Content Display
- Formatted presentation with proper pagination
- Color coding for important information
- Header/footer with navigation instructions
- Related topics suggestions

### In-game Help Editing
- Admin-level tools for creating new help entries
- Modification of existing entries with versioning
- Content validation and formatting checks
- Real-time updates to the help database

## Key Files

### Header Files
- `help.hh` (Help system interface) - Defines core help structures and interfaces

### Implementation Files
- `help.cc` (718 LOC) - Primary help system implementation including:
  - Help entry loading and initialization
  - Search algorithms and topic matching
  - Help display formatting and pagination
  - Category management and organization
  - Admin-level editing functionality
  - Database integration for persistence

## System Behaviors

### Topic Organization
- Help entries are hierarchically arranged by category
- Topics can belong to multiple categories for better discoverability
- Related topics are cross-referenced for easier navigation
- Core topics appear in beginner-friendly sequences

### Keyword Search
- Players can search for help using relevant keywords
- Search results are ranked by relevance and category
- Partial matching supports abbreviated searches
- Common misspellings and synonyms are handled gracefully

### Context Sensitivity
- Some help content responds to player's current situation
- Command-specific help provides usage examples
- Class/race specific help adjusts to character attributes
- Level-appropriate information is prioritized in results

### Dynamic Updates
- Help content can be modified by administrators at runtime
- New help entries can be added without server restarts
- Obsolete entries can be flagged or removed as needed
- Help content evolution tracks game feature changes

### Access Control
- Level-restricted topics are only visible to qualified players
- Administrative help is hidden from regular players
- Some specialized topics require specific character attributes
- Progressive revelation of complex topics based on player experience

## Dependencies

### Dependencies On
- **Command System**: For processing help commands and arguments
- **Character System**: For level-based access control and context
- **Database/Persistence**: For storing and retrieving help entries
- **Editor System**: For modifying help content in-game

### Depended On By
- **Players**: For learning game mechanics and commands
- **New Player Onboarding**: For structured learning progression
- **Administrative Systems**: For staff documentation and policies
- **Command System**: For providing command-specific assistance

## Future Improvements

### Search Enhancements
- Implement more sophisticated search algorithms with fuzzy matching
- Add natural language processing for question-based queries
- Develop a more comprehensive keyword and synonym database
- Create a help topic recommender system based on player activity

### Content Management
- Develop a web-based help entry management interface
- Implement version control for help content changes
- Create templates for consistent help formatting
- Add multimedia support for diagrams or ASCII art illustrations

### User Experience
- Add a help browser with graphical navigation of topics
- Implement contextual help triggers based on player actions
- Create interactive tutorials linked to help content
- Develop a "tip of the day" system using help content

### Integration
- Connect help system more deeply with command feedback
- Create a help API for custom integrations with other systems
- Implement help content translation support
- Add player-contributed notes and tips with moderation
