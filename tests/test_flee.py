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

def test_flee_scenarios():
    print("--- Testing Tactical FLEE Scenarios ---\n")
    
    # 1. Simple FLEE at Distance 0 (Hardest)
    player = Character(id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=[])
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 1}, hp=10, max_hp=10, ac=12, zone=Zone.NEAR, inventory=[])
    
    print(f"Scenario 1: Simple FLEE (Distance 0)")
    print(f"Player Zone: {player.zone.name}, Enemy Zone: {enemy.zone.name}")
    
    # We'll run it a few times to show the math
    for i in range(3):
        result = RulesEngine.resolve_escape(player, [enemy])
        status = "SUCCESS" if result['success'] else "FAILED"
        print(f"   Trial {i+1}: {status}")
        print(f"      [Math] Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs "
              f"Enemy ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Penalty) = {result['enemy_total']})")
    print("-" * 30 + "\n")

    # 2. Tactical MOVE + FLEE (Easier)
    print(f"Scenario 2: Tactical MOVE (to MID) then FLEE")
    # Reset Player
    player.zone = Zone.NEAR
    
    # Step 1: Move to MID
    decision_move = {'type': 'FIXED', 'command': 'MOVE', 'target': 'MID'}
    execute_fixed_action('MOVE', decision_move, player, [enemy], debug_print_mock)
    
    print(f"New Player Zone: {player.zone.name}, Enemy Zone: {enemy.zone.name} (Distance 1)")
    
    for i in range(3):
        result = RulesEngine.resolve_escape(player, [enemy])
        status = "SUCCESS" if result['success'] else "FAILED"
        print(f"   Trial {i+1}: {status}")
        print(f"      [Math] Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs "
              f"Enemy ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Penalty) = {result['enemy_total']})")
    print("-" * 30 + "\n")

    # 3. Tactical FLEE then MOVE (If FLEE fails, MOVE still happens)
    print(f"Scenario 3: FLEE then MOVE (Fleeing from danger first)")
    player.zone = Zone.NEAR
    
    # We simulate the loop logic:
    action_order = ['FLEE', 'MOVE']
    decision_combo = {'type': 'FIXED_COMBO', 'action_order': action_order, 'move_target': 'MID'}
    
    print(f"Start: Player at {player.zone.name}")
    
    # Simulate turn
    for action in action_order:
        if action == 'FLEE':
            print(f"-> Attempting FLEE first...")
            result = RulesEngine.resolve_escape(player, [enemy])
            if result['success']:
                print(f"💨 SUCCESS! Player escaped. Stopping turn.")
                break
            else:
                print(f"🛑 FAILED! Closest enemy cut you off. Continuing to next action...")
        else:
            print(f"-> Moving to {decision_combo['move_target']} as fallback...")
            execute_fixed_action(action, decision_combo, player, [enemy], debug_print_mock)

    print(f"\nFinal State: Player at {player.zone.name}")

if __name__ == '__main__':
    test_flee_scenarios()
