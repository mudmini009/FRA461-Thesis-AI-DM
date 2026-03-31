import os
import sys
import json
# Change working directory to project root and add to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)
from src.services.data_manager import DataManager

def test():
    print("1. Loading Data...")
    dm = DataManager()
    party, enemies, _, _ = dm.load_game()
    
    target = enemies[0] # Grok
    initial_hp = target.hp
    print(f"   Grok HP: {initial_hp}")
    
    print("2. Modifying Data (Damage -1)...")
    target.take_damage(1)
    print(f"   Grok New HP: {target.hp}")
    
    print("3. Saving Data...")
    dm.save_game(party, enemies)
    
    print("4. verifying File Content...")
    with open("data/active/campaign_active.json", 'r') as f:
        data = json.load(f)
        saved_hp = data['enemies'][0]['hp']
        print(f"   Saved HP in File: {saved_hp}")
        
    if saved_hp == target.hp:
        print("✅ SUCCESS: Persistence works.")
    else:
        print("❌ FAILURE: File not updated.")

if __name__ == "__main__":
    test()
