# 🏰 Architecture Blueprint: AI Dungeon Master (Lite 5e)

**Status:** 🚧 Implementation Phase
**Tech Stack:** Python 3.12+ (Core Logic), Gemini 2.5 Flash-Lite (AI Intelligence), TOON (Data Serialization)
**Architecture Pattern:** Hybrid-Arbitrated "Two-Path" System

---

## 1. Core Philosophy

The system is engineered as a **"Stateless Machine"** to ensure mechanical accuracy, strictly separating narrative creativity from mathematical logic.

- **Stateless Execution:** The Rules Engine is a pure function pipeline. It receives input, calculates a result, and returns output without retaining internal state.
- **Single Source of Truth:** The `GameState` (Python Dataclass) is the absolute authority. AI is never allowed to "remember" game state independently.
- **Deterministic Logic:** All numerical calculations (HP, Dice Rolls, AC checks) occur 100% in Python code. AI is strictly forbidden from performing arithmetic.

---

## 2. System Architecture Diagram

```mermaid
graph TD
    UserInput[User Input] --> Router{Intent Router}

    %% Path A: Fixed Rules
    Router -- "Match: Rule (Attack/Move)" --> PathA[Path A: Fixed Action]
    PathA --> Engine[Rules Engine (Python)]

    %% Path B: Creative
    Router -- "Match: Creative/Unknown" --> PathB[Path B: Creative Action]
    PathB --> Arbiter[LLM Arbitrator]
    Arbiter -- "Define Mechanics (DC/Stat)" --> Engine

    %% Convergence
    Engine -- "Result (Success/Fail/Dmg)" --> Narrator[LLM Narrator]
    Narrator --> Client[Client UI/CLI]

    %% Data Flow
    State[(GameState)] -.-> Toon[TOON Converter]
    Toon -.-> Narrator
    Toon -.-> Arbiter
```

---

## 3. Data Models (The "Truth")

We prioritize Python dataclasses for internal logic speed, but utilize the TOON format for external AI communication to optimize context window usage.

### 3.1 Character Model (`src/models/character.py`)

Represents both Players and Enemies.

| Field       | Type      | Description                                |
| :---------- | :-------- | :----------------------------------------- |
| `id`        | str       | Unique identifier (e.g., p1, e1).          |
| `name`      | str       | Display name.                              |
| `role`      | str       | Class archetype (Fighter, Mage, Rogue).    |
| `stats`     | Dict      | PHYS (Str/Dex), MENT (Int/Wis), SOC (Cha). |
| `hp`        | int       | Current Health Points.                     |
| `max_hp`    | int       | Maximum Health Points.                     |
| `ac`        | int       | Armor Class (Target number to hit).        |
| `zone`      | Enum      | Relative positioning: NEAR, MID, FAR.      |
| `inventory` | List[str] | Items held (e.g., ['Potion', 'Rope']).     |

### 3.2 Game State Model (`src/models/game_state.py`)

The container for the entire simulation snapshot.

- **players:** List of Character objects.
- **enemies:** List of Character objects.
- **turn_count:** Integer tracking rounds.
- **phase:** Enum (PLAYER_TURN, ENEMY_TURN).
- **action_log:** List of strings (Last 5-10 actions). Short-term memory.
- **quest_goal:** Current objective string (e.g., "Find the hidden lever").
- **location_desc:** Environmental context (e.g., "A damp cave with dripping water").

### 3.3 TOON Format Strategy

**Why TOON?** Reduces token usage by ~40% compared to JSON and improves LLM readability for numerical data.

```yaml
# Example TOON Payload sent to Gemini
players[2]{id,name,role,hp,zone,phys,ment,soc,items}:
p1,Valen,Fighter,18/20,NEAR,+3,0,+1,[Potion]
p2,Elara,Mage,12/15,MID,-1,+3,+1,[Scroll]

enemies[2]{id,name,hp,zone,condition}:
e1,Spider A,0/15,NEAR,Dead
e2,Spider B,7/15,NEAR,Injured
```

---

## 4. The Two-Path Routing Logic (`src/router/`)

The Router is the "Frontal Lobe" of the system. It uses **Gemini 2.5 Flash-Lite** to classify user intent _before_ any logic is executed.

### Decision Tree

- **Input:** "I cast Firebolt at the spider!"

  - **Check:** Matches standard Lite 5e keywords (Attack, Cast, Move, Use Item).
  - **Result:** `FIXED` -> Path A (Rules Engine).

- **Input:** "I want to tie the rope to trip the goblin."
  - **Check:** No standard rule matches. Complex intent.
  - **Result:** `CREATIVE` -> Path B (LLM Arbitrator).

---

## 5. Rules Engine (`src/logic/`)

A collection of Pure Python Functions. This layer is the "Calculator."

### 5.1 Core Mechanics

- `roll(expression: str) -> dict`: Parses "1d20", "2d6+3". Returns stateless dict.
- `resolve_attack(attacker, target) -> dict`:
  - Calculation: d20 + PHYS vs Target AC.
  - Crit Logic: If natural 20, double damage dice.
  - Output: Object containing `{is_hit, damage, is_crit}`.
- `resolve_check(actor, stat, dc) -> bool`:
  - Calculation: d20 + Stat >= DC.

### 5.2 Ability Handlers

Hardcoded logic for specific class feats to ensure balance.

- `use_second_wind(char)`: Heals 1d10 + Level.
- `cast_magic_missile(char)`: Auto-hit, 3d4+3 Force damage.

---

## 6. Execution Flow Examples

### Scenario A: Combat (Path A - Fixed Action)

_Optimized for speed and precision._

1.  **Player:** "I swing my longsword at the Wolf Spider!"
2.  **Router:** Classifies as `FIXED` (Attack). Calls `RulesEngine.resolve_attack(p1, e1)`.
3.  **Engine (Python):**
    - Rolls d20 (result 15) + PHYS (+3) = 18.
    - Checks vs AC (12) -> HIT.
    - Rolls Damage -> 6.
    - Updates State: e1.hp decreases to 9.
4.  **System Log:** Generates raw string: `[System]: Hit! Dealt 6 Damage.`
5.  **LLM Narrator:** Receives Log + State.
    - **Output:** "Your blade strikes true, cutting deep into the spider's leg! It screeches in pain."

### Scenario B: Exploration (Path B - Creative Action)

_Optimized for flexibility._

1.  **Player:** "I want to decipher the ancient runes on the wall."
2.  **Router:** Classifies as `CREATIVE`. Forwards to LLM Arbitrator.
3.  **LLM Arbitrator:**
    - Analysis: Task requires intellect. Difficulty is Moderate.
    - Output (Function Call): `resolve_check(p1, MENT, 12)`
4.  **Engine (Python):**
    - Rolls d20 (10) + MENT (+2) = 12.
    - Checks 12 >= 12 -> SUCCESS.
5.  **LLM Narrator:** Receives "Success" signal.
    - **Output:** "You successfully translate the runes. They read: 'Beware of the shadows ahead...'"

---

## 7. Combat Loop Mechanics (Side Initiative)

To simplify the UI and logic flow, the system uses Side Initiative.

- **Phase 1: Player Turn (Blue Phase)**

  - Players can act in any order.
  - Engine accepts inputs for P1, P2, P3, etc.
  - Turn ends when all players act or "End Turn" is triggered.

- **Phase 2: Enemy Turn (Red Phase)**
  - **AI Logic:** Enemies select targets based on Zone (Prefer NEAR).
  - **Batch Processing:** Engine runs `resolve_attack` for all active enemies instantly.
  - **Narrative:** LLM summarizes the entire enemy round: _"The first spider bites P1, while the second shoots a web at P2 but misses."_

---

## 8. RAG Context Strategy

Every prompt sent to the LLM (Narrator or Arbitrator) includes a strictly formatted Context Block.

1.  **Current State (TOON):** Real-time HP, Position, and Inventory.
2.  **Narrative Context:**
    - Location: "The Dark Forest" (Sets the tone).
    - Goal: "Defeat the Spider Queen" (Keeps focus).
3.  **Action History:** Last 5 entries from `action_log` (Ensures continuity).
4.  **Rule Context:** Static definitions of Stats (PHYS/MENT/SOC) so the AI understands the capabilities.
