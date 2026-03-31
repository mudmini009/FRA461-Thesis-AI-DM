"""
NarratorAgent — generates immersive text descriptions of combat events.

Methods:
  - narrate_result()       : describes the outcome of a single dice roll
  - narrate_combat_round() : translates a mechanical combat log into DM narration
  - summarize_combat()     : collapses an entire combat into one recap sentence
"""
from typing import Optional, Deque
from src.agents.base import BaseLLMProvider


class NarratorAgent(BaseLLMProvider):

    def narrate_result(self, action_text: str, roll_result: int, dc: int, is_success: bool) -> str:
        """
        Acts as the Narrator. Describes the outcome of the dice roll.
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

    def narrate_combat_round(
        self,
        action_log: str,
        combat_context: str,
        combat_memory: Optional[Deque[str]] = None,
        story_memory: Optional[Deque[str]] = None,
        world_lore: str = "",
    ) -> str:
        """Generates immersive DM narration based on mechanically resolved actions."""
        memory_context = ""
        if story_memory:
            memory_context += f"\nSTORY HISTORY:\n" + "\n".join(f"- {event}" for event in list(story_memory)) + "\n"
        if combat_memory:
            memory_context += f"\nRECENT COMBAT HISTORY (Last few turns):\n" + "\n".join(f"- {event}" for event in list(combat_memory)) + "\n"

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
        except Exception:
            return "The party emerged victorious from a brutal battle."
