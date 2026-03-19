To move from a staged roadmap to a **"Ready for Migration"** state, the MCP server must evolve into a high-fidelity "Digital Twin" of the legacy codebase. It isn't just a search engine; it’s a translation layer that handles the "heavy lifting" of C++ interpretation so the agents can focus on Evennia architecture.

Here is the final-form requirement for the MCP server, categorized by the work it must perform for your agents.

---

## 1. The Resource Layer: Pre-Computed "Sources of Truth"
Before a single spec is written, these resources must be generated. Most of these require **computed static analysis** or **agentic pre-processing**.

### A. The Dependency & Impact Graph (Computed)
* **What it is:** A machine-readable map of how data flows between files (e.g., how `affect_modify` in `handler.c` impacts `one_hit` in `fight.c`).
* **Why:** Planning agents need this to define "Migration Waves." If they don't know that the `Object` system touches the `Character` system in 400 places, the wave ordering will fail.

### B. The "Golden Trace" Library (Agentic/Computed)
* **What it is:** A collection of "Behavioral Slices" that capture Input $\rightarrow$ Logic $\rightarrow$ Output.
* **Why:** To meet the 90%+ fidelity goal, the Implementation Agent needs to see that when a "Level 10 Warrior hits a Goblin with a Mace," the legacy code rolls $D8+4$ and produces *exactly* three specific `act()` strings.

### C. The Token & Formula Dictionary (Agentic)
* **What it is:** A clean catalog of every math formula and every `$token` used in the legacy `act()` calls.
* **Why:** Spec agents shouldn't have to "read" C++ math. The MCP should provide: `Formula: backstab_damage = (level * 2) + dex_bonus`.

---

## 2. The Tool Layer: Agentic Ergonomics
These tools allow agents to navigate the ~90 KLOC without getting lost in the "noise" of legacy Diku macros.

### A. The `explore_entity` Composite Tool
* **Function:** Instead of an agent calling `read_file`, `list_functions`, and `get_dependencies` separately, this single tool returns a **360-degree Dossier** of a legacy system (e.g., "The Poison Affect").
* **Contents:** Relevant C code, related help files (V3), builder guide notes (V4), and a summary of side effects.

### B. The "Interface Contract" Generator
* **Function:** An agent points this tool at a legacy C function (e.g., `damage()`), and the tool returns a **Typed Contract**: what are the inputs, what globals does it modify, and what messages does it send?

---

## 3. Curation & Pre-Computing Strategy
To reach this "Final Form," we need a mix of automated extraction and expert human/agentic oversight.

| Data Type | Generation Method | Reason |
| :--- | :--- | :--- |
| **Call Graphs / Symbol Tables** | **Computed (Clang/Static Analysis)** | Purely objective data; humans shouldn't do this. |
| **Logic Clustering (e.g., Spell Patterns)** | **Agentic (LLM Batch Processing)** | LLMs excel at seeing that 40 spells use the "Save or Die" pattern. |
| **Help File $\leftrightarrow$ Code Mapping** | **Agentic (LLM Batch Processing)** | Mapping the `spell_fireball` function to the `fireball.hlp` text. |
| **"Load-bearing Bug" Identification** | **Hand-Curated (Human Expert)** | Only a human knows that a specific rounding error in the 1998 code is "part of the game's feel." |
| **Global Scheduler Timeline** | **Hand-Curated/Computed** | Mapping the 100ms pulses to specific function calls to ensure phase-locked fidelity. |

---

## 4. The Final Form Prompt Library
The MCP server must also host the "System Prompts" for the three agent types to ensure they use the tools correctly.

* **The Architect's Prompt:** Focuses on using the Dependency Graph to minimize "circular implementation" risks.
* **The Spec-Writer's Prompt:** Focuses on extracting formulas and `game_act()` tokens to ensure 1:1 behavioral parity.
* **The Auditor's Prompt:** Focuses on cross-referencing the new Evennia Python code against the "Golden Trace" library to flag fidelity gaps.

---

## Analysis of "Completeness"
To satisfy your requirement that "we won't start until the MCP server is complete," the definition of **"Complete"** is:

> **The MCP server is complete when an agent can describe the full lifecycle of a 'Fireball'—from player command to mana deduction, saving throw calculation, damage application, and room-wide messaging—without ever being forced to read a raw `.c` file directly.**
