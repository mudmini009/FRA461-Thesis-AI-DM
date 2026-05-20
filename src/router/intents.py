import difflib
from typing import List, Optional, Deque, Tuple, Dict, Any
from src.models.character import Character, Condition, Zone, Stat
from src.logic.rules_engine import RulesEngine
from src.services.llm_service import LLMService

def _find_target(target_name_or_id: str, enemies: List[Character], settings: Optional[Dict[str, Any]] = None) -> Optional[Character]:
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
    fuzzy_cutoff = 0.4
    if settings is not None:
        fuzzy_cutoff = settings.get("engine", {}).get("fuzzy_match_cutoff", 0.4)
    active_names = {e.name.lower(): e for e in active_enemies}
    matches = difflib.get_close_matches(target_name_or_id, list(active_names.keys()), n=1, cutoff=fuzzy_cutoff)
    if matches:
        return active_names[matches[0]]
        
    # 3. Old Substring Match (Last Resort)
    for e in active_enemies:
        if target_name_or_id in e.name.lower():
            return e
            
    return None

def execute_fixed_action(action_type: str, decision: dict, player: Character, enemies: List[Character], debug_print, settings: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """Executes a single FIXED action (Move, Attack, Cast, Ability)."""
    log_msg = None

    # --- ABILITY PRE-EXECUTION GUARD ---
    ability_name = decision.get('ability_name')
    is_applicable_ability = False
    if ability_name:
        is_applicable_ability = (action_type == 'ABILITY' or (action_type == 'ATTACK' and ability_name.lower() == 'smite'))

    if is_applicable_ability:
        ability_found = False
        for ability in player.abilities:
            if ability.name.lower() == ability_name.lower():
                ability_found = True
                if ability.current_uses <= 0:
                    msg = f"⚠️ You have no uses of {ability.name} left! You need a {ability.recharge_type.value.replace('_', ' ')}."
                    print(f"   {msg}")
                    return False, msg
                # Decrement charge natively
                ability.current_uses -= 1
                debug_print(f"   🎟️ Consumed 1 charge of {ability.name}. ({ability.current_uses}/{ability.max_uses} left)")
                break
        
        if not ability_found:
             # The LLM hallucinated an ability they don't have, OR the user typed an invalid ability
             msg = f"⚠️ {player.name} does not have the ability: {ability_name}."
             print(f"   {msg}")
             return False, msg
    # -----------------------------------
    if action_type == 'MOVE':
        if player.has_moved:
            print(f"   ⚠️ {player.name} has already moved this turn!")
            return False, f"{player.name} has already moved this turn."
            
        target_zone_str = decision.get('target', decision.get('move_target', '')).upper()
        
        if not target_zone_str or target_zone_str not in ["NEAR", "MID", "FAR"]:
            print(f"   ⚠️ Invalid move destination: '{target_zone_str}'. Please specify NEAR, MID, or FAR.")
            return False, None
            
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
                return True, f"{player.name} is in the {target_zone.name} zone."
                
            player.zone = target_zone
            player.has_moved = True
            log_msg = f"{player.name} moved to the {target_zone.name} zone."
            print(f"   🏃 {log_msg}")
            return True, log_msg
            
        except Exception as e:
            print(f"   ⚠️ Failed to move: {e}")
            return False, None
            
    elif action_type == 'ATTACK':
        if player.has_acted:
            print(f"   ⚠️ {player.name} has already taken an action this turn!")
            return False, f"{player.name} has already taken an action this turn."
            
        target_name = decision.get('target', decision.get('attack_target'))
        target = _find_target(target_name, enemies, settings=settings) if target_name else None
        
        if not target:
            active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
            if active_enemies:
                target = active_enemies[0]
            else:
                print("   ⚠️ No active enemies to attack!")
                return False, None

        debug_print(f"   ⚔️  Executing Attack Sequence against {target.name}...")
        attack_type = decision.get('attack_type', 'melee')
        result = RulesEngine.resolve_attack(player, target, attack_type=attack_type, ability_name=ability_name)
        
        raw_rolls = result.get('raw_rolls', [result.get('roll', 0)])
        roll_info = f"{raw_rolls} + {player.stats.get(Stat.PHYS, 0)} (Bonus)"
        
        if result.get('is_hit'):
            player.has_acted = True
            outcome = "CRITICAL HIT" if result.get('is_crit') else "HIT"
            if result.get('is_crit'):
                 print(f"   🔥 CRITICAL HIT!")
                 debug_print("      (Natural 20!)")
            else:
                 print(f"   💥 HIT!")
                 debug_print(f"      (Rolled {roll_info} = {result.get('total', 0)} vs AC {target.ac})")
            
            print(f"   🩸 Damage Dealt: {result.get('damage', 0)}")
            print(f"   📉 {target.name} is now {target.get_health_status()} ({target.condition.name})")
            log_msg = f"{player.name} attacked {target.name}: {outcome} for {result.get('damage', 0)} damage."
        else:
            if result.get('message'):
                print(f"   ⚠️ {result['message']}")
                log_msg = f"{player.name} attacked {target.name}: FAILED ({result['message']})"
            else:
                print(f"   🛡️ MISS!")
                debug_print(f"      (Rolled {roll_info} = {result.get('total', 0)} vs AC {target.ac})")
                log_msg = f"{player.name} attacked {target.name}: MISS"
        
        return True, log_msg
        
    elif action_type == 'ABILITY':
        if player.has_acted:
            print(f"   ⚠️ {player.name} has already taken an action this turn!")
            return False, f"{player.name} has already taken an action this turn."
            
        target_name = decision.get('target', player.name) # Self by default
        # The ability_name was previously verified in the pre-guard above
        
        target = _find_target(target_name, enemies, settings=settings) if target_name else player
        if not target and target_name:
            self_aliases = {"self", "me", "myself", "player1", "player", player.name.lower(), player.id.lower()}
            if target_name.lower().strip() in self_aliases or target_name.lower() in player.name.lower():
                target = player
            
        debug_print(f"   ✨ Using {ability_name} on {target.name if target else 'No target'}...")
        result = RulesEngine.resolve_ability(player, target, ability_name=ability_name)
        
        if result.get('is_hit'):
            player.has_acted = True
            print(f"   ✨ {result.get('message', 'Ability used!')}")
            log_msg = f"{player.name} used {ability_name}: {result.get('message')}"
        else:
            print(f"   ⚠️ {result.get('message', 'Ability failed.')}")
            log_msg = f"{player.name} failed to use {ability_name}: {result.get('message')}"
            
        return True, log_msg
        
    elif action_type == 'CAST':
        if player.has_acted:
            print(f"   ⚠️ {player.name} has already taken an action this turn!")
            return False, f"{player.name} has already taken an action this turn."
            
        target_name = decision.get('target')
        spell_name = decision.get('spell_name', 'Magic Missile')
        target = _find_target(target_name, enemies, settings=settings) if target_name else None
        
        if not target:
            active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
            if active_enemies:
                target = active_enemies[0]
            else:
                print("   ⚠️ No active enemies to cast on!")
                return False, None
                
        debug_print(f"   ✨ Casting {spell_name} on {target.name}...")
        result = RulesEngine.resolve_spell(player, target, spell_name=spell_name)
        
        raw_rolls = result.get('raw_rolls', [result.get('roll', 0)])
        roll_info = f"{raw_rolls} + {player.stats.get(Stat.MENT, 0)} (Bonus)"
        
        if result.get('is_hit'):
            player.has_acted = True
            outcome = "CRITICAL HIT" if result.get('is_crit') else "HIT"
            if result.get('is_crit'):
                 print(f"   🔥 CRITICAL HIT!")
            else:
                 print(f"   💥 HIT!")
            
            print(f"   🩸 Damage Dealt: {result.get('damage', 0)}")
            print(f"   📉 {target.name} is now {target.get_health_status()} ({target.condition.name})")
            log_msg = f"{player.name} cast {spell_name} on {target.name}: {outcome} for {result.get('damage', 0)} damage."
        else:
            if result.get('message'):
                print(f"   ⚠️ {result['message']}")
                log_msg = f"{player.name} cast {spell_name} on {target.name}: FAILED ({result['message']})"
            else:
                print(f"   🛡️ MISS!")
                log_msg = f"{player.name} cast {spell_name} on {target.name}: MISS"
                
        return True, log_msg
    
    elif action_type == 'USE':
        if player.has_acted:
            print(f"   ⚠️ {player.name} has already taken an action this turn!")
            return False, f"{player.name} has already taken an action this turn."
            
        target_item = decision.get('target')
        if not target_item:
            print(f"   ⚠️ Use what?")
            return False, None
            
        if not player.inventory:
            print(f"   ⚠️ Your inventory is empty!")
            return False, None

        # ── Self-Target Guard ──────────────────────────────────────
        # The LLM sometimes returns target:player1 / target:self / target:<player_name>
        # when the player means "use potion on myself." In that case, we need to
        # figure out what ITEM they want to use from context or default to a potion.
        self_aliases = {"self", "me", "myself", "player1", "player", player.name.lower(), player.id.lower()}
        if target_item.lower().strip() in self_aliases:
            # Player targeted themselves — pick the most likely consumable from inventory
            potion_match = [item for item in player.inventory if "potion" in item.lower() or "heal" in item.lower()]
            if potion_match:
                target_item = potion_match[0]
            else:
                # Fallback: use the first inventory item
                target_item = player.inventory[0] if player.inventory else None
                if not target_item:
                    print(f"   ⚠️ Your inventory is empty!")
                    return False, None
            print(f"   🔍 Using '{target_item}' on yourself...")
        # ──────────────────────────────────────────────────────────
            
        # Try to find the item in inventory
        fuzzy_cutoff = 0.4
        if settings is not None:
            fuzzy_cutoff = settings.get("engine", {}).get("fuzzy_match_cutoff", 0.4)
        matches = difflib.get_close_matches(target_item, player.inventory, n=1, cutoff=fuzzy_cutoff)
        if not matches:
            print(f"   ⚠️ You don't seem to have a '{target_item}' in your inventory.")
            return False, None
            
        found_item = matches[0]
        
        print(f"   🔍 Analyzing '{found_item}'...")
        
        # We need an LLMService instance to use the Arbiter. 
        # Since execute_fixed_action doesn't have it in signature, we'll instantiate a fresh one temporarily for this isolated lookup.
        # Alternatively, we could refactor the signature, but this is cleaner for now.
        temp_llm = LLMService(settings=settings)
        arbiter_result = temp_llm.categorize_item(found_item)
        
        is_consumable = arbiter_result.get('is_consumable', False)
        effect_type = arbiter_result.get('effect_type', 'NONE')
        
        player.has_acted = True
        
        if is_consumable:
            if found_item in player.inventory:
                player.inventory.remove(found_item)
            msg = f"{player.name} used '{found_item}' (Consumed)."
            print(f"   🧪 [SYSTEM] {msg}")
            
            # Apply mechanical effect via RulesEngine using the AI's category
            effect_result = RulesEngine.resolve_item(player, found_item, effect_type)
            print(f"   ✨ {effect_result['message']}")
            log_msg = f"{msg} Result: {effect_result['message']}"
            
        else:
            if effect_type != "NONE":
                 effect_result = RulesEngine.resolve_item(player, found_item, effect_type)
                 print(f"   ✨ {effect_result['message']}")
                 log_msg = f"{player.name} used '{found_item}'. Result: {effect_result['message']}"
            else:
                 print(f"   ⚙️ [SYSTEM] Equipped/Interacted with '{found_item}'.")
                 log_msg = f"{player.name} interacted with '{found_item}'."
            
        return True, log_msg

    else:
        print(f"   ⚙️ Processing {action_type}... (To be implemented)")
        return False, None

def handle_creative_intent(decision: dict, user_input: str, player: Character, party: List[Character], enemies: List[Character], llm_service: LLMService, debug_print, combat_memory: Optional[Deque[str]] = None, story_memory: Optional[Deque[str]] = None, settings: Optional[Dict[str, Any]] = None, global_state: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """Handles Path B (Creative) logic and side effects."""
    description = decision.get('description', user_input)
    debug_print(f"   🤔 Arbiter Judging: '{description}'")
    
    judgment = llm_service.get_creative_judgment(party, enemies, player, description, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
    
    if judgment.get('allowed'):
        debug_print(f"   ✅ Allowed! Reason: {judgment.get('reason')}")
        
        default_dc = 10
        if settings is not None:
            default_dc = settings.get("engine", {}).get("default_dc", 10)
        stat_str = judgment.get('check_stat', 'PHYS')
        dc = judgment.get('dc', default_dc)
        if dc is None: dc = default_dc 
        
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
        
        log_msg = f"{player.name} attempted: {description}. Result: {outcome_text} (DC {dc})"
        
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
                        status_msg = f"{found_target.name} is now {new_condition.name}!"
                        print(f"   ⚠️ STATUS UPDATE: {status_msg}")
                        log_msg += f" | {status_msg}"
                    except KeyError:
                        debug_print(f"   ⚠️ Warning: Arbiter returned invalid condition '{condition_str}'")

        # Handle Item Consumption (Path B)
        consumed_item = judgment.get('consumed_item')
        if consumed_item and player.inventory:
            # Fuzzy match to ensure we remove the correct item string from the list
            fuzzy_cutoff = 0.4
            if settings is not None:
                fuzzy_cutoff = settings.get("engine", {}).get("fuzzy_match_cutoff", 0.4)
            matches = difflib.get_close_matches(consumed_item, player.inventory, n=1, cutoff=fuzzy_cutoff)
            if matches:
                item_to_remove = matches[0]
                player.inventory.remove(item_to_remove)
                consume_msg = f"'{item_to_remove}' was consumed/lost."
                print(f"   🔥 [SYSTEM] {consume_msg}")
                log_msg += f" | {consume_msg}"

        narration = llm_service.narrate_result(description, "Hidden", dc, success)
        print(f"   🗣️  DM: \"{narration}\"")
        return True, log_msg
    else:
        reason = judgment.get('reason', 'Action denied by Arbiter.')
        print(f"   🚫 Denied! Reason: {reason}")
        return False, f"{player.name} attempted: {description}. Result: DENIED ({reason})"
