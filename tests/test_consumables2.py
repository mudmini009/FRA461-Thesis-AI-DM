import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition
from src.logic.rules_engine import RulesEngine
from src.router.intents import execute_fixed_action

def debug_print_mock(*args):
    print(*args)

def test_consumables():
    print("--- Simulating Consumable Uses (Path A) ---")
    
    # Setup injured player with items
    player = Character(id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, hp=5, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Health Potion", "Antidote", "Rusty Sword"])
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=[])
    
    player.condition = Condition.BLINDED
    print(f"Initial State: {player.hp}/{player.max_hp} HP, Condition: {player.condition.name}, Inventory: {player.inventory}\n")

    # 1. Test Healing Potion
    print("[Testing Potion (HEAL)]")
    decision_use_potion = {'type': 'FIXED', 'command': 'USE', 'target': 'potion'}
    execute_fixed_action('USE', decision_use_potion, player, [enemy], debug_print_mock)
    print(f"After Potion: {player.hp}/{player.max_hp} HP, Inventory: {player.inventory}\n")
    
    if player.hp > 5 and "Health Potion" not in player.inventory:
        print("✅ SUCCESS: Potion healed player and was consumed.")
    else:
        print("❌ FAILURE: Potion logic failed.")

    # 2. Test Antidote
    print("[Testing Antidote (CURE)]")
    decision_use_antidote = {'type': 'FIXED', 'command': 'USE', 'target': 'antidote'}
    execute_fixed_action('USE', decision_use_antidote, player, [enemy], debug_print_mock)
    print(f"After Antidote: Condition: {player.condition.name}, Inventory: {player.inventory}\n")
    
    if player.condition == Condition.NORMAL and "Antidote" not in player.inventory:
        print("✅ SUCCESS: Antidote cured condition and was consumed.")
    else:
        print("❌ FAILURE: Antidote logic failed.")
        
    # 3. Test Non-Consumable
    print("[Testing Rusty Sword (EQUIP)]")
    decision_use_sword = {'type': 'FIXED', 'command': 'USE', 'target': 'sword'}
    execute_fixed_action('USE', decision_use_sword, player, [enemy], debug_print_mock)
    print(f"After Sword: Inventory: {player.inventory}\n")
    
    if "Rusty Sword" in player.inventory:
        print("✅ SUCCESS: Sword was NOT consumed.")
    else:
        print("❌ FAILURE: Sword was consumed unexpectedly.")

if __name__ == '__main__':
    test_consumables()
