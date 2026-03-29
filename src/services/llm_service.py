import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Deque, Optional
from src.models.character import Character
from src.models.toon_converter import TOONConverter
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
            
        if not settings:
            settings = {"llm": {"arbiter_model": "gemini-2.5-flash-lite", "narrator_model": "gemini-2.5-flash-lite", "arbiter_temperature": 0.3, "narrator_temperature": 0.7}}
            
        arbiter_model = settings.get("llm", {}).get("arbiter_model", "gemini-2.5-flash-lite")
        narrator_model = settings.get("llm", {}).get("narrator_model", "gemini-2.5-flash-lite")
        arbiter_temp = settings.get("llm", {}).get("arbiter_temperature", 0.3)
        narrator_temp = settings.get("llm", {}).get("narrator_temperature", 0.7)
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=arbiter_model,
            generation_config={"temperature": arbiter_temp, "response_mime_type": "text/plain"}
        )
        self.narrator_model = genai.GenerativeModel(
            model_name=narrator_model,
            generation_config={"temperature": narrator_temp}
        )

    def get_creative_judgment(self, party_state: List[Character], enemies_state: List[Character], active_player: Character, action_description: str, combat_memory: Optional[Deque[str]] = None, story_memory: Optional[Deque[str]] = None) -> Dict[str, Any]:
        """
        Acts as the Arbiter/Referee.
        Decides if an action is possible based on Party Inventory and Logic.
        """
        
        
        # 1. Build Context (TOON Format)
        toon_context = TOONConverter.convert(party_state, enemies_state)
        
        # 2. Build Memory Context
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
            
            # Safety defaults
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
                "consumed_item": None
            }

    def narrate_result(self, action_text: str, roll_result: int, dc: int, is_success: bool) -> str:
        """
        Acts as the Narrator.
        Describes the outcome of the dice roll.
        """
        outcome_str = "SUCCESS" if is_success else "FAILURE"
        
        prompt = f"""
        As the Dungeon Master, describe the outcome of this action in 1-2 immersive sentences.
        
        Action: "{action_text}"
        Dice Roll: {roll_result} (DC {dc}) -> {outcome_str}
        
        Keep it brief, vivid, and second-person ("You ...").
        """
        
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Narrator Error: {str(e)}"

    def narrate_combat_round(self, action_log: str, combat_context: str, combat_memory: Optional[Deque[str]] = None, story_memory: Optional[Deque[str]] = None, world_lore: str = "") -> str:
        """Generates immersive DM narration based on mechanically resolved actions."""
        
        memory_context = ""
        if story_memory:
            memory_list = list(story_memory)
            memory_context += f"\nSTORY HISTORY:\n" + "\n".join(f"- {event}" for event in memory_list) + "\n"
        if combat_memory:
            memory_list = list(combat_memory)
            memory_context += f"\nRECENT COMBAT HISTORY (Last few turns):\n" + "\n".join(f"- {event}" for event in memory_list) + "\n"
        
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""

        system_instruction = f"""
        You are an expert Dungeon Master in an immersive text-based RPG.
        Your job is to translate raw, mechanical combat logs into exciting, second-person narrative.
        {lore_context}
        Current Combat State (TOON Format):
        {combat_context}
        {memory_context}
        Instructions:
        1. Keep the narration brief (2-3 sentences max).
        2. Describe the physical action dynamically.
        3. Do NOT invent new mechanical outcomes or numbers.
        4. Focus on flavor and tension.
        CRITICAL: Do NOT use numbers. Instead, use the Health Status (e.g. "Values is Bloodied", "Grok is Critical") to describe their physical state.
        Focus on the visual impact, sound, and pain.
        """
        full_prompt = f"{system_instruction}\n\nLog to narrate:\n{action_log}"
        
        try:
            response = self.narrator_model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"Narrator Error: {str(e)}"
            
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
            
        except Exception as e:
             # Failsafe: Don't consume it, give it no effect
             return {"is_consumable": False, "effect_type": "NONE"}

    def summarize_combat(self, combat_memory: Deque[str]) -> str:
        """
        Collapses a full queue of mechanical combat logs into a single narrative sentence.
        """
        if not combat_memory:
            return "A brief skirmish occurred."
            
        combat_log = "\n".join(list(combat_memory))
        prompt = f"""
        You are the DM Summarizer.
        The party just finished a combat encounter.
        Here is the mechanical log of the fight:
        
        {combat_log}
        
        Write exactly ONE single narrative sentence summarizing the entire outcome of this fight.
        Focus on who was defeated and any interesting narrative details.
        Do NOT use any numbers, stats, HP, or mechanical terms.
        """
        
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "The party emerged victorious from a brutal battle."

    def generate_recap(self, log_lines: List[str]) -> str:
        """
        Safely slices the last 50 lines of the campaign log to prevent Context Window overflow,
        then generates a 'Previously on...' narrative recap.
        """
        recent_log = "\n".join(log_lines[-50:])
        prompt = f"""
        You are the Narrator of an ongoing TTRPG campaign.
        Read the following recent events from the campaign log and write a short, dramatic "Previously on..." recap (3-4 sentences max).
        
        RECENT LOG:
        {recent_log}
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Previously on our adventure... (Recap generation failed)."

    def extract_character_stats(self, bio: str) -> str:
        """
        Takes a custom bio and outputs symbolic tags in TOON format.
        The Python engine then strictly maps these tags to a balanced stat block, preventing AI stat hallucination.
        """
        prompt = f"""
        You are a Semantic Classifier for a TTRPG character creator.
        Read the following player biography and classify them into a strict Archetype and a Primary Focus stat.
        
        Valid Archetypes: fighter, wizard, rogue, cleric, ranger
        Valid Focus Stats: PHYS (Physical/Strength), MENT (Mental/Magic), SOC (Social/Charisma)

        BIOGRAPHY:
        "{bio}"

        OUTPUT FORMAT (TOON SYNTAX ONLY - 1 LINE STRICT):
        Example: archetype:wizard|focus:MENT
        You MUST NOT output JSON or any other text.
        """
        try:
             response = self.model.generate_content(prompt)
             return response.text.strip()
        except Exception as e:
             return "archetype:fighter|focus:PHYS" 

    def expand_world_lore(self, concept: str) -> str:
        """Takes a short world concept and expands it into rich setting detail."""
        prompt = f"""
        You are an expert worldbuilder for a dark fantasy/adventure TTRPG.
        Expand the following core concept into a 2-paragraph immersive World Lore document.
        Set the tone, describe the environment, and mention at least one looming threat.
        
        CONCEPT: "{concept}"
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "A dark and perilous world awaits. Danger lurks in every shadow."

    def generate_prologue(self, character_toon: str, world_lore: str) -> Dict[str, str]:
        """
        Generates a narrative "Cold Open" and outputs a symbolic enemy tag.
        Python intercepts this tag and provisions the mechanical Enemy TOON from a hardcoded template.
        """
        prompt = f"""
        You are the Dungeon Master starting a new campaign.
        Read the Character Details and World Lore, then generate a thrilling "Cold Open" prologue (2-3 paragraphs).
        The prologue MUST end by dropping the player immediately into a combat encounter against ONE enemy type.

        CHARACTER:
        {character_toon}

        WORLD LORE:
        {world_lore}

        OUTPUT FORMAT (STRICT TOON SYNTAX):
        You MUST return exactly ONE single line of text.
        You MUST separate keys using the '|' character. 
        You MUST NOT use actual line breaks (newlines). If you want to format multiple paragraphs, use the literal string '\\n' for line breaks.
        
        Example: prologue:First paragraph.\\n\\nSecond paragraph.|enemy_type:goblin
        """
        try:
             response = self.model.generate_content(prompt)
             raw_text = response.text.strip()
             # Hack for Gemini Flash Lite ignoring the prologue tag
             if not raw_text.lower().startswith("prologue:"):
                 raw_text = "prologue:" + raw_text
             
             data = TOONConverter.decode(raw_text)
             if "prologue" not in data: data["prologue"] = "You begin your journey, but danger approaches..."
             if "enemy_type" not in data: data["enemy_type"] = "goblin"
             # Clean up the output to prevent broken strings
             data["enemy_type"] = data["enemy_type"].lower().strip()
             return data
        except Exception as e:
             import traceback
             with open("data/error_log.txt", "w") as f:
                 f.write(traceback.format_exc())
             return {"prologue": "You awaken in a dark dungeon. An enemy approaches!", "enemy_type": "goblin"}
