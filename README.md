# 🏰 AI Dungeon Master (Lite 5e)

A "Hybrid-Arbitrated" AI Dungeon Master system designed for casual, single-device play.
Built with **Flutter** & **Dart**, powered by **Gemini 2.5 Flash-Lite**, and optimized with **TOON**.

---

## 🧠 Core Philosophy

The system is designed as a **"Stateless Machine"** to ensure accuracy and reduce complexity.

- **Stateless:** `Rules Engine` receives input → calculates → returns output (does not store state itself).
- **Single Source of Truth:** `GameState` (Dart Object) is the only source of truth for the game.
- **Deterministic Logic:** All numerical calculations (HP, Dice) happen 100% in Code (AI is forbidden from doing math).
- **Two-Path Architecture:** Balances rule adherence with narrative flexibility (Rule-First vs. LLM-First).

---

## 📂 Project Structure

```text
my_ai_dm_project/
├── pubspec.yaml             # Dependencies (flutter_gemini, etc.)
├── lib/
│   ├── main.dart            # Application Entry Point
│   │
│   ├── models/              # [Data Layer] - Single Source of Truth
│   │   ├── character.dart   # Defines Character stats (PHYS/MENT/SOC), HP, Zone.
│   │   ├── game_state.dart  # Central state object holding Players, Enemies, and History.
│   │   └── toon_converter.dart # Helper to convert Dart Objects -> TOON format for LLM Prompting.
│   │
│   ├── logic/               # [Core Logic] - Stateless Rules Engine (The "Calculator")
│   │   ├── rules_engine.dart # Main entry for Path A. Handles `resolveAttack`, `resolveCheck`.
│   │   ├── dice_roller.dart  # Pure RNG functions (d20, damage rolls). No AI here.
│   │   └── abilities.dart    # Hardcoded logic for Class Feats (e.g., Second Wind, Smite).
│   │
│   ├── router/              # [The Brain] - Decides Path A vs Path B
│   │   ├── intent_router.dart # Logic to classify input: "Fixed Action" (Rules) or "Creative" (AI).
│   │   └── intents.dart      # Enum definitions for intent types.
│   │
│   ├── services/            # [External Services] - AI & Data Fetching
│   │   ├── llm_service.dart  # API Client for Gemini 2.5 Flash-Lite (Narrator/Arbitrator).
│   │   └── rag_service.dart  # Prepares Context (State + History + Rules) for the LLM.
│   │
│   └── ui/                  # [Presentation Layer] - Minimalist Single-Device UI
│       ├── main_screen.dart # The Dashboard (Map + Chat + Selector).
│       ├── components/
│       │   ├── character_card.dart # Displays active player stats (PHYS/MENT/SOC).
│       │   ├── zone_map.dart       # Abstract Zone visualization (Near/Mid/Far).
│       │   └── action_log.dart     # Chat interface distinguishing System/AI messages.
│       └── popups/
│           └── enemy_popup.dart    # Simple "Inspect" card for enemies.
│
└── test/                    # [Quality Assurance] - Proof of Mechanism
    └── rules_test.dart      # Unit Tests verifying Rule Adherence (Attack rolls, HP updates).
```

---

## 🧩 Key Architectural Concepts

### 1. Two-Path Routing (`lib/router/`)

The **Router** receives player input and decides the processing path using a decision tree logic.

- **Path A (Fixed Action):** User input matches a rule (e.g., "Attack").
  - _Flow:_ `Router` -> `Rules Engine` (Calc) -> `LLM` (Narrate).
- **Path B (Creative Action):** User input is open-ended (e.g., "Persuade").
  - _Flow:_ `Router` -> `LLM` (Arbitrate DC) -> `Rules Engine` (Roll) -> `LLM` (Narrate).

### 2. Data Strategy (`lib/models/`)

- **Internal:** Uses Dart Classes for high-performance UI updates.
- **External:** Uses **TOON** format in `toon_converter.dart` to minimize token usage (~40% savings) when sending state to Gemini Flash-Lite.

**TOON Format Example:**

```yaml
players[4]{id,name,role,hp,zone,phys,ment,soc,items}: p1,Valen,Fighter,18/20,NEAR,+3,0,+1,[Potion]
```

### 3. Rules Engine (`lib/logic/`)

The "Calculator" containing pure functions.

- `rollDice(String notation)`: Input "1d20" -> Output `int`.
- `resolveAttack(Character attacker, Character target)`: Logic for `d20 + PHYS` vs `Target AC`.
- `resolveCheck(Character actor, Stat stat, int dc)`: Logic for `d20 + Stat` >= `DC`.

---

## 🔄 Execution Flows

### Scenario A: Combat (Path A - Fixed Action)

> **Player:** "I attack the Wolf Spider!"

1.  **Router:** Detect `Attack` → Call `RulesEngine.resolveAttack(p1, e1)`
2.  **Engine:** Roll d20, Check vs AC, Roll Dmg, Update State.
3.  **System:** Create Log `[System]: Hit! Dealt 6 Dmg.`
4.  **RAG:** Send `Log` + `State (TOON)` to **LLM Narrator**.
5.  **LLM:** "Your blade strikes true, cutting deep into the spider!"

### Scenario B: Exploration (Path B - Creative Action)

> **Player:** "I want to decipher the ancient runes on the wall."

1.  **Router:** Detect `Unknown` → Call **LLM (Arbitrator)**.
2.  **LLM (Arbitrator):** Analyze intent, set Difficulty (`DC 12`), Output `Call: resolveCheck(p1, MENT, 12)`.
3.  **Rules Engine:** Roll d20 + MENT, Check Success/Fail.
4.  **LLM (Narrator):** Receive Success → "You successfully translate the runes! They read: 'Beware of traps ahead'."

---

## ⚔️ Combat Loop (Side Initiative)

To solve the Single Device UI problem, we use **"Side Initiative"**:

1.  **Phase 1: Players Turn** 🔵
    - UI unlocks for all players.
    - Players choose who acts first.
2.  **Phase 2: Enemy Turn** 🔴
    - UI Locks.
    - **AI Logic:** Enemies select targets and Engine runs `resolveAttack` in batch.
    - **LLM:** Narrates summary.

---
