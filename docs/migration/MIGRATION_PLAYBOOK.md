# Migration Playbook

> **Purpose:** Consolidated guide for agents and developers working on the
> Legacy MUD → Evennia migration. Combines the MCP server reference, agent
> workflow descriptions, wave structure, and contract registry plan into one
> document. Intended to travel with the migration to the new Evennia repository.
>
> **Companion documents:** [CONSENSUS.md](CONSENSUS.md) (settled architectural
> decisions), [og-legacy-systems.md](og-legacy-systems.md) (legacy architecture
> reference), [migration-challenges.md](migration-challenges.md) (engineering
> collision points), five `EVENNIA_*.md` guides.

---

## 1. Project Overview

A legacy DikuMUD/ROM-style C++ MUD (~90 KLOC) is being migrated to an
Evennia-based Python game server. The goal is **player-visible behavioral
parity** — same commands, formulas, output text, and timing feel — while
adopting Evennia-native patterns (persistent DB, typeclasses, hook-driven
extension).

The legacy codebase is not directly available to migration agents. Instead,
all legacy research is conducted through the **MCP Documentation Server**, a
read-only reference layer that exposes ~5,300 code entities, ~25,000
dependency edges, LLM-generated documentation, behavioral analysis tools, and
curated system narrative documents.

---

## 2. MCP Server — What It Provides

The MCP server is the sole authoritative source on legacy implementation. It
runs from the `legacy-projects` repository and is accessed via stdio/JSON-RPC
by agents in the Evennia repository.

### 2.1 Tools (15)

**Entity Lookup:**
- `get_entity` — full entity record by ID (docs, source location, metrics,
  optional source code and graph neighbors)
- `get_source_code` — source code with configurable context lines

**Search:**
- `search` — 5-channel hybrid retrieval (doc/symbol semantic + doc/symbol
  keyword + trigram), floor filtering, cross-encoder reranking

**Graph Navigation:**
- `get_callers` / `get_callees` — call graph traversal, depth 1–3
- `get_dependencies` — filtered by relationship type and direction
- `get_class_hierarchy` — base and derived classes
- `get_related_entities` — all direct neighbors grouped by edge type

**Behavioral Analysis:**
- `get_behavior_slice` — transitive call cone with capabilities touched,
  globals used, categorized side effects
- `get_state_touches` — direct + transitive global variable usage
- `explain_interface` — behavioral contract: signature, mechanism,
  caller-derived contract, preconditions, calling patterns

**Capabilities:**
- `list_capabilities` — all 30 capability groups
- `get_capability_detail` — group definition, typed dependency edges,
  entry points
- `compare_capabilities` — shared/unique dependencies between 2+ groups
- `list_entry_points` — `do_*`, `spell_*`, `spec_*` functions
- `get_entry_point_info` — which capabilities an entry point exercises

### 2.2 Resources (9)

| URI | Content |
|-----|---------|
| `legacy://capabilities` | All capability groups |
| `legacy://capability/{name}` | Capability detail |
| `legacy://entity/{entity_id}` | Full entity record |
| `legacy://file/{path}` | Entities in a source file |
| `legacy://stats` | Server statistics |
| `legacy://components` | Index of all 29 system component docs — frontmatter metadata (id, name, kind, layer, depends_on, depended_on_by) |
| `legacy://component/{id}` | Full markdown content for a system component doc |
| `legacy://helps` | Index of all 582 in-game help entries — keywords, category, level, text length |
| `legacy://help/{index}` | Full text of a help entry (color codes stripped), retrieved by integer index |

The component resources provide architectural narrative context — what each
system does, how it works, its dependencies. These are curated documents, not
raw source analysis. Use them to understand how a feature fits into the
broader system before writing specs.

The help entry resources expose the legacy MUD's in-game help system (582
entries across 18 categories: spell, skill, misc, wizgen, etc.). Use them to
understand player-facing behavior descriptions and command syntax.

### 2.3 Prompts (5)

| Prompt | Purpose |
|--------|---------|
| `explain_entity` | Entity explanation workflow |
| `analyze_behavior` | Behavioral analysis with call cone and side effects |
| `compare_entry_points` | Compare entry points for shared dependencies |
| `explore_capability` | Explore a capability group's architecture |
| `research_feature` | Feature research for migration spec writing — combines code tools with component resources |

### 2.4 Entity IDs

Entity IDs use `{prefix}:{7hex}` format (e.g., `fn:a1b2c3d`). Prefixes: `fn`
(function/define), `cls` (class/struct), `var` (variable), `file` (file),
`sym` (other). The `search` tool is the **sole path** from human-readable text
to entity IDs.

---

## 3. Agent Roles and Workflows

### 3.1 Planning Agent

**Job:** Produce the migration manifest — chunk ordering, dependency
annotations, integration contracts.

**Key MCP usage:**
- `legacy://components` for the system inventory and dependency graph
- `legacy://component/{id}` for system-level complexity assessment
- `list_capabilities` / `get_capability_detail` for code-level complexity
  signals (function counts, edge density)
- `compare_capabilities` for cross-system coupling analysis

### 3.2 Spec-Writing Agent

**Job:** Produce implementation dossiers detailed enough that an implementing
agent can work from them alone, without legacy codebase access.

**Primary workflow** (see `research_feature` prompt):
1. `search` for the entity → get entity ID
2. `get_entity` for documentation, `get_source_code` for implementation
3. `get_behavior_slice` + `get_state_touches` for side effects and state
4. `explain_interface` for the behavioral contract
5. `legacy://components` to identify the parent system
6. `legacy://component/{id}` for architectural context

**Every spec must include** (per CONSENSUS.md §4.3):
- Exact formulas with coefficients (not "matching the original")
- Timing constants with units
- Exact message strings/templates with `game_act()` tokens
- State reads and writes, preconditions/postconditions
- Ordering rules (what happens before what)
- Failure/edge cases (minimum 3–5)
- Test cases derived from data contracts

### 3.3 Auditor Agent

**Job:** Check each spec for completeness, consistency, fidelity, and
testability.

**Key MCP usage:**
- `get_source_code` + `get_entity` to verify claimed formulas and constants
  against actual legacy implementation
- `explain_interface` to verify interface contracts
- Cross-reference against the contract registry for inter-spec consistency

**Per-spec audit checks:**
- Every formula has exact coefficients
- Every message template uses correct `game_act()` tokens
- State mutations are explicit (reads and writes enumerated)
- Edge cases covered (minimum 3–5)
- Test cases present and derived from data contracts
- No contradictions with previously accepted specs or contracts

**Per-wave audit:** Additional coherence check across all specs in the wave.

---

## 4. Wave Structure and Ordering

Five migration waves, with strict sequencing constraints. Full details in
CONSENSUS.md §2.1–2.3.

| Wave | Focus |
|------|-------|
| **0** | Substrate decisions (settled — see CONSENSUS.md §3) |
| **1** | Foundational infrastructure: stat pipeline, messaging, timing, position, entity lookup, data tables, world lifecycle |
| **2** | Thin vertical slice: move/look/display, minimal objects, minimal communication |
| **3** | World lifecycle: resets, NPC/object/corpse lifecycle, persistence |
| **4** | Heavy mechanics: affects, combat, magic, skills progression |
| **5** | Higher systems: NPC behavior, quests, economy, clans/PvP, admin/builder tools |

**Strictly sequential:** Messaging before any player-facing feature. Stat
pipeline before affects/combat/magic. World reset lifecycle before NPC
behavior. Position rules before command behavior specs.

**Stub-vs-implement rule** (CONSENSUS.md §2.2): Three systems **must be
implemented** before downstream specs — stat pipeline, messaging
(`game_act()`), and timing (`RuntimeScheduler`). The remaining four Wave 1
systems are stub-safe (frozen API, deferred implementation).

**Wave 1 scope** (CONSENSUS.md §2.3): Login → navigate → inspect → get/drop
items → inventory → score → say → sleep/wake. Pre-created test characters; no
character creation, no combat, no channels.

---

## 5. Contract Registry

Infrastructure contracts are the shared interface artifacts that downstream
specs depend on. Format defined in CONSENSUS.md §1.3.

### 5.1 Wave 1 Contracts

| Contract ID | Name | Priority |
|-------------|------|----------|
| INF-STAT-001 | stat_pipeline | Must implement first |
| INF-MSG-001 | messaging | Must implement first |
| INF-TIME-001 | timing | Must implement first |
| INF-POS-001 | position | Stub-safe |
| INF-ELOOKUP-001 | entity_lookup | Stub-safe |
| INF-DATA-001 | data_tables | Stub-safe |
| INF-WORLD-001 | world_lifecycle | Stub-safe |

### 5.2 Contract Format

Each contract is a YAML file in `contracts/` with fields:
`contract_id`, `name`, `version`, `status` (draft/accepted/revised),
`chunk`, `summary`, `depends_on`, `used_by`, `apis` (with signatures,
preconditions, postconditions, behavioral guarantees),
`acceptance_tests`, `downstream_impact`, `changelog`.

See CONSENSUS.md §1.3 for the full schema.

---

## 6. Immediate Next Steps

1. **Bootstrap the contract registry** — create `contracts/` with seven
   skeleton YAML files for the Wave 1 infrastructure contracts.

2. **Write the three "must implement first" specs:**
   - Stat pipeline — aggregation order, base/effective split, formula hooks
   - Messaging (`game_act()`) — token resolution, visibility, audience routing
   - Timing (`RuntimeScheduler`) — pulse phases, phase ordering

3. **Write remaining Wave 1 infrastructure specs:**
   - Position system (enum, transitions, command gating)
   - Entity lookup (`N.keyword` parser, partial matching, search scopes)
   - Data tables (race/class/skill/level registries — stub-safe, API-only)
   - World lifecycle skeleton (area loading, reset stubs)

4. **Write Wave 1 vertical slice integration spec** — the acceptance test
   exercising all in-scope actions from CONSENSUS.md §2.3.

---

## 7. Key Architectural Decisions (Summary)

All decisions are settled. CONSENSUS.md is the source of truth. Quick reference:

- **Typeclass strategy:** Split PC/NPC with shared `LivingMixin` (§3.1)
- **Object strategy:** Single `GameItem` typeclass with `item_type` enum (§3.2)
- **Room/Exit:** Standard subclasses with minimal extensions (§3.3)
- **Messaging:** Custom `game_act()` with flat positional args, legacy token
  vocabulary, visibility filtering (§3.4)
- **Timing:** Global `RuntimeScheduler` with phase-locked subsystem updates,
  legacy pulse ordering (§3.5)
- **Spells:** Framework + pattern catalog + bespoke exception catalog (§3.6)
- **Fidelity:** Player-visible parity — exact for output/formulas/timing,
  statistical for RNG, tolerance for sub-tick noise (§4.1)
