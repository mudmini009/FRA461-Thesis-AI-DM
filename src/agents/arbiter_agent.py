"""
ArbiterAgent — validates player actions and categorizes inventory items.

Methods:
  - get_creative_judgment(): decides if a creative action is allowed (TOON output)
  - categorize_item(): classifies an inventory item into a mechanical effect type
"""
from typing import List, Dict, Any, Deque, Optional
from src.agents.base import BaseLLMProvider
from src.models.character import Character
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
    ) -> Dict[str, Any]:
        """
        Acts as the Arbiter/Referee.
        Decides if an action is possible based on Party Inventory and Logic.
        """
        toon_context = TOONConverter.convert(party_state, enemies_state)

        memory_context = ""
        if story_memory:
            memory_context += "\nSTORY HISTORY (The larger narrative):\n" + "\n".join([f"- {m}" for m in story_memory])
        if combat_memory:
            memory_context += "\nRECENT COMBAT EVENTS (Immediate Context):\n" + "\n".join([f"- {m}" for m in combat_memory])

        prompt = f"""
        You are the ARBITER (Game Referee) for a TTRPG.
        Your job is to validate a CREATIVE ACTION proposed by a player.
        
        Note: Game State is provided in TOON format (players[N]{{fields}}: row, row). Inventory items are pipe-separated | within brackets.
        
        GAME STATE (TOON Format):
        {toon_context}
        {memory_context}
        
        ACTIVE PLAYER: {active_player.name}
        PROPOSED ACTION: "{action_description}"
        
        RULES:
        1. Check PHYS/LOGIC: Is this action possible?
        2. Check INVENTORY: If they use an item, DOES SOMEONE in the party have it?
        3. Determine Side Effects: If the action succeeds, does the target suffer a Condition? (RESTRAINED, PRONE, BLINDED, STUNNED, PACIFIED).
        4. Check Consumption: If the player uses an item in a way that destroys, consumes, or loses it (e.g., throwing a weapon away, burning a rope, eating a mushroom), add "consumed_item": "Item Name". Otherwise, return "consumed_item": null.
        5. ACTION ECONOMY: A turn is only 6 seconds. A player can do at most ONE Move and ONE Major Action (Attack, Cast, Use Item, or Stunt). If the proposed action attempts to do multiple major actions (e.g., attacking twice, drinking a potion AND attacking, or casting a spell AND attacking), you MUST deny it. Set allowed:false and provide a reason like "You do not have enough time in one turn to do all of that."

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
