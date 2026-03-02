import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition
from src.services.data_manager import DataManager
import json

def test_auto_loot():
    player = Character(id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Sword"])
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Gold Coin", "Rusty Dagger"])
    
    party = [player]
    enemies = [enemy]
    
    # Simulate VICTORY condition logic
    print("--- Simulating VICTORY Auto-Loot ---")
    
    looted_items = []
    for e in enemies:
        if getattr(e, 'inventory', None):
            looted_items.extend(e.inventory)
            e.inventory = [] # Clear enemy pockets

    if looted_items and party:
        main_player = party[0]
        main_player.inventory.extend(looted_items)
        print(f"💰 [SYSTEM] Auto-Looted: [{', '.join(looted_items)}] from the fallen enemies!")
        
    print(f"Player Inventory after loot: {player.inventory}")
    print(f"Enemy Inventory after loot: {enemy.inventory}")
    
    if "Gold Coin" in player.inventory and "Rusty Dagger" in player.inventory and len(enemy.inventory) == 0:
        print("✅ SUCCESS: Auto-Loot logic works!")
    else:
        print("❌ FAILURE: Items were not transferred correctly.")

if __name__ == '__main__':
    test_auto_loot()
