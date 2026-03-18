# Migration Planning — Next Steps

> Written after completing Discussion Rounds 1–3. All architectural open items
> in CONSENSUS.md are resolved. The discussion phase is complete.

---

## Where we are

Three rounds of agent discussion plus human decisions have produced a fully
settled CONSENSUS.md covering: workflow/process, migration ordering (5 waves),
typeclass strategy, object strategy, messaging signature, timing architecture,
spell system approach, spec granularity, fidelity definition, and Wave 1 scope.

There are **no remaining open items**.

---

## What comes next (in priority order)

### 1. Wave 0 — Formalize substrate decisions

The typeclass strategy (§3.1–3.3), timing model (§3.5), and handler patterns are
decided but not yet written as formal decision records. Options:

- **Lightweight:** Treat CONSENSUS.md §3 as the decision record and move
  straight to contracts. The decisions are already detailed enough.
- **Formal:** Write brief ADR-style documents in `docs/migration/decisions/`.
  Useful if other contributors need standalone references.

Recommendation: skip standalone ADRs — CONSENSUS.md is the source of truth.
Go directly to contract writing.

### 2. Bootstrap the contract registry

Create `migration/contracts/` with skeleton YAML files for the seven Wave 1
infrastructure pieces (format defined in CONSENSUS.md §1.3):

| Contract ID | Name | Notes |
|-------------|------|-------|
| INF-STAT-001 | stat_pipeline | Aggregation order, base/effective split, formula hooks |
| INF-MSG-001 | messaging | `game_act()` signature, token resolution, visibility, audience routing |
| INF-TIME-001 | timing | RuntimeScheduler, pulse phases, phase ordering |
| INF-POS-001 | position | Position enum, command gating rules, state transitions |
| INF-ELOOKUP-001 | entity_lookup | `N.keyword` syntax, partial matching, return types |
| INF-DATA-001 | data_tables | Race/class/skill/level tables, lookup API |
| INF-WORLD-001 | world_lifecycle | Area reset skeleton, room/exit loading, stub scope |

These start as `status: draft` skeletons. The spec-writing phase fills them in.

### 3. Write the three "must implement first" specs

CONSENSUS.md §2.2 identifies three systems that must be implemented (not stubbed)
before downstream specs can be written:

1. **Stat pipeline** — aggregation order affects combat formulas everywhere
2. **Messaging (`game_act()`)** — exact output contracts needed for every spec
3. **Timing (`RuntimeScheduler`)** — ordering guarantees shape every timed system

Each gets a full implementation dossier with formulas, constants, message
templates, state reads/writes, preconditions/postconditions, and test cases
(per §4.3). These are the first specs to go through the audit step.

### 4. Write remaining Wave 1 infrastructure specs

After the three critical specs, write dossiers for:

- Position system (enum, transitions, command gating)
- Entity lookup (N.keyword parser, partial matching, room/inventory/equipment
  search scopes)
- Data tables (race/class/skill/level registries — stub-safe, API-only)
- World lifecycle skeleton (area loading, reset stubs — stub-safe for Wave 1)

### 5. Wave 1 vertical slice integration spec

Once all seven infrastructure contracts are accepted, write the integration
spec that defines the Wave 1 acceptance test: a player logs in, navigates,
picks up items, checks score, says something, sleeps/wakes, and exercises
every in-scope action from §2.3.

### 6. MCP doc server enhancements (parallelizable)

The doc server roadmap (`docs/migration/doc_server_roadmap.md`) has V2/V3
enhancements that directly support spec writing:

- **V2:** `explore_entity` composite tool, `get_behavior_slice`, enhanced
  `get_callers`/`get_callees` with depth control
- **V3:** Capability-aware search, cross-subsystem dependency queries

These can be built in parallel with spec writing. The spec agents benefit from
better MCP tools, but the current V1 toolset is sufficient to start.

---

## Decision needed from human

Before starting contract/spec work: **where does the migration repo live?**

Options:
- A new directory in this workspace (e.g., `migration/`)
- The existing Evennia project repo (separate workspace)
- A dedicated migration repo

The contract registry and specs need a home.
