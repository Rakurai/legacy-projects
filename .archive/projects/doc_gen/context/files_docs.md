# Documentation Directory

This document summarizes the purpose and goals of each documentation file in the project. Use this as a reference for what each document is intended to achieve and who its primary audience is.

---

## Existing Documentation

### .ai/docs/best_practices.md
Defines coding, testing, documentation, and workflow standards for the project. Ensures consistency and quality for both AI agents and human contributors.

### .ai/context/files_old.md
Directory and summary of all original (legacy) source files, updated as new insights are discovered.

### .ai/context/files_docs.md
Directory and summary of all documentation files, updated as new docs are created or changed.

### .ai/context/dependency_graph.md
Static dependency graph of legacy source files, generated for context in documentation and migration tasks.

### .ai/docs/system_architecture_overview.md
Comprehensive overview of the Legacy MUD system architecture, including high-level features, technical architecture, component breakdowns, design patterns, and code organization.

### .ai/docs/components/infrastructure.md
Documents the Infrastructure Systems: game engine, network, memory management, persistence, and utilities. Details technical foundations and core utilities.

### .ai/docs/components/world_system.md
Describes the World System: areas, rooms, world map, environmental systems, resets, and terrain. Covers spatial structure and environmental simulation.

### .ai/docs/components/object_system.md
Explains the Object System: item management, prototypes, values, enhancement, loot, and persistence. Details object relationships and enhancement.

### .ai/docs/components/character_system.md
Documents the Character System: player and NPC management, attributes, progression, AI scripting, and combat. Covers character lifecycle and behaviors.

### .ai/docs/components/game_mechanics.md
Outlines Game Mechanics: affect/status system, combat, magic, skills, event system, quests, and special gameplay features. Explains core rules and effect systems.

### .ai/docs/components/interaction_systems.md
Covers Interaction Systems: command processing, communication, movement, object manipulation, socials, and auction. Details player input and action routing.

### .ai/docs/components/user_experience.md
Describes User Experience Systems: command aliases, marriage, scan/hunt, minigames, and quality-of-life features. Focuses on player engagement and convenience.

### .ai/docs/components/admin_systems.md
Documents Admin Systems: admin commands, world building, security, monitoring, help management, and quest tools. Details tools for administrators and builders.

### .ai/docs/components/help_system.md
Explains the Help System: in-game documentation, help categories, search, editing, and database integration. Covers help file structure and command integration.

---

## To Be Created

### .ai/docs/requirements_and_philosophy.md
Describes the technical and experiential requirements for the system, including the core game philosophy, user experience goals, and non-functional requirements.

### .ai/docs/game_overview.md
Provides a high-level summary of the game's history, legacy, core gameplay loop, and unique features. Serves as a reference for understanding the spirit and context of the original game.

### .ai/docs/architecture_overview.md
Outlines the high-level system architecture, major components, data flow, and integration points. Guides future design and implementation decisions.

### .ai/docs/component_summaries.md
Summarizes each major game system or component (e.g., areas, mobiles, objects, player system, combat, communication, admin tools) and their responsibilities.

### .ai/docs/migration_plan.md
Details the plan for migrating legacy data and features to the new system, including mapping, conversion tools, and validation steps.

### .ai/docs/ai_integration.md
Documents how AI and automation are used in the project, including prompt engineering, workflows, and context management.

### .ai/context/files_new.md
Directory and summary of all new Python source files, organized by dependency and updated as files are added or changed.

### .ai/docs/summary_headers_batch_affect.md
Summarizes the header files in src/include/affect/ (Affect.hh, Type.hh, affect_int.hh, affect_list.hh), providing an overview of the affect system's types, enums, and internal APIs.

---

This document will evolve as new documentation is added or existing docs are updated.
