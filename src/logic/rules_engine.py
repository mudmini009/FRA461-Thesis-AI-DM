from src.models.character import Character, Stat, Zone, Condition
from src.logic.dice_roller import roll

class RulesEngine:
    pass # Base class mechanics happen here

    @staticmethod
    def use_item(user: Character, item_name: str, effect_type: str) -> dict:
        """
        Applies mathematical effects of an item to a character based on the LLM Arbiter's strict categorization.
        Returns a dict with 'success' and 'message'.
        """
        # effect_type should be one of: SMALL_HEAL, BIG_HEAL, CURE, DAMAGE, NONE
        
        if effect_type == "SMALL_HEAL" or effect_type == "HEAL":
            value = 10
            old_hp = user.hp
            user.hp = min(user.hp + value, user.max_hp)
            healed_amount = user.hp - old_hp
            
            if healed_amount > 0 and user.condition == Condition.UNCONSCIOUS:
                user.condition = Condition.NORMAL
            return {"success": True, "message": f"Restored {healed_amount} HP! (Now {user.hp}/{user.max_hp})"}
            
        elif effect_type == "BIG_HEAL":
            value = 25
            old_hp = user.hp
            user.hp = min(user.hp + value, user.max_hp)
            healed_amount = user.hp - old_hp
            
            if healed_amount > 0 and user.condition == Condition.UNCONSCIOUS:
                user.condition = Condition.NORMAL
            return {"success": True, "message": f"Restored {healed_amount} HP! (Now {user.hp}/{user.max_hp})"}
            
        elif effect_type == "CURE":
            if user.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]:
                old_cond = user.condition
                user.condition = Condition.NORMAL
                return {"success": True, "message": f"Cured condition: {old_cond.name} -> NORMAL."}
            else:
                 return {"success": False, "message": f"Cannot cure {user.condition.name} with this item."}
                 
        elif effect_type == "DAMAGE":
            value = 15
            user.take_damage(value)
            return {"success": True, "message": f"The item backfired/exploded! Took {value} damage."}
            
        elif effect_type == "NARRATIVE":
             return {"success": True, "message": f"You examine the '{item_name}'. (Narrative Effect)"}

        return {"success": True, "message": f"Used '{item_name}'."}

    @staticmethod
    def resolve_item(user: Character, item_name: str, effect_type: str) -> dict:
        """
        Wraps use_item to return a standard dictionary format compatible with the evaluation tracer.
        """
        if user.condition in [Condition.STUNNED, Condition.UNCONSCIOUS, Condition.DEAD]:
            return {
                'is_hit': False,
                'message': f"{user.name} is {user.condition.name} and cannot use items!",
                'roll': 0, 'total': 0, 'damage': 0, 'is_crit': False, 'disadvantage': False,
                'state_mutated': None
            }
            
        result = RulesEngine.use_item(user, item_name, effect_type)
        return {
            'is_hit': result['success'],
            'roll': 0,
            'total': 0,
            'damage': 0,
            'is_crit': False,
            'disadvantage': False,
            'message': result['message'],
            'attacker_name': user.name,
            'target_name': user.name,
            'state_mutated': result['message']
        }

    @staticmethod
    def resolve_escape(player: Character, enemies: list) -> dict:
        """
        Resolves a FLEE action using contested 1d20 + PHYS rolls.
        Proximity penalty is applied to the enemy's roll based on Zone distance.
        """
        active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS, Condition.PACIFIED]]
        if not active_enemies:
            return {
                'success': True,
                'message': "No active enemies to flee from!",
                'player_total': 0, 'enemy_total': 0, 'distance': 0
            }

        zones = [Zone.NEAR, Zone.MID, Zone.FAR]
        player_idx = zones.index(player.zone)
        
        # Find closest enemy distance
        closest_distance = 999
        closest_enemy = active_enemies[0]
        for e in active_enemies:
            dist = abs(player_idx - zones.index(e.zone))
            if dist < closest_distance:
                closest_distance = dist
                closest_enemy = e

        # Proximity Penalty applies to the ENEMY'S roll
        enemy_bonus = closest_enemy.stats.get(Stat.PHYS, 0)
        proximity_modifier = 0
        if closest_distance == 0:
            proximity_modifier = 5
        elif closest_distance == 1:
            proximity_modifier = 2

        # Roll for Player
        player_bonus = player.stats.get(Stat.PHYS, 0)
        player_result = roll(f"1d20+{player_bonus}")
        player_total = player_result['total']

        # Roll for Enemy
        enemy_hit_bonus = enemy_bonus + proximity_modifier
        enemy_result = roll(f"1d20+{enemy_hit_bonus}")
        enemy_total = enemy_result['total']

        success = player_total > enemy_total

        return {
            'success': success,
            'player_total': player_total,
            'player_roll': player_result['rolls'][0],
            'player_bonus': player_bonus,
            'enemy_total': enemy_total,
            'enemy_roll': enemy_result['rolls'][0],
            'enemy_bonus': enemy_bonus,
            'proximity_modifier': proximity_modifier,
            'distance': closest_distance,
            'closest_enemy_name': closest_enemy.name
        }

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
    def resolve_spell(caster: Character, target: Character, spell_name: str) -> dict:
        """
        Resolves a basic spell attack, always using MENT stat, with no disadvantage for distance.
        """
        if caster.condition in [Condition.STUNNED, Condition.UNCONSCIOUS, Condition.DEAD]:
            return {
                'is_hit': False,
                'message': f'{caster.name} is {caster.condition.name} and cannot cast spells!',
                'roll': 0, 'total': 0, 'damage': 0, 'is_crit': False, 'disadvantage': False
            }

        if target.condition in [Condition.DEAD]:
            return {
                'is_hit': False,
                'message': 'Target is already dead!',
                'roll': 0, 'total': 0, 'damage': 0, 'is_crit': False, 'disadvantage': False
            }

        tactical_bonus = 0
        if target.condition in [Condition.STUNNED, Condition.RESTRAINED, Condition.UNCONSCIOUS, Condition.BLINDED, Condition.PRONE]:
            tactical_bonus += 5
        
        if caster.condition in [Condition.BLINDED, Condition.RESTRAINED]:
            tactical_bonus -= 5

        # Spells always use MENT and 1d10
        stat_bonus = caster.stats.get(Stat.MENT, 0)
        
        hit_expression = f"1d20{stat_bonus + tactical_bonus:+}"
        final_roll = roll(hit_expression)
        
        d20_roll = final_roll['rolls'][0]
        attack_total = final_roll['total']
        is_crit = final_roll['is_critical']
        
        is_hit = is_crit or (attack_total >= target.ac)

        damage = 0
        
        if is_hit:
            dice_count = 2 if is_crit else 1
            dmg_expression = f"{dice_count}d10+{stat_bonus}"
            damage_result = roll(dmg_expression)
            
            damage = damage_result['total']
            if damage < 0: damage = 0
            
            target.take_damage(damage)
        
        return {
            'is_hit': is_hit,
            'roll': d20_roll,
            'raw_rolls': final_roll['rolls'],
            'total': attack_total,
            'damage': damage,
            'is_crit': is_crit,
            'disadvantage': False,
            'message': None,
            'attacker_name': caster.name,
            'target_name': target.name,
            'spell_name': spell_name
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
