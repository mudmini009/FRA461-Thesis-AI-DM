from typing import List
import random
from src.models.character import Character, Condition, Stat
from src.logic.rules_engine import RulesEngine


class EnemyAI:
    """
    Stateless Enemy AI for Side Initiative.
    Executes the enemy team's turn by iterating through active enemies
    and performing attacks against the player party.
    """

    @staticmethod
    def execute_turn(enemies: List[Character], party: List[Character]) -> List[str]:
        logs = []
        
        # 1. Active Enemy Check
        active_enemies = [
            e for e in enemies 
            if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]
        ]

        if not active_enemies:
            return logs # No enemies to act

        # 2. Iterate each enemy
        for enemy in active_enemies:
            # A. Target Selection (Simple: Random living player)
            valid_targets = [
                p for p in party 
                if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]
            ]

            if not valid_targets:
                logs.append(f"{enemy.name} looks around, finding no targets remaining.")
                continue
            
            # Simple Logic: Random Target
            target = random.choice(valid_targets)
            
            # B. Execute Attack via RulesEngine
            # Assuming basic melee attack for now
            logs.append(f"👹 {enemy.name} attacks {target.name}!")
            
            result = RulesEngine.resolve_attack(enemy, target)
            
            # C. Format Logs
            if result['is_crit']:
                logs.append(f"   🔥 CRITICAL HIT! (Nat 20!)")
            
            if result['is_hit']:
                logs.append(f"   💥 HIT! ({result['total']} vs AC {target.ac}) -> {result['damage']} DMG")
                
                # Check for condition changes in target
                if target.hp <= 0:
                    logs.append(f"   💀 {target.name} falls {target.condition.name}!")
                else:
                    logs.append(f"   📉 {target.name} HP: {target.hp}/{target.max_hp}")
            else:
                logs.append(f"   🛡️ MISS! ({result['total']} vs AC {target.ac})")
                
        return logs
