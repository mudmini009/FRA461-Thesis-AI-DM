"""
ArbiterAgent — validates player actions and categorizes inventory items.

Methods:
  - get_creative_judgment(): decides if a creative action is allowed (TOON output)
  - categorize_item(): classifies an inventory item into a mechanical effect type
"""
from typing import List, Dict, Any, Deque, Optional
from src.agents.base import BaseLLMProvider
from src.models.character import Character, Stat
from src.models.toon_converter import TOONConverter


class ArbiterAgent(BaseLLMProvider):

    def get_creative_judgment(
        self,
        party_state: List[Character],
        enemies_state: List[Character],
        active_player: Character,
        action_description: str,
        combat_memory: Optional[Deque[str]] = None,
        story_memory: Optional[Deque[str]] = None,
        global_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Acts as the Arbiter/Referee.
        Decides if an action is possible based on Party Inventory and Logic.
        """
        toon_context = TOONConverter.convert(party_state, enemies_state, global_state)

        memory_context = ""
        if story_memory:
            memory_context += "\nSTORY HISTORY (The larger narrative):\n" + "\n".join([f"- {m}" for m in story_memory])
        if combat_memory:
            memory_context += "\nRECENT COMBAT EVENTS (Immediate Context):\n" + "\n".join([f"- {m}" for m in combat_memory])

        prompt = f"""
        You are the ARBITER (Game Referee) for a TTRPG.
        Your job is to validate a CREATIVE ACTION proposed by a player.
        
        Note: Game State is provided in TOON format (world{{fields}}: row, players[N]{{fields}}: row). 
        - The "world" header contains absolute time (Day, Hour, Phase) and combat status.
        - Inventory items are pipe-separated | within brackets.
        - Ability charges are shown as Name(Current/Max) within brackets.
        
        GAME STATE (TOON Format):
        {toon_context}
        {memory_context}
        
        ACTIVE PLAYER: {active_player.name}
        PROPOSED ACTION: "{action_description}"
        
        RULES:
        1. Check PHYS/LOGIC: Is this action possible?
        2. LORE SYNERGY (CRITICAL): Read the active player's "Title" and "Lore". If their narrative background gives them a logical advantage for this specific action (e.g., a "Blind Monk" using hearing to track, or a "Thief" picking a lock), you MUST lower the DC significantly (e.g., lower by 3 to 5 points) or grant an automatic success. Briefly mention this synergy in your "reason".
        3. Check INVENTORY: If they use an item, DOES SOMEONE in the party have it?
        4. Determine Side Effects: If the action succeeds, does the target suffer a Condition? (RESTRAINED, PRONE, BLINDED, STUNNED, PACIFIED).
        5. Check Consumption: If the player uses an item in a way that destroys, consumes, or loses it (e.g., throwing a weapon away, burning a rope, eating a mushroom), add "consumed_item": "Item Name". Otherwise, return "consumed_item": null.
        6. ACTION ECONOMY: A turn is only 6 seconds. A player can do at most ONE Move and ONE Major Action. If they attempt multiple major actions, set allowed:false.

        OUTPUT FORMAT (TOON SYNTAX ONLY - 1 LINE STRICT):
        For this performance upgrade, you MUST NOT output JSON. You must output a single line of pipe-separated key:value pairs.
        Example: allowed:true|reason:Target is distracted|check_stat:PHYS|dc:12|on_success_condition:PRONE|target_name_guess:Goblin|consumed_item:null
        """

        try:
            response = self.model.generate_content(prompt)
            data = TOONConverter.decode(response.text.strip())

            if "allowed" not in data: data["allowed"] = False
            if "check_stat" not in data: data["check_stat"] = "PHYS"
            if "dc" not in data: data["dc"] = 15
            if "on_success_condition" not in data: data["on_success_condition"] = None
            if "target_name_guess" not in data: data["target_name_guess"] = None
            if "consumed_item" not in data: data["consumed_item"] = None

            return data

        except Exception as e:
            return {
                "allowed": False,
                "reason": f"Arbiter Error: {str(e)}",
                "check_stat": "PHYS",
                "dc": 99,
                "on_success_condition": None,
                "target_name_guess": None,
                "consumed_item": None,
            }

    def categorize_item(self, item_name: str) -> Dict[str, Any]:
        """
        Uses the LLM to dynamically classify an unknown item string into a strict backend mechanical category.
        """
        prompt = f"""
        You are the Item Arbiter for a pure Python Game Engine.
        A player wants to USE the following item from their inventory:="{item_name}"
        
        Your job is to categorize this item into one of the following strict mechanical types:
        - SMALL_HEAL: Equivalent to a standard potion or bandage (+10 HP).
        - BIG_HEAL: Equivalent to a major heal or elixir (+25 HP).
        - CURE: Removes bad conditions like BLINDED or STUNNED (e.g., Antidote, Eyedrops).
        - DAMAGE: A destructive item they accidentally or intentionally used on themselves (e.g., Bomb).
        - NONE: A standard weapon, key, or junk item with no immediate mechanical buff.
        
        Determine if the item is consumed upon use (is_consumable). Weapons are usually NOT consumable, whereas food/potions/bombs ARE.
        
        OUTPUT FORMAT (TOON SYNTAX ONLY - 1 LINE STRICT):
        For this performance upgrade, you MUST NOT output JSON. You must output a single line of pipe-separated key:value pairs.
        Example: is_consumable:true|effect_type:SMALL_HEAL
        """
        try:
            response = self.model.generate_content(prompt)
            data = TOONConverter.decode(response.text.strip())

            if "is_consumable" not in data: data["is_consumable"] = False
            if "effect_type" not in data: data["effect_type"] = "NONE"

            return data

        except Exception:
            return {"is_consumable": False, "effect_type": "NONE"}

    def judge_puzzle_attempt(
        self,
        player: Character,
        puzzle_obstacle: str,
        base_dc: int,
        action_description: str,
        world_lore: str = "",
        story_memory=None,
    ) -> Dict[str, Any]:
        """
        Evaluates a creative puzzle solution using the same Arbiter logic
        used for combat creative actions.

        The Arbiter judges:
          - Is the solution physically/logically possible?
          - Does the player's class/lore give them a synergy advantage?
          - What stat should be checked? What's the modified DC?

        Returns:
            {
                "allowed": bool,
                "check_stat": "PHYS" | "MENT" | "SOC",
                "modified_dc": int,
                "reason": str,
            }
        """
        memory_context = ""
        if story_memory:
            memory_context = "\nSTORY CONTEXT:\n" + "\n".join(
                [f"- {m}" for m in list(story_memory)[-5:]]
            )

        prompt = f"""You are the ARBITER (Game Referee) for a TTRPG exploration puzzle.
A player has encountered an OBSTACLE and is proposing a creative solution.
Your job is to judge whether the approach is logical and determine the difficulty.

PLAYER INFO:
- Name: {player.name}
- Class: {player.role}
- Title: {getattr(player, 'title', 'Adventurer')}
- Background: {getattr(player, 'lore', 'A brave adventurer.')}
- Stats: PHYS={player.stats.get(Stat.PHYS, 0)}, MENT={player.stats.get(Stat.MENT, 0)}, SOC={player.stats.get(Stat.SOC, 0)}
- Inventory: {', '.join(player.inventory) if player.inventory else 'Empty'}

WORLD LORE:
{world_lore[:500]}
{memory_context}

PUZZLE OBSTACLE: "{puzzle_obstacle}"
BASE DIFFICULTY (DC): {base_dc}
PLAYER'S PROPOSED SOLUTION: "{action_description}"

RULES:
1. LOGIC CHECK: Is this solution physically/logically possible given the obstacle?
   - If completely nonsensical (e.g., "I fly" when they can't fly), set allowed:false.
   - If reasonable but difficult, set allowed:true with a high DC.
2. LORE SYNERGY (CRITICAL): If the player's class, title, lore, or inventory gives them
   a logical advantage for THIS specific solution, LOWER the DC significantly (by 3-6 points).
   Example: A Mage using wind magic vs a gas cloud → lower DC from 14 to 8.
   Example: A Fighter trying to punch through a stone wall → keep DC high.
3. STAT SELECTION: Choose which stat (PHYS, MENT, or SOC) best fits the approach.
   - Physical solutions (breaking, climbing, jumping) → PHYS
   - Mental solutions (magic, puzzles, mechanisms) → MENT
   - Social solutions (negotiation, deception, performance) → SOC
4. DC RANGE: Modified DC must be between 5 (very easy) and 20 (nearly impossible).

OUTPUT FORMAT (TOON SYNTAX ONLY - 1 LINE STRICT):
allowed:true|check_stat:MENT|modified_dc:10|reason:Wind magic directly counters gas cloud. Mage synergy lowers DC."""

        try:
            response = self.model.generate_content(prompt)
            data = TOONConverter.decode(response.text.strip())

            # Enforce defaults and type safety
            if "allowed" not in data:
                data["allowed"] = True
            if "check_stat" not in data:
                data["check_stat"] = "PHYS"
            if "modified_dc" not in data:
                data["modified_dc"] = base_dc
            if "reason" not in data:
                data["reason"] = "The Arbiter considers your approach."

            # Clamp DC to valid range
            try:
                data["modified_dc"] = max(5, min(20, int(data["modified_dc"])))
            except (ValueError, TypeError):
                data["modified_dc"] = base_dc

            return data

        except Exception as e:
            # Fallback: allow the attempt with original DC
            return {
                "allowed": True,
                "check_stat": "PHYS",
                "modified_dc": base_dc,
                "reason": f"Arbiter unavailable, using base DC. ({str(e)[:50]})",
            }
