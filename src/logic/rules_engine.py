import random
from src.models.character import Character, Stat, Zone, Condition

class RulesEngine:
    @staticmethod
    def resolve_attack(attacker: Character, target: Character, attack_type: str = 'melee') -> dict:
        # Step 1: Validate Target
        if target.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
            return {
                'is_hit': False,
                'message': 'Target is dead or unconscious!',
                'roll': 0,
                'total': 0,
                'damage': 0,
                'is_crit': False,
                'disadvantage': False,
            }

        # Step 2: Calculate Zone Distance
        zones = [Zone.NEAR, Zone.MID, Zone.FAR]
        attacker_idx = zones.index(attacker.zone)
        target_idx = zones.index(target.zone)
        distance = abs(attacker_idx - target_idx)

        if attack_type == 'melee' and distance > 0:
             return {
                'is_hit': False,
                'message': 'Target is out of melee range!',
                'roll': 0,
                'total': 0,
                'damage': 0,
                'is_crit': False,
                'disadvantage': False,
            }
        
        # Step 3: Determine Stat & Damage Dice
        attack_stat = Stat.PHYS
        damage_dice_sides = 6
        damage_dice_count = 1
        weapon_bonus = 0

        role = attacker.role.lower()
        if role == 'fighter':
             attack_stat = Stat.PHYS
             damage_dice_sides = 8
        elif role == 'paladin':
             attack_stat = Stat.PHYS
             damage_dice_sides = 6
             damage_dice_count = 2
        elif role == 'cleric':
             attack_stat = Stat.PHYS
             damage_dice_sides = 8
        elif role == 'mage':
             if attack_type == 'melee':
                 attack_stat = Stat.PHYS
                 damage_dice_sides = 6
             else:
                 attack_stat = Stat.MENT
                 damage_dice_sides = 10
        else:
             attack_stat = Stat.PHYS
             damage_dice_sides = 6
        
        stat_bonus = attacker.stats.get(attack_stat, 0)
        
        # Step 4: Disadvantage
        has_disadvantage = (attack_type != 'melee' and distance >= 2)

        # Step 5: Roll to Hit
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        d20_roll = min(roll1, roll2) if has_disadvantage else roll1

        attack_total = d20_roll + stat_bonus
        is_crit = (d20_roll == 20)
        is_hit = is_crit or (attack_total >= target.ac)

        # Step 6: Apply Damage
        damage = 0
        if is_hit:
            actual_dice_count = damage_dice_count * 2 if is_crit else damage_dice_count
            
            for _ in range(actual_dice_count):
                damage += random.randint(1, damage_dice_sides)
            
            damage += stat_bonus + weapon_bonus
            
            if damage < 0:
                damage = 0
            
            target.take_damage(damage)
        
        return {
            'is_hit': is_hit,
            'roll': d20_roll,
            'total': attack_total,
            'damage': damage,
            'is_crit': is_crit,
            'disadvantage': has_disadvantage,
            'message': None # Explicitly adding message key to avoid key errors if accessed
        }

    @staticmethod
    def resolve_check(actor: Character, stat: Stat, dc: int) -> bool:
        bonus = actor.stats.get(stat, 0)
        d20_roll = random.randint(1, 20)
        total = d20_roll + bonus
        return total >= dc
