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

    # ─── Exploration Narrator Methods ─────────────────────────────────────────
    # These four methods are NEW. They do not alter any existing method above.

    def narrate_room_entry(self, node: dict, world_lore: str = "", story_memory=None) -> str:
        """
        Narrates moving into a new node.
        Critically grounded: the system prompt lists ONLY the exits from
        node['connected_to'] so the LLM cannot hallucinate new paths.
        """
        connected = node.get("connected_to", [])
        exits_str = ", ".join(connected) if connected else "none — you are trapped here"
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""
        memory_context = ""
        if story_memory:
            memory_context = "\nSTORY SO FAR:\n" + "\n".join(f"- {e}" for e in list(story_memory)) + "\n"

        prompt = f"""
        You are the Dungeon Master narrating a player's arrival into a new room.
        {lore_context}{memory_context}
        ROOM DATA:
        Name: {node.get('name', 'Unknown Room')}
        Type: {node.get('event_type', 'safe')}
        Description: {node.get('base_description', '')}
        VALID EXITS (node IDs): {exits_str}

        INSTRUCTIONS:
        1. Write 2-3 sentences in second person ("You enter...", "The room...").
        2. Describe the atmosphere vividly based on the Description above.
        3. You MAY hint at the exits, but you MUST NOT mention any exit that
           is not in the VALID EXITS list above. Do NOT invent new paths.
        4. Do NOT reveal combat specifics — just the atmosphere.
        5. Keep it immersive and tense.
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"You enter {node.get('name', 'the room')}. The air is heavy with tension."

    def narrate_exploration_look(self, node: dict, world_lore: str = "") -> str:
        """
        Describes the current room in rich detail for a LOOK/INSPECT command.
        Explicitly lists only the valid exits drawn from connected_to —
        the LLM cannot hallucinate additional paths.
        """
        connected = node.get("connected_to", [])
        exits_str = ", ".join(connected) if connected else "none"
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""

        prompt = f"""
        You are the Dungeon Master. The player has asked to look around.
        {lore_context}
        ROOM DATA:
        Name: {node.get('name', 'Unknown Room')}
        Type: {node.get('event_type', 'safe')}
        Description: {node.get('base_description', '')}
        VALID EXITS (ONLY these — do not invent others): {exits_str}

        INSTRUCTIONS:
        1. Write a rich, evocative description of the room in 3-4 sentences.
        2. Second person ("You see...", "The walls...").
        3. EXPLICITLY mention the available exits by name at the end.
           You may ONLY name exits that are in the VALID EXITS list.
        4. If the room has enemies (event_type: combat/boss), describe signs
           of danger without inventing specific enemies — leave it ominous.
        5. Do NOT invent rooms, corridors, or exits that are not listed.
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"{node.get('base_description', 'You look around carefully.')}"

    def narrate_encounter_start(self, node: dict, enemy_name: str, world_lore: str = "") -> str:
        """
        Cold open / Initiative phase narration.

        CEO DIRECTIVE — Lost Action Fix:
        The player's MOVE input has been fully consumed by the Exploration Router.
        This narration IS the Initiative phase. It must explicitly signal that
        combat has begun and prompt the player to take their FIRST combat action.
        The Combat Loop inherits a clean Turn 1 with no swallowed inputs.

        System prompt enforces: end with a clear 'Initiative' call-to-action.
        """
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""

        prompt = f"""
        You are the Dungeon Master. The player has just walked into an ambush.
        {lore_context}
        ROOM: {node.get('name', 'Unknown')}
        SCENE: {node.get('base_description', '')}
        ENEMY: {enemy_name}

        INSTRUCTIONS:
        1. Write a dramatic, visceral 2-3 sentence ambush/encounter opening.
        2. Describe the enemy emerging from the environment.
        3. Build maximum tension.
        4. CRITICAL: The final sentence MUST explicitly signal the start of combat
           and invite the player's first action. Use something like:
           "Roll for Initiative — what is your first move?"
           or "The battle begins — what do you do?"
        5. Second person, present tense. No mechanical numbers.
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"An enemy emerges! {enemy_name} stands before you. Roll for Initiative — what is your first move?"

    def narrate_node_cleared(self, node: dict, world_lore: str = "") -> str:
        """
        Post-combat narration when the node is marked cleared.
        Called immediately after start_combat_loop() returns 'VICTORY'
        and before returning control to the exploration loop.
        """
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""

        prompt = f"""
        You are the Dungeon Master. The player has just won a combat encounter.
        {lore_context}
        ROOM: {node.get('name', 'Unknown')}
        SCENE: {node.get('base_description', '')}

        INSTRUCTIONS:
        1. Write 2-3 sentences describing the aftermath of victory.
        2. The silence after battle. The cost of the fight. The smell of ash or blood.
        3. End with a brief nudge toward what lies ahead — keep it open-ended.
        4. Second person. No mechanical numbers or HP.
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"The last enemy falls. The room is yours now. Silence returns to {node.get('name', 'the chamber')}."

    def narrate_hub_welcome(self, player_name: str, world_lore: str = "", story_memory=None) -> str:
        """
        Generates a welcome/re-entry narration for the Hub.
        Used both for new arrivals and returning adventurers.
        """
        lore_context = f"\nWORLD LORE:\n{world_lore}\n" if world_lore else ""
        memory_context = ""
        if story_memory and len(story_memory) > 0:
            memory_context = "\nADVENTURER'S RECENT HISTORY:\n" + "\n".join(f"- {e}" for e in list(story_memory)) + "\n"
            context_note = "They are RETURNING to the guild after recent adventures."
        else:
            context_note = "They are arriving at the guild for the first time."

        prompt = f"""
        You are the Dungeon Master narrating the player's arrival at the Adventurer's Guild.
        {lore_context}{memory_context}
        Player: {player_name}
        {context_note}

        INSTRUCTIONS:
        1. 2-3 sentences. Evoke the warmth and safety of the guild versus the dangers outside.
        2. If the player has a story history, reference their recent deeds briefly.
        3. End by hinting at the Quest Board and the adventures waiting.
        4. Second person. No mechanical terms.
        """
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"The Guildhall doors swing open to welcome you, {player_name}. The hearth crackles. Adventure awaits on the Quest Board."
