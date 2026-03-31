"""
CampaignAgent — manages long-form session narrative generation.

Methods:
  - generate_recap()    : "Previously on..." summary from campaign log
  - generate_prologue() : Cold Open cinematic intro + enemy tag
"""
from typing import List, Dict
from src.agents.base import BaseLLMProvider
from src.models.toon_converter import TOONConverter


class CampaignAgent(BaseLLMProvider):

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
        except Exception:
            return "Previously on our adventure... (Recap generation failed)."

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
            data["enemy_type"] = data["enemy_type"].lower().strip()
            return data
        except Exception:
            import traceback
            import os
            os.makedirs("data", exist_ok=True)
            with open("data/error_log.txt", "w") as f:
                f.write(traceback.format_exc())
            return {"prologue": "You awaken in a dark dungeon. An enemy approaches!", "enemy_type": "goblin"}
