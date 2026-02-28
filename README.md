# 🏰 AI Dungeon Master (FIBO Senior Project)

> **FIBO DEMO DAY SHOWCASE (Feb 20-21, 2026)**  
> _Interactive AI-Powered Tabletop RPG Engine_

This project demonstrates a **Hybrid AI Game Master** that combine the narrative flexibility of Large Language Models (LLM) with the mechanical precision of a hard-coded Rules Engine. It solves the "AI Hallucination" problem by keeping math and game state strictly in Python while letting the AI handle creativity and narration.

---

## 📊 Core Features

- ⚔️ **Two-Path Architecture:** Automatically routes player intent to either the **Rules Engine** (for standard actions) or the **LLM Arbiter** (for creative improv).
- 🎲 **Stateless Rules Engine:** Deterministic Python logic for initiative, dice rolling, range checks, and damage calculation.
- 🤖 **LLM Arbiter:** A "Referee" AI that judges creative actions, assigns Difficulty Classes (DC), and applies symbolic status effects (e.g., `STUNNED`, `RESTRAINED`).
- 🏃 **Tactical Zone Combat:** Grid-less tactical movement using `NEAR`, `MID`, and `FAR` zones with range-based disadvantage.
- 🃏 **Initiative Queue:** A dynamic turn-order system where every character (Player & Enemy) rolls initiative at the start of combat.
- ⚡ **Dynamic Sequence Actions:** Supports complex commands like "I shoot then run away" or "I run in then attack", executing them in the order specified by the user.

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
    - **The Automatic Way:** Just run the game! (`python demo_day.py`). The system will detect that you are missing a key, pause the game, and prompt you to paste it in the terminal. It will then automatically create the `.env` file for you.
    - **The Manual Way:** Create a new file named `.env` in the root folder of this project and paste your key inside like this:
      ```env
      GEMINI_API_KEY=your_key_here_xyz123
      ```

5.  **Run the Game**
    ```bash
    python demo_day.py
    ```

---

## 📂 Project Structure

```text
AI_Dungeon_Master/
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
│   ├── fibo_backup.json     # Clean state for resets
│   ├── fibo_active.json     # Current live session data
│   └── campaign.json        # Base character definitions
└── tests/                   # [QA] Unit tests for Rules Engine
    └── test_rules.py        # Pytest verifying Rule Adherence
```

---

## 🧩 Architectural Philosophy

The system is built as a **"Stateless Symbolic Machine"** to ensure 100% mechanical consistency.

1.  **Rule-First Decisioning:** If an action matches a standard game mechanic (Attack, Move, Item), the AI is bypassed for the calculation. The Python engine handles the math.
2.  **Symbolic Grounding:** When the AI allows a creative action (e.g., "I pull the rug"), it must return a **Symbolic Side Effect** (e.g., `target_condition: PRONE`). The Python engine then applies this to the live model.
3.  **TOON Serialization:** Uses a custom compact format for game state to reduce LLM token usage by up to 50%, ensuring faster response times and lower costs.

---

##  Game Rules
See [LITE_5E_RULES.md](file:///home/mudmini009/AI_Dungeon_Master/LITE_5E_RULES.md) for the complete mechanical breakdown of the FIBO Lite 5e system.
