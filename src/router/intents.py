import difflib
from typing import List, Optional
from src.models.character import Character, Condition, Zone, Stat
from src.logic.rules_engine import RulesEngine
from src.services.llm_service import LLMService

def _find_target(target_name_or_id: str, enemies: List[Character]) -> Optional[Character]:
    """Helper to resolve target ID using 3-tier matching."""
    if not target_name_or_id:
        return None
        
    target_name_or_id = target_name_or_id.lower().strip()
    active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
    
    # 1. Exact ID Match (Primary)
    for e in active_enemies:
        if getattr(e, 'id', '').lower() == target_name_or_id:
            return e
            
    # 2. Fuzzy String Match (Fallback for Typos)
    active_names = {e.name.lower(): e for e in active_enemies}
    matches = difflib.get_close_matches(target_name_or_id, list(active_names.keys()), n=1, cutoff=0.4)
    if matches:
        return active_names[matches[0]]
        
    # 3. Old Substring Match (Last Resort)
    for e in active_enemies:
        if target_name_or_id in e.name.lower():
            return e
            
    return None

def execute_fixed_action(action_type: str, decision: dict, player: Character, enemies: List[Character], debug_print) -> bool:
    """Executes a single FIXED action (Move or Attack)."""
    if action_type == 'MOVE':
        target_zone_str = decision.get('target', decision.get('move_target', '')).upper()
        
        if not target_zone_str or target_zone_str not in ["NEAR", "MID", "FAR"]:
            print(f"   ⚠️ Invalid move destination: '{target_zone_str}'. Please specify NEAR, MID, or FAR.")
            return False
            
        try:
            target_zone = Zone[target_zone_str]
            zones = [Zone.NEAR, Zone.MID, Zone.FAR]
            current_idx = zones.index(player.zone)
            target_idx = zones.index(target_zone)
            
            if abs(current_idx - target_idx) > 1:
                step = 1 if target_idx > current_idx else -1
                target_zone = zones[current_idx + step]
                print(f"   ⚠️ You can only move 1 zone per turn. Moving you to {target_zone.name} instead.")
            elif current_idx == target_idx:
                print(f"   🏃 You are already in the {target_zone.name} zone.")
                return True
                
            player.zone = target_zone
            print(f"   🏃 {player.name} moved to the {target_zone.name} zone.")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Failed to move: {e}")
            return False
            
    elif action_type == 'ATTACK':
        target_name = decision.get('target', decision.get('attack_target'))
        target = _find_target(target_name, enemies) if target_name else None
        
        if not target:
            active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
            if active_enemies:
                target = active_enemies[0]
            else:
                print("   ⚠️ No active enemies to attack!")
                return False

        debug_print(f"   ⚔️  Executing Attack Sequence against {target.name}...")
        attack_type = decision.get('attack_type', 'melee')
        result = RulesEngine.resolve_attack(player, target, attack_type=attack_type)
        
        raw_rolls = result.get('raw_rolls', [result.get('roll', 0)])
        roll_info = f"{raw_rolls} + {player.stats.get(Stat.PHYS, 0)} (Bonus)"
        
        if result.get('is_crit'):
             print(f"   🔥 CRITICAL HIT!")
             debug_print("      (Natural 20!)")
        
        if result.get('is_hit'):
            if not result.get('is_crit'):
                 print(f"   💥 HIT!")
                 debug_print(f"      (Rolled {roll_info} = {result.get('total', 0)} vs AC {target.ac})")
            print(f"   🩸 Damage Dealt: {result.get('damage', 0)}")
            print(f"   📉 {target.name} is now {target.get_health_status()} ({target.condition.name})")
        else:
            if result.get('message'):
                print(f"   ⚠️ {result['message']}")
            else:
                print(f"   🛡️ MISS!")
                debug_print(f"      (Rolled {roll_info} = {result.get('total', 0)} vs AC {target.ac})")
        return True
    
    else:
        print(f"   ⚙️ Processing {action_type}... (To be implemented)")
        return False

def handle_creative_intent(decision: dict, user_input: str, player: Character, party: List[Character], enemies: List[Character], llm_service: LLMService, debug_print) -> bool:
    """Handles Path B (Creative) logic and side effects."""
    description = decision.get('description', user_input)
    debug_print(f"   🤔 Arbiter Judging: '{description}'")
    
    judgment = llm_service.get_creative_judgment(party, enemies, player, description)
    
    if judgment.get('allowed'):
        debug_print(f"   ✅ Allowed! Reason: {judgment.get('reason')}")
        
        stat_str = judgment.get('check_stat', 'PHYS')
        dc = judgment.get('dc', 10)
        if dc is None: dc = 10 
        
        try:
            target_stat = Stat[stat_str]
        except KeyError:
            target_stat = Stat.PHYS 
            
        debug_print(f"   🎲 Rolling Check: {target_stat.value} (DC {dc})")
        
        check_result = RulesEngine.resolve_check(player, target_stat, dc)
        success = check_result['success']
        
        outcome_text = "PASSED" if success else "FAILED"
        bonus = player.stats.get(target_stat, 0)
        roll_str = f"{check_result.get('raw_rolls', [])} + {bonus}"
        
        debug_print(f"   {'🌟' if success else '💀'} Check {outcome_text}! (Rolled {roll_str} = {check_result.get('total', 0)} vs DC {dc})")
        
        if success:
            condition_str = judgment.get('on_success_condition')
            target_name = judgment.get('target_name_guess')
            
            if condition_str and target_name:
                found_target = None
                all_actors = party + enemies
                for char in all_actors:
                    if target_name.lower() in char.name.lower():
                        found_target = char
                        break
                
                if found_target:
                    try:
                        new_condition = Condition[condition_str]
                        found_target.condition = new_condition
                        print(f"   ⚠️ STATUS UPDATE: {found_target.name} is now {new_condition.name}!")
                    except KeyError:
                        debug_print(f"   ⚠️ Warning: Arbiter returned invalid condition '{condition_str}'")

        narration = llm_service.narrate_result(description, "Hidden", dc, success)
        print(f"   🗣️  DM: \"{narration}\"")
        return True
    else:
        print(f"   🚫 Denied! Reason: {judgment.get('reason')}")
        return False
