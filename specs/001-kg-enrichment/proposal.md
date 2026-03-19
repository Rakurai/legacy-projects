# Knowledge Graph Proposal: From Capability Groups to Evidence-Driven Graph Enrichment

> **Status:** Proposal. Synthesizes decisions from multi-round agent discussions,
> corpus-wide data surveys, and external feedback evaluation. Awaiting review
> before implementation begins.
>
> **Supersedes:** [CG.md](../../projects/classify_fns/CG.md) as the strategic
> direction for how the legacy codebase is modeled and exposed to consuming agents.
> CG.md's chunk registry, readiness levels, and dossier template remain valid
> downstream artifacts; only the canonical organizing structure changes.
>
> **See also:**
> [migration-challenges.md](migration-challenges.md) ·
> [CONSENSUS.md](analysis/CONSENSUS.md) ·
> [generated-docs-additions.md](analysis/generated-docs-additions.md) ·
> [doc_server_roadmap.md](doc_server_roadmap.md) ·
> [DESIGN_v2.md](../../mcp/doc_server/specs/v2/DESIGN_v2.md) ·
> [speculative_agent_reqs.md](speculative_agent_reqs.md)

---

## 1. Migration Challenge Summary

The legacy codebase is a Diku/ROM-derivative C++ MUD server (~90 KLOC): a
single-threaded main loop where the world is ephemeral, state lives in memory,
and a global tick drives everything in lockstep. The migration target is Evennia,
a Django+Twisted Python framework where the world is persistent in a database,
state is transparently persisted, and behavior is event-driven with no global tick.
The full tension is documented in [migration-challenges.md](migration-challenges.md).

Consuming agents — both spec-creating and system-planning — never read the legacy
source directly. The MCP documentation server is their only window into the
codebase. Everything an agent can know about the legacy system must be queryable
through the server's tool surface. The quality of every migration spec depends on
the quality and structure of what the server exposes.

The corpus available to the server today:

| Artifact | Scale |
|----------|-------|
| Code entities (Doxygen-parsed) | 5,305 (2,365 functions, 2,369 variables, 136 classes/structs, 82 defines, 11 enums) |
| Graph nodes (NetworkX multigraph) | 14,507 |
| Graph edges (typed) | 44,544 — `uses` (16,683), `calls` (9,875), `represented_by` (9,710), `contained_by` (6,567), `includes` (1,656), `inherits` (53) |
| LLM-generated entity docs | 5,295 entries |
| Entities with rationale | 4,387 (83% of documented entities) |
| Entities with usages dict | 2,889 (24,803 individual caller entries) |
| V2 curated system docs | 29 component files with YAML frontmatter |

The server's information surface grows across four versions
([doc_server_roadmap.md §2](doc_server_roadmap.md)): Implementation (V1, live),
Conceptual (V2, designed), User-Facing (V3, intent), Specification (V4, intent).
This proposal concerns how the data underlying all four layers is structured and
enriched.

---

## 2. Why Single-Assignment Capability Groups Failed

The current model assigns each of 852 transitive callees to exactly one of 30
capability groups ([capability_defs.json](../../artifacts/capability_defs.json)).
Each group is typed as `domain`, `policy`, `projection`, `infrastructure`, or
`utility`. The model works well enough for coarse migration planning — the chunk
registry ([CG.md §12.3](../../projects/classify_fns/CG.md)) uses it
successfully — but breaks down under scrutiny as a canonical organizing structure.

### The evidence

**Cross-domain usage is pervasive.** A corpus-wide survey found 126 locked
functions called from 2+ different capability groups. `stc` (send-to-character)
is called from 22 of 30 groups, with only 16% of calls originating in its
assigned group. `IS_IMMORTAL` is called from 18 groups. These are not edge
cases — they are the norm for infrastructure-level functions.

**Mechanism patterns are multi-dimensional.** 62% of the 656 matched locked
functions show 2+ mechanism patterns in their documentation briefs (e.g., a
function that does both state validation and output formatting). Single-group
assignment forces a choice that discards real information.

**Categories conflate domain and mechanism.** Groups like `admin`, `flags`, and
`persistence` name mechanisms or policy layers, not domains. Groups like `combat`,
`magic`, and `quests` name domains. Groups like `output` and `string_ops` name
services. These are not the same kind of thing, yet they participate equally in
dependency analysis and wave computation.

**84% of entities are invisible.** The capability model classifies only 852 of
5,305 entities. Variables (2,369), classes/structs (136), defines (82), and enums
(11) have no group assignment. The `Character` class has 1,060 incoming `uses`
edges and 90 `contained_by` members — it is arguably the most important entity in
the codebase, yet it has no capability classification.

**The audit found systematic problems.** The group-by-group audit
([GROUPS.md](../../projects/classify_fns/GROUPS.md)) identified 38 suspects
across 17 groups, with several groups flagged for splits or merges. Every group
containing infrastructure-level functions had misplacement issues because the
assignment question ("which one group does this belong to?") has no good answer
for cross-cutting entities.

### Conclusion

Capability groups remain useful as one **projection** of the knowledge graph —
a way to answer "show me the combat-related functions" — but cannot serve as the
canonical organizing structure. The graph itself, with its typed edges and
multi-dimensional entity attributes, is the canonical structure. Groups become a
derived view.

---

## 3. What We Have Today: Evidence Inventory

Before proposing additions, an honest accounting of what already exists.

### 3.1 Code graph

The Doxygen-parsed code graph
([code_graph.gml](../../artifacts/code_graph.gml)) is a NetworkX MultiDiGraph
with 14,507 nodes and 44,544 typed edges. Node types include `file` (4,678),
`body` (4,370), `member` (4,328), `decl` (662), and `compound` (469). The six
edge types capture structural containment (`contained_by`, `represented_by`),
behavioral dependencies (`calls`, `uses`), file relationships (`includes`), and
type hierarchies (`inherits`).

This graph is already a knowledge graph backbone. It captures who calls whom, who
uses what data, what belongs to which file or class, and how types relate. What it
lacks is semantic annotation — the edges say "A calls B" but not "A calls B to
apply damage after a successful hit roll."

### 3.2 Generated documentation

The doc_gen pipeline's four-pass LLM annotation produced 5,295 per-entity
documentation entries ([generated_docs/](../../artifacts/generated_docs/)). Each
entry includes fields generated from distinct evidence and serving distinct roles
(see [generated-docs-additions.md](analysis/generated-docs-additions.md) for the
full analysis):

| Field | What it encodes | Coverage |
|-------|-----------------|----------|
| `brief` + `details` | Implementor's view: what the function does and how | 5,295 entries |
| `rationale` | Caller's view: synthesized from usages evidence | 4,387 entities (83% of documented) |
| `notes` | Behavioral anomalies, invariants, edge cases | ~83% of entities |
| `usages` | Raw call-site evidence: per-caller usage descriptions | 2,889 entities (24,803 caller entries) |
| `state` | Doc generation pass: `refined_summary`, `generated_summary`, `extracted_summary` | All entries |

The critical insight from [generated-docs-additions.md §5](analysis/generated-docs-additions.md):
these four fields together constitute a near-complete behavioral contract for
well-documented functions. `brief`+`details` is the implementor's view,
`rationale` is the consumer's view, `usages` is the evidence layer, `notes` is
the risk layer. The MCP server currently treats all of them as opaque text
columns — stored, full-text searched, and returned, but not structurally
exploited.

### 3.3 Capability artifacts

30 groups with typed dependency edges, 852 locked functions, 195 inter-group
dependency edges, 13 computation waves. The chunk registry
([CG.md §12.3](../../projects/classify_fns/CG.md)) derives 30 implementation
chunks classified by mode (19 native, 5 adaptation, 3 reference, 2 replacement,
1 substrate) and planning phase (B, C, D).

### 3.4 V2 component documentation

29 curated markdown files in [artifacts/components/](../../artifacts/components/)
with YAML frontmatter encoding system identity (`id`, `kind`, `layer`,
`depends_on`, `depended_on_by`) and tagged headings encoding section metadata
(`section_kind`, `grounding_status`, `narrative_role`). Stage 0 of the V2 build
pipeline ([DESIGN_v2.md §5](../../mcp/doc_server/specs/v2/DESIGN_v2.md)) is
complete. Stages 1–4 remain.

### 3.5 MCP V1 server

19 tools across entity lookup, search, graph navigation, behavioral analysis, and
capability querying. PostgreSQL + pgvector with hybrid semantic + keyword search.
Fully operational. Tool inventory in
[doc_server_roadmap.md §3](doc_server_roadmap.md).

---

## 4. The Knowledge Graph Approach

### Core thesis

The existing code graph is already a knowledge graph backbone. The proposal is not
to build a new graph but to **enrich the existing one** by:

1. Carrying through doc-derived evidence that the current build pipeline discards
2. Materializing implicit semantic relationships as explicit queryable edges
3. Computing derived attributes from graph topology + doc evidence
4. Enabling multi-label classification instead of single-assignment

### Governing principle: evidence before ontology

The external agent feedback proposed 10 semantic node types and 7 new edge types
as a starting point. Evaluation showed that only ~2 of the proposed node types
have sufficient evidence today — the rest would require speculative inference.
Edge types like `implements` and `supports` encode interpretation, not evidence.

The build order must follow **evidence cost**, not conceptual priority:

- **Step 1** costs nothing (carry existing fields through the pipeline)
- **Step 2** is pure aggregation over existing data (explode usages dicts)
- **Step 3** is graph computation over existing edges (identify data families)
- **Step 4** requires lightweight heuristics over topology + text
- **Step 5** requires clustering or LLM-assisted labeling

Each step is independently deployable, testable, and valuable. No step requires
the subsequent one. Premature steps (curated semantic node types, interpretive
edge types) are deferred until the evidence steps produce the substrate they need.

### Step 1: Carry doc fields through

The V1 build pipeline currently discards `doc_state` and does not compute derived
signals from `notes` or `rationale`. These additions require zero new LLM
inference:

| Addition | Source | Purpose |
|----------|--------|---------|
| `doc_state` column | `state` field in generated_docs | Trust signal: `refined_summary` vs `extracted_summary` tells agents which entities need source-level verification ([generated-docs-additions.md §7](analysis/generated-docs-additions.md)) |
| `notes_length` column | Character count of `notes` | Complexity proxy alongside `fan_in`, `fan_out`, and `bridge_score` — never a standalone signal, but functions with dense notes tend to have more documented quirks |
| `is_contract_seed` flag | `fan_in > threshold` AND non-null `rationale` | Marks high-fan-in entities with rich caller-derived behavioral descriptions — natural starting points for Wave 1 contract stubs ([generated-docs-additions.md §3](analysis/generated-docs-additions.md)) |
| `rationale_specificity` score | Heuristic over rationale text (length + domain-term density) | Distinguishes "facilitates various operations" from "the authoritative dispatch point for all HP-reducing effects" |

### Step 2: Explode usages into semantic edges

This is the single highest-value addition. The `usages` dict on 2,889 entities
contains 24,803 caller→callee entries where each entry is a natural-language
description of **how** the caller uses the callee. Today this is an opaque JSONB
blob on the entity row.

Materializing it as a dedicated `entity_usages` table
([generated-docs-additions.md §4](analysis/generated-docs-additions.md)):

```sql
CREATE TABLE entity_usages (
    callee_id      TEXT REFERENCES entities(entity_id),
    caller_compound TEXT,
    caller_sig     TEXT,
    description    TEXT,
    embedding      vector(768),
    PRIMARY KEY (callee_id, caller_compound, caller_sig)
);
```

This converts "A calls B" into "A calls B **to apply duration-based stat
penalties after combat hits**." The semantic dimension is what integration surface
tools need — not edge counts but behavioral descriptions of cross-boundary
calling patterns.

The inverted view (for each caller, collect all callee usage descriptions) answers
"what does this function use, and specifically why?" — qualitatively richer than
a flat callee list.

### Step 3: Derive data-family edges

From `contained_by` + `uses` patterns, identify which classes/structs are **data
families** — entities that define a conceptual domain through their member
variables and the functions that touch them. The `Character` class (1,060
incoming `uses` edges, 90 `contained_by` members) is the canonical example.

This step promotes classes/structs as first-class navigable nodes rather than
passive containers. A "data family" node gets:

- Member list (from `contained_by` edges)
- Top accessor/mutator functions (from `uses` edges, ranked by frequency)
- Subsystem distribution of users (which capability groups or subsystems touch it)
- Role in the type hierarchy (from `inherits` edges)

No new data is needed — this is a graph computation over existing edges with a
presentation layer on top.

### Step 4: Compute role tags (multi-label)

From graph topology + doc evidence, assign **derived** tags to each entity. An
entity can have multiple tags. Tags are not curated — they are computed from
observable signals:

| Tag | Signal |
|-----|--------|
| `infrastructure` | High fan-in (>20 callers), low domain-term density in brief |
| `domain_logic` | Medium fan-in, domain-specific terms in brief/rationale |
| `data_access` | Primarily `uses` edges to class members, few `calls` edges |
| `output` | References to `act()`, `stc()`, formatting functions in callees |
| `validation` | Precondition-language in notes ("must be", "requires", "should not") |
| `lifecycle` | References to creation/destruction/extraction patterns |
| `entry_point` | Matches `do_*`, `spell_*`, `spec_*` naming patterns (already known) |

Tags are stored as a JSONB array on the entity row. They are a vocabulary for
filtering and faceting, not a classification system. An entity tagged
`[infrastructure, output]` is an infrastructure-level output service — more
informative than forcing it into either the `output` group or the `runtime` group.

### Step 5: Derive intent labels

From usages clustering + rationale text, group entities by **behavioral intent**
— what callers use them for, not what they are internally.

This is where capability group responsibilities are absorbed. Each old group
becomes a query-time projection over intent labels:

- The `combat` group → entities where intent labels include `damage_delivery`,
  `hit_resolution`, `combat_state_management`
- The `affects` group → entities with `buff_application`, `debuff_application`,
  `duration_tracking`, `stat_modification`
- The `output` group → entities with `player_messaging`, `room_notification`,
  `format_rendering`

The labels are finer-grained than capability groups and an entity can have
multiple. No information is lost — the old group assignment is retained as a
`legacy_capability` field for backward compatibility with the chunk registry.

Intent labels require either embedding-based clustering over rationale/usages text
or a lightweight LLM classification pass. This is the first step that may require
new inference, which is why it comes last. It is also **non-blocking** for spec
work — Steps 1–4 plus the V2 narrative layer provide sufficient evidence for
spec-creating and auditor agents. Intent labels are additive refinement.

Operationally, clustering should be done at the **label level first**: cluster the
usage descriptions into candidate label vocabulary, then assign entities to labels.
Do not attempt to classify all 5,000+ entities in one pass — that risks
hallucinated categories.

### What NOT to do

- **Premature semantic node types.** The external feedback proposed Service,
  DataStructure, Algorithm, Protocol, etc. Only DataStructure and Service have
  clear evidence today (from `contained_by` patterns and fan-in topology
  respectively). The others require interpretive judgment that the evidence steps
  don't yet support. Defer until Step 4 tags stabilize.

- **Interpretive edge types.** `implements`, `supports`, `enforces` are opinions
  about relationships, not observations. The evidence graph should contain
  `calls`, `uses`, and usage descriptions — not pre-baked interpretations that
  constrain how agents reason.

- **Single-assignment of anything.** The entire point of the transition is that
  entities have multiple roles. Any new classification axis that forces a single
  value per entity repeats the capability group mistake.

- **Answer-oriented tool sprawl.** Tools like `get_formula`,
  `get_spell_cluster`, `estimate_complexity` embed assumptions about what agents
  will ask. General traversal tools that agents compose are more durable than
  specialized tools that guess at queries.

---

## 5. Absorbing CG.md Responsibilities

[CG.md](../../projects/classify_fns/CG.md) defines four views that the analysis
pipeline must produce. Each survives under the knowledge graph approach, but the
canonical layer shifts.

### View A: Evidence graph → Code graph + generated docs (enriched)

View A was "the minimally interpreted graph of legacy-derived relationships and
classifications." This is already the code graph + generated docs. Steps 1–3
strengthen it by carrying through discarded fields, materializing usages as edges,
and promoting data families as navigable nodes. The evidence graph is not replaced
— it is enriched.

### View B: Semantic model → Multi-label role tags + intent labels

View B was "the interpreted model that separates domain behavior from policy,
presentation, infrastructure, runtime, and utility concerns." The 30-group
taxonomy with 5 types served this role.

Under the knowledge graph approach, View B becomes the combination of:

- **Role tags** (Step 4): orthogonal, multi-label, derived from observable signals
- **Intent labels** (Step 5): behavioral groupings derived from caller evidence
- **Subsystem links** (V2): architectural home(s) with role and confidence

These three dimensions replace the single `capability` column. The old group
assignment is retained as `legacy_capability` for backward compatibility.

### View C: Chunk plan → Unchanged, consumes the graph

The 30-chunk registry in
[CG.md §12.3](../../projects/classify_fns/CG.md) with its mode classification
(native, adaptation, reference, replacement, substrate) and planning phase
assignment (B, C, D) remains valid. Chunks are **consumers** of the knowledge
graph, not defined by it. A chunk references entities by ID; whether those
entities have one capability label or five role tags does not affect the chunk
boundary.

The chunk registry's dependency edges (derived from capability-level typed edges)
should eventually be re-derived from the richer knowledge graph — but this is a
refinement, not a rewrite. The existing edges are good enough for planning.

### View D: Traceability → Edge structure provides it

View D was "links between evidence, understanding, specs, code, and validation."
The knowledge graph's edge structure provides traceability by construction:

- Entity → `entity_usages` → caller chains: who uses this and how
- Entity → `entity_subsystem_links` → system context: what narrative explains this
- Entity → `calls`/`uses` edges → behavioral dependencies
- Chunk → entity list → knowledge graph: audit trail from plan to evidence

The readiness levels ([CG.md §10](../../projects/classify_fns/CG.md)), chunk
dossier template ([CG.md §11](../../projects/classify_fns/CG.md)), and the
five-wave migration structure ([CONSENSUS.md §2.1](analysis/CONSENSUS.md)) sit
above the knowledge graph layer and are unchanged by this proposal.

---

## 6. Integration with MCP Server Versions

The four-layer information surface
([doc_server_roadmap.md §2](doc_server_roadmap.md)) remains the organizing
framework. Each knowledge graph enrichment step maps to a server version. The
knowledge graph is the accumulation of all layers, not a separate artifact.

### V1 — Enriched entity model (Steps 1–2)

Steps 1 and 2 are build pipeline additions to the existing V1 infrastructure.
No new tools are required — existing tools gain richer responses.

**Schema additions:**

- `entities` table gains: `doc_state TEXT`, `notes_length INT`,
  `is_contract_seed BOOLEAN`, `rationale_specificity REAL`
- New `entity_usages` table (§4, Step 2): ~24,803 rows with embeddings

**Tool enhancements:**

- `get_entity` response gains `doc_state`, `notes_length`, `is_contract_seed`
  fields. When `include_usages=true`, inlines the top N usage patterns.
- `search` gains `source=usages` mode for semantic search over usage
  descriptions: "apply a debuff before combat resolution" finds the callee
  entities whose usage descriptions match.
- `get_hotspots` can incorporate `notes_length` as an additional complexity
  signal alongside `fan_in`/`fan_out`/`bridge_score`.

**Build pipeline change:** Extend `build_mcp_db.py` to carry `doc_state` through
from generated_docs, compute `notes_length` and `is_contract_seed` at entity
load time, and populate the `entity_usages` table by exploding the `usages`
dicts. Estimated scope: ~200 LOC in the build script, one schema migration.

### V2 — Narrative layer + graph enrichment (Steps 3–4)

V2's design ([DESIGN_v2.md](../../mcp/doc_server/specs/v2/DESIGN_v2.md)) adds
curated system narratives, chunked for semantic search, with entity↔subsystem
links. This is unchanged. The knowledge graph enrichment from Steps 3–4 makes
V2 curation more effective:

- **Data-family nodes** (Step 3) provide natural anchors for the
  `entity_subsystem_links` table. The `Character` data family maps to
  `character_data` subsystem; the `Room` family maps to `world_system`. The
  curation agent uses data-family membership as strong evidence for link creation.

- **Role tags** (Step 4) help the curation agent assign link roles. An entity
  tagged `[infrastructure, output]` gets role `utility` or `supporting` in most
  subsystem links, while an entity tagged `[domain_logic, lifecycle]` gets role
  `core`.

**New tools (knowledge graph specific):**

- `explain_interface(entity)` — The five-part contract view from
  [generated-docs-additions.md §5](analysis/generated-docs-additions.md):
  signature, what-it-does (brief+details), contract (rationale), preconditions
  (notes), top calling patterns (usages). Pre-computed from existing fields, no
  LLM at query time. This is the single most requested tool shape across all
  three Round 3+mcp agent discussions.

- `get_data_family(class_or_struct)` — Given a class/struct entity, return its
  members, top accessor/mutator functions ranked by usage frequency, subsystem
  distribution of users, and role in the type hierarchy. Answers "what is
  `Character` and who touches it?"

### V3 — Help files as graph nodes (Step 5 enabler)

V3 adds in-game help entries. Under the knowledge graph approach, help entries
become nodes linked to code entities via name matching + embedding similarity.

Intent labels (Step 5) serve as join keys between help topics and code entities.
A help entry about "fireball" links to the `spell_fireball` entity, but also to
entities with intent label `damage_delivery` and `spell_casting_pipeline` — giving
the agent the full implementation surface for the feature the player knows as
"fireball."

### V4 — Builder guide as constraint nodes

V4 adds builder's guide sections about data formats, value field meanings, flag
definitions, and reset instruction syntax. These become nodes linked to the
entities that implement them — `obj->value[0]` in the guide links to the
functions that read `value[0]`, via the data-family structure from Step 3.

### Capability tool transition

Once V2 subsystem links, data families, and role tags are available, the V1
capability-group tools (`list_capabilities`, `get_capability_detail`,
`compare_capabilities`) become secondary navigation aids rather than the primary
semantic entry points. They remain functional and useful for chunk registry
back-compatibility and rough concern grouping, but agents should prefer
subsystem-based and role-tag-based navigation for richer results.

### Layered growth principle

Each version adds a layer of evidence. The knowledge graph is the union of all
layers. V1 enrichment provides the structural backbone. V2 adds narrative
context. V3 adds user expectations. V4 adds configuration constraints. At no
point does a later version need to restructure an earlier one — they are additive
by construction, matching the design principle from
[DESIGN_v2.md §8](../../mcp/doc_server/specs/v2/DESIGN_v2.md).

The multi-label, evidence-first graph design ensures that later layers slot in
without restructuring earlier ones. V3 help entries become graph nodes linked
via name matching and embeddings to the same entity rows that V1 enriched. V4
builder guide sections link to data-family members from Step 3. Intent labels
from Step 5 serve as join keys across all layers. Each version adds edges and
attributes to existing nodes — the schema grows additively.

---

## 7. Tool Surface for Consuming Agents

### Design philosophy

Three agent types consume the server
([speculative_agent_reqs.md §3](speculative_agent_reqs.md),
[CONSENSUS.md §1.1](analysis/CONSENSUS.md)):

- **Spec-creating agents** work iteratively and surgically — resolve an entity,
  trace its dependencies, understand its interface contract, check adjacent
  system narratives.
- **Planning agents** work at breadth — system inventory, dependency graph,
  complexity signals, critical paths.
- **Auditor agents** work in verification mode — given a spec dossier's claims,
  compare them against the legacy evidence. The auditor's primary tool is
  `explain_interface` applied to every entity referenced in a spec: does the
  spec's stated contract match the caller-derived behavioral expectations? The
  auditor uses the same evidence the spec agent used, accessed through the same
  tools, but applied as a cross-reference rather than a discovery operation.

The tool surface distinguishes **tools** from **prompts**:

- **Tools** handle data retrieval and server-side computation: joins,
  aggregations, embedding search, graph traversal. They return structured data.
- **Prompts** handle complex multi-step research workflows: how to explore a
  feature, how to audit a spec, how to plan a chunk. They describe expert
  strategy as a sequence of tool calls that the agent executes.

Do not build tools that merely compose two other tools to save a round-trip — 
write a prompt instead. Tools are justified when they perform server-side work
that agents cannot replicate client-side (e.g., `get_integration_surface`
joins `entity_usages` with `entity_subsystem_links` and ranks results by
cross-boundary frequency — an agent cannot do this without N+1 queries).

The default is **fewer, more general traversal-oriented tools** that agents
compose, rather than a sprawling menu of specialized queries. Tool calls are
cheap; agent judgment about what to explore next is the valuable part.

### Enhanced existing tools

| Tool | Enhancement |
|------|-------------|
| `get_entity` | Gains `doc_state`, `role_tags`, `is_contract_seed` fields. Optional `include_usages=true` inlines top usage patterns. |
| `search` | Gains `source=usages` mode for semantic search over usage descriptions. |
| `get_hotspots` | Gains `notes_length` as complexity signal. |
| `get_entity` + `get_subsystem_context` | Combined workflow: code-level view + narrative context. The knowledge graph makes both richer without changing the tool boundary. |

### New tools

| Tool | Purpose | Phase |
|------|---------|-------|
| `explain_interface` | Five-part contract view: signature, mechanism (brief+details), contract (rationale), preconditions (notes), calling patterns (usages). Pre-computed, no LLM. Primary tool for both spec agents and auditor agents. | V1 enrichment |
| `get_data_family` | Given a class/struct: members, top accessors/mutators, subsystem distribution, type hierarchy role. | V2 |
| `get_integration_surface` | Given two subsystem IDs (or a subsystem ID and a capability label): returns `(caller_entity, callee_entity, usage_description)` triples where the caller belongs to system A and the callee belongs to system B, ranked by cross-boundary frequency. Requires server-side join over `entity_usages` + `entity_subsystem_links`. Answers "how does combat use the affect system?" | V2 |

### Tools NOT to build

- `get_formula` — Too narrow. The `details` field is full-text searchable;
  agents can find formulas via `search` and then read source code.
- `get_spell_cluster` — Premature. Spell clustering requires Step 5 intent
  labels, and the clusters themselves are an intermediate artifact, not a
  stable query target.
- `estimate_complexity` — A prompt recipe, not a tool. The prompt
  composes `get_hotspots` + `get_behavior_slice` + `notes_length` signals
  and describes how to interpret their combination. The data comes from
  general tools; the interpretation strategy is encoded in the prompt.
- Per-system inventory tools — Generic graph traversal (`get_dependencies`,
  `get_related_entities`) with subsystem filtering is sufficient.

### Prompts (canned analysis recipes)

Prompts orchestrate multi-step tool workflows. They encode expert strategy, not
data:

- **`explore_feature`** — Starting from an entry point or entity: (1) resolve via
  `get_entity`; (2) get behavior slice for side effects and capabilities touched;
  (3) call `explain_interface` for the contract view; (4) call
  `get_subsystem_context` for narrative framing; (5) walk key callees with
  `explain_interface` to understand integration points. The prompt describes the
  workflow; the agent executes the tool calls.

- **`audit_contract`** — The auditor agent's primary workflow. Given a spec
  dossier's postconditions: (1) for each postcondition, identify the involved
  entities; (2) call `explain_interface` on each to get the caller-derived
  behavioral expectations; (3) compare the spec's claims against the evidence —
  does the spec say `damage()` does X, and does the rationale/usages evidence
  support that? (4) Use `get_integration_surface` to verify that cross-system
  contracts are consistent with the calling patterns in the evidence. (5) Check
  that the spec covers all entry points the chunk registry says it should
  (via `get_capability_detail` or `get_entry_point_info`). The prompt describes
  the verification strategy; the auditor agent executes the tool calls.

- **`plan_chunk`** — Given a chunk from the registry: list member entities with
  `get_capability_detail`, assess complexity via `get_hotspots` + `notes_length`,
  identify integration dependencies via `get_integration_surface`, retrieve
  narrative context via `get_subsystem_context` for the chunk's primary subsystem.

---

## 8. Build Order

The build order follows evidence cost — cheap mechanical steps first,
inference-requiring steps last. Each step is independently deployable and
testable. The focus of this proposal is V1 enrichment; subsequent versions
are described tentatively to show that the graph design accommodates them.

### Phase 0: This proposal (current)

No code changes. Document review and decision lock.

### Phase 1: V1 enrichment (Steps 1–2) — the immediate work

**Scope:** Extend `build_mcp_db.py` to:

1. Carry `doc_state` through from generated_docs `state` field
2. Compute `notes_length` (character count of `notes` field)
3. Compute `is_contract_seed` flag (`fan_in > threshold` AND non-null rationale)
4. Compute `rationale_specificity` score (length + domain-term heuristic)
5. Create `entity_usages` table and populate from usages dicts (~24,803 rows)
   with embeddings

**Estimated scope:** ~200 LOC build script changes, schema migration for new
columns + table.

**Deliverables:** `explain_interface` tool (composition over existing + new
fields). Enhanced `get_entity` and `search` responses.

**Prerequisite:** None beyond current V1 server.

### V2: Narrative layer + graph enrichment (Steps 3–4)

V2 adds curated system narratives, entity↔subsystem links, and system-level
dependency edges per [DESIGN_v2.md](../../mcp/doc_server/specs/v2/DESIGN_v2.md).
The `entity_usages` table from Phase 1 informs curation decisions — usage
descriptions provide evidence for subsystem links beyond what call-graph edges
alone reveal.

Data-family promotion (Step 3) and role tag computation (Step 4) are natural
companions to V2 curation: data families provide anchors for subsystem links,
and role tags help assign link roles. These should be computed during or
alongside V2, not deferred to a separate phase.

Deliverables: V2 tools (`list_subsystems`, `get_subsystem`,
`get_subsystem_context`, `get_subsystem_dependencies`,
`search_subsystem_docs`), `get_data_family`, `get_integration_surface`.

### V3: Help files as graph nodes

V3 adds in-game help entries as nodes linked to code entities via name matching
and embedding similarity. The multi-label graph design already accommodates
this — help nodes link to the same entity rows that V1 enriched, using intent
labels (Step 5, if computed by then) or direct entity references as join keys.
Help entries add the user-expectation perspective that V1/V2 lack.

Format, chunking strategy, and entity-linking approach are not yet determined
(see [doc_server_roadmap.md §5](doc_server_roadmap.md)).

### V4: Builder guide as constraint nodes

V4 adds builder's guide sections about data formats, value field meanings, flag
definitions, and reset instruction syntax as nodes linked to the entities that
implement them. Data-family structure from Step 3 provides natural link targets
(e.g., `obj->value[0]` in the guide links to the functions that read
`value[0]`).

Ingestion strategy depends on the guide's HTML structure (see
[doc_server_roadmap.md §6](doc_server_roadmap.md)).

### Intent labels (Step 5) — non-blocking refinement

Intent labels require either embedding-based clustering over rationale/usages
text or a lightweight LLM classification pass. This is the only step that may
need new inference. It is valuable but **not blocking** for spec work — agents
can operate effectively with V1 enrichment + V2 narrative + role tags. Intent
labels are additive refinement that can land at any point after Phase 1.

---

## 9. Decisions Record

| Decision | Rationale | Evidence |
|----------|-----------|----------|
| **Single-assignment → multi-label** | 126 cross-domain functions, 62% multi-mechanism, `stc` in 22 groups | Corpus survey (`.scratch/full_survey.py`) |
| **Evidence-first build order** | External feedback proposed premature 10-type ontology; only ~2 types have evidence today | External agent evaluation |
| **Capability groups as projection** | Backward compatibility with chunk registry + they still answer "show me combat functions" | Chunk registry is a downstream consumer, not a data source |
| **`entity_usages` as #1 priority** | Highest value-to-cost ratio: 24,803 entries → unlocks `explain_interface`, `get_integration_surface`, intent label clustering | [generated-docs-additions.md §4](analysis/generated-docs-additions.md) |
| **No new LLM calls for Steps 1–4** | All enrichments are aggregation/indexing over existing data; new inference deferred to Step 5 only if needed | Field-by-field analysis in [generated-docs-additions.md §8](analysis/generated-docs-additions.md) |
| **Tools for computation, prompts for workflow** | Tools do server-side work (joins, aggregation, search); prompts describe multi-step research strategies. Don't build tools that merely compose two other tools — write a prompt. | MCP server prompt capability + agent discussion consensus |
| **`explain_interface` as the key new tool** | Five-part contract view maps directly to existing doc fields; all three agent discussions independently requested it | [generated-docs-additions.md §5](analysis/generated-docs-additions.md), [speculative_agent_reqs.md](speculative_agent_reqs.md) |
| **Retain `legacy_capability` field** | Chunk registry and existing tools reference capability by name; breaking change has no benefit | Backward compatibility principle |

---

## 10. What This Does NOT Address

This proposal concerns how the legacy codebase is **modeled and exposed** through the
MCP server. It does not cover:

- **Runtime ordering.** The game loop's phase-locked execution order
  ([migration-challenges.md §2](migration-challenges.md)) is an implementation
  design problem, not a knowledge representation problem. The global scheduler
  decision ([CONSENSUS.md §3.5](analysis/CONSENSUS.md)) stands.

- **`act()` format strings and message catalog.** `act()` calls are already in
  the code graph — agents can query call sites via `get_callers`/`get_callees`
  and read the source code to extract format string literals. The spec-creating
  agent's job includes parsing code blocks and extracting I/O contracts;
  pre-extracting format strings into a separate catalog is not a doc server
  responsibility.

- **Data table values.** Race stats, class skill groups, spell mana costs are
  **configuration data**, not code structure. The knowledge graph describes the
  functions that *consult* these tables. The table contents themselves are the
  implementing agent's responsibility to migrate from code chunks, directed by
  the spec. There is no circumstance where a planning or spec agent needs an
  individual row of data from a table — what they need is the function that
  reads it and the contract around that function, which `explain_interface`
  provides.

- **Golden trace library.** Behavioral traces of specific scenarios require either
  legacy server instrumentation or reconstructed scenario analysis — runtime data,
  not static analysis.

- **Chunk dossier generation.** Dossiers ([CG.md §11](../../projects/classify_fns/CG.md))
  are a Phase 5 deliverable that *consumes* the knowledge graph. The knowledge
  graph must exist for dossiers to be rich, but the dossier template itself is
  orthogonal to graph structure.

- **Target-side architecture.** Typeclass strategy, handler patterns, timing model,
  and messaging layer decisions ([CONSENSUS.md §3](analysis/CONSENSUS.md)) are
  target-system commitments. The knowledge graph is legacy-grounded — it describes
  what exists, not what should be built.

---

## Appendix: Terminology

| Term | Definition |
|------|------------|
| **Knowledge graph** | The enriched code graph: original Doxygen-parsed nodes and edges + doc-derived attributes + materialized usage edges + derived role/intent tags + V2 subsystem links. Not a separate artifact — it is the union of all evidence layers in the MCP database. |
| **Data family** | A class or struct entity (e.g., `Character`, `Room`, `Object`) with high `contained_by` + `uses` edge counts, serving as a conceptual anchor for a domain's state. |
| **Role tag** | A derived, multi-valued label describing an entity's architectural role (infrastructure, domain_logic, data_access, output, validation, lifecycle, entry_point). Computed from observable signals, not curated. |
| **Intent label** | A derived, multi-valued label describing what callers use an entity for (damage_delivery, buff_application, player_messaging, etc.). Finer-grained than capability groups. May require clustering or LLM inference to produce. |
| **Capability group** | One of the 30 groups in `capability_defs.json`. Retained as `legacy_capability` on the entity row for backward compatibility. Now a projection of the knowledge graph, not its canonical structure. |
| **Evidence** | Observable facts derivable from source code, call graphs, and LLM-generated documentation without additional interpretive inference. The knowledge graph is evidence-first: derived attributes are computed from evidence, curated labels are deferred. |
| **Projection** | A filtered, structured view of the knowledge graph answering a specific kind of question. Capability groups, subsystem links, role tags, and intent labels are all projections. No projection is canonical — the graph is. |
