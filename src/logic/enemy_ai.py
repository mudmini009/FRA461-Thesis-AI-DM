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
    def execute_turn(enemies: List[Character], party: List[Character]) -> List[str]:
        """
        Executes the turn for all active enemies.
        Returns a list of log strings describing what happened.
        """
        logs = []
        
        # 1. Filter Active Enemies (Check Incapacitated States)
        active_enemies = []
        for e in enemies:
             # Skip if Dead, Unconscious, or Stunned
             if e.condition in [Condition.DEAD, Condition.UNCONSCIOUS, Condition.STUNNED]:
                 if e.condition != Condition.DEAD:
                     logs.append(f"⚠️ {e.name} is {e.condition.name} and cannot act!")
                 continue
             active_enemies.append(e)
        
        if not active_enemies:
            if not logs: logs.append("No active enemies to act.")
            return logs # No enemies left to act
            
        # 2. Filter Valid Targets (Living Players)
        valid_targets = [p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
        
        if not valid_targets:
            logs.append("The enemies look around, finding no standing threats.")
            return logs

        # 3. Execution Loop
        for enemy in active_enemies:
            # A. Target Selection (Smart AI)
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
            
            # B. Perform Action (Standard Attack)
            # Reusing the RulesEngine from Path A
            result = RulesEngine.resolve_attack(enemy, target)
            
            # C. Format Log
            outcome = "MISS"
            damage_text = ""
            
            raw_rolls = result.get('raw_rolls', [result['roll']])
            bonus = enemy.stats.get(Stat.PHYS, 0) # Assuming PHYS for simple enemy AI
            # Or retrieve from result if we stored bonus there, but we didn't. 
            # Recalculating bonus for display is fine, or just showing [Roll] is enough.
            # Let's just show "Rolled [14]"
            
            if result['is_hit']:
                outcome = "HIT"
                damage_text = f" for {result['damage']} damage"
                if result['is_crit']:
                    outcome = "CRITICAL HIT"
            
            log_entry = f"👹 {enemy.name} attacks {target.name}: {outcome}! (Rolled {raw_rolls} = {result['total']}){damage_text}"
            logs.append(log_entry)
            
            # Check if target went down, so other enemies don't keep attacking a corpse
            if target.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
                 logs.append(f"   ⚠️ {target.name} has fallen!")
                 valid_targets.remove(target) # Remove from potential targets
                 if not valid_targets:
                     break # No more targets left

        return logs
