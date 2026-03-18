# Prompt Contracts: MCP Documentation Server

<!-- Canonical V1 prompt contracts. Updated per spec 005: resolve_entity references replaced with search; entity_id-only pattern. -->
**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

MCP prompts provide canned conversation starters for common workflows. Prompts return message arrays that guide the AI assistant through multi-step analysis tasks using the documentation server's tools and resources.

**Total Prompts**: 4 (covering entity explanation, behavior analysis, entry point comparison, capability exploration)

---

## 1. Explain Entity

### Prompt Name: `explain_entity`

**Description**: Generate a comprehensive explanation of an entity including its purpose, implementation, usage context, and architectural role.

**Parameters:**
```typescript
{
  entity_name: string  // Entity name or signature
}
```

**Generated Messages:**
```typescript
[
  {
    "role": "user",
    "content": "I need to understand the function/class/entity: {entity_name}. Please provide a comprehensive explanation including:\n\n1. What it does (brief summary)\n2. How it works (detailed implementation notes)\n3. Where it's used (callers and usage context)\n4. What it depends on (callees and dependencies)\n5. Its role in the architecture (capability membership, metrics)"
  },
  {
    "role": "assistant",
    "content": "I'll analyze {entity_name} using the Legacy documentation server. Let me gather information:\n\n1. First, I'll resolve the entity name to get its full details\n2. Then I'll examine its callers to understand usage context\n3. Next, I'll look at its callees to understand dependencies\n4. Finally, I'll check its capability membership and architectural role\n\nStarting with entity resolution..."
  }
]
```

**Workflow Steps:**
1. `search(query=entity_name)` → Get entity_id from results <!-- spec 005: search replaces resolve_entity -->
2. `get_entity(entity_id, include_code=true, include_neighbors=true)` → Full details
3. `get_callers(entity_id, depth=2, limit=10)` → Usage context
4. `get_callees(entity_id, depth=2, limit=10)` → Dependencies
5. `get_capability_detail(capability)` → Architectural context (if entity has capability)

**Example Output (AI's Response):**
```markdown
# Analysis of `damage` Function

## What It Does
**Brief**: Apply damage to a character, handling death, corpse creation, and position updates.

**Signature**: `void damage(Character *ch, Character *victim, int dam)`
**Location**: `src/fight.cc:142-203`
**Capability**: `combat`

## How It Works
[Source code and detailed implementation notes from `details` field]

## Where It's Used
Called by 23 functions including:
- `do_kill` (command handler)
- `spell_fireball` (spell damage)
- `spec_cast_mage` (mobile AI)
- [...]

## What It Depends On
Calls 8 functions including:
- `update_pos` (position management)
- `make_corpse` (death handling)
- `send_to_char` (messaging)
- [...]

## Architectural Role
- **Capability**: `combat` (domain-level)
- **Fan-in**: 23 (highly reused)
- **Fan-out**: 8
- **Bridge Function**: No (all callers/callees in combat capability)
- **Entry Point**: No

## Side Effects
- **State Mutation**: Updates character HP, position
- **Messaging**: Sends damage messages to room
- **Scheduling**: May trigger death events
```

---

## 2. Analyze Behavior

### Prompt Name: `analyze_behavior`

**Description**: Perform a comprehensive behavioral analysis of a function including its call cone, capabilities touched, side effects, and global state interactions.

**Parameters:**
```typescript
{
  entity_name: string,
  max_depth?: number = 5
}
```

**Generated Messages:**
```typescript
[
  {
    "role": "user",
    "content": "I need to understand the behavioral footprint of {entity_name}. Please analyze:\n\n1. What it transitively calls (full call cone)\n2. Which capability groups it exercises\n3. What global state it touches\n4. What side effects it produces\n5. Complexity and risk assessment"
  },
  {
    "role": "assistant",
    "content": "I'll perform a behavioral analysis of {entity_name} using call cone traversal and side-effect detection. This will reveal its transitive dependencies and architectural impact.\n\nStarting analysis..."
  }
]
```

**Workflow Steps:**
1. `search(query=entity_name)` → Get entity_id from results <!-- spec 005: search replaces resolve_entity -->
2. `get_behavior_slice(entity_id, max_depth=max_depth, max_cone_size=200)` → Full behavioral data
3. `get_state_touches(entity_id)` → Global variable usage <!-- spec 005: entity_id only -->

**Example Output:**
```markdown
# Behavioral Analysis of `do_kill`

## Call Cone (Depth 5)
- **Direct callees**: 12 functions
- **Transitive cone**: 87 functions (truncated from 120+ due to size limit)
- **Max depth reached**: 5

## Capabilities Exercised
| Capability | Direct | Transitive | Functions |
|------------|--------|------------|-----------|
| combat | 8 | 42 | damage, update_pos, make_corpse, ... |
| character_state | 3 | 18 | get_char_world, char_from_room, ... |
| output | 1 | 12 | send_to_char, act, ... |
| persistence | 0 | 5 | save_char_obj, log_string, ... |

**Cross-Capability Calls**: 4 different capability groups exercised

## Global State Touches
- **Direct**: `gsn_backstab`, `gsn_trip` (combat skill globals)
- **Transitive**: `player_list`, `object_list`, `room_array` (world state)

## Side Effects
| Category | Direct | Transitive | Confidence |
|----------|--------|------------|------------|
| Messaging | send_to_char, act | 12 functions | Exact |
| Persistence | - | save_char_obj, log_string | Exact |
| State Mutation | damage, update_pos | 23 functions | Exact |
| Scheduling | - | event_dispatch | Heuristic |

## Complexity & Risk Assessment
- **Call Cone Size**: Large (87 functions, truncated)
- **Capability Span**: 4 groups (moderate cross-cutting)
- **State Mutation**: High (23 functions mutate state)
- **Side Effect Scope**: Messaging, persistence, state, scheduling
- **Risk Level**: HIGH (complex behavior, wide impact, requires careful testing)
```

---

## 3. Compare Entry Points

### Prompt Name: `compare_entry_points`

**Description**: Compare multiple entry points (commands, spells, special procedures) to identify shared dependencies, unique functionality, and potential refactoring opportunities.

**Parameters:**
```typescript
{
  entry_point_names: string[]  // 2+ entry point names (e.g., ["do_look", "do_examine"])
}
```

**Generated Messages:**
```typescript
[
  {
    "role": "user",
    "content": "I want to compare these entry points: {entry_point_names}. Please identify:\n\n1. Shared dependencies (functions both call)\n2. Unique dependencies (functions only one calls)\n3. Capability overlap (which capabilities each exercises)\n4. Potential for code reuse or refactoring"
  },
  {
    "role": "assistant",
    "content": "I'll compare {entry_point_names} by analyzing their call cones and capability footprints. This will reveal opportunities for consolidation or highlight their distinct roles.\n\nGathering data..."
  }
]
```

**Workflow Steps:**
1. For each entry point:
   - `search(query=name)` → entity_id <!-- spec 005: search replaces resolve_entity -->
   - `get_behavior_slice(entity_id, max_depth=5)` → Call cone
   - `get_entry_point_info(entity_id)` → Capabilities exercised
2. Compute intersection (shared) and set differences (unique) across call cones
3. Compare capability footprints

**Example Output:**
```markdown
# Comparison of `do_look` vs. `do_examine`

## Entry Point Overview
| Entry Point | Signature | Direct Callees | Transitive Cone | Capabilities |
|-------------|-----------|----------------|-----------------|--------------|
| do_look | void do_look(Character *ch, String argument) | 8 | 42 | room_management, character_state, output |
| do_examine | void do_examine(Character *ch, String argument) | 6 | 35 | item_inspection, character_state, output |

## Shared Dependencies (15 functions)
Functions called by BOTH entry points:
- `get_char_world` (character lookup)
- `send_to_char` (output)
- `act` (messaging)
- `one_argument` (parsing)
- [...]

## Unique to `do_look` (27 functions)
Functions ONLY called by `do_look`:
- `show_room_description` (room display)
- `show_exits` (exit listing)
- [...]

## Unique to `do_examine` (20 functions)
Functions ONLY called by `do_examine`:
- `show_item_details` (item inspection)
- `get_item_condition` (condition checking)
- [...]

## Capability Overlap
| Capability | do_look | do_examine | Overlap |
|------------|---------|------------|---------|
| character_state | 12 | 10 | 8 shared |
| output | 18 | 15 | 12 shared |
| room_management | 15 | 0 | 0 shared |
| item_inspection | 0 | 18 | 0 shared |

## Refactoring Opportunities
1. **Shared Dependency Core** (15 functions): Consider extracting common parsing/output logic into shared utility
2. **Distinct Purposes**: `do_look` focuses on room management, `do_examine` on item inspection — low consolidation potential
3. **Output Overlap**: Both use similar messaging patterns — could unify output formatting

## Risk Assessment
- **Minimal overlap** (15/62 unique functions shared)
- **Distinct capability domains** (room_management vs. item_inspection)
- **Recommendation**: Keep separate; low refactoring value
```

---

## 4. Explore Capability

### Prompt Name: `explore_capability`

**Description**: Explore a capability group's structure, dependencies, entry points, and architectural role.

**Parameters:**
```typescript
{
  capability_name: string
}
```

**Generated Messages:**
```typescript
[
  {
    "role": "user",
    "content": "I want to understand the {capability_name} capability group. Please explain:\n\n1. What it does (purpose and scope)\n2. Its functions and organization\n3. What it depends on (other capabilities)\n4. What depends on it (reverse dependencies)\n5. Entry points and user-facing features\n6. Hotspots and complexity"
  },
  {
    "role": "assistant",
    "content": "I'll analyze the {capability_name} capability using the documentation server. This will reveal its architectural role, dependencies, and complexity.\n\nGathering capability data..."
  }
]
```

**Workflow Steps:**
1. `get_capability_detail(capability_name, include_functions=false)` → Overview + dependencies
2. `list_entry_points(capability=capability_name)` → Entry points
3. `get_hotspots(metric="fan_in", capability=capability_name, limit=10)` → Most-called functions
4. `get_hotspots(metric="bridge", capability=capability_name, limit=10)` → Cross-capability bridges
5. `compare_capabilities(capabilities=[capability_name, ...dependent_caps])` → Dependency analysis

**Example Output:**
```markdown
# Exploration of `combat` Capability

## Overview
**Type**: Domain
**Description**: Combat mechanics including damage, death, corpses, and positioning
**Function Count**: 127
**Stability**: Stable
**Doc Quality**: 95 high, 25 medium, 7 low
<!-- spec 005: doc_quality_dist no longer in server responses; agent would need to derive this from brief/details presence -->

## Dependencies (Outgoing)
| Target Capability | Edge Type | Call Count | Purpose |
|-------------------|-----------|------------|---------|
| character_state | requires_core | 342 | Character attribute access, state queries |
| output | requires_projection | 156 | Combat messages, damage notifications |
| persistence | requires_infrastructure | 45 | Death logging, corpse persistence |
| utility | uses_utility | 89 | Random numbers, string formatting |

## Reverse Dependencies (Incoming)
| Source Capability | Edge Type | Call Count |
|-------------------|-----------|------------|
| magic | requires_core | 203 |
| special_procedures | requires_core | 78 |
| commands | requires_core | 134 |

## Entry Points (12 total)
- `do_kill` — Initiate combat
- `do_flee` — Escape combat
- `do_backstab` — Rogue attack
- [...]

## Hotspots (Most-Called Functions)
| Function | Fan-In | Fan-Out | Role |
|----------|--------|---------|------|
| damage | 23 | 8 | Core damage application |
| update_pos | 31 | 4 | Position management after hit/death |
| check_hit | 18 | 12 | Hit/miss calculation |
| [...]

## Bridge Functions (Cross-Capability)
| Function | Connects To | Role |
|----------|-------------|------|
| damage | character_state, output, persistence | Damage application with state updates, messaging, logging |
| [...]

## Architectural Role
- **Core domain capability**: Central to game mechanics
- **High coupling**: 342 calls to character_state (unavoidable for combat logic)
- **Output-heavy**: 156 calls to output (combat is message-intensive)
- **Stable design**: Well-documented (95/127 functions high quality)

## Complexity Assessment
- **Size**: Large (127 functions)
- **Coupling**: High (depends on 4 capabilities, depended on by 3)
- **Hotspots**: 3 functions with fan-in > 20 (damage, update_pos, check_hit)
- **Risk**: Moderate (stable but central; changes ripple widely)
```

---

## Prompt Naming Convention

- **Verb + Object**: `explain_entity`, `analyze_behavior`, `explore_capability`
- **Action-oriented**: Prompts describe what the AI will do

---

## Prompt Composition

All prompts follow this structure:
1. **User message**: States the goal and expected deliverables
2. **Assistant message**: Describes the workflow and confirms understanding

The AI assistant then executes the workflow using the documentation server's tools and resources, synthesizing results into a coherent analysis document.

---

## Extensibility (V2)

Future prompts may include:
- `migrate_entity` — Analyze migration strategy for an entity
- `trace_data_flow` — Follow data through call chains
- `find_similar_code` — Semantic search for code patterns
- `suggest_refactoring` — Identify refactoring opportunities

These are placeholders for V2 capabilities when subsystem documentation and additional analysis tools are available.
