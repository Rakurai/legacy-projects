# Legacy C/C++ File Directory
This directory lists all legacy source/header files, grouped by system component. Each file is categorized based on references in the component documentation.
---
## Character System System [link](.ai/docs/components/character_system.md)
### Header Files
- `/src/include/Character.hh` - Defines the Character class, representing a player or NPC. Includes stats, inventory, status flags, group/party info, and macros for attribute and permission checks.
- `/src/include/MobProgActList.hh` - Defines the action queue for NPCs, managing scheduled actions with prioritization, delayed execution capability, and safe command processing specific to mobile characters.
- `/src/include/Player.hh` - Extends the Character class with player-specific functionality including persistent data storage, configuration preferences, progression tracking, authentication, and customization options.
- `/src/include/Battle.hh` - Defines the Battle class that manages the arena combat system, including battle state, level restrictions, and entry fees
- `/src/include/MobProg.hh` - Defines the MobProg system for NPC behavior scripting with trigger conditions, conditional execution, and flexible actions for defining complex NPC behaviors and interactions.
- `/src/include/DepartedPlayer.hh` - Defines the DepartedPlayer class that maintains records of players/immortals who have left the game, supporting list traversal and persistence of departure information.
- `/src/include/MobilePrototype.hh` - Defines templates for NPC creation with base attributes, behaviors, equipment specifications, shop capabilities, and special flags that control mobile behavior parameters.
### Implementation Files
- `/src/mob_prog.cc` - Implements the mobile program scripting system with triggers, conditions, and commands that control NPC behavior and interaction.
- `/src/Player.cc` - Implements player initialization and tracking, including skill learning and evolution.
- `/src/Character.cc` - Implements core character functionality including initialization, cleanup, and memory management for character resources and attributes.
- `/src/mob_commands.cc` - Implements special commands available to NPCs through the mobile program system for actions like movement, combat, and quest interactions.
- `/src/set-stat.cc` - Implements comprehensive character attribute manipulation system including commands for viewing and modifying character stats, with permission controls, validation logic, and both temporary and permanent stat adjustments.
- `/src/conn/State.cc` - Implements state machine initialization with static instances of all connection states, providing centralized access to the connection state system.
- `/src/conn/ReadNewMOTDState.cc` - Implements comprehensive new player welcome sequence including class selection, race selection, skill selection, MOTD display, and new character setup.
- `/src/conn/RollStatsState.cc` - Implements character attribute generation system including stat rolling, race/class modifiers, rerolling limits, validation against min/max values, and final stat distribution.

## Object System System [link](.ai/docs/components/object_system.md)
### Header Files
- `/src/include/lootv2.hh` - Defines the enhanced loot generation system (LootV2) with advanced probability distribution for item drops, tiered rarity system, context-sensitive generation, and specialized drop tables.
- `/src/include/ObjectValue.hh` - Defines the value system for objects with type-specific properties, providing specialized behavior for different object types (weapons, containers, food, etc.) through polymorphic value interpretation.
- `/src/include/ExtraDescr.hh` - Defines the ExtraDescr class that provides additional keyword-based descriptions for object features, enhancing world detail and enabling object puzzle mechanics through special descriptions.
- `/src/include/EQSocket.hh` - Defines the EQSocket class representing equipment socket system for item customization, handling socket creation, quality types, and integration with the gem enhancement system.
- `/src/include/ObjectPrototype.hh` - Defines templates for object creation with static properties, type-specific behaviors, and base attributes used to instantiate item instances throughout the game world.
- `/src/include/Object.hh` - Defines the Object class representing items in the game world, managing properties, location state, contained objects, affects, and item lifecycle from creation to destruction.
- `/src/include/gem/gem.hh` - Defines the gem enhancement system for equipment customization, including socket creation, gem insertion/removal mechanics, gem types with different bonuses, and quality-based enhancement calculations.
### Implementation Files
- `/src/ObjectPrototype.cc` - Implements object template loading from area files with specialized handling for different item types and their custom property values.
- `/src/ObjectValue.cc` - Implements operations for object values, including arithmetic and bitwise operations.
- `/src/lootv2.cc` - Implements an enhanced loot generation system building on the base loot tables with more sophisticated drop mechanics, improved rarity controls, and contextual treasure generation.
- `/src/tables.cc` - Implements game data tables containing structured information for races, classes, skills, items, spells, and other core game mechanics.
- `/src/storage.cc` - Implements an item storage system enabling players to store possessions between sessions across different locations, with capacity limits, access controls, and persistence mechanisms.
- `/src/objstate.cc` - Implements object persistence between server restarts, ensuring items on the ground and their states remain intact, with special handling for quest items and modified containers.
- `/src/loot_tables.cc` - Implements the core loot distribution system with multi-tiered tables, weighted probabilities, monster-specific drops, and treasure generation algorithms that control item distribution throughout the game.
- `/src/Object.cc` - Implements object functionality, including cleanup and unique item generation.
- `/src/handler.cc` - Implements core entity management functions for characters, objects, and affects, handling state transitions and updates.
- `/src/gem/gem.cc` - Implements the gem socketable enhancement system allowing players to customize equipment with gems providing various bonuses, including socket creation, gem insertion/removal, and stat/ability modifications.

## World System System [link](.ai/docs/components/world_system.md)
### Header Files
- `/src/include/Location.hh` - Defines the Location class that represents precise positions in the game world, combining room references with position information for character/object positioning and relative location calculations.
- `/src/include/Room.hh` - Defines the Room class, representing a location in the game world. Manages exits, contents, affects, flags, and provides methods for character movement and room state.
- `/src/include/GameTime.hh` - Defines the GameTime class that manages in-game time with hour/day/month/year tracking, time-based event triggering, and sunlight cycle calculations affecting gameplay.
- `/src/include/Exit.hh` - Defines the Exit class that represents connections between rooms, handling directions, door states (open/closed/locked), visibility rules, and access controls for room-to-room navigation.
- `/src/include/Sector.hh` - Defines the Sector enumeration and utilities for room terrain types, determining movement costs, skill effects, environmental conditions, and visual representation on the world map.
- `/src/include/RoomID.hh` - Defines the RoomID class implementing a unique identifier system for room instances, combining virtual number with instance number to enable multiple instances of the same room template.
- `/src/include/World.hh` - Defines the World class serving as the central coordinator for the game environment, managing areas, tracking global state, handling world-wide updates, and controlling area reset scheduling.
- `/src/include/Vnum.hh` - Defines the Vnum class providing a type-safe virtual number identifier system for game entities, with range operations, comparisons, and serialization support for area-specific identification.
- `/src/include/RoomPrototype.hh` - Defines the RoomPrototype class serving as a template for creating room instances, storing base room properties such as descriptions, flags, sector type, and other attributes.
- `/src/include/Weather.hh` - Defines the Weather class implementing a dynamic weather simulation with seasonal variations, sky conditions, atmospheric pressure tracking, room-specific effects, and forecasting capabilities.
- `/src/include/ExitPrototype.hh` - Defines the ExitPrototype class serving as a template for creating Exit instances, storing base properties like destination, key requirements, flags, and descriptions for room connections.
- `/src/include/Reset.hh` - Defines the Reset class managing area respawn instructions, controlling mobile and object placement, equipment for mobiles, door states, and periodic world refreshing.
- `/src/include/worldmap/Worldmap.hh` - Provides the core world map interface for managing and visualizing the game world's spatial organization, supporting terrain representation and map generation.
- `/src/include/worldmap/MapColor.hh` - Defines color constants and functions for world map visualization, supporting terrain types and features with color-coded representation for ASCII map display.
- `/src/include/worldmap/Coordinate.hh` - Defines the coordinate system for world positions with operations for translation, validation, and distance calculations in the world's 2D/3D spatial representation system.
- `/src/include/worldmap/Quadtree.hh` - Implements spatial partitioning for efficient area queries and neighbor finding in the world map system, optimizing spatial searches with logarithmic complexity.
- `/src/include/worldmap/Region.hh` - Defines geographical regions in the world map with boundary management and property handling, organizing the world into named areas with distinct characteristics.
### Implementation Files
- `/src/Room.cc` - Implements room instance creation, character movement tracking, and environmental state management like light levels.
- `/src/Area.cc` - Implements area loading from files, area initialization, reset mechanics, and tracking of players/immortals in areas.
- `/src/RoomPrototype.cc` - Implements room template loading from area files, handling sector type conversion and special room flags, and providing room instance creation.
- `/src/Weather.cc` - Implements dynamic weather system with seasonal variations, atmospheric pressure simulation, and changing sky conditions that affect gameplay.
- `/src/World.cc` - Implements central world management for areas, rooms, and world-level updates, providing a coordinator for all environment systems.
- `/src/RoomID.cc` - Implements room identification functionality with a compact representation combining vnum and instance number, providing parsing and formatting utilities.
- `/src/worldmap/Region.cc` - Implements geographical region management with boundary detection, point-in-polygon testing, region property management, and named region lookup for defining distinct areas within the game world.
- `/src/worldmap/Coordinate.cc` - Implements coordinate system operations including distance calculations, translations, vector mathematics, path calculations, and coordinate normalization for the world map system.
- `/src/worldmap/Worldmap.cc` - Implements a visual world map system with color-coded terrain representation, mapping coordinates to sector types.

## Game Mechanics System [link](.ai/docs/components/game_mechanics.md)
### Header Files
- `/src/include/dispel.hh` - Declares interfaces for the dispel mechanics system that removes magical effects, with level-based calculations and support for different dispel variants like dispel magic and cancel.
- `/src/include/QuestArea.hh` - Defines the QuestArea class for specialized areas with quest-specific properties, including start room tracking, quest-related object handling, and mission state management.
- `/src/include/War.hh` - Defines the War class and related structures that implement the clan warfare system, including war declarations, scoring mechanics, victory conditions, peace negotiations, and timed war events.
- `/src/include/find.hh` - Declares the target finding system used by spells and effects, implementing sophisticated target acquisition with validity checking, range validation, and context-aware selection strategies.
- `/src/include/music.hh` - Defines the bardic music system including song effects, instrument types, performance skill integration, and area-based magical effects created through musical performances.
- `/src/include/Guild.hh` - Defines the Guild class representing professional organizations for character specialization, providing skill-based advancement paths and profession-specific abilities.
- `/src/include/Shop.hh` - Defines the Shop class implementing in-game merchants with opening hours, specialized merchandise, profit margins for buying/selling items, and shopkeeper interaction behaviors.
- `/src/include/Clan.hh` - Defines the Clan class and related structures for player organizations, including hierarchical leadership roles, membership management, clan-specific permissions, and shared resources.
- `/src/include/Duel.hh` - Defines the Duel class implementing the player versus player dueling system, including challenge management, arena handling, combat rules, spectator support, and duel resolution.
- `/src/include/skill/skill.hh` - Declares core skill system interfaces and skill_table_t structure for managing skill properties and requirements, linking skill identifiers with their implementation and parameters.
- `/src/include/skill/Type.hh` - Defines the comprehensive skill::type enum class containing all possible skill types in the game, providing type-safe skill identification and categorization for the skill system.
- `/src/include/event/Handler.hh` - Defines the Handler interface with a notify method for event subscribers, providing the base class for components that need to respond to game events.
- `/src/include/event/event.hh` - Defines the event type enumeration for the event system, providing fine-grained categorization of events, system-specific event definitions, and event priority classification.
- `/src/include/event/Dispatcher.hh` - Defines the event dispatcher implementing the publish-subscribe pattern, managing event subscriptions and coordinating event distribution to registered handlers.
- `/src/include/affect/Affect.hh` - Defines the Affect class and related structures for status effects, including list management, comparators, and accessors for characters, objects, and rooms.
- `/src/include/affect/Type.hh` - Declares the affect::type enum class, listing all possible affect types such as buffs, debuffs, weapon flags, and object prefixes/suffixes with type-safe enumeration.
### Implementation Files
- `/src/remort.cc` - Implements the character advancement system allowing high-level characters to restart with enhanced abilities.
- `/src/dispel.cc` - Implements the dispel mechanics system, including dispellable effect types, level-based saving throws, and effect removal methods (dispel, cancel, undo).
- `/src/War.cc` - Implements the clan war system with war declaration mechanics, event tracking, participant scoring, and war resolution logic.
- `/src/effects.cc` - Implements core effect application logic, handling temporary and permanent effects, effect stacking and overwriting, and effect timing and duration management.
- `/src/event/Dispatcher.cc` - Implements the event dispatching system, managing event publication to subscribed handlers with careful iteration to handle subscription modifications during event processing.

## Interaction Systems System [link](.ai/docs/components/interaction_systems.md)
### Header Files
- `/src/include/act.hh` - Declares the core message formatting system for action feedback with token substitution for different perspectives (actor, target, observers) and visibility filtering based on context.
- `/src/include/Note.hh` - Defines the Note class and related structures for the bulletin board system, implementing multiple themed boards with permissions, read tracking, searching, and note manipulation functions.
- `/src/include/channels.hh` - Defines interfaces for the communication channel system including global, organizational, and special channels.
- `/src/include/Auction.hh` - Defines the Auction class that manages player-to-player item sales, including bidding mechanics, auction states, timing, cancellation handling, and notification systems.
- `/src/include/Actable.hh` - Defines the Actable interface for entities that can perform actions, providing a common abstraction layer for action execution across different entity types.
- `/src/include/interp.hh` - Defines the command system structure including the command table, position requirements, and declarations for hundreds of command handler functions.
- `/src/include/comm.hh` - Declares core network communication functions for socket handling, data buffering, and connection management.
- `/src/include/Social.hh` - Defines the Social class representing pre-defined emotive commands with multiple target support, customized messages for different perspectives, and online editing capabilities for administrators.
- `/src/include/Disabled.hh` - Defines structures and functions for the command disabling system, allowing administrators to temporarily disable specific commands with reason tracking and persistence.
- `/src/include/Edit.hh` - Defines the Edit class implementing an in-game text editor with line-based editing, string manipulation, and formatting capabilities for notes, descriptions, and other text content.
- `/src/include/conn/State.hh` - Defines the connection state machine for player login process, including states for character creation, authentication, and game entry with state transition management.
### Implementation Files
- `/src/channels.cc` - Implements broadcast chat channels (gossip, auction, etc.) with toggling, history tracking, and permission controls.
- `/src/interp.cc` - Implements the command interpretation system, including command parsing, lookup, and dispatch functionality. Contains the extensive command table and `interpret()` function that processes all user input.
- `/src/act_comm.cc` - Implements core communication commands including say, tell, whisper, and emote with visibility checking and formatting for different perspectives.
- `/src/Note.cc` - Implements the bulletin board system with multiple themed boards, note creation/editing/deletion, and unread message tracking.
- `/src/ignore.cc` - Implements a multi-level player communication filtering system allowing players to selectively block different types of communication (tells, channels, etc.) from specific players with commands for adding, removing, and listing ignored players.
- `/src/act.cc` - Implements the core message formatting system for action feedback that shows different perspectives to different observers.
- `/src/act_move.cc` - Implements movement commands and related location transitions including directional movement, special movement types, and visibility tracking.
- `/src/act_info.cc` - Implements commands for gathering information about the game world, characters, and objects including look, examine, who, and score.
- `/src/comm.cc` - Implements network communication including socket management, descriptor handling, input/output processing, and the main game loop.
- `/src/social.cc` - Implements the social action system with predefined emotive commands, multiple target support, and online social editing tools.

## User Experience System [link](.ai/docs/components/user_experience.md)
### Implementation Files
- `/src/scan.cc` - Implements multi-directional area scanning functionality that extends player perception beyond the current room, with distance-based information filtering, visibility rules, and formatted output of detected entities.
- `/src/hunt.cc` - Implements the hunting/tracking system that allows players to follow other characters across the world, with skill-based success rates, environmental modifiers, trail detection algorithms, and directional guidance.
- `/src/paint.cc` - Implements the paintball minigame with specialized weapons, ammunition management, team assignments, scoring logic, and non-lethal combat mechanics for recreational player competition.
- `/src/marry.cc` - Implements the character marriage system with proposal mechanics, ceremony management, relationship benefits, status tracking, and divorce handling for formal player-to-player social relationships.
- `/src/alias.cc` - Implements the command aliasing system that allows players to create custom command shortcuts with parameter substitution, persistent storage, and security protections against recursive aliases and command abuse.

## Admin Systems System [link](.ai/docs/components/admin_systems.md)
### Implementation Files
- `/src/wiz_admin.cc` - Implements basic administrative functions and essential game management commands for immortal-level administrators
- `/src/wiz_quest.cc` - Implements quest management system including creation, tracking, rewards, and special event controls
- `/src/wiz_secure.cc` - Implements security and access control systems including ban management, account security, and privilege enforcement
- `/src/wiz_build.cc` - Implements world building commands for creating and modifying game areas, rooms, objects, and mobiles
- `/src/wiz_gen.cc` - Implements core immortal functionality for character management, object/mobile control, security, and general administrative tasks
- `/src/Disabled.cc` - Implements functionality for disabling commands, including persistence of disabled commands to disk and command disabling verification.
- `/src/wiz_coder.cc` - Implements debugging and development tools for monitoring system performance, memory usage, and other technical aspects

## Infrastructure System [link](.ai/docs/components/infrastructure.md)
### Header Files
- `/src/include/macros.hh` - Defines utility macros used throughout the codebase, including debug helpers, logging shortcuts, memory management wrappers, common function patterns, and platform-specific adaptations.
- `/src/include/file.hh` - Declares file I/O utility functions for loading and saving game data, with abstractions for file operations, error handling, and both text and binary file support.
- `/src/include/vt100.hh` - Defines VT100 terminal control sequences for cursor movement, screen clearing, color and attribute control, and special character display in terminal-based interfaces.
- `/src/include/GarbageCollectingList.hh` - Defines container classes for managing lists of garbage-collected objects with automatic cleanup, safe iteration during modifications, and deferred deletion during traversal.
- `/src/include/Pooled.hh` - Implements memory pooling for frequently allocated objects, reducing memory fragmentation and improving performance through pre-allocated memory blocks and efficient object recycling.
- `/src/include/declare.hh` - Contains comprehensive forward declarations for classes, structs, global variables, and function prototypes to facilitate cross-component references while minimizing include dependencies.
- `/src/include/Garbage.hh` - Defines the Garbage base class for reference-counted objects, providing foundation for safe memory management with automatic cleanup when objects are no longer referenced.
- `/src/include/sql.hh` - Declares the SQLite database interface with connection pooling, transaction handling, prepared statement support, result set processing, and error handling mechanisms.
- `/src/include/memory.hh` - Declares memory management utilities for tracking allocations, detecting memory leaks, and providing allocation statistics and reporting for debugging memory-related issues.
- `/src/include/Tail.hh` - Defines the Tail class implementing a file monitoring utility with real-time display functionality, line buffer management, and dynamic file tracking for log monitoring.
- `/src/include/telnet.hh` - Defines telnet protocol implementation including option negotiation, suboption processing, command codes, and protocol state tracking for network connections.
- `/src/include/merc.hh` - Defines foundational game structures and constants, providing core data structure definitions, historical system compatibility, global reference tables, and legacy macros.
- `/src/include/random.hh` - Declares pseudorandom number generation utilities, including dice-style random rolls, range-based selection, and percentage chance calculations used throughout the game code.
- `/src/include/typename.hh` - Declares a type name resolution system that provides runtime type information, type comparison utilities, object type identification, and pretty-printing of type names.
- `/src/include/Format.hh` - Defines type-safe string formatting utilities for consistent text representation, string composition, type-aware formatting patterns, and parameter substitution with performance optimization.
- `/src/include/lookup.hh` - Declares entity lookup functions for finding characters, objects, and rooms by various identifiers, supporting name-based and ID-based searches with visibility rules and fuzzy matching.
- `/src/include/Game.hh` - Defines the Game singleton that manages central game state, provides access to global subsystems, controls initialization and shutdown sequences, and maintains critical game variables.
- `/src/include/Flags.hh` - Defines the flag manipulation system used across components, supporting efficient bit operations, type-safe flag management, named flag constants, and operations for testing and modifying flag states.
- `/src/include/util/Image.hh` - Declares utilities for ASCII art generation and manipulation, including character-based drawing primitives, box and line drawing, screen buffer management, and multi-color text support.
### Implementation Files
- `/src/file.cc` - Implements file I/O utilities for reading and writing game data, including parsing for different data types and formats.
- `/src/load_config.cc` - Implements dynamic configuration file loading, parsing JSON-based configuration data to set runtime parameters and game settings with validation and error handling.
- `/src/debug.cc` - Includes debugging utilities and commands for the game. Provides tools for developers to test and debug various game functionalities.
- `/src/lookup.cc` - Implements entity lookup functionality for finding characters, objects, and rooms by various identifiers, with support for name matching, visibility rules, and scoped searches.
- `/src/Game.cc` - Defines global variables and functions related to game state, including logging controls (`log_all`) and time tracking (`current_time`).
- `/src/typename.cc` - Implements runtime type information and name management utilities for object type identification, conversion, and comparison across the game's entity system.
- `/src/sqlite.cc` - Implements SQLite database interface with connection management, query execution, and result processing.
- `/src/update.cc` - Implements the central game update loop with pulse-based timing, managing periodic updates for characters, objects, combat, weather, and other game systems with specialized update frequencies.
- `/src/argument.cc` - Implements sophisticated command argument parsing utilities including number_argument for number-name format, one_argument for quote-aware tokenization, mult_argument for quantity parsing, and entity_argument for complex entity references.
- `/src/memory.cc` - Implements memory management utilities defined in memory.hh, providing functionality for memory allocation tracking, leak detection, and memory usage statistics.
- `/src/config.cc` - Implements game configuration management including settings storage, validation, and runtime adjustment of game parameters.
- `/src/util/Image.cc` - Implements ASCII art and visualization utilities for generating maps, diagrams, and other visual representations needed for in-game display and administrative tools.

