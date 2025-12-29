# 🏰 AI Dungeon Master (Lite 5e) - Python Core

A "Hybrid-Arbitrated" AI Dungeon Master backend system.
Refactored from Flutter to **Python** for automated simulation and logic verification.
Powered by **Gemini 2.5 Flash-Lite** and optimized with **TOON**.

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
├── src/
│   ├── models/              # [Data Layer] - Single Source of Truth
│   │   ├── character.py     # Defines Character stats (PHYS/MENT/SOC), HP, Zone.
│   │   ├── game_state.py    # Central state object holding Players, Enemies, and History.
│   │   └── toon_converter.py # Helper to convert Objects -> TOON format for LLM Prompting.
│   │
│   ├── logic/               # [Core Logic] - Stateless Rules Engine (The "Calculator")
│   │   ├── rules_engine.py  # Main entry for Path A. Handles `resolve_attack`, `resolve_check`.
│   │   ├── dice_roller.py   # Pure RNG functions (d20, damage rolls). No AI here.
│   │   └── abilities.py     # Hardcoded logic for Class Feats (e.g., Second Wind, Smite).
│   │
│   ├── router/              # [The Brain] - Decides Path A vs Path B
│   │   ├── intent_router.py # Logic to classify input: "Fixed Action" (Rules) or "Creative" (AI).
│   │   └── intents.py       # Enum definitions for intent types.
│   │
│   └── services/            # [External Services] - AI & Data Fetching
│       ├── llm_service.py   # API Client for Gemini 2.5 Flash-Lite (Narrator/Arbitrator).
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

- `roll_dice(notation)`: Input "1d20" -> Output int.
- `resolve_attack(attacker, target)`: Logic for d20 + PHYS vs Target AC.
- `resolve_check(actor, stat, dc)`: Logic for d20 + Stat >= DC.

## 🔄 Execution Flows

### Scenario A: Combat (Path A - Fixed Action)

**Player:** "I attack the Wolf Spider!"

1. **Router:** Detect Attack → Call `rules_engine.resolve_attack(p1, e1)`
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
