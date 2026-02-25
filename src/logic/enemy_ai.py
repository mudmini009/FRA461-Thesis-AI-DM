import random
from typing import List
from src.models.character import Character, Condition, Stat
from src.logic.rules_engine import RulesEngine

class EnemyAI:
    """
    Stateless AI Logic for controlling Enemy Actions.
    Adopts a 'Side Initiative' approach where all enemies act after the player team.
    """
    
    @staticmethod
    def take_single_turn(enemy: Character, party: List[Character]) -> List[str]:
        """
        Executes the turn for a single enemy.
        Returns a list of log strings describing what happened.
        """
        logs = []
        
        if enemy.condition in [Condition.DEAD, Condition.UNCONSCIOUS, Condition.STUNNED]:
             logs.append(f"⚠️ {enemy.name} is {enemy.condition.name} and cannot act!")
             return logs
            
        # 2. Filter Valid Targets (Living Players)
        valid_targets = [p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
        
        if not valid_targets:
            logs.append("The enemies look around, finding no standing threats.")
            return logs

        # 3. Execution (Smart AI)
        # Priority 1: Proximity (Same Zone)
        # Priority 2: Weakness (Lowest HP)
        
        # 1. Filter by Zone
        proximity_targets = [p for p in valid_targets if p.zone == enemy.zone]
        candidates = proximity_targets if proximity_targets else valid_targets
        
        # 2. Filter by Weakness (Lowest HP)
        # Find the minimum HP among candidates
        min_hp = min(c.hp for c in candidates)
        weakest_targets = [c for c in candidates if c.hp == min_hp]
        
        # 3. Final Selection (Random among the "best" targets)
        target = random.choice(weakest_targets)
        
        # B. Perform Action (Move then Attack)
        from src.models.character import Zone
        all_zones = [Zone.NEAR, Zone.MID, Zone.FAR]
        
        enemy_idx = all_zones.index(enemy.zone)
        target_idx = all_zones.index(target.zone)
        distance = abs(enemy_idx - target_idx)
        
        # Move closer if out of range For 5e Lite, let's assume all basic enemies want to be in MELEE right now. 
        # In the future we can add 'role_preferred_range'.
        if distance > 0:
            step = 1 if target_idx > enemy_idx else -1
            new_zone = all_zones[enemy_idx + step]
            enemy.zone = new_zone
            logs.append(f"🏃 👹 {enemy.name} moves to the {new_zone.name} zone toward {target.name}.")
                
        # (Re-evaluate distance after moving)
        enemy_idx = all_zones.index(enemy.zone)
        distance = abs(enemy_idx - target_idx)
            
        # Target Selection (Assuming melee only for base enemies right now)
        if distance == 0:
            # Now, attempt attack
            # Reusing the RulesEngine from Path A
            result = RulesEngine.resolve_attack(enemy, target)
            
            if not result['is_hit'] and result.get('message') == 'Target is out of melee range!':
                # They moved but couldn't reach
                pass
            else:
                # C. Format Log
                outcome = "MISS"
                damage_text = ""
                
                raw_rolls = result.get('raw_rolls', [result['roll']])
                
                if result['is_hit']:
                    outcome = "HIT"
                    damage_text = f" for {result['damage']} damage"
                    if result['is_crit']:
                        outcome = "CRITICAL HIT"
                
                log_entry = f"👹 {enemy.name} attacks {target.name}: {outcome}! (Rolled {raw_rolls} = {result['total']}){damage_text}"
                logs.append(log_entry)
            
        # Check if target went down
        if target and target.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
             logs.append(f"   ⚠️ {target.name} has fallen!")
             
        return logs
