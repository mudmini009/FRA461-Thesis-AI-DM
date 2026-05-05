"""
test_quest_generation.py — Unit tests for procedural quest generation.

Tests:
  1. Schema validation (valid/invalid quest maps)
  2. Graph connectivity detection
  3. Enemy tag enforcement
  4. Fallback template loading
  5. QuestLoader management methods (save, delete, count, bestiary)
"""
import os
import sys
import json
import unittest
import tempfile
import shutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.agents.quest_cartographer_agent import QuestCartographerAgent
from src.services.quest_loader import QuestLoader

BESTIARY_TAGS = ["goblin", "bandit", "skeleton", "wolf", "cultist", "goblin_ambusher", "mine_boss"]


def _make_valid_quest():
    """Returns a minimal valid quest dict."""
    return {
        "quest_id": "test_quest",
        "name": "Test Quest",
        "description": "A test.",
        "entrance_node": "node_01",
        "nodes": {
            "node_01": {
                "node_id": "node_01", "name": "Entrance",
                "base_description": "The entrance.",
                "connected_to": ["node_02"],
                "event_type": "safe",
                "visited": False, "cleared": True,
                "enemy_tag": None,
                "lore_fragment": "Lore 1."
            },
            "node_02": {
                "node_id": "node_02", "name": "Boss Room",
                "base_description": "The boss.",
                "connected_to": ["node_01"],
                "event_type": "boss",
                "visited": False, "cleared": False,
                "enemy_tag": "goblin",
                "lore_fragment": "Lore 2."
            },
        }
    }


class TestQuestSchemaValidation(unittest.TestCase):
    """Tests the _validate_quest_schema static method."""

    def test_valid_quest_passes(self):
        quest = _make_valid_quest()
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_missing_entrance_node(self):
        quest = _make_valid_quest()
        del quest["entrance_node"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("entrance_node" in e for e in errors))

    def test_missing_nodes_dict(self):
        quest = _make_valid_quest()
        del quest["nodes"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("nodes" in e for e in errors))

    def test_dangling_connected_to_reference(self):
        quest = _make_valid_quest()
        quest["nodes"]["node_01"]["connected_to"] = ["node_99"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("node_99" in e for e in errors))

    def test_invalid_enemy_tag(self):
        """Invalid enemy_tag alone is now allowed (backward compat) as long as
        enemy_name OR enemy_tag exists. Test that removing BOTH triggers error."""
        quest = _make_valid_quest()
        del quest["nodes"]["node_02"]["enemy_tag"]
        # No enemy_name either — this should now fail
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("missing both" in e for e in errors))

    def test_no_combat_nodes(self):
        quest = _make_valid_quest()
        quest["nodes"]["node_02"]["event_type"] = "safe"
        quest["nodes"]["node_02"]["enemy_tag"] = None
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("combat" in e.lower() or "boss" in e.lower() for e in errors))

    def test_unreachable_node(self):
        quest = _make_valid_quest()
        # Add a node that nothing connects to
        quest["nodes"]["node_03"] = {
            "node_id": "node_03", "name": "Orphaned Room",
            "base_description": "Nobody can reach me.",
            "connected_to": [],
            "event_type": "safe",
            "visited": False, "cleared": True,
            "enemy_tag": None,
            "lore_fragment": "Orphan lore."
        }
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("unreachable" in e.lower() for e in errors))

    def test_missing_required_field_in_node(self):
        quest = _make_valid_quest()
        del quest["nodes"]["node_01"]["base_description"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("base_description" in e for e in errors))

    def test_combat_node_missing_enemy_tag(self):
        """A combat node with no enemy_tag AND no enemy_name should fail."""
        quest = _make_valid_quest()
        quest["nodes"]["node_02"]["enemy_tag"] = None
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertTrue(any("missing both" in e for e in errors))

    def test_defaults_injected_for_missing_visited_cleared(self):
        """Validator should auto-inject visited=False and cleared defaults."""
        quest = _make_valid_quest()
        del quest["nodes"]["node_01"]["visited"]
        del quest["nodes"]["node_01"]["cleared"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, BESTIARY_TAGS)
        self.assertEqual(errors, [])
        self.assertEqual(quest["nodes"]["node_01"]["visited"], False)
        self.assertEqual(quest["nodes"]["node_01"]["cleared"], True)  # safe node default


class TestQuestLoaderManagement(unittest.TestCase):
    """Tests the new quest management methods."""

    def test_count_available_quests(self):
        count = QuestLoader.count_available_quests()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 1)  # sample_dungeon should always exist

    def test_list_bestiary_tags(self):
        tags = QuestLoader.list_bestiary_tags()
        self.assertIn("goblin", tags)
        self.assertIn("bandit", tags)

    def test_save_and_delete_generated_quest(self):
        """Test save + delete lifecycle for a generated quest."""
        test_id = "_test_generated_quest"
        test_data = _make_valid_quest()
        test_data["quest_id"] = test_id

        # Save
        QuestLoader.save_generated_quest(test_id, test_data)
        path = os.path.join("data", "quests", f"{test_id}.json")
        self.assertTrue(os.path.exists(path))

        # Verify it loads
        loaded = QuestLoader.load_quest(test_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["quest_id"], test_id)

        # Delete (not protected)
        QuestLoader._PROTECTED_QUESTS.discard(test_id)  # Ensure not protected
        QuestLoader.delete_quest(test_id)
        self.assertFalse(os.path.exists(path))

    def test_protected_quests_not_deleted(self):
        """sample_dungeon and hub should never be deleted."""
        QuestLoader.delete_quest("sample_dungeon")
        path = os.path.join("data", "quests", "sample_dungeon.json")
        self.assertTrue(os.path.exists(path))

    def test_fallback_template_exists(self):
        """The fallback template must exist."""
        path = os.path.join("data", "quests", "_fallback_template.json")
        self.assertTrue(os.path.exists(path))
        with open(path, "r") as f:
            data = json.load(f)
        self.assertIn("entrance_node", data)
        self.assertIn("nodes", data)

    def test_underscore_files_excluded_from_listing(self):
        """Files prefixed with _ should not appear in quest listing."""
        quests = QuestLoader.list_available_quests()
        ids = [q["id"] for q in quests]
        self.assertNotIn("_fallback_template", ids)


class TestFallbackLoading(unittest.TestCase):
    """Tests the fallback quest template loading."""

    def test_fallback_loads_and_patches(self):
        result = QuestCartographerAgent._load_fallback(
            "test_fb", "Fallback Quest", "A test fallback.", ["wolf"]
        )
        self.assertEqual(result["quest_id"], "test_fb")
        self.assertEqual(result["name"], "Fallback Quest")
        # Check that enemy tags are patched
        for node in result["nodes"].values():
            if node.get("event_type") in ("combat", "boss"):
                self.assertEqual(node["enemy_tag"], "wolf")


if __name__ == "__main__":
    unittest.main()
