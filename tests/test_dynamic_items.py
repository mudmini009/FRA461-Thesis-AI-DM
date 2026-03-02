import os
import sys
import json

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition
from src.router.intents import execute_fixed_action

def debug_print_mock(*args):
    print(*args)

def test_dynamic_items():
    print("--- Simulating Dynamic Consumable Uses (Item Arbiter) ---\n")
    
    # We will give the player weird, non-standard items that aren't in any static dictionary.
    weird_inventory = [
        "Radioactive Moon Cactus",  # Should be healing or damage depending on AI interpretation 
        "Grandma's Chicken Soup",   # Should be BIG_HEAL or SMALL_HEAL
        "Mystic Eyedrops of Clarity",# Should be CURE
        "Frag Grenade"             # Should be DAMAGE
    ]
    
    player = Character(
        id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, 
        hp=5, max_hp=30, ac=15, zone=Zone.NEAR, inventory=weird_inventory
    )
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=[])
    
    player.condition = Condition.BLINDED
    print(f"Initial State: {player.hp}/{player.max_hp} HP, Condition: {player.condition.name}")
    print(f"Inventory: {player.inventory}\n")
    print("--------------------------------------------------\n")

    # 1. Test Grandma's Soup (Healing)
    print(f"🗣️  Player action: USE Grandma's Chicken Soup")
    decision = {'type': 'FIXED', 'command': 'USE', 'target': "Grandma's Chicken Soup"}
    execute_fixed_action('USE', decision, player, [enemy], debug_print_mock)
    print(f"📊 State After: {player.hp}/{player.max_hp} HP, Inventory: {player.inventory}\n")
    
    # 2. Test Mystic Eyedrops (Cure)
    print(f"🗣️  Player action: USE Mystic Eyedrops of Clarity")
    decision = {'type': 'FIXED', 'command': 'USE', 'target': "Mystic Eyedrops of Clarity"}
    execute_fixed_action('USE', decision, player, [enemy], debug_print_mock)
    print(f"📊 State After: Condition: {player.condition.name}, Inventory: {player.inventory}\n")

    # 3. Test Frag Grenade (Damage)
    print(f"🗣️  Player action: USE Frag Grenade")
    decision = {'type': 'FIXED', 'command': 'USE', 'target': "Frag Grenade"}
    execute_fixed_action('USE', decision, player, [enemy], debug_print_mock)
    print(f"📊 State After: {player.hp}/{player.max_hp} HP, Inventory: {player.inventory}\n")

    # 4. Test Radioactive Moon Cactus (Wildcard)
    print(f"🗣️  Player action: USE Radioactive Moon Cactus")
    decision = {'type': 'FIXED', 'command': 'USE', 'target': "Radioactive Moon Cactus"}
    execute_fixed_action('USE', decision, player, [enemy], debug_print_mock)
    print(f"📊 State After: {player.hp}/{player.max_hp} HP, Inventory: {player.inventory}\n")
    
if __name__ == '__main__':
    test_dynamic_items()
