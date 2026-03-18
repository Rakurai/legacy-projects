This analysis resolves the Round 1 divergences and establishes the architectural commitments required to move into Wave 1 implementation.

---

## Topic A: The Stubs Disagreement

### Decision
Adopt a **Hybrid Implementation Model**. Infrastructure that serves as a "math or message substrate" must be **fully implemented**[cite: 3]. Systems that are "leaf nodes" or "effect providers" may use **stubbed contracts**.

*   **Must be Full:** Stat Pipeline, Messaging Layer, Data Tables, Entity Lookup[cite: 2, 3].
*   **Stub-Safe:** Combat (can be stubbed for Magic specs), Affect Effects (can be stubbed for Combat specs), Magic Spells[cite: 2, 8].

### Rationale
Gemini’s "hot path" argument is correct for the **Stat Pipeline**: if the aggregation math is slightly off due to a stub's simplification, every downstream system (Combat, Magic, Skills) will be built on a "floating foundation" that risks the 90% fidelity goal[cite: 3, 8]. However, velocity requires we don't build the entire magic system before testing combat; therefore, the *effect* of a spell (the result) is stub-safe, but the *pipeline* that calculates its success must be real[cite: 2].

### Risk
**Contract Drift:** A stubbed interface (e.g., `AffectHandler.add()`) might lack a required parameter discovered during Magic implementation (e.g., `source_entity`). 
*   **Mitigation:** Mandatory "Interface Audit" before any stub moves to implementation[cite: 6].

---

## Topic B: Timing Orchestration

### Decision
**Centralized Heartbeat Script per Living Entity.** 
*   **The Pulse:** A single Evennia `Script` attached to the character typeclass, ticking every 2 seconds (the legacy "Violence Pulse")[cite: 3].
*   **The Sub-Cycle:** A simple counter inside `at_repeat()` manages frequencies:
    *   **Counter % 1 == 0:** Execute `violence_update()` (2s).
    *   **Counter % 2 == 0:** Execute `regen_update()` and `affect_update()` (4s)[cite: 3].

### Rationale
Legacy systems rely on **strict phase ordering** (e.g., damage resolves *before* healing in a tick)[cite: 3]. Global loops are Evennia anti-patterns, but per-character scripts with internal counters maintain the required execution order for that specific character's state changes[cite: 8].

### Risk
**Phase Drift:** 50 NPCs in a room might tick at slightly different sub-second offsets. 
*   **Mitigation:** For MUD fidelity, "simultaneous" resolution is less important than "consistent order of operations." Per-character scripts provide enough parity for the player experience[cite: 8].

---

## Topic C: Typeclass Strategy

### Decision
**LivingMixin + Discrete PC/NPC Classes.**
*   **Hierarchy:** 
    *   `LivingMixin`: Handles Stats, Combat, Affects, and `act()`.
    *   `AccountPlayer(DefaultCharacter, LivingMixin)`: Handles PC-specific ghost states and XP[cite: 8].
    *   `NonPlayerCharacter(DefaultCharacter, LivingMixin)`: Handles Vnum prototypes and MobProgs[cite: 8].
*   **Objects:** A single **`GameItem(DefaultObject)`** typeclass using **Component-based Attributes** (e.g., `item.db.weapon_data` exists only if the item is a weapon)[cite: 8].

### Rationale
Applying `LivingMixin` to both classes allows the combat pipeline to treat targets identically while keeping the pervasive `IS_NPC()` logic isolated in the discrete classes[cite: 8]. Using a single `GameItem` class mirrors the legacy "ObjectValue" union while utilizing Evennia’s flexible Attribute system for type-specific data[cite: 8].

---

## Topic D: Messaging Layer Contract

### Decision
Finalize the **`game_act()`** signature and resolution logic.

### Contract Shape
```python
def game_act(template: str, actor, victim=None, obj=None, 
             audience=TO_ROOM, visibility_check=True):
    """
    Standard: $n (actor), $N (victim), $e/$m/$s (pronouns), $p (object).
    """
```
*   **Token Substitution:** Use a custom `ActFormatter` that maps legacy tokens to `actor/victim/obj` properties[cite: 8].
*   **Visibility:** Handled **internally** by `game_act`. It performs `recipient.can_see(actor)` check. If `False`, it replaces `$n` with "someone"[cite: 8].
*   **Audience:** Handle `TO_CHAR`, `TO_VICT`, `TO_ROOM`, `TO_NOTVICT` via `msg_contents(exclude=[...])`[cite: 8].

---

## Topic E: Contract Registry Format

### Decision
**JSON-Schema backed YAML files** located in `/contracts/`.

### Contract Example: Stat Pipeline
```yaml
id: infra_stat_pipeline
version: 1.0
methods:
  - name: get_effective_stat
    args: { stat_name: string }
    returns: integer
    guarantees:
      - "Must aggregate: Base + Equipment + Affects"
      - "Must apply 0-25 hard cap for attributes"
      - "Must use floor() for all divisions"
```

### Rationale
Machine-readable formats allow future Auditor Agents to validate Python code against the spec automatically[cite: 6].

---

## Topic F: The 200-Spell Problem

### Decision
**Framework + Data-Driven Catalog.**
1.  **Framework:** Define a `SpellEffect` base class for standard behaviors (Check Saves → Roll Damage → Apply Affects)[cite: 8].
2.  **Clustering:** Use the MCP V1 tools to cluster the ~150 "standard" spells. These become data entries in a `spell_registry`[cite: 8].
3.  **Bespoke Exceptions:** Only the ~50 unique spells (e.g., `gate`, `enchant weapon`) receive individual implementation dossiers[cite: 8].

---

## Topic G: Wave 1 Acceptance Criteria

### Decision
**"The Navigable World"**[cite: 8].

| Deliverable | Acceptance Criteria |
| :--- | :--- |
| **Stat Pipeline** | `get_effective_stat` returns correct legacy values for a test character. |
| **Messaging** | `$n` and visibility tokens render identically to legacy in the logs. |
| **Vertical Slice** | A player can: Login, `look` (with invis filtering), `move`, `get/drop` items. |

*   **Out of Scope:** Combat, NPC AI, Mana/HP costs, Area Resets[cite: 8].
