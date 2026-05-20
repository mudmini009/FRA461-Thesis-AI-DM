"""
QuestArchitectAgent — generates quest board entries from world lore and character context.

Outputs a JSON array of quest summaries (title, description, theme, enemy_tags).
Uses the Arbiter model (low temp) for structured output reliability.
Python validates the schema before returning.
"""
import json
from typing import List, Dict, Any, Optional
from src.agents.base import BaseLLMProvider
from src.models.toon_converter import TOONConverter


# Hardcoded fallback board entries for when LLM fails
_FALLBACK_BOARD = [
    {
        "quest_id": "rat_cellar",
        "name": "Trouble in the Cellar",
        "description": "The Guild's own cellar has been overrun by unusually aggressive rats. "
                       "Clear them out before they get into the food stores.",
        "theme": "vermin",
        "enemy_tags": ["goblin"],
        "num_nodes": 3,
    },
    {
        "quest_id": "bandit_road",
        "name": "Bandit Ambush on the King's Road",
        "description": "Merchant caravans have reported armed bandits blocking the eastern road. "
                       "The Guild needs someone to clear the route.",
        "theme": "bandit",
        "enemy_tags": ["bandit"],
        "num_nodes": 4,
    },
]


class QuestArchitectAgent(BaseLLMProvider):

    def generate_quest_board(
        self,
        character_toon: str,
        world_lore: str,
        bestiary_tags: List[str],
        num_quests: int = 3,
        existing_quest_ids: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates quest board summaries that match the world lore and character.

        Returns a list of dicts, each with:
          quest_id, name, description, theme, enemy_tags, num_nodes

        Falls back to hardcoded entries if LLM fails or returns invalid JSON.
        """
        existing_ids = existing_quest_ids or []
        existing_clause = ""
        if existing_ids:
            existing_clause = (
                f"\nALREADY ON THE BOARD (do NOT duplicate these): {', '.join(existing_ids)}\n"
            )

        tags_str = json.dumps(bestiary_tags)

        prompt = f"""You are a quest designer for a dark-fantasy TTRPG.
Generate exactly {num_quests} quest board postings for an Adventurer's Guild.

CHARACTER CONTEXT:
{character_toon}

WORLD LORE:
{world_lore}
{existing_clause}
AVAILABLE ENEMY TYPES (you MUST only use tags from this list):
{tags_str}

OUTPUT FORMAT (TOON SYNTAX ONLY - STRICT):
You MUST NOT output JSON or XML. You must output exactly {num_quests} lines of pipe-separated key:value pairs.
Each line must represent a single quest posting with the following keys:
- quest_id: a unique snake_case identifier (e.g. "haunted_chapel")
- name: a short quest title (e.g. "The Haunted Chapel")
- description: 1-2 sentence hook for the quest board
- theme: one word theme (e.g. "undead", "bandits", "beasts")
- enemy_tags: array of 1-2 tags from the AVAILABLE ENEMY TYPES list above inside brackets (e.g. [skeleton,cultist])
- num_nodes: integer between 3 and 5 (how many rooms/locations)

CRITICAL: Output EXACTLY {num_quests} lines. Do NOT write any code fences, introduction, or explanations. Use only pipe (|) delimiters.

EXAMPLE OUTPUT:
quest_id:burned_chapel|name:The Burned Chapel|description:Strange lights flicker in the ruins of the old chapel on Gallows Hill.|theme:undead|enemy_tags:[skeleton,cultist]|num_nodes:4
"""

        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                raw = response.text.strip()

                # Parse TOON lines
                lines = [line.strip() for line in raw.split('\n') if line.strip()]
                # Strip ``` if present
                lines = [line for line in lines if not line.startswith("```")]

                quests = []
                for line in lines:
                    q = TOONConverter.decode(line)
                    if q:
                        quests.append(q)

                if not isinstance(quests, list):
                    raise ValueError("Response is not a list of quests")

                # Validate each quest entry
                validated = []
                for q in quests:
                    if not all(k in q for k in ("quest_id", "name", "description", "enemy_tags", "num_nodes")):
                        continue
                    # Sanitize quest_id
                    q["quest_id"] = str(q["quest_id"]).lower().replace(" ", "_").replace("-", "_")
                    # Enforce enemy_tags against bestiary
                    if not isinstance(q["enemy_tags"], list):
                        q["enemy_tags"] = [str(q["enemy_tags"])]
                    q["enemy_tags"] = [t for t in q["enemy_tags"] if t in bestiary_tags]
                    if not q["enemy_tags"]:
                        q["enemy_tags"] = [bestiary_tags[0]]  # fallback to first tag
                    # Clamp num_nodes
                    q["num_nodes"] = max(3, min(6, int(q.get("num_nodes", 4))))
                    # Set theme default
                    if "theme" not in q:
                        q["theme"] = "adventure"
                    validated.append(q)

                if len(validated) >= 1:
                    return validated[:num_quests]

                # If nothing validated, retry
                if attempt == 0:
                    continue

            except Exception as e:
                if attempt == 0:
                    continue
                print(f"   ⚠️ Quest board generation failed: {e}")

        # Fallback
        print("   📋 [SYSTEM] Using fallback quest board.")
        return _FALLBACK_BOARD[:num_quests]
