# Redesign Opportunities: Beyond Faithful Recreation

> **Purpose:** Track ideas for genuine gameplay or UX improvements that were not
> feasible in the original Diku/ROM architecture but become possible on Evennia.
> These are aspirational — they are explicitly **out of scope** for the core
> migration, which targets faithful recreation of the legacy experience.
>
> **Why separate:** Planning agents working on migration specs must not confuse
> fidelity goals with redesign ideas. The core migration produces a game
> indistinguishable from the original. Redesign opportunities are evaluated
> independently, after the faithful system is working, and only adopted if they
> improve the game without disrupting the player experience that the migration
> preserves.
>
> **See also:** [migration-challenges.md](migration-challenges.md) (the faithful
> recreation challenges that take priority)

---

## How to Use This Document

Items here are **not commitments**. They are ideas worth considering once the
faithful recreation is stable. Each entry describes what the legacy system does,
what becomes possible on Evennia, and why it might be worth changing. Items should
only be promoted to actual work when:

1. The faithful version of the system is implemented and working.
2. The change genuinely improves the experience (not just "we can, so we should").
3. The change does not break player expectations without clear justification.

---

## Persistence-Enabled Opportunities

### NPC Memory

**Legacy:** NPCs are ephemeral clones. When an area resets, all NPC state is
wiped — they have no memory of previous interactions.

**Evennia enables:** NPCs are persistent DB objects. They can remember being
attacked, remember conversations, track grudges or gratitude across sessions.
An NPC shopkeeper could refuse service to a player who robbed them. A guard
could recognize a repeat offender.

**Trade-off:** This changes NPC behavior in ways players wouldn't expect from
the original. Only worth doing if it makes specific interactions more engaging
without breaking the overall game feel.

### Persistent Ground State

**Legacy:** Items on the ground vanish at the next area reset. The world
resets to a clean state periodically.

**Evennia enables:** Dropped items persist. Player-altered room state (broken
doors, spent campfires) could persist across sessions. The world could bear
marks of player activity.

**Trade-off:** Accumulation must still be managed (decay timers, cleanup logic).
The "clean reset" model has a gameplay purpose — it ensures fairness and
predictability. Selective persistence (some things stay, others decay) is more
interesting than blanket persistence.

---

## Combat Opportunities

### Richer Action Economy

**Legacy:** Combat is auto-attack with optional commands interleaved. The
action model is: you are always swinging your weapon; spells, skills, and
items are extras you choose to use during rounds.

**Evennia enables:** Per-action command systems where each round presents
explicit choices. Queue-based combat where players plan multiple actions.
Reaction systems where defenders choose responses. None of this was practical
in the original tick-driven auto-attack loop.

**Trade-off:** The auto-attack feel IS the game for many players. Any change
here fundamentally alters combat identity. This is the highest-risk redesign
item on this list.

### Multi-Room Combat and Pursuit

**Legacy:** Combat is per-room. Fleeing ends combat. There is no pursuit or
ranged combat across rooms.

**Evennia enables:** CombatHandler Scripts could span multiple rooms,
tracking combatants as they move. Ranged attacks across rooms become
feasible. Pursuit mechanics could allow NPCs or PCs to follow fleeing targets.

**Trade-off:** This would be a new feature, not a recreation. Only worth
considering if specific game content would benefit.

---

## Character System Opportunities

### Multi-Character Support

**Legacy:** One character per player, no Account/Character separation.

**Evennia enables:** Multiple characters per account, character selection
screen, alt management. Players could have different characters for different
playstyles without maintaining separate logins.

**Trade-off:** The legacy game's social model assumes one identity per player.
Clan membership, reputation, and inter-player relationships are all built on
this assumption. Multi-character would need social-system adjustments.

### Improved Character Creation

**Legacy:** A rigid state machine: name → password → race → class → stats →
alignment → done. Each step is a single prompt with limited feedback.

**Evennia enables:** EvMenu-driven character creation with rich descriptions,
preview of racial abilities, stat reroll with visual comparison, help text at
every step. This is one of the few areas where improved UX is unambiguously
positive — the legacy chargen is purely a product of its limitations.

**Trade-off:** Low risk. Players who remember the original will appreciate
the improvement. This is a strong candidate for early adoption.

---

## NPC Intelligence Opportunities

### Behavior Trees / State Machines

**Legacy:** NPCs use spec functions (hardcoded tick-driven behaviors) and
MobProgs (simple if/then scripts). Behavior is reactive and stateless between
triggers.

**Evennia enables:** Full Python behavior trees, persistent state machines,
learning/adaptive NPCs. An NPC could patrol a route, investigate disturbances,
call for backup, and remember the encounter for next time.

**Trade-off:** More intelligent NPCs would change the feel of the game
significantly. The legacy world has a specific charm in its predictable NPCs.
Richer AI might be better suited to new content than to recreations of
existing encounters.

---

## Infrastructure Opportunities

### Hot Reload

**Legacy:** Code changes require full server restart. Copyover preserves
connections but still restarts the process.

**Evennia enables:** Server reload refreshes all Python code without
disconnecting players. This is a framework feature, not something we build.
But it changes the development model — iterations can happen on a live server.

**Trade-off:** No trade-off. This is a pure improvement inherited from the
framework.

### Web Client

**Legacy:** Telnet-only access with ANSI color codes.

**Evennia enables:** A web-based client alongside traditional telnet. The
webclient can display richer formatting, clickable elements (via MXP or
custom web UI), and potentially graphical elements.

**Trade-off:** The telnet experience must be preserved as the primary client.
A web client is additive, not a replacement. But it opens the game to players
who don't have or want a telnet client.

### Structured Data Over the Wire

**Legacy:** All output is plain text with ANSI color codes. Clients parse
the text to extract information.

**Evennia enables:** GMCP (Generic MUD Communication Protocol) can send
structured data alongside text — HP/mana/move as numbers, room info as
JSON, inventory as structured lists. Smart clients can build graphical
gauges, maps, and inventory panels from this data.

**Trade-off:** This is purely additive — text output stays the same, GMCP
is optional data for capable clients. A strong candidate for implementation
alongside the faithful recreation.

---

## Economy and Social Opportunities

### Persistent Auction History

**Legacy:** The auction system is ephemeral — items are listed, bid on, and
sold in a global channel, with no history.

**Evennia enables:** Auction history stored in the database. Price tracking,
sale records, buyer/seller relationships. Could inform a more sophisticated
economy over time.

**Trade-off:** The auction system's simplicity is part of its charm. History
and analytics are additive, not replacements.

### Persistent Mail and Notes

**Legacy:** The note system stores messages in a database (SQLite), surviving
restarts. This already works.

**Evennia enables:** Richer formatting, threading, and search. Evennia's Msg
model provides a foundation.

**Trade-off:** Minimal risk. Improvements to a system that already persists.
