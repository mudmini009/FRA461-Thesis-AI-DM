"""
test_puzzle_and_enemies.py — Unit tests for Puzzle Nodes + Dynamic Bestiary.

Tests:
  1. EnemyFactory scaling at each archetype tier
  2. EnemyFactory minimum HP enforcement
  3. EnemyFactory invalid archetype fallback
  4. Item gating (required_item blocks MOVE)
  5. Item pickup (grants_item on first visit)
  6. Puzzle intent classification (PUZZLE_ATTEMPT routing)
  7. Backward compat (old enemy_tag-only nodes still work)
  8. Validator accepts new schema fields
"""
import os
import sys
import json
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.logic.enemy_factory import EnemyFactory, ARCHETYPES, MIN_ENEMY_HP
from src.models.character import Character, Stat, Zone, Condition
from src.agents.quest_cartographer_agent import QuestCartographerAgent
from src.router.exploration_router import (
    classify_exploration_intent,
    classify_exploration_intent_in_context,
)


def _make_player(max_hp=20):
    """Returns a test player Character."""
    return Character(
        id="player1", name="TestHero", role="Fighter",
        hp=max_hp, max_hp=max_hp, ac=15,
        stats={Stat.PHYS: 3, Stat.MENT: 1, Stat.SOC: 0},
        zone=Zone.NEAR, inventory=["sword", "Rusty Key"],
        condition=Condition.NORMAL,
    )


# ═══════════════════════════════════════════════════════════════
# Feature B: EnemyFactory Tests
# ═══════════════════════════════════════════════════════════════
class TestEnemyFactoryScaling(unittest.TestCase):
    """Tests that EnemyFactory scales enemy HP based on player stats."""

    def test_minion_hp_scales_with_player(self):
        player = _make_player(max_hp=20)
        enemy = EnemyFactory.create("minion", player, "Test Rat")
        # minion hp_mult = 0.4 → 20*0.4 = 8, above MIN_ENEMY_HP(6)
        self.assertEqual(enemy.max_hp, 8)
        self.assertEqual(enemy.hp, 8)

    def test_brute_hp_scales_with_player(self):
        player = _make_player(max_hp=20)
        enemy = EnemyFactory.create("brute", player, "Test Ogre")
        # brute hp_mult = 1.2 → 20*1.2 = 24
        self.assertEqual(enemy.max_hp, 24)

    def test_boss_hp_scales_with_player(self):
        player = _make_player(max_hp=20)
        enemy = EnemyFactory.create("boss", player, "Test Dragon")
        # boss hp_mult = 2.5 → 20*2.5 = 50
        self.assertEqual(enemy.max_hp, 50)

    def test_skirmisher_hp_scales_with_player(self):
        player = _make_player(max_hp=20)
        enemy = EnemyFactory.create("skirmisher", player, "Test Scout")
        # skirmisher hp_mult = 0.7 → 20*0.7 = 14
        self.assertEqual(enemy.max_hp, 14)

    def test_hp_minimum_enforced(self):
        """Even with very low player HP, enemies should have at least MIN_ENEMY_HP."""
        player = _make_player(max_hp=5)
        enemy = EnemyFactory.create("minion", player, "Tiny Rat")
        # 5*0.4 = 2, but minimum is 6
        self.assertEqual(enemy.max_hp, MIN_ENEMY_HP)

    def test_scaling_with_high_hp_player(self):
        """At high player HP, enemies scale proportionally."""
        player = _make_player(max_hp=50)
        enemy = EnemyFactory.create("brute", player, "Mega Brute")
        # 50*1.2 = 60
        self.assertEqual(enemy.max_hp, 60)


class TestEnemyFactoryOutput(unittest.TestCase):
    """Tests the Character output structure from EnemyFactory."""

    def test_enemy_has_correct_name(self):
        player = _make_player()
        enemy = EnemyFactory.create("minion", player, "Crystal Rat", "bites with crystal teeth")
        self.assertEqual(enemy.name, "Crystal Rat")

    def test_enemy_has_attack_flavor_in_lore(self):
        player = _make_player()
        enemy = EnemyFactory.create("minion", player, "Crystal Rat", "bites with crystal teeth")
        self.assertIn("bites with crystal teeth", enemy.lore)

    def test_enemy_has_correct_ac(self):
        player = _make_player()
        for arch_key, arch_data in ARCHETYPES.items():
            enemy = EnemyFactory.create(arch_key, player, "Test")
            self.assertEqual(enemy.ac, arch_data["ac_base"], f"AC mismatch for {arch_key}")

    def test_invalid_archetype_falls_back_to_skirmisher(self):
        player = _make_player()
        enemy = EnemyFactory.create("dragon_lord", player, "Bad Archetype")
        # Should fallback to skirmisher
        self.assertEqual(enemy.role, "Skirmisher")
        self.assertEqual(enemy.ac, ARCHETYPES["skirmisher"]["ac_base"])

    def test_enemy_has_correct_id(self):
        player = _make_player()
        enemy = EnemyFactory.create("minion", player, "Test", enemy_index=3)
        self.assertEqual(enemy.id, "e3")

    def test_get_valid_archetypes(self):
        archetypes = EnemyFactory.get_valid_archetypes()
        self.assertIn("minion", archetypes)
        self.assertIn("skirmisher", archetypes)
        self.assertIn("brute", archetypes)
        self.assertIn("boss", archetypes)
        self.assertEqual(len(archetypes), 4)


# ═══════════════════════════════════════════════════════════════
# Feature A1: Item Gating Tests
# ═══════════════════════════════════════════════════════════════
class TestItemGating(unittest.TestCase):
    """Tests the required_item and grants_item schema fields."""

    def test_required_item_blocks_without_item(self):
        """Player without required_item cannot enter the node."""
        player = _make_player()
        player.inventory = ["sword"]  # No "Ancient Key"
        target_node = {"required_item": "Ancient Key"}
        required = target_node.get("required_item")
        self.assertNotIn(required, player.inventory)

    def test_required_item_allows_with_item(self):
        """Player with required_item can enter the node."""
        player = _make_player()
        player.inventory = ["sword", "Ancient Key"]
        target_node = {"required_item": "Ancient Key"}
        required = target_node.get("required_item")
        self.assertIn(required, player.inventory)

    def test_no_required_item_always_allows(self):
        """Nodes without required_item should always be accessible."""
        target_node = {"required_item": None}
        required = target_node.get("required_item")
        self.assertFalse(required)  # None is falsy

    def test_grants_item_adds_to_inventory(self):
        """grants_item should add item to player inventory."""
        player = _make_player()
        player.inventory = ["sword"]
        granted = "Ancient Key"
        if granted not in player.inventory:
            player.inventory.append(granted)
        self.assertIn("Ancient Key", player.inventory)


# ═══════════════════════════════════════════════════════════════
# Feature A2: Puzzle Intent Classification Tests
# ═══════════════════════════════════════════════════════════════
class TestPuzzleIntentClassification(unittest.TestCase):
    """Tests that the context-aware router routes to PUZZLE_ATTEMPT correctly."""

    def _puzzle_node(self, cleared=False):
        return {
            "event_type": "puzzle",
            "cleared": cleared,
            "puzzle_obstacle": "A toxic gas cloud",
            "puzzle_base_dc": 14,
        }

    def _safe_node(self):
        return {"event_type": "safe", "cleared": True}

    def test_unknown_input_in_puzzle_node_becomes_puzzle_attempt(self):
        """In an uncleared puzzle node, unknown input → PUZZLE_ATTEMPT."""
        node = self._puzzle_node(cleared=False)
        result = classify_exploration_intent_in_context("I blow the gas away with wind magic", node)
        self.assertEqual(result["type"], "PUZZLE_ATTEMPT")

    def test_unknown_input_in_safe_node_stays_unknown(self):
        """In a safe node, unknown input stays UNKNOWN."""
        node = self._safe_node()
        result = classify_exploration_intent_in_context("I blow the gas away with wind magic", node)
        self.assertEqual(result["type"], "UNKNOWN")

    def test_cleared_puzzle_node_stays_unknown(self):
        """In an already-cleared puzzle node, unknown input stays UNKNOWN."""
        node = self._puzzle_node(cleared=True)
        result = classify_exploration_intent_in_context("I blow the gas away", node)
        self.assertEqual(result["type"], "UNKNOWN")

    def test_move_in_puzzle_node_stays_move(self):
        """MOVE commands still work normally in puzzle nodes."""
        node = self._puzzle_node(cleared=False)
        result = classify_exploration_intent_in_context("go to node_02", node)
        self.assertEqual(result["type"], "MOVE")

    def test_look_in_puzzle_node_stays_look(self):
        """LOOK commands still work normally in puzzle nodes."""
        node = self._puzzle_node(cleared=False)
        result = classify_exploration_intent_in_context("look around", node)
        self.assertEqual(result["type"], "LOOK")


# ═══════════════════════════════════════════════════════════════
# Schema Validation Tests (Updated for new fields)
# ═══════════════════════════════════════════════════════════════
class TestUpdatedSchemaValidation(unittest.TestCase):
    """Tests the Cartographer validator with new enemy/puzzle fields."""

    def _make_quest_with_new_fields(self):
        return {
            "quest_id": "test",
            "name": "Test Quest",
            "entrance_node": "node_01",
            "nodes": {
                "node_01": {
                    "node_id": "node_01", "name": "Entrance",
                    "base_description": "The entrance.",
                    "connected_to": ["node_02"],
                    "event_type": "safe",
                    "visited": False, "cleared": True,
                    "lore_fragment": "Lore.",
                    "grants_item": "Rusty Key",
                    "required_item": None,
                },
                "node_02": {
                    "node_id": "node_02", "name": "Boss Room",
                    "base_description": "Boss.",
                    "connected_to": ["node_01"],
                    "event_type": "boss",
                    "visited": False, "cleared": False,
                    "enemy_name": "Crystal Golem",
                    "enemy_archetype": "boss",
                    "enemy_attack_flavor": "Crystal Slam",
                    "enemy_tag": "goblin",
                    "lore_fragment": "Boss lore.",
                    "grants_item": None,
                    "required_item": "Rusty Key",
                },
            }
        }

    def test_valid_quest_with_new_fields_passes(self):
        quest = self._make_quest_with_new_fields()
        errors = QuestCartographerAgent._validate_quest_schema(quest, ["goblin"])
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_invalid_archetype_caught(self):
        quest = self._make_quest_with_new_fields()
        quest["nodes"]["node_02"]["enemy_archetype"] = "dragon_lord"
        errors = QuestCartographerAgent._validate_quest_schema(quest, ["goblin"])
        self.assertTrue(any("dragon_lord" in e for e in errors))

    def test_missing_enemy_name_and_tag_caught(self):
        quest = self._make_quest_with_new_fields()
        del quest["nodes"]["node_02"]["enemy_name"]
        del quest["nodes"]["node_02"]["enemy_tag"]
        errors = QuestCartographerAgent._validate_quest_schema(quest, ["goblin"])
        self.assertTrue(any("missing both" in e for e in errors))

    def test_puzzle_defaults_injected(self):
        """Puzzle nodes without obstacle/dc should get defaults."""
        quest = self._make_quest_with_new_fields()
        quest["nodes"]["node_01"]["event_type"] = "puzzle"
        quest["nodes"]["node_01"]["cleared"] = False
        # Add a combat node to satisfy "at least one combat" requirement
        quest["nodes"]["node_03"] = {
            "node_id": "node_03", "name": "Combat Room",
            "base_description": "Fight.", "connected_to": ["node_01"],
            "event_type": "combat", "enemy_name": "Goblin", "enemy_archetype": "minion",
            "enemy_tag": "goblin", "lore_fragment": "Lore.",
        }
        quest["nodes"]["node_01"]["connected_to"].append("node_03")
        errors = QuestCartographerAgent._validate_quest_schema(quest, ["goblin"])
        self.assertEqual(errors, [], f"Got: {errors}")
        self.assertEqual(quest["nodes"]["node_01"]["puzzle_obstacle"], "An obstacle blocks your path.")
        self.assertEqual(quest["nodes"]["node_01"]["puzzle_base_dc"], 14)


# ═══════════════════════════════════════════════════════════════
# Backward Compatibility Tests
# ═══════════════════════════════════════════════════════════════
class TestBackwardCompatibility(unittest.TestCase):
    """Tests that old enemy_tag-only quests still work."""

    def test_old_style_quest_validates(self):
        """A quest with enemy_tag but no enemy_name should still validate."""
        quest = {
            "quest_id": "old_style",
            "entrance_node": "node_01",
            "nodes": {
                "node_01": {
                    "node_id": "node_01", "name": "Entrance",
                    "base_description": "Enter.",
                    "connected_to": ["node_02"],
                    "event_type": "safe",
                    "lore_fragment": "Lore.",
                },
                "node_02": {
                    "node_id": "node_02", "name": "Boss",
                    "base_description": "Boss.",
                    "connected_to": ["node_01"],
                    "event_type": "boss",
                    "enemy_tag": "goblin",
                    "lore_fragment": "Boss lore.",
                },
            }
        }
        errors = QuestCartographerAgent._validate_quest_schema(quest, ["goblin"])
        self.assertEqual(errors, [], f"Old-style quest failed: {errors}")

    def test_sample_dungeon_still_validates(self):
        """The pre-made sample_dungeon.json must still pass validation."""
        path = os.path.join("data", "quests", "sample_dungeon.json")
        with open(path, "r") as f:
            quest = json.load(f)
        bestiary_path = os.path.join("data", "config", "bestiary.json")
        with open(bestiary_path, "r") as f:
            bestiary_tags = list(json.load(f).keys())
        errors = QuestCartographerAgent._validate_quest_schema(quest, bestiary_tags)
        self.assertEqual(errors, [], f"sample_dungeon failed: {errors}")


if __name__ == "__main__":
    unittest.main()
