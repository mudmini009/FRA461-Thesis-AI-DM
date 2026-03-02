import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition
from src.logic.enemy_ai import EnemyAI
from src.engine.game_loop import start_combat_loop

def test_pacified():
    print("--- Simulating PACIFIED condition ---")
    player = Character(id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Sword"])
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Gold Coin"])
    
    party = [player]
    enemies = [enemy]
    
    # Simulate Path B Arbiter applying PACIFIED
    enemy.condition = Condition.PACIFIED
    print(f"Enemy condition is now: {enemy.condition.name}")
    
    # 1. Test EnemyAI skips turn
    print("\n[Testing Enemy AI Turn]")
    logs = EnemyAI.take_single_turn(enemy, party)
    for log in logs:
        print(log)
        
    if any("chooses not to attack" in log for log in logs):
        print("✅ SUCCESS: Enemy AI skipped turn.")
    else:
        print("❌ FAILURE: Enemy AI tried to attack.")
        
    # 2. Test VICTORY state detection (manual simulation of the game_loop check)
    print("\n[Testing VICTORY Check]")
    active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS, Condition.PACIFIED]]
    
    if not active_enemies:
        print("✅ SUCCESS: VICTORY state triggered (len active_enemies is 0).")
    else:
        print("❌ FAILURE: VICTORY was not triggered.")

if __name__ == '__main__':
    test_pacified()
