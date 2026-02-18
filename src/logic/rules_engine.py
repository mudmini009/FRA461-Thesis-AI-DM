from src.models.character import Character, Stat, Zone, Condition
from src.logic.dice_roller import roll

class RulesEngine:
    @staticmethod
    def resolve_attack(attacker: Character, target: Character, attack_type: str = 'melee') -> dict:
        # Step 1: Validate Attacker & Target
        if attacker.condition in [Condition.STUNNED, Condition.UNCONSCIOUS, Condition.DEAD]:
            return {
                'is_hit': False,
                'message': f'{attacker.name} is {attacker.condition.name} and cannot attack!',
                'roll': 0, 'total': 0, 'damage': 0, 'is_crit': False, 'disadvantage': False
            }

        if target.condition in [Condition.DEAD]:
            return {
                'is_hit': False,
                'message': 'Target is already dead!',
                'roll': 0, 'total': 0, 'damage': 0, 'is_crit': False, 'disadvantage': False
            }

        # Step 1.5: Tactical Modifiers (Advantage/Disadvantage)
        # If Target is STUNNED/RESTRAINED/UNCONSCIOUS -> Auto-Crit or massive advantage? 
        # For 5e Lite: Advantage (+5 to roll)
        tactical_bonus = 0
        tactical_message = ""
        
        if target.condition in [Condition.STUNNED, Condition.RESTRAINED, Condition.UNCONSCIOUS, Condition.BLINDED, Condition.PRONE]:
            tactical_bonus += 5
            tactical_message = f"(+5 Advantage vs {target.condition.name})"
        
        if attacker.condition in [Condition.BLINDED, Condition.RESTRAINED]:
            tactical_bonus -= 5
            tactical_message += f"(-5 Disadvantage: {attacker.condition.name})"

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

        # Step 5: Roll to Hit (Using Dice Engine)
        # We roll "1d20 + total_bonus"
        total_hit_bonus = stat_bonus + tactical_bonus
        hit_expression = f"1d20{total_hit_bonus:+}"
        
        roll1 = roll(hit_expression)
        final_roll = roll1

        if has_disadvantage:
            roll2 = roll(hit_expression)
            # Take the lower total
            if roll2['total'] < roll1['total']:
                final_roll = roll2
        
        d20_roll = final_roll['rolls'][0] # The raw die result
        attack_total = final_roll['total']
        is_crit = final_roll['is_critical']
        
        # Determine Hit
        is_hit = is_crit or (attack_total >= target.ac)

        # Step 6: Apply Damage
        damage = 0
        damage_details = None
        
        if is_hit:
            # Critical Hit: Double dice count
            final_dice_count = damage_dice_count * 2 if is_crit else damage_dice_count
            total_bonus = stat_bonus + weapon_bonus
            
            # Construct damage string: e.g. "1d8+5"
            dmg_expression = f"{final_dice_count}d{damage_dice_sides}+{total_bonus}"
            damage_result = roll(dmg_expression)
            
            damage = damage_result['total']
            damage_details = damage_result
            
            if damage < 0:
                damage = 0
            
            target.take_damage(damage)
        
        return {
            'is_hit': is_hit,
            'roll': d20_roll,
            'raw_rolls': final_roll['rolls'], # Added raw rolls for transparency
            'total': attack_total,
            'damage': damage,
            'is_crit': is_crit,
            'disadvantage': has_disadvantage,
            'message': None,
            'attacker_name': attacker.name,
            'target_name': target.name
        }

    @staticmethod
    def resolve_check(actor: Character, stat: Stat, dc: int) -> dict:
        bonus = actor.stats.get(stat, 0)
        # Roll 1d20 + bonus
        result = roll(f"1d20+{bonus}")
        return {
            'success': result['total'] >= dc,
            'total': result['total'],
            'raw_rolls': result['rolls']
        }
