## 1. MCP Server: Addressing Agent Information Needs

### Assessment
The current V1/V2 roadmap provides excellent structural and narrative depth, but a **fidelity gap** exists regarding exact player-facing output and data constants[cite: 4].
*   **Coverage Gaps:** Spec-creating agents cannot achieve 90%+ fidelity without the **V3 (User-Facing)** layer, which contains the exact output strings and help-file contracts[cite: 4]. `migration-challenges.md` highlights the complexity of the `act()` messaging system; without V3, agents might "hallucinate" idiomatic Python messages instead of the required legacy text[cite: 3, 4].
*   **Tool Sprawl vs. Consolidation:** With over 20 tools planned, agents risk "context fragmentation." The proposed `explore_entity` is a vital "composite tool" to reduce API chatter[cite: 6].
*   **Boundary Discipline:** The server should provide **behavioral slices** (e.g., "this function modifies HP and sends a message") but must not suggest Evennia-specific implementations like "use a TickerHandler"[cite: 4, 6].

### Recommendation
**Accelerate V3/V4 ingestion.** Spec agents require the V3 help files to define "indistinguishable" output and V4 builder guides to capture the "data-level contracts" (damage dice, etc.) that aren't always clear in C++ code[cite: 4]. Implement `explore_entity` immediately as the default starting point for all spec research[cite: 6].

---

## 2. Agent Workflow: Hierarchical and Iterative

### Assessment
A purely linear workflow will fail due to **cross-system coupling** (e.g., the combat system's reliance on the stat computation pipeline)[cite: 3].
*   **Pipeline:** A **System Planning Agent** must define the "Contract Registry" (shared interfaces) before spec agents begin[cite: 6].
*   **Auditor Agent:** Essential at the **per-system** level to verify specs against the `migration-challenges.md` list (e.g., "Does this combat spec account for the 2-second global tick feel?")[cite: 3].

### Recommendation
Adopt a **Hierarchical-Iterative** model. Planning agents produce the "Interface Registry" first. Spec agents then work in waves, with an **Auditor Agent** performing "Fidelity Gates" before implementation[cite: 6]. If an implementation agent finds a legacy side effect the spec missed, it triggers a mandatory spec revision.

---

## 3. Migration Ordering and Bootstrapping

### Assessment
The dependency graph shows a long chain: **Utilities → Data Tables → Character Data → Combat**[cite: 2].
*   **Minimum Infrastructure:** You cannot write a verifiable combat spec without the **Stat Computation Pipeline** and the **Messaging Layer (`act()`)**[cite: 3].
*   **Ordering:** The "Wave" structure should prioritize Layer 1 and 2 infrastructure[cite: 2].

| Wave | Systems | Dependency Goal |
| :--- | :--- | :--- |
| **Wave 1** | Messaging, Stat Pipeline, Data Tables | Establish the communication and math foundation. |
| **Wave 2** | Character Data, Position System, Persistence | Enable entity lifecycle and state. |
| **Wave 3** | Affect System, Combat, Magic | Implement core gameplay loops. |

### Recommendation
**Infrastructure-first.** Do not spec combat until the Stat Pipeline (base + equipment + affects) and `act()` messaging contracts are locked[cite: 3]. Use **full implementations** for Layer 1; stubs are too risky for the stat pipeline, which is the "hot path" for fidelity[cite: 3].

---

## 4. Fidelity Verification: The "Indistinguishable" Standard

### Assessment
Fidelity in a MUD is primarily **textual and temporal**[cite: 3].
*   **Threshold:** "Indistinguishable" means matching the **output buffer** and the **rhythm of the tick**[cite: 3]. Rounding differences in damage are acceptable *if* they don't change the number of hits to kill a standard mob.
*   **Method:** The MCP's **behavioral slices** (side-effect markers) are the key[cite: 4]. We can generate "Fidelity Traces"—logs of legacy inputs and expected `act()` outputs—to use as automated test cases in Evennia.

### Recommendation
Create a **"Legacy Trace" tool** within the MCP server that extracts input/output sequences from the legacy system to serve as "Golden Files" for Evennia unit tests[cite: 4].

---

## 5. Spec Granularity and Scope

### Assessment
Broad specs (e.g., "The Magic System") lead to context overflow[cite: 3]. 
*   **Granularity:** Decompose by **functional pipeline**. "Combat" should be split into `Hit Resolution`, `Damage Calculation`, and `Death/Looting`[cite: 3].
*   **Emphasis:** Specs must be **data-heavy**. A spec that doesn't include the exact C++ formula for `one_hit()` or the `damage()` elemental cascade is a failure[cite: 2, 3].

### Recommendation
One spec per **Implementation Unit** (e.g., a single Evennia Script or Handler)[cite: 5]. Prioritize **Data Contracts** (formulas and tables) over prose descriptions to ensure the Python code behaves exactly like the C++[cite: 3].

---

## 6. The Shared Infrastructure Problem

### Assessment
The **Messaging Layer (`act()`)** and **Stat Pipeline** are the two biggest blockers[cite: 3].
*   **Messaging:** Every player-facing system depends on it. It must handle pronoun substitution (`$n`, `$N`) and visibility checks (invis/detect hidden) identically to the original[cite: 2, 3].
*   **Stat Pipeline:** This is the most performance-sensitive area[cite: 3]. It must aggregate base stats, equipment bonuses, and active affects[cite: 3].

### Recommendation
**Standalone Infrastructure Specs.** Write these first as "Contract Sources."
1.  **Stat Pipeline:** Define the `TraitHandler` and caching strategy to handle the high-frequency combat lookups[cite: 3, 5].
2.  **Messaging:** Wrap Evennia's `msg_contents` to create a legacy-compatible `act()` utility[cite: 3, 5].
