"""
CharacterAgent — Zero-Hallucination hybrid character creation engine.

Methods:
  - generate_narrative_profile() : classifies a bio into an archetype_tag + narrative fields
  - expand_world_lore()          : expands a world concept into a structured Markdown document
"""
from typing import Dict, Any
from src.agents.base import BaseLLMProvider
from src.models.toon_converter import TOONConverter


class CharacterAgent(BaseLLMProvider):

    def generate_narrative_profile(self, bio: str, edit_instructions: str = "") -> Dict[str, Any]:
        """
        Zero-Hallucination Hybrid Character Engine.
        
        The LLM ONLY generates narrative/classification data:
          - archetype_tag: maps to a hardcoded stat template (never hallucinated numbers)
          - name, dynamic_title, lore, stat_justification, flavor_trinkets
        
        Python then merges these fields with the safe math from data/premade/characters/<tag>.json.
        """
        full_bio = bio
        if edit_instructions:
            full_bio = f"{bio}\n\n[PLAYER EDIT REQUEST]: {edit_instructions}"

        valid_archetypes = "fighter, mage, rogue, cleric, ranger, paladin"
        prompt = f"""\
You are the Character Creation Engine for a dark fantasy RPG.
Read the player biography below and output a character profile.

VALID ARCHETYPES: {valid_archetypes}

BIOGRAPHY:
"{full_bio}"

RULES:
1. Choose the single BEST archetype_tag from the valid list above.
2. If a name is not in the bio, invent a fitting one.
3. lore must be 2-3 immersive sentences expanding the bio into a full backstory.
4. stat_justification must be ONE sentence explaining WHY this archetype matches the bio (e.g. 'Your raw battlefield experience marks you as a Fighter...'). DO NOT mention numbers.
5. dynamic_title is a short evocative nickname (e.g. 'The Iron-Armed Vanguard', 'The Blind Monk'). Max 5 words.
6. flavor_trinkets are 1-2 unique narrative items fitting the bio (e.g. 'Scratched mercenary insignia', 'A folded letter never sent'). These are PURELY COSMETIC — no game effect.

OUTPUT FORMAT (TOON SYNTAX - 1 STRICT LINE, pipe-separated):
archetype_tag:fighter|name:Jax|dynamic_title:The Iron-Armed Vanguard|lore:A cynical mercenary...|stat_justification:Your battlefield scars mark you as a Fighter.|flavor_trinkets:Scratched insignia,Lucky hexagonal coin

CRITICAL: Use a 1 line. No JSON. No line breaks. Replace any commas inside field values with semicolons. Separate trinkets with a comma.
"""
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```"): raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = TOONConverter.decode(raw)

            if "archetype_tag" not in data: data["archetype_tag"] = "fighter"
            if "name" not in data: data["name"] = "Hero"
            if "dynamic_title" not in data: data["dynamic_title"] = ""
            if "lore" not in data: data["lore"] = "A brave adventurer seeking glory."
            if "stat_justification" not in data: data["stat_justification"] = "A well-rounded warrior."
            if "flavor_trinkets" not in data: data["flavor_trinkets"] = ""

            data["archetype_tag"] = data["archetype_tag"].lower().strip()
            return data

        except Exception:
            return {
                "archetype_tag": "fighter", "name": "Hero",
                "dynamic_title": "", "lore": "A brave adventurer.",
                "stat_justification": "A steadfast warrior.", "flavor_trinkets": ""
            }

    def expand_world_lore(self, concept: str, edit_instructions: str = "") -> str:
        """Expands a world concept into a structured lore document with mandated sections."""
        full_concept = concept
        if edit_instructions:
            full_concept = f"{concept}\n\n[EDIT REQUEST]: {edit_instructions}"

        prompt = f"""\
You are an expert worldbuilder for a dark fantasy TTRPG.
Expand the following core concept into a rich World Lore document.

CONCEPT: "{full_concept}"

You MUST output EXACTLY these four sections in this order. Keep each to 2-3 sentences.

### Atmosphere & Setting
[Describe the tone, environment, and what it FEELS like to be there.]

### Key Factions
[Name 2-3 factions or power groups and their role in this world.]

### Magic & Technology
[Describe how magic or technology works, its source, and its cost.]

### Looming Threat
[Describe the single greatest danger or conflict brewing in this world.]

Do NOT include any text before the first ### heading.
"""
        try:
            response = self.narrator_model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return (
                "### Atmosphere & Setting\nA dark and perilous world awaits.\n\n"
                "### Key Factions\nRival guilds vie for power.\n\n"
                "### Magic & Technology\nAncient magic flows unpredictably.\n\n"
                "### Looming Threat\nA shadow stirs at the edge of the world."
            )
