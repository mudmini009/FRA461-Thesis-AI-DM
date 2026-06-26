<div align="center">
  <h1>🏰 DualPath-Core</h1>
  <p><i>A Multi-Agent Hybrid TTRPG Engine | FIBO Senior Thesis (2026)</i></p>

  [![Project Status](https://img.shields.io/badge/Status-Final_Release-success?style=for-the-badge&logo=github)](https://github.com/mudmini009/dualpath-core-ttrpg-engine)
  [![Ruleset](https://img.shields.io/badge/Ruleset-Our_Lite_5e-blueviolet?style=for-the-badge)](./LITE_5E_RULES.md) 
  [![Model](https://img.shields.io/badge/AI-Gemini_2.5_Flash_Lite-blue?style=for-the-badge)](https://ai.google.dev/)
</div>

---

> **🎓 FIBO SENIOR THESIS (2026) - FINAL RELEASE & GRADUATION DEMO**
> _Next-Gen Agentic Orchestration for Tabletop RPGs_

This project features a **Multi-Agent Hybrid Architecture** designed to solve the "AI Hallucination" problem in TTRPGs. By implementing a **Two-Path Orchestrator**, the system autonomously routes player intent between a **Deterministic Python Rules Engine** (for mechanical precision) and an **LLM-based Creative Arbiter** (for improvisational logic). Through a rigorous **Multi-Agent Handshake**, the engine ensures that all game state mutations are grounded in hard-coded logic while maintaining the narrative flexibility of Large Language Models.

> ### 🎓 Thesis Artifact Download Center
> 
> | Document Type | File Link | Key Focus Area |
> | :--- | :--- | :--- |
> | 📄 **Thesis Report** | [docs/อ.โซ่-อ.ปอ-AI DM-FinalSenior.pdf](./docs/อ.โซ่-อ.ปอ-AI%20DM-FinalSenior.pdf) | Full academic manuscript, methodology & diagrams |
> | 📊 **Defense Slides** | [docs/Thesis_Final.pdf](./docs/Thesis_Final.pdf) | Final Q&A presentation slide deck |
> | 🖼️ **Academic Poster** | [docs/65340500046_Poster.pdf](./docs/65340500046_Poster.pdf) | Senior project showcase poster |

---

## 📊 Core Features

- **`⚔️ Two-Path Architecture`** — Automatically routes player intent to either the rules engine (Path A) or creative LLM arbiter (Path B).
- **`🎲 Stateless Rules Engine`** — Pure Python logic calculates D&D 5e dice checks, AC, combat math, and ranges deterministically.
- **`🤖 LLM Arbiter`** — Evaluates creative roleplay actions, determines DC, and returns symbolic status conditions (`STUNNED`, `PRONE`).
- **`🏃 Tactical Zone Combat`** — Grid-less zone-based movement (`NEAR`, `MID`, `FAR`) with automatic distance restrictions.
- **`🃏 Initiative Turn Queue`** — Dynamic round sequencing rolling `d20 + PHYS` for fair turn order.
- **`🧠 Contextual Short Memory`** — Efficient sliding-window deque limits LLM prompt context to the last 10 round states.
- **`📜 Campaign Logging`** — Background logging of player actions and system mathematical check logs to `campaign_log.txt`.
- **`⚡ Dynamic Sequence Actions`** — Combines movement and combat in specified orders (e.g. "move NEAR and smite").
- **`🎒 Inventory Engine`** — Dynamic auto-looting, disposable items, and strict consumable tracking.
- **`🗣️ Narrative Diplomacy`** — Talk out of encounters utilizing social checks and the `PACIFIED` state.
- **`💡 Developer Debug Mode`** — Diagnostic toggle exposing raw LLM outputs, AST structures, and dice rolls.

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
python main.py
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
├── docs/                    # [THESIS] Graduation reports, presentation slides, posters, and system manuals
│   ├── Thesis_Final.pdf         # Defense presentation slides
│   ├── อ.โซ่-อ.ปอ-AI DM-FinalSenior.pdf # Final graduation thesis report
│   ├── 65340500046_Poster.pdf   # Project academic poster
│   ├── appendix_c_project_manual.md # Appendix C: System structure and usage manuals (Thai)
│   ├── presentation_backup_slides_appendix.md # Q&A Defense slides appendix (Thai)
│   ├── evaluation_master_appendix_thai.md # Comprehensive 90-scenario evaluation matrix (Thai)
│   └── baseline_comparison_deep_dive_th.md # Proposed vs Baseline model deep-dive (Thai)
├── archive/                 # [HISTORY] Past iterations and research
│   ├── phase2_demo/         # Old FIBO lab scripts and demo JSONs
│   ├── references/          # Academic research papers and references
│   └── old_docs/            # Past presentations and progress reports
├── main.py                  # [ENTRY] Full game entry point and dedicated launcher
├── LITE_5E_RULES.md         # [RULES] The formal "Lite 5e" rulebook for the AI and Player
├── ARCHITECTURE.md          # [DOCS] High-level system design overview (proposed Two-Path engine)
├── requirements.txt         # [DEPS] Project dependencies (frozen from conda env)
├── src/
│   ├── agents/              # [AGENTS] Specialized LLM agents
│   │   ├── base.py          # BaseLLMProvider – shared API setup & model init
│   │   ├── arbiter_agent.py # ArbiterAgent – creative action evaluation & side effects
│   │   ├── narrator_agent.py# NarratorAgent – descriptions & flavor text
│   │   ├── campaign_agent.py# CampaignAgent – recaps & prologue cold-opens
│   │   ├── character_agent.py# CharacterAgent – world lore & background setup
│   │   ├── quest_architect_agent.py # QuestArchitectAgent – high-level quest summary
│   │   └── quest_cartographer_agent.py # QuestCartographerAgent – map generation & 7-Layer Guardrails
│   ├── engine/              # [ORCHESTRATOR] Pre-game flow & main loop
│   │   ├── startup.py       # Pre-game flow: character sheets, API key checks, prologue
│   │   └── game_loop.py     # Main loop orchestrating Explore/Combat transitions
│   ├── ui/                  # [CLI] Presentation layer (HUD and menus)
│   │   ├── character_sheet.py # Character stats & world lore renderer
│   │   ├── dashboard.py     # ASCII target trackers & status bars
│   │   ├── menu.py          # Main, recap, and pause menus
│   │   ├── combat_ui.py     # Combat HUD and log renderer
│   │   └── exploration_ui.py# Exploration/Hub HUD with command hints & quest boards
│   ├── router/              # [THE BRAIN] Intent Classification & Routing
│   │   ├── intent_router.py # Two-path orchestrator routing player input
│   │   ├── intents.py       # Intent execution (Smite constraints & moves check)
│   │   └── exploration_router.py # Regex/LLM hybrid router
│   ├── logic/               # [CALCULATOR] Pure Python Mechanics
│   │   ├── rules_engine.py  # D&D 5e dice checks, AC, combat calculations
│   │   ├── combat_manager.py# Initiative queue manager
│   │   ├── enemy_ai.py      # Enemy target selection (lowest HP focus)
│   │   ├── enemy_factory.py # Skeleton & Flesh scaling algorithm
│   │   ├── dice_roller.py   # Base RNG rolls
│   │   ├── abilities.py     # Ability registry
│   │   └── time_manager.py  # Time flow & automatic rest healing logic
│   ├── models/              # [STATE] Single Source of Truth
│   │   ├── character.py     # Character dataclass (stats, abilities, conditions)
│   │   ├── game_state.py    # GameState container
│   │   └── toon_converter.py# Bidirectional TOON parser
│   └── services/            # [IO] External APIs & Save/Load Persistence
│       ├── llm_service.py   # Backward-compatible agent facade
│       ├── data_manager.py  # Campaign saving/loading system
│       └── rag_service.py   # Context synthesis
├── data/
│   ├── active/              # Live session data (session state & continuous logs)
│   │   ├── campaign_active.json # Current active save file
│   │   ├── campaign_log.txt     # Irreversible campaign session history
│   │   └── world_lore.txt       # Active lore context
│   ├── config/              # User-facing settings & database templates
│   │   ├── settings.json        # Dynamic engine parameters (max history, DC, etc.)
│   │   ├── settings_backup.json # Safe settings fallback
│   │   └── bestiary.json        # Enemy blueprint databases
│   └── premade/             # Out-of-the-box template databases
│       ├── characters/      # Precompiled class JSONs
│       └── lore/            # Pre-written setting files
└── evaluation/              # [QA] Comprehensive validation suites
    ├── combat/              # Old combat simulation files
    │   ├── evaluation_runner.py # Combat-only runner
    │   └── scenario_suite.json  # 50 scenarios
    └── system_suite/        # Full System Q/A & comparative suite
        ├── comprehensive_runner.py # Comparative 90-scenario runner
        ├── generate_master_suite.py# Programmatic scenario generator
        ├── master_scenario_suite.json # Full 90-scenario master suite
        └── results/             # Proposed vs Baseline CSV summaries and trace logs
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

---

## 📜 Citation

If you use the DualPath-Core architecture, code, or evaluation datasets in your academic research, please cite our upcoming work:

```bibtex
@misc{mudmini0092026dualpath,
  author = {Nott, Mud},
  title = {DualPath-Core: A Multi-Agent Hybrid TTRPG Engine},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub Repository},
  howpublished = {\url{https://github.com/mudmini009/dualpath-core-ttrpg-engine}}
}
```
