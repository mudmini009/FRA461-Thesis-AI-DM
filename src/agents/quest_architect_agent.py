"""
QuestArchitectAgent — generates quest board entries from world lore and character context.

Outputs a JSON array of quest summaries (title, description, theme, enemy_tags).
Uses the Arbiter model (low temp) for structured output reliability.
Python validates the schema before returning.
"""
import json
from typing import List, Dict, Any, Optional
from src.agents.base import BaseLLMProvider


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

OUTPUT FORMAT — You MUST return ONLY a valid JSON array. No markdown, no explanation.
Each element must have these exact keys:
- "quest_id": a unique snake_case identifier (e.g. "haunted_chapel")
- "name": a short quest title (e.g. "The Haunted Chapel")
- "description": 1-2 sentence hook for the quest board
- "theme": one word theme (e.g. "undead", "bandits", "beasts")
- "enemy_tags": array of 1-2 tags from the AVAILABLE ENEMY TYPES list above
- "num_nodes": integer between 3 and 5 (how many rooms/locations)

EXAMPLE OUTPUT:
[
  {{
    "quest_id": "burned_chapel",
    "name": "The Burned Chapel",
    "description": "Strange lights flicker in the ruins of the old chapel on Gallows Hill.",
    "theme": "undead",
    "enemy_tags": ["skeleton", "cultist"],
    "num_nodes": 4
  }}
]

Return ONLY the JSON array. No other text."""

        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                raw = response.text.strip()

                # Strip markdown code fences if the model wraps them
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

                quests = json.loads(raw)

                if not isinstance(quests, list):
                    raise ValueError("Response is not a JSON array")

                # Validate each quest entry
                validated = []
                for q in quests:
                    if not all(k in q for k in ("quest_id", "name", "description", "enemy_tags", "num_nodes")):
                        continue
                    # Sanitize quest_id
                    q["quest_id"] = q["quest_id"].lower().replace(" ", "_").replace("-", "_")
                    # Enforce enemy_tags against bestiary
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
