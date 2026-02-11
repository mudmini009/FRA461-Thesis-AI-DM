# 🏰 AI Dungeon Master (Lite 5e) - Python Core

A "Hybrid-Arbitrated" AI Dungeon Master backend system.
Refactored from Flutter to **Python** for automated simulation and logic verification.
Powered by **Gemini 2.5 Flash-Lite** and optimized with **TOON**.

---

# 🐉 AI Dungeon Master Core

## 🚀 Current Progress (Phase 1: Architecture)

We are building the **Two-Path Architecture** described in the thesis.

### ✅ Components Completed:

1.  **Intent Router (`src/router/`):**
    - Uses **Gemini 2.5 Flash-Lite** to classify user input.
    - Distinguishes between `FIXED` (Rules) and `CREATIVE` (Narrative) actions.
2.  **Rules Engine (`src/logic/`):**
    - `dice_roller.py`: A stateless, deterministic dice parser.
    - `enemy_ai.py`: Basic Side Initiative AI (Auto-Turn).
    - Supports standard D&D notation (e.g., `1d20+5`).

### 🕹️ How to Run

1. Activate environment: `conda activate ai_dm_core` (or your preferred env)
2. Run the main loop:
   ```bash
   python src/router/intent_router.py
   ```

---

## 🧠 Core Philosophy

The system is designed as a **"Stateless Machine"** to ensure accuracy and reduce complexity.

- **Stateless:** `Rules Engine` receives input → calculates → returns output (does not store state itself).
- **Single Source of Truth:** `GameState` (Python Object) is the only source of truth for the game.
- **Deterministic Logic:** All numerical calculations (HP, Dice) happen 100% in Code (AI is forbidden from doing math).
- **Two-Path Architecture:** Balances rule adherence with narrative flexibility (Rule-First vs. LLM-First).

---

## 📂 Project Structure

```text
my_ai_dm_project/
├── .env                     # Secrets (API Key) - gitignored
├── requirements.txt         # Python Dependencies (google-generativeai, etc.)
├── main.py                  # Simulation Entry Point
├── data/                    # [Persistence Layer]
│   └── campaign.json        # External Game Data (Party & Enemies)
├── src/
│   ├── models/              # [Data Layer] - Single Source of Truth
│   │   ├── character.py     # Defines Character stats (PHYS/MENT/SOC), HP, Zone.
│   │   ├── game_state.py    # Central state object holding Players, Enemies, and History.
│   │   └── toon_converter.py # Helper to convert Objects -> TOON format for LLM Prompting.
│   │
│   ├── logic/               # [Core Logic] - Stateless Rules Engine (The "Calculator")
│   │   ├── rules_engine.py  # Main entry for Path A. Handles `resolve_attack`, `resolve_check`.
│   │   ├── enemy_ai.py      # [NEW] Logic for Enemy Turn (Target Selection & Attack).
│   │   ├── dice_roller.py   # Pure RNG functions (d20, damage rolls). No AI here.
│   │   └── abilities.py     # Hardcoded logic for Class Feats (e.g., Second Wind, Smite).
│   │
│   ├── router/              # [The Brain] - Decides Path A vs Path B
│   │   ├── intent_router.py # Logic to classify input: "Fixed Action" (Rules) or "Creative" (AI).
│   │   └── intents.py       # Enum definitions for intent types.
│   │
│   └── services/            # [External Services] - AI & Data Fetching
│       ├── llm_service.py   # API Client for Gemini 2.5 Flash-Lite (Narrator/Arbitrator).
│       ├── data_manager.py  # Loads JSON data and converts strings to Enums.
│       └── rag_service.py   # Prepares Context (State + History + Rules) for the LLM.
│
└── tests/                   # [Quality Assurance] - Proof of Mechanism
    └── test_rules.py        # Pytest unit tests verifying Rule Adherence.
```

## 🧩 Key Architectural Concepts

### 1. Two-Path Routing (src/router/)

The Router receives player input and decides the processing path using a decision tree logic.

**Path A (Fixed Action):** User input matches a rule (e.g., "Attack").
_Flow:_ Router -> Rules Engine (Calc) -> LLM (Narrate).

**Path B (Creative Action):** User input is open-ended (e.g., "Persuade").
_Flow:_ Router -> LLM (Arbitrator) -> Rules Engine (Roll) -> LLM (Narrate).

### 2. Data Strategy (src/models/)

**Internal:** Uses Python Classes (Dataclasses) for fast processing.

**External:** Uses TOON format in `toon_converter.py` to minimize token usage (~40% savings) when sending state to Gemini Flash-Lite.

**TOON Format Example:**

```yaml
players[4]{id,name,role,hp,zone,phys,ment,soc,items}: p1,Valen,Fighter,18/20,NEAR,+3,0,+1,[Potion]
```

### 3. Rules Engine (src/logic/)

The "Calculator" containing pure functions.

- `roll(expression)`: Input "1d20" -> Output dict `{total, rolls, is_crit}`.
- `resolve_attack(attacker, target)`: Logic for d20 + PHYS vs Target AC.
- `resolve_check(actor, stat, dc)`: Logic for d20 + Stat >= DC.

## 🔄 Execution Flows

### Scenario A: Combat (Path A - Fixed Action)

**Player:** "I attack the Wolf Spider!"

1. **Router:** Detect Attack → Call `RulesEngine.resolve_attack(p1, e1)`
2. **Engine:** Roll d20, Check vs AC, Roll Dmg, Update State.
3. **System:** Create Log `[System]: Hit! Dealt 6 Dmg.`
4. **RAG:** Send Log + State (TOON) to LLM Narrator.
5. **LLM:** "Your blade strikes true, cutting deep into the spider!"

### Scenario B: Exploration (Path B - Creative Action)

**Player:** "I want to decipher the ancient runes on the wall."

1. **Router:** Detect Unknown → Call LLM (Arbitrator).
2. **LLM (Arbitrator):** Analyze intent, set Difficulty (DC 12), Output Call: `resolve_check(p1, MENT, 12)`.
3. **Rules Engine:** Roll d20 + MENT, Check Success/Fail.
4. **LLM (Narrator):** Receive Success → "You successfully translate the runes! They read: 'Beware of traps ahead'."

---

## 🧠 Phase 2: The AI Arbiter

The system now supports **Improvised Creative Actions** (Path B).

### 🤖 The Arbiter Role

When a player attempts a non-standard action, the system calls the `LLMService` which acts as a Referee.

1.  **Context Aware:** It reads the **Inventory** of ALL party members (Teamwork support).
2.  **Physics Check:** It validates if the action is logically possible (Arbiter Judgement).
3.  **Stat Assignment:** It decides which Stat (PHYS/MENT/SOC) to roll and sets a DC (Difficulty Class).

### 🗣️ The Narrator Role

After the dice roll (Calculated by Python), the result is sent back to the LLM to generate an immersive description.

**Example:**

> **Player:** "I use my rope to trip the running goblin."
> **Arbiter:** "Allowed (Has Rope). Roll PHYS (DC 15)."
> **Dice:** Player rolls 18 (Success).
> **Narrator:** "You deftly toss the rope, tangling the goblin's legs. It crashes face-first into the dirt!"

### 🔗 Symbolic Grounding (Side Effects)

The Arbiter doesn't just narrate; it **updates the Python Game State**.

- If the Arbiter determines a target suffers a Condition (e.g., `RESTRAINED`, `PRONE`), it returns this in the JSON.
- The **Rules Engine** automatically applies this condition to the target's data model.
- **Result:** The Goblin's status explicitly changes from `NORMAL` to `RESTRAINED` in code, affecting future logic.
