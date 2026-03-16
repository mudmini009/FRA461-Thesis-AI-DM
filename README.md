<div align="center">
  <h1>🏰 AI Dungeon Master</h1>
  <p><i>FIBO Senior Project (2026)</i></p>

  [![Project Status](https://img.shields.io/badge/Status-Phase_3_On_Going-success?style=for-the-badge&logo=github)](https://github.com/mudmini009/FRA461-Thesis-AI-DM)
  [![Ruleset](https://img.shields.io/badge/Ruleset-Our_Lite_5e-blueviolet?style=for-the-badge)](./LITE_5E_RULES.md)
  [![Model](https://img.shields.io/badge/AI-Gemini_2.5_Flash_Lite-blue?style=for-the-badge)](https://ai.google.dev/)
</div>

---

> **FIBO DEMO DAY SHOWCASE (Feb 20-21, 2026)**  
> _Interactive AI-Powered Tabletop RPG Engine_

This project demonstrates a **Hybrid AI Game Master** that has shifted focus toward robust backend logic rather than heavy UI. It solves the "AI Hallucination" problem by utilizing a **Two-Path Architecture** that combines the narrative flexibility of Large Language Models (LLM) with the mechanical precision of a **Deterministic Python Rules Engine**. Through a seamless **Multi-Agent Handshake**, math and game state are kept strictly in Python while the AI handles creativity and immersive narration.

---

## 📊 Core Features

- ⚔️ **Two-Path Architecture:** Automatically routes player intent to either the **Rules Engine** (for standard actions) or the **LLM Arbiter** (for creative improv).
- 🎲 **Stateless Rules Engine:** Deterministic Python logic for initiative, dice rolling, range checks, and damage calculation.
- 🤖 **LLM Arbiter:** A "Referee" AI that judges creative actions, assigns Difficulty Classes (DC), and applies symbolic status effects (e.g., `STUNNED`, `RESTRAINED`).
- 🏃 **Tactical Zone Combat:** Grid-less tactical movement using `NEAR`, `MID`, and `FAR` zones with range-based disadvantage.
- 🃏 **Initiative Queue:** A dynamic turn-order system where every character (Player & Enemy) rolls initiative at the start of combat.
- 🧠 **Contextual Short-Term Memory:** Utilizes an efficient $\mathcal{O}(1)$ `collections.deque` sliding window to inject recent gameplay events (max 10) directly into the Arbiter and Narrator LLM prompts, ensuring contextual continuity without wasting API tokens on the stateless routing layer.
- 📜 **Continuous Campaign Record:** Background process that permanently logs an irreversible, real-time transcript of player inputs, DM generations, and hidden internal Python math `[SYSTEM]` checkpoints to a `.txt` file for future RAG summarization models.
- ⚡ **Dynamic Sequence Actions:** Supports complex commands like "I shoot then run away" or "I run in then attack", executing them in the order specified by the user.
- 🎒 **Inventory Engine:** Auto-looting, dynamic disposable items, and rigorous LLM-categorized consumable mechanics.
- 🗣️ **Narrative State Transitions:** Talk your way out of fights with Diplomacy (`PACIFIED` state), or use tactical math-based fleeing mechanics.
- 💡 **QoL Features:** "Idiot-proof" automated API key wizard and developer debug toggles to expose underlying AI processing.

---
## 📜 Game Rules

For the complete mechanical breakdown of the **FIBO Lite 5th Edition** system, check out the official rulebook:  

> [!TIP]
> **[👉 Official Rulebook: LITE_5E_RULES.md](./LITE_5E_RULES.md)**

---

## 🛠️ How to Run

**Prerequisites:**
- Python 3.10+
- Gemini API Key (set in `.env` as `GOOGLE_API_KEY`)

**Launch the Demo:**
```bash
# Initialize environment (Example using Conda)
conda activate ai_dm_core

# Install dependencies
pip install -r requirements.txt

# Run the dedicated launcher
python demo_day.py
```

---

## 🚀 Quick Start / Installation

1.  **Clone the Repository**
    ```bash
    git clone [repository_url]
    cd AI_Dungeon_Master
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Get a Free API Key**
    - The game requires a Google Gemini API Key to run.
    - [Get your free key from Google AI Studio here](https://aistudio.google.com/app/apikey).

4.  **Setup the Environment (Pick ONE method)**
    - **The Automatic Way:** Just run the game! (`python main.py`). The system will detect that you are missing a key, pause the game, and prompt you to paste it in the terminal. It will then automatically create the `.env` file for you.
    - **The Manual Way:** Create a new file named `.env` in the root folder of this project and paste your key inside like this:
      ```env
      GEMINI_API_KEY=your_key_here_xyz123
      ```

5.  **Configure Settings (Optional)**
    - You can tweak the engine's behavior without touching Python code!
    - Open `data/settings.json` to configure:
      - Memory Queue Size (`max_history_events`)
      - Default Difficulty Classes (`default_dc`)
      - AI Creativity (`arbiter_temperature`, `narrator_temperature`)
      - Target Fuzzy Matching strictness (`fuzzy_match_cutoff`).
    - *Note: If you delete this file, the engine will safely regenerate it with default values.*

6.  **Run the Game**
    ```bash
    python main.py
    ```

---

## 📂 Project Structure

```text
AI_Dungeon_Master/
├── docs/                    # [THESIS] Final 2026 graduation thesis reports (WIP)
├── archive/                 # [HISTORY] Past iterations and research
│   ├── phase2_demo/         # Old FIBO lab scripts and demo JSONs
│   ├── references/          # Academic research papers and references
│   └── old_docs/            # Past presentations and progress reports
├── demo_day.py              # [LAUNCHER] Interactive combat prototype entry point
├── main.py                  # Simulation entry point
├── LITE_5E_RULES.md         # [RULES] The formal "Lite 5e" rulebook for the AI and Player
├── ARCHITECTURE.md          # [DOCS] High-level system design overview
├── requirements.txt         # [DEPS] Project dependencies
├── src/
│   ├── engine/              # [ORCHESTRATOR] The Main Simulation Loop
│   │   └── game_loop.py     # Handles turn queue and execution flow
│   ├── ui/                  # [DASHBOARD] CLI Presentation
│   │   └── dashboard.py     # Renders HP, ASCII targets, and zones
│   ├── router/              # [THE BRAIN] Intent Classification & Action Logic
│   │   ├── intent_router.py # Pure LLM interface (JSON output only)
│   │   └── intents.py       # Action execution handlers (MOVE/ATTACK)
│   ├── logic/               # [CALCULATOR] Pure Python Mechanics
│   ├── models/              # [STATE] Single Source of Truth
│   │   ├── character.py     # Data classes for HP, Stats, Zones, and Conditions
│   │   ├── game_state.py    # Global state container
│   │   └── toon_converter.py# Object-to-String serializer for minimal token usage
│   └── services/            # [IO] External APIs & Persistence
│       ├── llm_service.py   # Gemini API integration for Arbitration and Narration
│       ├── data_manager.py  # JSON save/load system
│       └── rag_service.py   # RAG/Context preparation
├── data/                    # [DATA] Game state persistence
│   ├── campaign_backup.json # Clean state for resets
│   ├── campaign_active.json # Current live session data
│   ├── campaign_log.txt     # [STORY] Continuous transcript of all player/DM actions
│   ├── settings_backup.json # Reference file of the original safe default settings
│   ├── settings.json        # [CONFIG] Editable JSON for backend parameters
│   └── world_lore.txt       # [LORE] Static RAG context for the Narrator
├── evaluation/              # [QA] Automated functional testing and verification suite
│   └── combat/              # Two-Path Architecture combat testing
│       ├── evaluation_runner.py  # Validation script with unittest.mock patching
│       ├── scenario_suite.json   # 50 JSON scenarios covering routing, grounding, and syncing
│       └── results/              # Auto-generated timestamped trace logs (.json) and metrics (.csv)
└── tests/                   # [QA] Unit tests for Rules Engine
    ├── test_rules.py        # Pytest verifying Rule Adherence
    ├── test_mock.py         # Sandbox patch testing
    └── test_wraps.py        # Sandbox wraps testing
```

---

## 🧩 Architectural Philosophy

The system is built as a **"Stateless Symbolic Machine"** to ensure 100% mechanical consistency.

1.  **Rule-First Decisioning:** If an action matches a standard game mechanic (Attack, Move, Item), the AI is bypassed for the calculation. The Python engine handles the math.
2.  **Symbolic Grounding:** When the AI allows a creative action (e.g., "I pull the rug"), it must return a **Symbolic Side Effect** (e.g., `target_condition: PRONE`). The Python engine then applies this to the live model.
3.  **TOON Serialization:** Uses a custom compact format for game state to reduce LLM token usage by up to 50%, ensuring faster response times and lower costs.

---

## ☑️ Development Progress

**💾 Data & State Management**
- [x] External JSON State Persistence: Game state (Party & Enemies) is loaded and saved dynamically via `data/campaign.json` using the `DataManager`, avoiding hardcoded stats.
- [x] Bidirectional TOON Serialization (Token-Oriented Object Notation): A custom serialization pipeline (`TOONConverter`) drastically reduces API overhead. State is compressed into TOON before sending to the Arbiter. Furthermore, all LLM API outputs (including Intent Routers and Arbiter logic) are explicitly forced via system prompts to return 1-line TOON (`key:value|key:value`), completely eliminating verbose JSON outputs. This achieves ~50% total token reduction and lower latency.
- [x] Decoupled Health vs. Tactical Conditions: The `Character` model strictly separates Health Status (e.g., Unscathed, Bloodied, Critical) from Tactical Conditions (Enum: `NORMAL`, `STUNNED`, `BLINDED`), ensuring narrative damage doesn't overwrite mechanical penalties.
- [x] Dual-Stream Memory & Context Collapse (State-Dependent Pruning): Upgraded the sliding window into a two-tier system: `combat_memory` (`maxlen=10`) and `story_memory` (`maxlen=5`), both fully configurable via `settings.json`. Implemented an automatic interception hook on `VICTORY` or `FLEE` states that feeds the raw combat logs to an LLM Summarizer. The AI compresses the mathematical battle into a single narrative sentence, pushes it to `story_memory`, and flushes the combat queue, preventing token bloat.
- [x] Static Lore Injection (Static RAG): Implemented a fail-safe retrieval system that loads world-building context from `data/world_lore.txt`. This allows for instant "World Flavor" shifts without code changes. The engine handles missing lore files with a hardcoded fallback.
- [x] Robust Backend Configuration (`settings.json`): Abstracted hardcoded variables into an open-source-friendly JSON config file. Exposes core engine parameters and LLM API settings. Built a bulletproof boot sequence in `DataManager` with Python fallbacks to repair missing config files.
- [x] Persistent Campaign Journal (System Log): Implemented an append-only logging system that permanently records every player input and AI output in real-time to a local file. Includes an auto-reset mechanism triggered during new game boots, creating a parseable script for future save/load summarization.

**🧠 The Intent Router (Two-Path Architecture)**
- [x] Path A (Fixed Rules Routing): Standard RPG mechanics (Attack, Move) bypass the LLM for calculation, sending the action directly to the Python `RulesEngine` to mathematically guarantee zero AI hallucinations.
- [x] Path B (Creative Improv Routing): Complex user prompts are intelligently routed to the `LLMService` (Arbiter), which judges logical feasibility, assigns a DC (Difficulty Class), and automatically outputs a Symbolic Side Effect (e.g., `BLINDED`).
- [x] Dynamic Action Sequencing (`FIXED_COMBO`): The LLM parses multi-step user intents and extracts an `action_order` array. The game engine dynamically executes the sequence exactly as the user typed it.
- [x] Action Fairness & Multi-Agent Economy Guard: The engine strictly enforces a 5e-style action economy by tracking `has_acted` and `has_moved` flags on the `Character` model, refreshed via `reset_turn()`. If an Arbiter denies a creative request, the turn is refunded. However, invalid mechanical requests (e.g., double-attacks, out-of-range moves) are deterministically denied and the turn consumed, ensuring the AI cannot be exploited or cheat.

**⚔️ Combat & Rules Engine**
- [x] Stateless Rules Engine (`RulesEngine`): Pure Python math logic handles all 1d20 dice rolls, AC (Armor Class) checks, Critical Hit doubling logic, and Stat modifiers (PHYS/MENT/SOC). [Newly Expanded] Integrated `resolve_spell` which utilizes the MENT stat and a native 1d10 damage system, and `resolve_item` which wraps consumable logic into standardized dictionary outputs for perfect evaluation tracing.
- [x] Individual Rolling Initiative Queue: Upgraded from legacy "Side vs. Side" turns to a granular, individual turn order. Every combatant rolls 1d20 + PHYS at the start of combat. The loop acts seamlessly, prompting players, triggering EnemyAI, bypassing DEAD characters, and incrementing rounds.
- [x] 3-Tier Intelligent Target Selection: LLM ID Extraction identifies the exact hidden ID (Tier 1). Fuzzy Spell Matching utilizes `difflib.get_close_matches` to catch typos (Tier 2). Auto-Fallback defaults to the first active enemy to prevent wasted inputs (Tier 3).
- [x] Enemy AI Tactics (`EnemyAI`): A lightweight AI that targets the nearest valid opponent and executes a single turn, narrating the sequence automatically on its turn.
- [x] Mechanical Status Effects: Conditions have actual engine consequences. `STUNNED` characters forfeit their turn, while `BLINDED` triggers disadvantage mechanics inside the `RulesEngine`.

**🏃 Spatial & Movement Mechanics (Zones)**
- [x] Tactical Zone Tracking: Grid-less combat utilizing distinct range zones (`NEAR`, `MID`, `FAR`).
- [x] Range Penalties: Using melee weapons outside `NEAR` range automatically triggers "Out of Range" failures, forcing tactical positioning.
- [x] Movement Enforcement (1-Zone Rule): The engine prevents teleportation, restricting movement to exactly 1 adjacent zone per turn and resolving incorrect distance requests.
- [x] AI Gap-Closing: Melee-equipped enemies are programmed to automatically spend their turn moving one zone closer if they are out of range of the player.

**🖥️ UI & Narrative Generation**
- [x] LLM Generative Narration: The system translates raw, calculated Python logs into immersive, D&D-style second-person narration.
- [x] Immersive CLI Dashboard: A cleanly formatted terminal UI that hides raw enemy HP numbers to prevent metagaming, displaying visual health descriptors and exact player stats instead.
- [x] Developer Debug Mode: A toggle command that exposes the raw LLM JSON outputs, parsed intents, and true Python math logs to prove the system works.
- [x] Demo Day Launcher (`demo_day.py`): A dedicated, crash-resistant script with ASCII art, an interactive command loop, and an auto-reset function (`restart`) to cleanly restore state.
- [x] "Idiot-Proof" Onboarding (QoL): An automated boot sequence that intercepts missing `GEMINI_API_KEY` errors, prompts the user via CLI, and generates the `.env` file to prevent crashes.

**🎒 Item & Inventory Mechanics**
- [x] Symbolic Disposable Items (Path B): Complex narrative item usage is routed to the Arbiter. If the AI determines the item is destroyed, it returns a `consumed_item` key, prompting the engine to `.pop()` it from the inventory.
- [x] Automated Victory Looting (Auto-Loot): Upon triggering the `VICTORY` state, the engine extracts item strings from defeated enemies, transfers them to the player, empties enemy pockets, saves the game, and prints a formatted UI summary.
- [x] Hardcoded Consumable Logic (Path A - Mechanics): Standard items bypass the LLM entirely to guarantee zero hallucinations via an `ITEM_EFFECTS` dictionary. `HEAL` items restore HP, `CURE` items revert status conditions, and `DAMAGE` items apply fixed mechanical damage. [Enhanced Security] The `USE` command performs a secure inventory verification, asserting the item's existence in `player.inventory` before executing `.remove()`, neutralizing hallucinated item usage.

**🗣️ Narrative State Transitions**
- [x] Diplomacy & Pacification (Path B): Players can dynamically talk their way out of fights. The LLM Arbiter can assign a `PACIFIED` status. The EnemyAI recognizes this, forfeits its turn, and the game loop correctly counts them as "defeated" to trigger a `VICTORY`.
- [x] Tactical Fleeing Mechanics (Path A): The Intent Router parses "flee" commands as FIXED actions. The `RulesEngine` resolves a contested 1d20 + PHYS check. Enemies receive a Proximity Penalty bonus to their roll based on Zone distance (+5 if Same Zone, +2 if Adjacent). A successful player roll exits combat, while failures rightfully consume the turn.

**🧪 Automated Evaluation & Verification**
- [x] 50-Scenario Functional Stress Test: Developed a comprehensive `evaluation_runner.py` that utilizes `unittest.mock` to patch internal engine methods and capture a deep-dive `trace_log.json`.
- [x] Grounded Result Metrics: Following the implementation of Permission Guardrails and expanded resolvers, the system achieved a 100% Grounding Precision ($P_{ground}$) and 76% State Synchronization ($S_{sync}$), proving the multi-agent "Handshake" is mathematically reliable.

**🚧 Future Work / Missing Features**
- **Narrative State Transitions:**
    - [ ]  **World Exploration Mode:** Disabling Initiative and transitioning to a free-form RAG exploration state.
    - [ ]  **Lore Expansion:** Populating `world_lore.txt` with more complex situational data to further ground the AI's creative narration.
    - [ ]  **Optional Story Summarizer (Load Feature):** Utilizing the newly built Campaign Log to let the LLM generate a "Previously on..." summary when players load a saved game.

---

## 🎓 Acknowledgments & References

This project is built upon the foundational research of AI-assisted narrative generation and LLM-based agent architecture. We would like to acknowledge the following papers for their inspiration on our hybrid system:

- 📄 **Jørgensen et al. (2024)** – *ChatRPG: A Multi-Agent "ReAct" Game Master*
- 📄 **Sakellaridis (2024)** – *LLM-Based Agent as Dungeon Master*
- 📄 **Song et al. (2024)** – *Tool-Assisted AI DM: Function Calling & External Tools*

> [!NOTE]
> *Full academic PDFs can be found in the `<samp>archive/references/</samp>` directory.*
