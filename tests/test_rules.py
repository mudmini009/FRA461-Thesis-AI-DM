import pytest
import sys
import os

# Add project root to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.character import Character, Stat, Zone, Condition
from src.logic.rules_engine import RulesEngine

class TestComprehensiveRulesEngine:
    @pytest.fixture
    def setup_characters(self):
        attacker = Character(
            id='p1',
            name='Hero',
            role='Fighter',
            hp=20,
            max_hp=20,
            ac=10,
            stats={Stat.PHYS: 2, Stat.MENT: 0, Stat.SOC: 0},
            zone=Zone.NEAR,
        )

        target = Character(
            id='e1',
            name='Goblin',
            role='Enemy',
            hp=20,
            max_hp=20,
            ac=12,
            stats={Stat.PHYS: 0, Stat.MENT: 0, Stat.SOC: 0},
            zone=Zone.NEAR,
        )
        return attacker, target

    def test_attack_roll_should_include_stat_modifier(self, setup_characters):
        attacker, target = setup_characters
        result = RulesEngine.resolve_attack(attacker, target)
        roll = result['roll']
        total = result['total']
        
        assert total == roll + 2  # PHYS is +2

    def test_attack_hit_vs_ac_logic(self, setup_characters):
        attacker, _ = setup_characters
        
        # Guaranteed Hit (except Nat 1)
        # Create new target with AC 1
        low_ac_target = Character(
            id='e_low',
            name='Weakling',
            role='Enemy',
            hp=20,
            max_hp=20,
            ac=1,
            stats={Stat.PHYS: 0, Stat.MENT: 0, Stat.SOC: 0},
            zone=Zone.NEAR
        )

        result = RulesEngine.resolve_attack(attacker, low_ac_target)
        if result['roll'] != 1:
             assert result['is_hit'] is True

        # Hard to Hit
        # Create new target with AC 30
        high_ac_target = Character(
            id='e_high',
            name='Tank',
            role='Enemy',
            hp=20,
            max_hp=20,
            ac=30,
            stats={Stat.PHYS: 0, Stat.MENT: 0, Stat.SOC: 0},
            zone=Zone.NEAR
        )
        
        result = RulesEngine.resolve_attack(attacker, high_ac_target)
        if result['roll'] != 20:
             assert result['is_hit'] is False

    def test_damage_application_reduces_hp(self, setup_characters):
        attacker, _ = setup_characters
        low_ac_target = Character(
            id='e_low',
            name='Weakling',
            role='Enemy',
            hp=20,
            max_hp=20,
            ac=0,
            stats={Stat.PHYS: 0, Stat.MENT: 0, Stat.SOC: 0},
            zone=Zone.NEAR
        )
        
        initial_hp = low_ac_target.hp
        
        # Repeat until we get a hit (to avoid Nat 1)
        result = RulesEngine.resolve_attack(attacker, low_ac_target)
        while not result['is_hit']:
            result = RulesEngine.resolve_attack(attacker, low_ac_target)
            
        damage = result['damage']
        assert low_ac_target.hp == initial_hp - damage

    def test_fighter_uses_phys_and_d8(self, setup_characters):
        _, target = setup_characters
        attacker = Character(
            id='f1',
            name='Fighter',
            role='Fighter',
            hp=20,
            max_hp=20,
            ac=10,
            stats={Stat.PHYS: 0},
            zone=Zone.NEAR
        )
        
        # Run multiple times to estimate dice range [1-8]
        # This is a probabilistic test
        saw_high_damage = False
        for _ in range(50):
            target.hp = 1000 # Prevent death
            res = RulesEngine.resolve_attack(attacker, target)
            if res['is_hit'] and not res['is_crit']:
                dmg = res['damage']
                assert 1 <= dmg <= 8
                if dmg > 6:
                    saw_high_damage = True
        
    def test_paladin_uses_phys_and_2d6(self, setup_characters):
        _, target = setup_characters
        attacker = Character(
            id='p1',
            name='Paladin',
            role='Paladin',
            hp=20,
            max_hp=20,
            ac=10,
            stats={Stat.PHYS: 0},
            zone=Zone.NEAR
        )
        # 2d6 range is 2-12.
        for _ in range(50):
            target.hp = 1000
            res = RulesEngine.resolve_attack(attacker, target)
            if res['is_hit'] and not res['is_crit']:
                dmg = res['damage']
                assert 2 <= dmg <= 12

    def test_mage_uses_ment_and_d10_for_spells(self, setup_characters):
        _, target = setup_characters
        attacker = Character(
            id='m1',
            name='Mage',
            role='Mage',
            hp=20,
            max_hp=20,
            ac=10,
            stats={Stat.MENT: 3, Stat.PHYS: 0},
            zone=Zone.NEAR
        )
        # Ranged Spell
        for _ in range(20):
            target.hp = 1000
            res = RulesEngine.resolve_attack(attacker, target, attack_type='ranged')
            # Check modifier usage
            if res['total'] > 0:
                assert res['total'] == res['roll'] + 3
            if res['is_hit'] and not res['is_crit']:
                dmg = res['damage']
                # d10 + 3 => range 4-13
                assert 4 <= dmg <= 13

    def test_melee_at_distance_0_is_allowed(self, setup_characters):
        attacker, target = setup_characters
        attacker.zone = Zone.NEAR
        target.zone = Zone.NEAR
        res = RulesEngine.resolve_attack(attacker, target, attack_type='melee')
        assert res.get('message') is None # Or check if message is not error

    def test_melee_at_distance_1_is_blocked(self, setup_characters):
        attacker, target = setup_characters
        attacker.zone = Zone.NEAR
        target.zone = Zone.MID
        res = RulesEngine.resolve_attack(attacker, target, attack_type='melee')
        assert res['is_hit'] is False
        assert 'out of melee range' in res['message']

    def test_ranged_at_distance_2_has_disadvantage(self, setup_characters):
        attacker, target = setup_characters
        attacker.zone = Zone.NEAR
        target.zone = Zone.FAR
        res = RulesEngine.resolve_attack(attacker, target, attack_type='ranged')
        assert res['disadvantage'] is True

    def test_cannot_attack_dead_target(self, setup_characters):
        attacker, target = setup_characters
        target.condition = Condition.DEAD
        res = RulesEngine.resolve_attack(attacker, target)
        assert res['is_hit'] is False
        assert 'dead' in res['message']

    def test_case_insensitive_role(self, setup_characters):
        _, target = setup_characters
        attacker = Character(
            id='f2',
            name='Fighter',
            role='fiGHTer',
            hp=20,
            max_hp=20,
            ac=10,
            stats={Stat.PHYS: 0},
            zone=Zone.NEAR
        )
        res = RulesEngine.resolve_attack(attacker, target)
        assert res['roll'] > 0
