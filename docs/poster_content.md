# FIBO Senior Thesis - Short A4 Poster Content

---

### HEADER
**AGENTIC-DUALPATH-CORE: A MULTI-AGENT HYBRID TTRPG ENGINE**
Senior Thesis | 29 May 2026 | 12:00 - 13:00 | Room FB607
Author: Mr. Pollapaat Suttimala (mudnott@gmail.com | +66 86-965-2595)
Advisor: Asst. Prof. Dr. Suriya Natsupakpong
Co-advisor: Asst. Prof. Dr. Paisit Khan-Ar-Sa

---

### 1. PROBLEM & CHALLENGE
* **Hallucination:** AI Dungeon Masters often invent rules, miscalculate HP, and allow illegal moves (e.g., walking through walls).
* **The Language Challenge:** Players use rich, creative language (*"I slide under the table"*). Rigid code fails to understand this. We need an AI to understand intent, but rigid code to handle the math.

### 2. SYSTEM OVERVIEW (TWO-PATH ROUTER)
* **Path A (Python Rules):** Handles standard attacks, movement, and spells. Guarantees 100% accurate math with zero AI token cost.
* **Path B (LLM Arbiter):** Judges creative actions and puzzles. AI decides difficulty, and Python applies the status effects.
* **TOON Data Format:** A custom compressed text format that sends game state to the AI, saving 40% in token costs.

### 3. EXPLORATION ENGINE
* **Point-Crawl Graph:** Rooms are connected nodes. 
* **Hybrid Router:** Uses Python regex for simple commands (`look`, `rest`) and AI for complex sentences.
* **Spatial Guardrails:** Python verifies if a room is connected *before* the AI acts, preventing players from teleporting through walls.
* **Infinite Lore Prevention:** Separates exploration logs from combat to stop repeating room descriptions.

### 4. COMBAT & INITIATIVE
* **Dynamic Turn Order:** Initiative Queue (d20 + Physical stat) sorts players and enemies fairly.
* **Zone-Based Combat:** Grid-less zones (`NEAR`, `MID`, `FAR`). Distant attacks automatically get mathematical disadvantages calculated by Python.
