#!/usr/bin/env python3
"""
Script to update specific file summaries in files_old.json.
"""
import json
import os

# File to update
JSON_FILE = "/Users/qte2333/repos/legacy/context/files_old.json"

# New summaries to add
new_summaries = {
    "/src/JSON/cJSON.cc": {
        "category": "infrastructure",
        "summary": "Implements wrapper functions around the cJSON library, providing high-level convenience methods for file loading/saving and structured data serialization/deserialization operations used by the game's configuration system."
    },
    "/src/deps/cJSON/cJSON.c": {
        "category": "infrastructure",
        "summary": "Implements the cJSON library core functionality, providing comprehensive JSON parsing, manipulation, and generation capabilities with memory management, error handling, and data conversion facilities."
    },
    "/src/deps/cJSON/cJSON.h": {
        "category": "infrastructure",
        "summary": "Declares the cJSON library's interface, defining data structures for JSON representation and function prototypes for parsing, generating, and manipulating JSON data with minimal dependencies."
    },
    "/src/event/Dispatcher.cc": {
        "category": "game_mechanics",
        "summary": "Implements the event dispatching system, managing event publication to subscribed handlers with careful iteration to handle subscription modifications during event processing."
    },
    "/src/include/DepartedPlayer.hh": {
        "category": "character_system",
        "summary": "Defines the DepartedPlayer class that maintains records of players/immortals who have left the game, supporting list traversal and persistence of departure information."
    },
    "/src/include/Descriptor.hh": {
        "category": "infrastructure",
        "summary": "Defines the Descriptor class managing network connections, handling input/output buffers, connection states, authentication, character association, and telnet protocol negotiation."
    },
    "/src/include/Disabled.hh": {
        "category": "admin_systems",
        "summary": "Defines structures and functions for the command disabling system, allowing administrators to temporarily disable specific commands with reason tracking and persistence."
    },
    "/src/include/Duel.hh": {
        "category": "game_mechanics",
        "summary": "Defines the Duel class implementing the player versus player dueling system, including challenge management, arena handling, combat rules, spectator support, and duel resolution."
    },
    "/src/include/Edit.hh": {
        "category": "interaction",
        "summary": "Defines the Edit class implementing an in-game text editor with line-based editing, string manipulation, and formatting capabilities for notes, descriptions, and other text content."
    },
    "/src/include/ExitPrototype.hh": {
        "category": "world_system",
        "summary": "Defines the ExitPrototype class serving as a template for creating Exit instances, storing base properties like destination, key requirements, flags, and descriptions for room connections."
    },
    "/src/include/JSON/cJSON.hh": {
        "category": "infrastructure",
        "summary": "Declares wrapper functions around the cJSON library, providing structured data serialization/deserialization and file operations for configuration and data storage."
    },
    "/src/include/Logging.hh": {
        "category": "infrastructure",
        "summary": "Defines the logging system interface with multiple severity levels, configurable output targets, context-enriched logging functions, and error reporting facilities."
    },
    "/src/include/Reset.hh": {
        "category": "world_system",
        "summary": "Defines the Reset class managing area respawn instructions, controlling mobile and object placement, equipment for mobiles, door states, and periodic world refreshing."
    },
    "/src/include/RoomID.hh": {
        "category": "world_system",
        "summary": "Defines the RoomID class implementing a unique identifier system for room instances, combining virtual number with instance number to enable multiple instances of the same room template."
    },
    "/src/include/RoomPrototype.hh": {
        "category": "world_system",
        "summary": "Defines the RoomPrototype class serving as a template for creating room instances, storing base room properties such as descriptions, flags, sector type, and other attributes."
    },
    "/src/include/Social.hh": {
        "category": "interaction",
        "summary": "Defines the Social class representing pre-defined emotive commands with multiple target support, customized messages for different perspectives, and online editing capabilities for administrators."
    },
    "/src/include/Tail.hh": {
        "category": "infrastructure",
        "summary": "Defines the Tail class implementing a file monitoring utility with real-time display functionality, line buffer management, and dynamic file tracking for log monitoring."
    },
    "/src/include/Vnum.hh": {
        "category": "world_system",
        "summary": "Defines the Vnum class providing a type-safe virtual number identifier system for game entities, with range operations, comparisons, and serialization support for area-specific identification."
    },
    "/src/include/Weather.hh": {
        "category": "world_system",
        "summary": "Defines the Weather class implementing a dynamic weather simulation with seasonal variations, sky conditions, atmospheric pressure tracking, room-specific effects, and forecasting capabilities."
    },
    "/src/include/World.hh": {
        "category": "world_system",
        "summary": "Defines the World class serving as the central coordinator for the game environment, managing areas, tracking global state, handling world-wide updates, and controlling area reset scheduling."
    },
    "/src/include/affect/Affect.hh": {
        "category": "affect_system",
        "summary": "Defines the Affect class and related structures for status effects, including list management, comparators, and accessors for characters, objects, and rooms."
    },
    "/src/include/affect/Type.hh": {
        "category": "affect_system",
        "summary": "Declares the affect::type enum class, listing all possible affect types such as buffs, debuffs, weapon flags, and object prefixes/suffixes with type-safe enumeration."
    },
    "/src/include/affect/affect_int.hh": {
        "category": "affect_system",
        "summary": "Declares internal functions for manipulating lists of Affect objects, intended for internal use within affect modules with implementation details hidden from external callers."
    },
    "/src/include/affect/affect_list.hh": {
        "category": "affect_system",
        "summary": "Declares additional internal list operations for affects, including adding, removing, copying, deduplicating, and sorting affects within affect containers."
    },
    "/src/include/argument.hh": {
        "category": "command_system",
        "summary": "Declares command argument parsing functions and defines entity flags used by entity_argument for parsing references to players, mobiles, objects, and rooms with both C and C++ string support."
    },
    "/src/include/conn/State.hh": {
        "category": "connection",
        "summary": "Defines the connection state machine for player login process, including states for character creation, authentication, and game entry with state transition management."
    },
    "/src/include/constants.hh": {
        "category": "constants",
        "summary": "Defines core game constants including system limits, gameplay values, configuration parameters, and magic numbers used throughout the codebase for consistent operation."
    },
    "/src/include/event/Dispatcher.hh": {
        "category": "game_mechanics",
        "summary": "Defines the event dispatcher implementing the publish-subscribe pattern, managing event subscriptions and coordinating event distribution to registered handlers."
    },
    "/src/include/event/Handler.hh": {
        "category": "game_mechanics",
        "summary": "Defines the Handler interface with a notify method for event subscribers, providing the base class for components that need to respond to game events."
    },
    "/src/include/event/event.hh": {
        "category": "game_mechanics",
        "summary": "Defines the event type enumeration for the event system, providing fine-grained categorization of events, system-specific event definitions, and event priority classification."
    },
    "/src/include/gem/gem.hh": {
        "category": "object_system",
        "summary": "Defines the gem enhancement system for equipment customization, including socket creation, gem insertion/removal mechanics, gem types with different bonuses, and quality-based enhancement calculations."
    },
    "/src/include/lookup.hh": {
        "category": "infrastructure",
        "summary": "Declares entity lookup functions for finding characters, objects, and rooms by various identifiers, supporting name-based and ID-based searches with visibility rules and fuzzy matching."
    },
    "/src/include/magic.hh": {
        "category": "game_mechanics",
        "summary": "Defines the magic system's spell function type and declares hundreds of individual spell functions that comprise the game's magic system, organized by spell category and effect type."
    },
    "/src/include/skill/Type.hh": {
        "category": "skills",
        "summary": "Defines the comprehensive skill::type enum class containing all possible skill types in the game, providing type-safe skill identification and categorization for the skill system."
    },
    "/src/include/skill/skill.hh": {
        "category": "skills",
        "summary": "Declares core skill system interfaces and skill_table_t structure for managing skill properties and requirements, linking skill identifiers with their implementation and parameters."
    },
    "/src/include/worldmap/Coordinate.hh": {
        "category": "worldmap",
        "summary": "Defines the coordinate system for world positions with operations for translation, validation, and distance calculations in the world's 2D/3D spatial representation system."
    },
    "/src/include/worldmap/MapColor.hh": {
        "category": "worldmap",
        "summary": "Defines color constants and functions for world map visualization, supporting terrain types and features with color-coded representation for ASCII map display."
    },
    "/src/include/worldmap/Quadtree.hh": {
        "category": "worldmap",
        "summary": "Implements spatial partitioning for efficient area queries and neighbor finding in the world map system, optimizing spatial searches with logarithmic complexity."
    },
    "/src/include/worldmap/Region.hh": {
        "category": "worldmap",
        "summary": "Defines geographical regions in the world map with boundary management and property handling, organizing the world into named areas with distinct characteristics."
    },
    "/src/include/worldmap/Worldmap.hh": {
        "category": "worldmap",
        "summary": "Provides the core world map interface for managing and visualizing the game world's spatial organization, supporting terrain representation and map generation."
    }
}

# Load existing JSON
try:
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

# Update with new summaries
updated_count = 0
for file_path, summary_data in new_summaries.items():
    if file_path in data:
        # Update existing entry
        data[file_path]["category"] = summary_data["category"]
        data[file_path]["summary"] = summary_data["summary"]
        updated_count += 1
        print(f"Updated: {file_path}")
    else:
        # File not found in the JSON
        print(f"Warning: {file_path} not found in the JSON file")

# Write back to the file
try:
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Successfully updated {updated_count} file summaries in {JSON_FILE}")
except Exception as e:
    print(f"Error writing to JSON file: {e}")
    exit(1)
