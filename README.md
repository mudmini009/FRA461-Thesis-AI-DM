<div align="center">
  <h1>🏰 DualPath-Core</h1>
  <p><i>A Multi-Agent Hybrid TTRPG Engine | FIBO Senior Thesis (2026)</i></p>

  [![Project Status](https://img.shields.io/badge/Status-Phase_3_On_Going-success?style=for-the-badge&logo=github)](https://github.com/mudmini009/FRA461-Thesis-AI-DM)
  [![Ruleset](https://img.shields.io/badge/Ruleset-Our_Lite_5e-blueviolet?style=for-the-badge)](./LITE_5E_RULES.md) 
  [![Model](https://img.shields.io/badge/AI-Gemini_2.5_Flash_Lite-blue?style=for-the-badge)](https://ai.google.dev/)
</div>

---

> **FIBO PROGRESS 2 SHOWCASE** > _Next-Gen Agentic Orchestration for Tabletop RPGs_

This project features a **Multi-Agent Hybrid Architecture** designed to solve the "AI Hallucination" problem in TTRPGs. By implementing a **Two-Path Orchestrator**, the system autonomously routes player intent between a **Deterministic Python Rules Engine** (for mechanical precision) and an **LLM-based Creative Arbiter** (for improvisational logic). Through a rigorous **Multi-Agent Handshake**, the engine ensures that all game state mutations are grounded in hard-coded logic while maintaining the narrative flexibility of Large Language Models.

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
├── main.py                  # [ENTRY] Full game entry point
├── LITE_5E_RULES.md         # [RULES] The formal "Lite 5e" rulebook for the AI and Player
├── ARCHITECTURE.md          # [DOCS] High-level system design overview
├── requirements.txt         # [DEPS] Project dependencies
├── src/
│   ├── agents/              # [AGENTS] Specialized LLM agents (post-refactor)
│   │   ├── base.py          # BaseLLMProvider – shared API setup & model init
│   │   ├── arbiter_agent.py # ArbiterAgent – action validation & item categorization
│   │   ├── narrator_agent.py# NarratorAgent – combat narration & outcome description
│   │   ├── campaign_agent.py# CampaignAgent – recap & cold-open prologue generation
│   │   └── character_agent.py# CharacterAgent – Zero-Hallucination character & world lore 
│   ├── engine/              # [ORCHESTRATOR] Pre-game flow & main combat loop
│   │   ├── startup.py       # Pre-game flow: character creation, lore, prologue
│   │   └── game_loop.py     # Handles turn queue and execution flow
│   ├── ui/                  # [CLI] Presentation layer
│   │   ├── character_sheet.py # Character Sheet & World Lore TUI renderers
│   │   ├── dashboard.py     # Renders HP, ASCII targets, and zones
│   │   └── menu.py          # Main menu, recap menu
│   ├── router/              # [THE BRAIN] Intent Classification & Action Logic
│   │   ├── intent_router.py # Two-path router (FIXED vs CREATIVE)
│   │   └── intents.py       # Action execution handlers (MOVE/ATTACK/USE)
│   ├── logic/               # [CALCULATOR] Pure Python Mechanics
│   │   ├── rules_engine.py  # Dice, DC checks, damage math
│   │   ├── combat_manager.py# Initiative queue
│   │   ├── enemy_ai.py      # Enemy turn logic
│   │   ├── dice_roller.py   # Dice rolling utilities
│   │   └── abilities.py     # Ability definitions
│   ├── models/              # [STATE] Single Source of Truth
│   │   ├── character.py     # Character dataclass (stats, lore, conditions)
│   │   ├── game_state.py    # Global state container
│   │   └── toon_converter.py# TOON serializer for minimal token usage
│   └── services/            # [IO] External APIs & Persistence
│       ├── llm_service.py   # Backward-compatible façade over src/agents/
│       ├── data_manager.py  # JSON save/load system
│       └── rag_service.py   # RAG/Context preparation
├── data/
│   ├── active/              # Live session data (written during gameplay)
│   │   ├── campaign_active.json  # Current save state
│   │   ├── campaign_log.txt      # Continuous transcript
│   │   └── world_lore.txt        # Active world context for the Narrator
│   ├── config/              # Engine configuration (edited by user)
│   │   ├── settings.json         # Editable engine parameters
│   │   ├── settings_backup.json  # Safe default settings fallback
│   │   └── bestiary.json         # Enemy stat templates
│   └── premade/             # Hand-crafted selection templates
│       ├── characters/      # Premade class JSON files (fighter, mage, rogue…)
│       └── lore/            # Premade world lore .txt files
├── archive/progress_2/      # Deprecated files from pre-Phase-3 (kept for history)
├── evaluation/              # [QA] Evaluation & regression suite
│   └── combat/
│       ├── evaluation_runner.py  # 50-scenario regression runner
│       ├── scenario_suite.json   # Structured test scenarios
│       └── results/              # Auto-generated trace logs and metrics CSV
└── tests/                   # [QA] Unit tests
    ├── test_rules.py        # RulesEngine pytest coverage
    ├── test_persistence.py  # DataManager save/load parity
    └── test_*.py            # Other scenario and module tests
```


---

## 🧩 Architectural Philosophy

The system is built as a **"Stateless Symbolic Machine"** utilizing a **Hybrid-Arbitrated Two-Path System** to ensure 100% mechanical consistency while maintaining narrative freedom.

1.  **Rule-First Decisioning (Path A):** If an action matches a standard game mechanic (Attack, Move, Item), the AI is bypassed for the calculation. The Python engine handles the math deterministically.
2.  **Symbolic Grounding (Path B):** When the AI allows a creative action (e.g., "I pull the rug"), it must return a **Symbolic Side Effect** (e.g., `target_condition: PRONE`). The Python engine then applies this to the live model.
3.  **TOON Serialization:** Uses a custom compact format (Token-Oriented Object Notation) for game state to reduce LLM token usage by up to 50%, ensuring faster response times and lower costs.

*(Note: Earlier extensive architectural drafts have been preserved in the `archive/` folder).*

---

## ☑️ Development Progress

> [!NOTE]
> The full architectural breakdown and progression log has grown significantly. 
> Please see the dedicated [**FEATURE_TRACKER.md**](FEATURE_TRACKER.md) for a comprehensive list of all technical guardrails, agent architectures, and game mechanics implemented in the AI Dungeon Master.



---

## 🎓 Acknowledgments & References

This project is built upon the foundational research of AI-assisted narrative generation and LLM-based agent architecture. We would like to acknowledge the following papers for their inspiration on our hybrid system:

- 📄 **Jørgensen et al. (2024)** – *ChatRPG: A Multi-Agent "ReAct" Game Master*
- 📄 **Sakellaridis (2024)** – *LLM-Based Agent as Dungeon Master*
- 📄 **Song et al. (2024)** – *Tool-Assisted AI DM: Function Calling & External Tools*

> [!NOTE]
> *Full academic PDFs can be found in the `<samp>archive/references/</samp>` directory.*
