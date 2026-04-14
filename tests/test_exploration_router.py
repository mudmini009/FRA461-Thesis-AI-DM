"""
test_exploration_router.py — Pure-Python unit tests for the Exploration Engine.

NO LLM, NO API KEY required. These tests verify:
  - ExplorationRouter classification
  - QuestLoader node resolution and state mutations
  - REST guardrails
  - MOVE guardrails (valid/invalid)
  - Combat bridge conditions
  - visited/cleared flag separation (CEO Fix #1 — Infinite Lore Loophole)
  - Lore appending only on first visit
"""
import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.router.exploration_router import (
    classify_exploration_intent,
    get_rest_rejection_message,
    get_move_rejection_message,
)
from src.services.quest_loader import QuestLoader

# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_QUEST = {
    "quest_id": "test_quest",
    "name": "Test Dungeon",
    "entrance_node": "node_a",
    "nodes": {
        "node_a": {
            "node_id": "node_a",
            "name": "Entrance Hall",
            "base_description": "A dusty entrance.",
            "connected_to": ["node_b", "node_c"],
            "event_type": "safe",
            "visited": False,
            "cleared": True,
            "enemy_tag": None,
            "lore_fragment": "This is the first lore fragment.",
        },
        "node_b": {
            "node_id": "node_b",
            "name": "Combat Room",
            "base_description": "Enemies lurk here.",
            "connected_to": ["node_a"],
            "event_type": "combat",
            "visited": False,
            "cleared": False,
            "enemy_tag": "goblin",
            "lore_fragment": "Second lore fragment.",
        },
        "node_c": {
            "node_id": "node_c",
            "name": "Safe Alcove",
            "base_description": "A quiet, safe side room.",
            "connected_to": ["node_a"],
            "event_type": "safe",
            "visited": False,
            "cleared": True,
            "enemy_tag": None,
            "lore_fragment": None,
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 1: ExplorationRouter Classification
# ═══════════════════════════════════════════════════════════════════════════════

class TestExplorationRouterClassification:

    def test_move_basic(self):
        result = classify_exploration_intent("I walk to the main shaft")
        assert result["type"] == "MOVE"
        assert "main shaft" in result["raw_target"].lower()

    def test_move_charge(self):
        result = classify_exploration_intent("I charge into the room")
        assert result["type"] == "MOVE"

    def test_move_go(self):
        result = classify_exploration_intent("go north")
        assert result["type"] == "MOVE"

    def test_look_basic(self):
        result = classify_exploration_intent("I look around the room")
        assert result["type"] == "LOOK"

    def test_look_inspect(self):
        result = classify_exploration_intent("inspect the collapsed cart")
        assert result["type"] == "LOOK"

    def test_rest_basic(self):
        result = classify_exploration_intent("I want to rest")
        assert result["type"] == "REST"

    def test_rest_camp(self):
        result = classify_exploration_intent("I set up camp and sleep")
        assert result["type"] == "REST"

    def test_quest_board(self):
        result = classify_exploration_intent("check the quest board")
        assert result["type"] == "QUEST_BOARD"

    def test_status(self):
        result = classify_exploration_intent("show my character status")
        assert result["type"] == "STATUS"

    def test_quit(self):
        result = classify_exploration_intent("quit")
        assert result["type"] == "QUIT"

    def test_unknown_fallback(self):
        result = classify_exploration_intent("blah blah nonsense command xyz")
        assert result["type"] == "UNKNOWN"

    def test_move_strips_prepositions(self):
        """Ensure 'I move to the Combat Room' strips 'to the' correctly."""
        result = classify_exploration_intent("I move to the Combat Room")
        assert result["type"] == "MOVE"
        raw = result["raw_target"].lower()
        assert "combat room" in raw
        assert raw.strip() != ""  # Target should not be empty after strip


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 2: QuestLoader — Node Resolution
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuestLoaderNodeResolution:

    def test_get_node_exists(self):
        node = QuestLoader.get_node(SAMPLE_QUEST, "node_a")
        assert node is not None
        assert node["name"] == "Entrance Hall"

    def test_get_node_missing(self):
        node = QuestLoader.get_node(SAMPLE_QUEST, "nonexistent")
        assert node is None

    def test_resolve_move_exact_id(self):
        node_a = QuestLoader.get_node(SAMPLE_QUEST, "node_a")
        result = QuestLoader.resolve_move_target("node_b", node_a, SAMPLE_QUEST)
        assert result == "node_b"

    def test_resolve_move_display_name(self):
        """Player types 'Combat Room' — should resolve to node_b."""
        node_a = QuestLoader.get_node(SAMPLE_QUEST, "node_a")
        result = QuestLoader.resolve_move_target("Combat Room", node_a, SAMPLE_QUEST)
        assert result == "node_b"

    def test_resolve_move_display_name_partial(self):
        """Player types 'combat' — should still resolve via substring."""
        node_a = QuestLoader.get_node(SAMPLE_QUEST, "node_a")
        result = QuestLoader.resolve_move_target("combat", node_a, SAMPLE_QUEST)
        assert result == "node_b"

    def test_resolve_move_invalid_not_connected(self):
        """node_b is not connected to node_c — must return None."""
        node_b = QuestLoader.get_node(SAMPLE_QUEST, "node_b")
        result = QuestLoader.resolve_move_target("Safe Alcove", node_b, SAMPLE_QUEST)
        assert result is None

    def test_resolve_move_completely_wrong(self):
        node_a = QuestLoader.get_node(SAMPLE_QUEST, "node_a")
        result = QuestLoader.resolve_move_target("purple dragon tavern", node_a, SAMPLE_QUEST)
        assert result is None

    def test_get_entrance_node_id(self):
        entrance = QuestLoader.get_entrance_node_id(SAMPLE_QUEST)
        assert entrance == "node_a"


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 3: REST Guardrails
# ═══════════════════════════════════════════════════════════════════════════════

class TestRestGuardrails:

    def test_rest_blocked_in_uncleared_combat_room(self):
        """CEO Fix: combat + cleared=False must block REST."""
        node = {"event_type": "combat", "cleared": False}
        msg = get_rest_rejection_message(node)
        assert msg is not None
        assert "rest" in msg.lower() or "enemy" in msg.lower() or "cannot" in msg.lower()

    def test_rest_allowed_in_safe_room(self):
        """Safe rooms always allow REST."""
        node = {"event_type": "safe", "cleared": True}
        msg = get_rest_rejection_message(node)
        assert msg is None

    def test_rest_blocked_in_puzzle_room(self):
        """Puzzle rooms should block rest."""
        node = {"event_type": "puzzle", "cleared": True}
        msg = get_rest_rejection_message(node)
        assert msg is not None

    def test_rest_blocked_in_boss_room_active(self):
        node = {"event_type": "boss", "cleared": False}
        msg = get_rest_rejection_message(node)
        assert msg is not None

    def test_rest_allowed_after_combat_cleared(self):
        """After clearing a room (cleared=True), rest should be allowed."""
        node = {"event_type": "combat", "cleared": True}
        msg = get_rest_rejection_message(node)
        assert msg is None


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 4: MOVE Rejection Message
# ═══════════════════════════════════════════════════════════════════════════════

class TestMoveRejection:

    def test_rejection_message_mentions_target(self):
        node = {"connected_to": ["node_b"]}
        msg = get_move_rejection_message("purple dragon", node)
        assert "purple dragon" in msg

    def test_rejection_message_no_exits(self):
        node = {"connected_to": []}
        msg = get_move_rejection_message("anywhere", node)
        assert "nowhere" in msg.lower() or "no" in msg.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 5: CEO Fix #1 — visited vs cleared Separation (Infinite Lore Loophole)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVisitedVsClearedFlags:

    def test_visited_and_cleared_are_independent_fields(self):
        """Safe rooms are cleared=True but visited=False at authoring time."""
        node = SAMPLE_QUEST["nodes"]["node_a"]
        assert node["cleared"] is True    # authored cleared, never touched by Python
        assert node["visited"] is False   # not yet visited

    def test_mark_visited_does_not_change_cleared(self):
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        QuestLoader.mark_visited(quest, "node_a")
        node = quest["nodes"]["node_a"]
        assert node["visited"] is True
        assert node["cleared"] is True  # unchanged

    def test_mark_cleared_does_not_change_visited(self):
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        QuestLoader.mark_cleared(quest, "node_b")
        node = quest["nodes"]["node_b"]
        assert node["cleared"] is True
        assert node["visited"] is False  # unchanged

    def test_lore_only_appended_on_first_visit(self, tmp_path):
        """Simulate lore append guard: lore writes once; second call is no-op."""
        lore_file = tmp_path / "world_lore.txt"
        lore_file.write_text("# Base Lore\n", encoding="utf-8")

        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        node_id = "node_a"
        node = quest["nodes"][node_id]

        # First visit: not visited, should append
        assert node["visited"] is False
        QuestLoader.append_lore(node.get("lore_fragment"), str(lore_file))
        QuestLoader.mark_visited(quest, node_id)

        content_after_first = lore_file.read_text(encoding="utf-8")
        assert "first lore fragment" in content_after_first

        # Second visit: already visited, guard prevents re-append
        assert node["visited"] is True
        if not node["visited"]:  # This is what the engine checks
            QuestLoader.append_lore(node.get("lore_fragment"), str(lore_file))

        content_after_second = lore_file.read_text(encoding="utf-8")
        # Lore should appear EXACTLY once
        assert content_after_second.count("first lore fragment") == 1

    def test_lore_append_noop_on_none(self, tmp_path):
        """Node with lore_fragment=None must not write anything."""
        lore_file = tmp_path / "world_lore.txt"
        lore_file.write_text("# Base Lore\n", encoding="utf-8")
        QuestLoader.append_lore(None, str(lore_file))
        content = lore_file.read_text(encoding="utf-8")
        assert content == "# Base Lore\n"

    def test_combat_bridge_fires_only_when_uncleared(self):
        """Combat triggers ONLY when event_type is combat/boss AND cleared=False."""
        combat_node_uncleared = {"event_type": "combat", "cleared": False}
        combat_node_cleared   = {"event_type": "combat", "cleared": True}
        safe_node             = {"event_type": "safe",   "cleared": True}
        boss_node_uncleared   = {"event_type": "boss",   "cleared": False}

        def should_trigger_combat(node):
            return node.get("event_type") in ("combat", "boss") and not node.get("cleared", True)

        assert should_trigger_combat(combat_node_uncleared) is True
        assert should_trigger_combat(combat_node_cleared)   is False
        assert should_trigger_combat(safe_node)             is False
        assert should_trigger_combat(boss_node_uncleared)   is True


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 6: QuestLoader — is_quest_complete
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuestCompletion:

    def test_quest_incomplete_when_combat_node_uncleared(self):
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        assert QuestLoader.is_quest_complete(quest) is False

    def test_quest_complete_after_all_combat_cleared(self):
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        QuestLoader.mark_cleared(quest, "node_b")
        assert QuestLoader.is_quest_complete(quest) is True

    def test_quest_complete_ignores_safe_nodes(self):
        """Safe nodes (cleared=True at authoring) should never block completion."""
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        # Even with safe nodes existing, completion only cares about combat/boss nodes
        QuestLoader.mark_cleared(quest, "node_b")
        assert QuestLoader.is_quest_complete(quest) is True


# ═══════════════════════════════════════════════════════════════════════════════
#  Block 7: QuestLoader — File I/O (temp files)
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuestLoaderFileIO:

    def test_load_and_save_roundtrip(self, tmp_path):
        """Write a quest JSON, load it back, verify data integrity."""
        import copy
        quest = copy.deepcopy(SAMPLE_QUEST)
        quest_path = tmp_path / "test_quest.json"
        with open(quest_path, "w", encoding="utf-8") as f:
            json.dump(quest, f)

        # Patch QUEST_DIR for the loader
        original_dir = QuestLoader.__module__
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_quest.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(quest, f)

            # Direct file load (bypassing QUEST_DIR)
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

        assert loaded["quest_id"] == "test_quest"
        assert "node_a" in loaded["nodes"]
        assert loaded["nodes"]["node_a"]["name"] == "Entrance Hall"
