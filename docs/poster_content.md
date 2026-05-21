# FIBO Senior Thesis Poster Content (Copy-Paste Ready)

This document contains the exact text for your senior thesis poster using simple, clear, and accurate terminology. All overly complex or misleading terms have been replaced with direct, standard engineering terms. The testing/evaluation section has been removed to focus on the technical details of the work.

---

## HEADER BLOCK

### Title
AGENTIC-DUALPATH-CORE: A MULTI-AGENT HYBRID TTRPG ENGINE

### Subtitle
SENIOR THESIS | 29 MAY 2026 | 12:00 - 13:00 | ROOM FB607, FIBO BUILDING

### Author & Contact
**Author:** Mr. Pollapaat Suttimala  
**Contact:** mudnott@gmail.com | +66 86-965-2595  
**Institution:** Institute of Field Robotics (FIBO), King Mongkut's University of Technology Thonburi (KMUTT)

### Advisor & Co-advisor
**Advisor:** Asst. Prof. Dr. Suriya Natsupakpong  
**Co-advisor:** Asst. Prof. Dr. Paisit Khan-Ar-Sa

---

## SECTION 1: INTRODUCTION & CHALLENGE

### Problem Statement
Standard AI-driven Dungeon Masters in Tabletop Role-Playing Games (TTRPGs) frequently suffer from the **"Hallucination Problem"**. When a single Large Language Model (LLM) controls the entire game, it routinely makes calculation errors, forgets character health points (HP), ignores inventory limits, and allows players to bypass physical boundaries (like walking through solid walls).

### The Natural Language Challenge
* Natural language is rich, flexible, and ambiguous. Players expect to describe their actions freely (e.g., *"I slide under the table to slash the goblin's ankles"* or *"I crawl down carefully toward the Grinding Chamber"*).
* Rigid traditional code cannot interpret these creative, unstructured sentences.
* Therefore, the system requires an **LLM-based classifier** to understand natural player intents, but needs a **hard-coded backend** to calculate the mathematical rules of the game.

### Proposed Solution
We introduce **Agentic-DualPath-Core**, a hybrid system that separates creative roleplay from mathematical game mechanics. By implementing a **Two-Path Router**, the system routes standard commands to a Python rules engine and creative commands to an LLM Arbiter.

---

## SECTION 2: SYSTEM OVERVIEW (TWO-PATH ARCHITECTURE)

*(Note: You definitely should include a System Overview diagram! It is highly expected in FIBO senior thesis posters to visually show how the system works without relying only on text.)*

The core engine divides gameplay actions into two separate execution pathways:

1. **Path A (Standard Rules - Python Engine):**
   * **Scope:** Standard movement, weapon attacks, standard spells, and inventory items.
   * **Execution:** Processed entirely in Python using predefined formulas (e.g., rolling dice, checking Armor Class, subtracting HP).
   * **Advantages:** 100% calculation accuracy, zero token cost, and instant execution.

2. **Path B (Creative Rules - LLM Arbiter):**
   * **Scope:** Environmental puzzle attempts and creative actions not covered by standard rules.
   * **Execution:** Sent to the LLM (Gemini Flash Lite) to judge the action. The LLM determines the Difficulty Class (DC) and outputs specific game conditions (e.g., target state: `PRONE` or `STUNNED`).
   * **Advantages:** Flexible narrative freedom grounded by standard Python state updates.

### TOON (Token-Oriented Object Notation) Data Serialization
* To send the game state (player stats, inventory, monster HP) to the LLM, we developed a highly compressed custom text format called TOON.
* **Impact:** Reduces token usage by approximately 40% compared to standard JSON, saving API costs and speeding up LLM response times.

---

## SECTION 3: NODE-BASED EXPLORATION ENGINE

To expand the game beyond turn-based combat, we engineered a Point-Crawl Exploration Engine with strict structural guardrails:

### Point-Crawl Graph & State Separation
* The game map is a structured network of nodes (representing rooms, hallways, and chambers) connected via a defined JSON data structure.
* **Infinite Lore Prevention:** Separates exploration logs from combat state, ensuring room descriptions are only generated once upon entry. This avoids repetitive text generation and prevents context overflow.

### Hybrid Exploration Router
To navigate these nodes naturally, player inputs are processed in three sequential passes:
1. **Pass 1 (Regex - Zero Cost):** Simple keywords (e.g., `look`, `rest`, `status`, `inventory`) are instantly resolved in Python.
2. **Pass 2 (LLM - Semantic Matching):** Natural language movement sentences (e.g., *"I'll carefully head down toward the Grinding Chamber"*) are parsed by the LLM and mapped to a valid exit name from the active node.
3. **Pass 3 (Puzzle Context):** If the player is in a room with an uncleared puzzle, unrecognized inputs are automatically treated as puzzle-solving attempts and sent to the LLM Arbiter.

### Spatial Hallucination Guardrails
* Python verifies if the destination node is connected to the current node *before* calling the LLM. This strictly prevents spatial hallucinations, ensuring players cannot walk through walls or enter nonexistent rooms.

---

## SECTION 4: PLAYTEST DEMO CAPTURE

Here is an authentic console log showing how the Hybrid Router and spatial guardrails process player actions:

```text
[EXPLORATION] Entered: Mine Entrance
🗣️ DM: The air hangs heavy and damp. The only path forward is the Main Shaft...

> Player: I go to the next room
🛑 [SYSTEM] Invalid MOVE blocked: 'the next room' 
(Python spatial guardrail blocks illegal movement instantly before calling AI)

> Player: Go to main shaft
[MOVE] -> Main Shaft (Pass 1: Regex matches keyword 'go' -> zero token cost)
🗣️ DM: Timber beams groan overhead. Exits lead East and North...

> Player: I blow the toxic gas away with wind magic
[PUZZLE_ATTEMPT] (Pass 3: Sent to LLM Arbiter since room contains a gas puzzle)
🎲 d20 + MENT: 14 + 3 = 17 (DC 15) -> SUCCESS!
🗣️ DM: The gas dissipates, clearing the path into the Ambush Chamber.
```

---

## SECTION 5: COMBAT & INITIATIVE QUEUE

* **Dynamic Turn Order:** At the start of combat, all entities roll initiative (d20 + Physical stat). The system uses an **Initiative Queue** to sort combatants and loop through turns fairly.
* **Zone-Based Positioning:** The battlefield uses grid-less zones (`NEAR`, `MID`, `FAR`). Attacking a target two zones away automatically incurs a mathematical disadvantage, calculated entirely in Python.
