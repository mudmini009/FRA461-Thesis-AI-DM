# Lite 5e Ruleset (Thesis Edition)

## Introduction

Welcome, adventurers! This rulebook is designed for new players and specifically for this thesis project. Our system is heavily inspired by Dungeons & Dragons 5th Edition, but streamlined to be:

- **Easy to learn**
- **Fast to play**
- **Optimized for LLM/AI Dungeon Master interaction**

Whether you are a sword-swinging warrior, a cleric calling upon divine power, or a mage who bends reality, these rules provide a fair framework for your play while maintaining total narrative freedom.

---

## How to Play

The core gameplay loop is simple:

1.  **The LLM/DM describes the situation** (e.g., “A goblin jumps out from behind the barrel!”)
2.  **The player states their intent** (e.g., “I swing my sword at the goblin!”)
3.  **The system rolls dice to resolve success** (e.g., d20 + PHYS or d20 + MENT vs. AC/DC)
4.  **The outcome is narrated** (e.g., “Your sword strikes true! The goblin takes 7 damage.”)

---

## Dice Basics

We primarily use the **d20** system:

- **Skill Checks:** `d20 + Stat Modifier` vs. `Difficulty Class (DC)`
- **Attack Rolls:** `d20 + Stat Modifier` vs. `Enemy Armor Class (AC)`
- **Damage Rolls:** Rolling smaller dice (d6, d8, etc.)

**Special Rolls (Advantage & Disadvantage):**

- **Advantage:** Grants a +5 flat bonus to the roll (e.g., when the enemy is Stunned or Unconscious).
- **Disadvantage:** Incurs a -5 flat penalty to the roll (e.g., when you are Blinded), OR requires rolling 2 dice and taking the lowest result (for Ranged attacks against a Far target).
- **Natural 20:** Automatic resolution success (**Critical Success**) and deals double damage (for attacks).
- **Natural 1:** Automatic resolution failure (**Critical Failure**) and may incur narrative consequences.

---

## Stats & Modifiers

We have condensed the standard 6 D&D Ability Scores into just **3 Core Stats**:

| Stat                | Covers                               | Example Actions                           |
| :------------------ | :----------------------------------- | :---------------------------------------- |
| **Physical (PHYS)** | Strength, Dexterity, Constitution    | Attacking, climbing, dodging, shoving     |
| **Mental (MENT)**   | Intelligence, Wisdom, Perception     | Recalling lore, spotting traps, puzzles   |
| **Social (SOC)**    | Charisma, Persuasion                 | Persuading, lying, intimidating           |

Each stat has a **Modifier** ranging from **–2 to +5**, which is added to your d20 rolls.

---

## Hit Points (HP)

- All characters start with **20 HP** at Level 1.
- Damage reduces HP.
- **0 HP = Unconscious.**
- If left untreated, reaching 0 HP can lead to death.

---

## Combat System

Combat is **Turn-based** and utilizes a grid-less **Zone-based** positioning system.

### Turn Order

The system uses an **Initiative Queue** to determine a fair and dynamic turn order:

1.  **Initiative Roll:** At the start of combat, all characters roll `d20 + PHYS bonus`.
2.  **Sorting:** Whoever rolls highest goes first (Similar to D&D 5e utilizing Dexterity, but in Lite 5e we use the consolidated **PHYS** stat).
3.  **Looping:** Once everyone in the queue has acted, a new Round begins and the turn order loops back to the top of the queue.
4.  **Unconscious Characters:** If a character drops to 0 HP or suffers a condition that prevents taking actions, the system automatically skips their turn.

On your turn, you may take **1 Action + 1 Move**, and you may **choose the order** in which they resolve (e.g., Move into range then Attack, or Attack then run away).

- **Action:** Attack (Melee/Ranged), Cast a Spell (if applicable), Use a Special Ability, Use an Item (drink potion, throw bomb), Interact with the Environment (kick a door, pull a lever).
- **Move:** Traverse to a different Zone (Maximum 1 Zone per turn).

### Movement & Zones

We do not use battle grids; instead, space is divided into **Zones**:

- **Same Zone (NEAR):** Allows for both Melee and Ranged attacks.
- **Adjacent Zone (MID):** Allows for Ranged attacks, but Melee attacks fail.
- **Far Zone (FAR):** Allows for Ranged attacks, but incurs **Disadvantage** (The system rolls two d20s and takes the **lowest result**) because the target is 2 zones away (e.g., Near to Far).

Players may Move exactly 1 Zone per turn as their Move action.

### Attacking

Attacks are divided into 2 categories based on the weapon:

#### 1. Melee Attack

- **Condition:** Attacker and Target must be in the **Same Zone**.
- **Roll Formula:** `d20 + PHYS` vs `AC`
- **Damage:** `Weapon Dice + PHYS`

#### 2. Ranged / Spell Attack

- **Condition:** Can attack across any Zone (Attacking a target 2 zones away incurs **Disadvantage**).
- **Roll Formula:** `d20 + MENT` (for Spells) or `d20 + PHYS` (for Bows) vs `AC`
- **Damage:** `Spell/Weapon Dice + MENT` (for Spells) or `+ PHYS` (for Bows)

- **Critical Hit (Nat 20):** Damage is doubled.

### Fleeing / Escaping

To flee from combat, a player must declare their intent to escape (e.g., "I run away!"). The system resolves this using a contested **PHYS** check against the closest active enemy:

- **Player Roll:** `d20 + PHYS`
- **Enemy Roll:** `d20 + PHYS` + **Proximity Penalty**

**Proximity Penalty:** It is significantly harder to escape if enemies are right next to you. The enemy receives a mathematical bonus to their roll based on the distance (in Zones) between you and them:
- **Same Zone (Distance 0):** Enemy gets a **+5 bonus**.
- **Adjacent Zone (Distance 1):** Enemy gets a **+2 bonus**.
- **Far Zone (Distance 2+):** No bonus (+0).

*Tactical Tip:* Since you get 1 Move and 1 Action per turn, you should use your Move to increase your distance from the enemy, and then use your Action to Flee in the same sequence, reducing the enemy's proximity penalty! If your total beats the enemy's total, you successfully escape combat. If you fail, the enemy cuts off your escape and your turn is consumed.

---

## Example Classes

### **Fighter**

- **HP:** 20 | **AC:** 16 (Chainmail)
- **Attack (Melee):** Longsword → `1d8 + PHYS`
- **Ability:** `Second Wind` → Heals HP `1d10 + 1` (1 use / combat)

### **Paladin**

- **HP:** 20 | **AC:** 16 (Chainmail)
- **Attack (Melee):** Greatsword → `2d6 + PHYS`
- **Ability:** `Smite` → Adds `2d8` damage (2 uses / day)
- **Ability:** `Lay on Hands` → Heals HP `1d8 + MENT` (1 use / day)

### **Cleric**

- **HP:** 18 | **AC:** 18 (Plate + Shield)
- **Attack (Melee):** Warhammer → `1d8 + PHYS`
- **Ability:** `Pray` (Roll MENT vs DC 13) → Choose outcome: Heal an ally (`1d8 + MENT`) or Damage an enemy (`1d8 + MENT` Radiant Dmg)

### **Mage**

- **HP:** 15 | **AC:** 12 (Robes + Mage Armor)
- **Attack (Ranged Spell):** Firebolt → `1d10 + MENT` (Ranged)
- **Attack (Melee):** Quarterstaff → `1d6 + PHYS` (Melee - Emergency case)
- **Spells:** 2 uses / day (Free-form magic; the LLM Arbiter handles DC and the narrative impact)

---

## Items & Inventory

Throughout the adventure, characters will acquire and use items. Our system enforces specific rules for **Consumable Items**:

- **Fixed Mechanical Usage (Path A):** If you explicitly command the use of a standard RPG item (e.g., "I drink my Potion" or "I read the Scroll"), the system checks against hardcoded keywords (potion, scroll, ration, food, bomb). If matched, that item is automatically consumed and removed from your inventory array.
- **Creative Improvised Usage (Path B):** If you narratively repurpose an item (e.g., "I use my rope to light a fire for illumination" or "I smash my empty glass bottle against the wall to cause a distraction"), the AI (Arbiter) evaluates if the narrative action causes the item to be **lost, consumed, or destroyed**. If the Arbiter determines it was consumed, the item is removed from your inventory.

*Note: You cannot use or interact with items that do not currently exist within your inventory array.*

---

## Rest & Time

### Short Rest

- **Duration:** 1 Hour
- **Effect:** Restores HP equal to `1d8 + Modifier` (if applicable), refreshes limited-use abilities (e.g., Second Wind).

### Long Rest

- **Duration:** 8 Hours (Must be done in a safe location)
- **Effect:** Completely restores all HP, Spells, and limited-use abilities to maximum.

---

## Conditions

- **Unconscious:** 0 HP; unable to perform any actions.
- **Stunned:** Forfeits their turn entirely in the Initiative Queue for that round.
- **Restrained:** All d20 rolls utilizing the PHYS stat suffer Disadvantage.
- **Dead:** Removed from the game unless resurrected.

---

## Leveling Up

(Note: Optional feature for prototype, may not be implemented yet)

- **+5 Max HP** per level.
- **Choose between:** +1 to a Stat OR a new spell/ability use.
- **Simple XP System:** 250 XP required per level.
