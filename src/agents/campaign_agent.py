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
        Generates a narrative 'Cold Open' that ends with the player arriving at
        the Adventurer's Guild. Python saves the result to story_memory so the
        hub narrator can reference it directly.
        """
        prompt = f"""
        You are the Dungeon Master starting a new campaign.
        Write an atmospheric "Cold Open" prologue in 3 beats.

        CHARACTER:
        {character_toon}

        WORLD LORE:
        {world_lore}

        THE THREE BEATS (follow this structure exactly):
        BEAT 1 (World Introduction): 1-2 sentences. Paint the atmosphere of the world.
        BEAT 2 (The Peril): 1-2 sentences. The character faces or narrowly escapes a danger on their way through the city.
        BEAT 3 (Arrival — MANDATORY): The character SURVIVES and arrives at the Adventurer's Guild.
          Your final 1-2 sentences MUST describe the character pushing open the heavy wooden doors
          of the Adventurer's Guild and stepping inside. This is NOT optional.
          Do NOT end on a cliffhanger. Do NOT end in the middle of a fight. The journey ENDS at the Guild.

        OUTPUT FORMAT (STRICT):
        One single line. Keys separated by '|'. No real newlines — use '\\n' for paragraph breaks.
        Example: prologue:Beat 1 text.\\n\\nBeat 2 text.\\n\\nBeat 3 ending at guild.|enemy_type:goblin
        (enemy_type is a placeholder for the world's main threat. It is NOT used in this scene.)
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
