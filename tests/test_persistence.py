import os
import sys
import json
import copy

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.services.data_manager import DataManager
from src.models.character import Character, Condition, Stat, Zone


def _make_test_enemy() -> Character:
    """Provisions a self-contained test enemy — no reliance on campaign_active.json."""
    with open("data/config/bestiary.json", "r") as f:
        bestiary = json.load(f)
    tag = list(bestiary.keys())[0]
    raw = bestiary[tag]
    converted_stats = {}
    for k, v in raw.get("stats", {}).items():
        try:
            converted_stats[Stat[k.upper()]] = v
        except KeyError:
            pass
    return Character(
        id="e_test",
        name=tag.capitalize(),
        role="Enemy",
        hp=raw.get("hp", 10),
        max_hp=raw.get("max_hp", 10),
        ac=raw.get("ac", 10),
        stats=converted_stats,
        zone=Zone.FAR,
        inventory=raw.get("inventory", []),
        condition=Condition.NORMAL,
    )


def test():
    print("1. Loading Data...")
    dm = DataManager()
    party, enemies, cm, sm, global_state = dm.load_game()

    # Provision a fresh test enemy rather than relying on campaign_active.json
    # (new games start with enemies=[], so this test must be self-contained)
    test_enemy = _make_test_enemy()
    enemies = [test_enemy]
    print(f"   Test Enemy: {test_enemy.name}, HP: {test_enemy.hp}")

    print("2. Modifying Data (Damage -1)...")
    initial_hp = test_enemy.hp
    test_enemy.take_damage(1)
    print(f"   New HP: {test_enemy.hp}")

    print("3. Saving Data...")
    dm.save_game(party, enemies, combat_memory=cm, story_memory=sm, global_state=global_state)

    print("4. Verifying File Content...")
    with open("data/active/campaign_active.json", "r") as f:
        data = json.load(f)
        saved_hp = data["enemies"][0]["hp"]
        print(f"   Saved HP in File: {saved_hp}")

    if saved_hp == test_enemy.hp:
        print("✅ SUCCESS: Persistence works.")
    else:
        print("❌ FAILURE: File not updated.")
    assert saved_hp == test_enemy.hp, f"Expected {test_enemy.hp}, got {saved_hp}"

    # Restore enemies to empty so we don't pollute the live save
    dm.save_game(party, [], combat_memory=cm, story_memory=sm, global_state=global_state)
    print("   ✅ Cleanup: Restored enemies=[] in save file.")


if __name__ == "__main__":
    test()
