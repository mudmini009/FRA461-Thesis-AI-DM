"""
LLMService — backward-compatible façade over the specialized agent layer.

All callers (evaluation_runner.py, intents.py, intent_router.py, game_loop.py, startup.py)
import this class unchanged. Internally it delegates every method to the correct agent.

Architecture:
  LLMService
    ├── ArbiterAgent   → get_creative_judgment, categorize_item
    ├── NarratorAgent  → narrate_result, narrate_combat_round, summarize_combat
    ├── CampaignAgent  → generate_recap, generate_prologue
    └── CharacterAgent → generate_narrative_profile, expand_world_lore
"""
from typing import List, Dict, Any, Deque, Optional
from src.models.character import Character
from src.agents.arbiter_agent import ArbiterAgent
from src.agents.narrator_agent import NarratorAgent
from src.agents.campaign_agent import CampaignAgent
from src.agents.character_agent import CharacterAgent


class LLMService:
    """
    Public façade — identical interface to the original monolith.
    Instantiates all four agents with the same settings object,
    then delegates each method call to the appropriate agent.
    """

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self._arbiter = ArbiterAgent(settings=settings)
        self._narrator = NarratorAgent(settings=settings)
        self._campaign = CampaignAgent(settings=settings)
        self._character = CharacterAgent(settings=settings)

    # ─── Arbiter ─────────────────────────────────────────────
    def get_creative_judgment(
        self,
        party_state: List[Character],
        enemies_state: List[Character],
        active_player: Character,
        action_description: str,
        combat_memory: Optional[Deque[str]] = None,
        story_memory: Optional[Deque[str]] = None,
        global_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._arbiter.get_creative_judgment(
            party_state, enemies_state, active_player,
            action_description, combat_memory, story_memory,
            global_state=global_state
        )

    def categorize_item(self, item_name: str) -> Dict[str, Any]:
        return self._arbiter.categorize_item(item_name)

    # ─── Narrator ────────────────────────────────────────────
    def narrate_result(self, action_text: str, roll_result: int, dc: int, is_success: bool) -> str:
        return self._narrator.narrate_result(action_text, roll_result, dc, is_success)

    def narrate_combat_round(
        self,
        action_log: str,
        combat_context: str,
        combat_memory: Optional[Deque[str]] = None,
        story_memory: Optional[Deque[str]] = None,
        world_lore: str = "",
    ) -> str:
        return self._narrator.narrate_combat_round(
            action_log, combat_context, combat_memory, story_memory, world_lore
        )

    def summarize_combat(self, combat_memory: Deque[str]) -> str:
        return self._narrator.summarize_combat(combat_memory)

    # ─── Campaign ────────────────────────────────────────────
    def generate_recap(self, log_lines: List[str]) -> str:
        return self._campaign.generate_recap(log_lines)

    def generate_prologue(self, character_toon: str, world_lore: str) -> Dict[str, str]:
        return self._campaign.generate_prologue(character_toon, world_lore)

    # ─── Character ───────────────────────────────────────────
    def generate_narrative_profile(self, bio: str, edit_instructions: str = "") -> Dict[str, Any]:
        return self._character.generate_narrative_profile(bio, edit_instructions)

    def expand_world_lore(self, concept: str, edit_instructions: str = "") -> str:
        return self._character.expand_world_lore(concept, edit_instructions)

    # ─── Exploration Narrator ────────────────────────────────────
    def narrate_room_entry(self, node: dict, world_lore: str = "", story_memory=None) -> str:
        return self._narrator.narrate_room_entry(node, world_lore, story_memory)

    def narrate_exploration_look(self, node: dict, world_lore: str = "") -> str:
        return self._narrator.narrate_exploration_look(node, world_lore)

    def narrate_encounter_start(self, node: dict, enemy_name: str, world_lore: str = "") -> str:
        return self._narrator.narrate_encounter_start(node, enemy_name, world_lore)

    def narrate_node_cleared(self, node: dict, world_lore: str = "") -> str:
        return self._narrator.narrate_node_cleared(node, world_lore)

    def narrate_hub_welcome(self, player_name: str, world_lore: str = "", story_memory=None, prologue_text: str = "") -> str:
        return self._narrator.narrate_hub_welcome(player_name, world_lore, story_memory, prologue_text)
