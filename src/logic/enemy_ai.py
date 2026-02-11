import random
from typing import List
from src.models.character import Character, Condition
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
        
        # 1. Filter Active Enemies
        active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
        
        if not active_enemies:
            return logs # No enemies left to act
            
        # 2. Filter Valid Targets (Living Players)
        valid_targets = [p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
        
        if not valid_targets:
            logs.append("The enemies look around, finding no standing threats.")
            return logs

        # 3. Execution Loop
        for enemy in active_enemies:
            # A. Target Selection (Simple Random for now)
            # In future, could target lowest HP or closest zone
            target = random.choice(valid_targets)
            
            # B. Perform Action (Standard Attack)
            # Reusing the RulesEngine from Path A
            result = RulesEngine.resolve_attack(enemy, target)
            
            # C. Format Log
            outcome = "MISS"
            damage_text = ""
            
            if result['is_hit']:
                outcome = "HIT"
                damage_text = f" for {result['damage']} damage"
                if result['is_crit']:
                    outcome = "CRITICAL HIT"
            
            log_entry = f"👹 {enemy.name} attacks {target.name}: {outcome}! (Rolled {result['total']}){damage_text}"
            logs.append(log_entry)
            
            # Check if target went down, so other enemies don't keep attacking a corpse
            if target.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
                 logs.append(f"   ⚠️ {target.name} has fallen!")
                 valid_targets.remove(target) # Remove from potential targets
                 if not valid_targets:
                     break # No more targets left

        return logs
