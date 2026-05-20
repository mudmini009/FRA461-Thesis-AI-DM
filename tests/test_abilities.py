import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition, Ability, RechargeType
from src.router.intents import execute_fixed_action

def debug_print_mock(*args):
    print("MOCK-DEBUG:", *args)

def test_cleric_ability_pray_charges():
    """Verify that Pray alone correctly consumes exactly 1 charge and resolves."""
    pray_ability = Ability(name="Pray", recharge_type=RechargeType.SHORT_REST, max_uses=3, current_uses=3)
    player = Character(
        id="p1", name="Inquisitor Valerius", role="Cleric", 
        stats={Stat.PHYS: 1, Stat.MENT: 20, Stat.SOC: 2}, hp=20, max_hp=20, ac=15, 
        zone=Zone.NEAR, inventory=[], abilities=[pray_ability]
    )
    enemy = Character(
        id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 1, Stat.MENT: 0, Stat.SOC: 0}, 
        hp=10, max_hp=10, ac=12, zone=Zone.NEAR, inventory=[]
    )

    decision = {
        'type': 'FIXED',
        'command': 'ABILITY',
        'ability_name': 'Pray',
        'target': 'p1'
    }

    assert player.abilities[0].current_uses == 3
    success, log_msg = execute_fixed_action('ABILITY', decision, player, [enemy], debug_print_mock)
    assert success is True
    assert player.abilities[0].current_uses == 2
    assert "used Pray" in log_msg


def test_cleric_combo_pray_attack_charges():
    """Verify a combo of Pray + Attack only consumes Pray charge once and executes both."""
    pray_ability = Ability(name="Pray", recharge_type=RechargeType.SHORT_REST, max_uses=3, current_uses=3)
    player = Character(
        id="p1", name="Inquisitor Valerius", role="Cleric", 
        stats={Stat.PHYS: 1, Stat.MENT: 20, Stat.SOC: 2}, hp=20, max_hp=20, ac=15, 
        zone=Zone.NEAR, inventory=[], abilities=[pray_ability]
    )
    enemy = Character(
        id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 1, Stat.MENT: 0, Stat.SOC: 0}, 
        hp=100, max_hp=100, ac=12, zone=Zone.NEAR, inventory=[]
    )

    decision = {
        'type': 'FIXED_COMBO',
        'action_order': ['ABILITY', 'ATTACK'],
        'ability_name': 'Pray',
        'attack_target': 'e1',
        'target': 'e1'
    }

    assert player.abilities[0].current_uses == 3

    # First action: ABILITY
    success1, log1 = execute_fixed_action('ABILITY', decision, player, [enemy], debug_print_mock)
    assert success1 is True
    assert player.abilities[0].current_uses == 2

    # Reset player's turn state so they can act in the same mock combo
    player.reset_turn()

    # Second action: ATTACK (should NOT decrement or validate Pray again because it's an ATTACK action type, not ABILITY or Smite)
    success2, log2 = execute_fixed_action('ATTACK', decision, player, [enemy], debug_print_mock)
    assert success2 is True
    assert player.abilities[0].current_uses == 2  # Still 2!
    assert "attacked" in log2


def test_paladin_combo_smite_attack_charges():
    """Verify that Smite + Attack correctly triggers the Smite pre-execution guard during ATTACK."""
    smite_ability = Ability(name="Smite", recharge_type=RechargeType.SHORT_REST, max_uses=2, current_uses=2)
    player = Character(
        id="p1", name="Sir Chad", role="Paladin", 
        stats={Stat.PHYS: 3, Stat.MENT: 1, Stat.SOC: 1}, hp=20, max_hp=20, ac=16, 
        zone=Zone.NEAR, inventory=[], abilities=[smite_ability]
    )
    enemy = Character(
        id="e1", name="Orc", role="Monster", stats={Stat.PHYS: 2, Stat.MENT: 0, Stat.SOC: 0}, 
        hp=15, max_hp=15, ac=13, zone=Zone.NEAR, inventory=[]
    )

    decision = {
        'type': 'FIXED',
        'command': 'ATTACK',
        'ability_name': 'Smite',
        'target': 'e1'
    }

    assert player.abilities[0].current_uses == 2
    success, log_msg = execute_fixed_action('ATTACK', decision, player, [enemy], debug_print_mock)
    assert success is True
    assert player.abilities[0].current_uses == 1
    assert "attacked" in log_msg


def test_combo_early_break_on_failure():
    """Verify that if the first action in a combo fails, the loop breaks early."""
    # We will simulate the loop from game_loop.py
    pray_ability = Ability(name="Pray", recharge_type=RechargeType.SHORT_REST, max_uses=0, current_uses=0)  # 0 uses left!
    player = Character(
        id="p1", name="Inquisitor Valerius", role="Cleric", 
        stats={Stat.PHYS: 1, Stat.MENT: 3, Stat.SOC: 2}, hp=20, max_hp=20, ac=15, 
        zone=Zone.NEAR, inventory=[], abilities=[pray_ability]
    )
    enemy = Character(
        id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 1, Stat.MENT: 0, Stat.SOC: 0}, 
        hp=10, max_hp=10, ac=12, zone=Zone.NEAR, inventory=[]
    )

    decision = {
        'type': 'FIXED_COMBO',
        'action_order': ['ABILITY', 'ATTACK'],
        'ability_name': 'Pray',
        'attack_target': 'e1',
        'target': 'e1'
    }

    actions_run = []
    action_order = decision['action_order']
    
    for action in action_order:
        actions_run.append(action)
        success, log_msg = execute_fixed_action(action, decision, player, [enemy], debug_print_mock)
        if not success:
            break
            
    assert actions_run == ['ABILITY']  # Broke early, didn't run ATTACK!
