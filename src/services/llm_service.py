import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from src.models.character import Character
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": 0.3, "response_mime_type": "application/json"}
        )
        # Narrator uses a slightly higher temp for creativity, but we can reuse the model or config
        self.narrator_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": 0.7} # Text output, not JSON
        )

    def get_creative_judgment(self, party_state: List[Character], active_player: Character, action_description: str) -> Dict[str, Any]:
        """
        Acts as the Arbiter/Referee.
        Decides if an action is possible based on Party Inventory and Logic.
        """
        
        # 1. Build Context (Party Inventories)
        party_context = "PARTY STATE:\n"
        for char in party_state:
            items_str = ", ".join(char.inventory) if char.inventory else "Empty"
            party_context += f"- {char.name} ({char.role}): [HP: {char.hp}/{char.max_hp}] [Items: {items_str}]\n"
            
        prompt = f"""
        You are the ARBITER (Game Referee) for a TTRPG.
        Your job is to validate a CREATIVE ACTION proposed by a player.
        
        CONTEXT:
        {party_context}
        
        ACTIVE PLAYER: {active_player.name}
        PROPOSED ACTION: "{action_description}"
        
        RULES:
        1. Check PHYS/LOGIC: Is this action possible?
        2. Check INVENTORY: If they use an item, DOES SOMEONE in the party have it?
        3. Determine Side Effects: If the action succeeds, does the target suffer a Condition? (RESTRAINED, PRONE, BLINDED, STUNNED).
        
        OUTPUT (JSON ONLY):
        {{
            "allowed": boolean,
            "reason": "Short explanation",
            "check_stat": "PHYS" | "MENT" | "SOC" | "NONE",
            "dc": integer (10-25),
            "on_success_condition": "RESTRAINED" | "PRONE" | "BLINDED" | "STUNNED" | null,
            "target_name_guess": "Name of the target from description (e.g. 'Goblin Scavenger') or null"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            # Safety defaults
            if "allowed" not in data: data["allowed"] = False
            if "check_stat" not in data: data["check_stat"] = "PHYS"
            if "dc" not in data: data["dc"] = 15
            if "on_success_condition" not in data: data["on_success_condition"] = None
            if "target_name_guess" not in data: data["target_name_guess"] = None
            
            return data
            
        except Exception as e:
            return {
                "allowed": False, 
                "reason": f"Arbiter Error: {str(e)}", 
                "check_stat": "PHYS", 
                "dc": 99,
                "on_success_condition": None,
                "target_name_guess": None
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
