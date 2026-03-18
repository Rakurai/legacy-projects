# Discussion Prompt: Migration Planning and MCP Server Design Review

> **For:** A Claude session reviewing the attached documents.
>
> **Attached documents:**
> - `doc_server_roadmap.md` — what the MCP documentation server provides across
>   four versions (V1 live, V2 designed, V3–V4 intent)
> - `og-legacy-overview.md` — architecture overview of the legacy C++ MUD codebase
> - `migration-challenges.md` — specific engineering challenges in faithfully
>   recreating the legacy game on Evennia
> - `speculative_agent_reqs.md` — agent requirements for consuming the MCP server
>
> **Goal:** Produce a structured analysis that informs migration planning
> decisions. The output should be concrete recommendations, not abstract
> observations. Where trade-offs exist, state them plainly.

---

## Context

We are migrating a ~90 KLOC C++ MUD (Diku/ROM derivative) to Evennia (Python).
The migration goal is **90%+ fidelity to the original player-facing experience**
— combat timing, output text, spell effects, NPC behavior, and skill mechanics
must be indistinguishable from the original. The internal architecture will use
clean Evennia patterns instead of Diku internals.

An MCP documentation server (V1 live, V2 in progress) exposes the legacy codebase
as a structured knowledge store: entity-level documentation, dependency graphs,
behavioral analysis, capability groupings, and (in V2) system-level narrative
documentation. This server is the primary tool that agents use to understand the
legacy system when producing specs and plans.

Two agent types will drive the migration:
- **Spec-creating agents** research individual features and produce implementation
  specs detailed enough for a coding agent to work from without legacy codebase
  access.
- **System planning agents** navigate the architecture to decide what to build,
  in what order, and with what dependencies.

---

## Topics for Analysis

### 1. MCP Server: What Do the Agents Actually Need?

Review the tools and data described in `doc_server_roadmap.md` against the agent
workflows and information needs in `speculative_agent_reqs.md` and the challenges
in `migration-challenges.md`.

Address:

- **Coverage gaps:** Are there questions a spec-creating agent will need answered
  that no current or planned tool can answer? Pay particular attention to the
  challenges in `migration-challenges.md` — for each challenge, can the agent get
  what it needs from V1+V2 tools, or is something missing?

- **Noise reduction:** The V1 server has 19 tools. The speculative requirements
  propose adding more (V2: 5 new + 2 enhanced, plus proposed tools like
  `explore_entity` and `explain_interface`). Is there a risk of tool sprawl where
  agents must make many calls to assemble what they need? Should some tools be
  consolidated or should composite tools exist for common workflows?

- **Boundary discipline:** The MCP server is a factual reference layer — it must
  not shift migration concerns to itself (no migration prescriptions, no target
  architecture guesses). But some information the agents need is inherently
  interpretive (e.g., "what is the effective contract of this function?" or "what
  user-visible behavior must be preserved?"). Where is the line between factual
  data the server provides and interpretive work the agent must do?

- **V3/V4 priority:** Given the fidelity goal, how important is in-game help text
  (V3) and builder's guide data (V4) for producing faithful specs? Should these
  be prioritized earlier than the roadmap suggests, or are V1+V2 sufficient for
  the bulk of spec work?

### 2. Agent Workflow: Iterative, Hierarchical, or Both?

The migration involves ~20 subsystems with complex dependencies. A single agent
session cannot hold the full context. The workflow must be decomposed.

Address:

- **Planning → spec → implementation pipeline:** Should a planning agent produce
  a migration plan (system ordering, dependency graph, integration contracts)
  that is then consumed by per-system spec-creating agents? Or should spec agents
  discover their own scope and dependencies as they go?

- **Iteration vs. one-pass:** Should specs go through revision cycles? If so,
  what triggers a revision — new information from adjacent system specs, feedback
  from an implementation agent, or explicit review?

- **Auditor agent:** Should a separate auditor agent review specs against fidelity
  criteria before they go to implementation? What would an auditor check?
  Possibilities: completeness (did the spec cover all user-visible behaviors?),
  consistency (does this spec's interface match what adjacent specs expect?),
  fidelity (does the spec preserve legacy behavior or inadvertently change it?).
  Is the auditor per-spec, per-system, or per-migration-wave?

- **Cross-system contract management:** Multiple systems share interfaces (the
  stat computation pipeline, the messaging layer, the affect system's hooks).
  How do we prevent specs from making incompatible assumptions about shared
  interfaces? Is there a "contract registry" that specs contribute to and
  consume from?

### 3. Migration Ordering and Bootstrapping

Review `migration-challenges.md` §12 (cross-cutting concerns) and the subsystem
dependency graph implied by the component docs.

Address:

- **Infrastructure-first dependencies:** Several challenges identify
  infrastructure that must exist before any game system can be built: the
  messaging layer (`act()` equivalent), the stat computation pipeline (affects +
  equipment + base stats), the position system, and the area reset mechanism.
  What is the minimum set of infrastructure that must be implemented before the
  first game system (e.g., combat) spec can be written?

- **System ordering:** Given the dependency graph (game engine → character data →
  affect system → combat → magic → skills → quests, etc.), what is a reasonable
  wave structure? Which systems are independent enough to be worked on in
  parallel? Which must be strictly sequential?

- **Stub vs. full implementation:** When a system depends on an interface that
  hasn't been built yet (e.g., combat depends on the affect system), should the
  spec assume a stub/interface contract, or should the dependency be fully
  implemented first? What are the risks of each approach?

### 4. Fidelity Verification

The migration goal is that a player cannot tell the difference between the
original and the reimplementation. How do we verify this?

Address:

- **What counts as "indistinguishable"?** Output text must match. Combat timing
  must match. But what about edge cases — rounding differences in damage
  calculations, slightly different RNG distributions, microsecond timing
  differences in tick-based events? Where is the fidelity threshold?

- **Verification method:** Can we extract expected behaviors from the legacy
  system (input/output traces, combat logs, spell effect sequences) and use them
  as test cases? Does the MCP server's behavioral analysis (V1 behavior slices,
  side-effect markers) help here, or is a different kind of artifact needed?

- **Regression across specs:** When spec B is written after spec A, how do we
  ensure B doesn't inadvertently break the contract A established? Is there a
  role for automated contract testing driven by spec artifacts?

### 5. Spec Granularity and Scope

Address:

- **What goes in a spec?** Should a spec for "the combat system" cover the
  entire damage pipeline, group combat, flee/recall, and death processing in one
  document? Or should it be decomposed into smaller specs (hit resolution,
  damage calculation, death processing, group mechanics) that can be implemented
  and verified independently?

- **Spec-to-implementation ratio:** Should one spec produce one implementation
  unit (one PR, one module)? Or can a spec describe a larger scope that is
  implemented incrementally?

- **Data contract emphasis:** Given the fidelity goal, should specs emphasize
  data contracts (exact stat formulas, exact timing values, exact output strings)
  more heavily than behavioral descriptions? A spec that says "damage is
  calculated like the original" is useless; a spec that says "damage = dice_roll
  * weapon_skill_modifier * enhanced_damage_bonus, capped at 1000, with sanctuary
  halving applied after resistance" is verifiable.

### 6. The Shared Infrastructure Problem

Several systems in `migration-challenges.md` are identified as cross-cutting
dependencies that many other systems rely on.

Address:

- **Messaging layer:** Nearly every system needs the `act()` equivalent. Should
  the messaging layer be specified and implemented as a standalone infrastructure
  spec before any game system specs begin? What is its minimal viable surface?

- **Stat computation pipeline:** Combat, skills, magic, and affects all query
  "effective stat" values that aggregate base + equipment + affects + remort
  bonuses. Should the stat pipeline be a standalone spec, or is it part of the
  character data model spec?

- **Position system:** Almost every command checks character position. Should
  position enforcement be part of the command interpreter spec, the character
  data model spec, or its own spec?

- **Are there other infrastructure pieces** not called out in the challenges
  document that would block spec work if they don't exist?

---

## Output Format

For each topic, provide:

1. **Assessment** — your analysis of the current state (what works, what's
   missing, what's risky)
2. **Recommendation** — a concrete proposal (not "consider doing X" but "do X
   because Y")
3. **Open questions** — anything you cannot resolve from the provided documents
   that needs human input or additional investigation

Where recommendations conflict across topics (e.g., "start with infrastructure"
vs. "start with the highest-value game system"), call out the tension and state
which you'd prioritize and why.
