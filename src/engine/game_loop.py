import os
from src.models.character import Condition
from src.services.llm_service import LLMService
from src.services.data_manager import DataManager
from src.models.toon_converter import TOONConverter
from src.logic.combat_manager import InitiativeQueue
from src.logic.enemy_ai import EnemyAI
from src.ui.dashboard import render_dashboard
from src.router.intent_router import classify_intent
from src.router.intents import execute_fixed_action, handle_creative_intent
from src.logic.rules_engine import RulesEngine

DEBUG_MODE = False

def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

def start_combat_loop(data_path: str = "data/active/campaign_active.json") -> str:
    """
    Main Combat Loop.
    Returns: "RESTART", "VICTORY", "DEFEAT", or "EXIT".
    """
    global DEBUG_MODE
    print("\n" + "="*50)
    print("🎮 AI DM PROTOTYPE: TWO-PATH ARCHITECTURE (PHASE 3)")
    print("="*50)
    
    # --- 1. LOAD DATA FROM JSON ---
    data_manager = DataManager(data_path)
    settings = data_manager.load_settings()
    world_lore = data_manager.load_lore()
    party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)

    DEBUG_MODE = settings.get("engine", {}).get("debug_mode", False)

    # --- 0. INITIALIZE SERVICES ---
    try:
        llm_service = LLMService(settings=settings)
        print("✅ LLM Arbiter Online")
    except Exception as e:
        print(f"❌ Failed to load LLM Service: {e}")
        return "EXIT"

    if not party:
        print(f"❌ Error: No party data found in {data_path}")
        return "EXIT"

    # Set Active Characters for Testing
    # Intialize Turn Queue
    queue = InitiativeQueue(party, enemies)

    while True:
        try:
            current_actor = queue.get_current_actor()
            
            if not current_actor:
                print("   ⚠️ Error: No active actors in queue!")
                break
                
            # --- DASHBOARD (FIBO UI) ---
            render_dashboard(party, enemies)
            
            print(f"[{current_actor.name}'s Turn]")
            
            # --- TURN LOGIC ---
            if current_actor in party:
                print(f"Action > ", end="", flush=True)
                user_input = input()
            
                # RESTART LOGIC
                if user_input.lower() == 'debug':
                    DEBUG_MODE = not DEBUG_MODE
                    print(f"   🔧 Debug Mode is now {'ON' if DEBUG_MODE else 'OFF'}")
                    continue
                if user_input.lower() == 'restart': return "RESTART"
                if user_input.lower() in ['exit', 'quit', 'q']: return "EXIT"
                if not user_input.strip(): continue

                # NEW: Write raw player action to campaign log
                DataManager.append_to_log(f"[{current_actor.name}] {user_input}")

                print("   Thinking...", end="\r", flush=True) # Loading effect
                
                # 1. ROUTER: Decide Intent
                current_toon_state = TOONConverter.convert(party, enemies, global_state)
                decision = classify_intent(user_input, current_toon_state)
                
                # Clear loading line
                print(" " * 20, end="\r")
                
                debug_print(f"🤖 Intent: {decision.get('type', 'ERROR').ljust(10)} | Command: {decision.get('command', 'N/A')}")

                # 2. PATH A: FIXED RULES (Delegated to RulesEngine)
                escaped = False
                if decision.get('type') == 'FIXED':
                    if decision.get('command') == 'FLEE':
                        result = RulesEngine.resolve_escape(current_actor, enemies)
                        if result['success']:
                            msg = f"💨 [SYSTEM] You successfully outran the enemies!"
                            print(f"   {msg}")
                            combat_memory.append(f"{current_actor.name} successfully fled from combat.")
                            DataManager.append_to_log(f"   [SYSTEM] {current_actor.name} successfully fled from combat.")
                            debug_print(f"      [Math] Escaped: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                            escaped = True
                        else:
                            msg = f"🛑 [SYSTEM] The enemy cuts off your escape!"
                            print(f"   {msg}")
                            combat_memory.append(f"{current_actor.name} failed to flee from combat.")
                            DataManager.append_to_log(f"   [SYSTEM] {current_actor.name} failed to flee from combat.")
                            debug_print(f"      [Math] Failed Escape: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                    elif decision.get('command') == 'REST':
                        if global_state.get('is_in_combat', False):
                            msg = f"🛑 [SYSTEM] You cannot rest while in active combat!"
                            print(f"   {msg}")
                            combat_memory.append(msg)
                            DataManager.append_to_log(f"   [SYSTEM] {msg}")
                        else:
                            # Not in combat, shouldn't hit this inside the combat loop realistically but for safety
                            msg = f"💤 [SYSTEM] You rest."
                            print(f"   {msg}")
                    else:
                        success, log_msg = execute_fixed_action(decision.get('command'), decision, current_actor, enemies, debug_print, settings=settings)
                        if log_msg:
                            combat_memory.append(log_msg)
                            DataManager.append_to_log(f"   [SYSTEM] {log_msg}")

                elif decision.get('type') == 'FIXED_COMBO':
                    action_order = decision.get('action_order', ['MOVE', 'ATTACK'])
                    for action in action_order:
                        if action == 'FLEE':
                            result = RulesEngine.resolve_escape(current_actor, enemies)
                            if result['success']:
                                print("   💨 [SYSTEM] You successfully outran the enemies!")
                                combat_memory.append(f"{current_actor.name} successfully fled from combat.")
                                DataManager.append_to_log(f"   [SYSTEM] {current_actor.name} successfully fled from combat.")
                                debug_print(f"      [Math] Escaped: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                                escaped = True
                                break
                            else:
                                print("   🛑 [SYSTEM] The enemy cuts off your escape!")
                                combat_memory.append(f"{current_actor.name} failed to flee from combat.")
                                DataManager.append_to_log(f"   [SYSTEM] {current_actor.name} failed to flee from combat.")
                                debug_print(f"      [Math] Failed Escape: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                        else:
                            success, log_msg = execute_fixed_action(action, decision, current_actor, enemies, debug_print, settings=settings)
                            if log_msg:
                                combat_memory.append(log_msg)
                                DataManager.append_to_log(f"   [SYSTEM] {log_msg}")

                if escaped:
                    print(f"   🔄 Extricating from combat...")
                    if combat_memory:
                        print(f"   [System] Summarizing combat for Story Memory...")
                        summary = llm_service.summarize_combat(combat_memory)
                        print(f"   📖 [STORY MEMORY] {summary}")
                        DataManager.append_to_log(f"[STORY SUMMARY] {summary}\n")
                        story_memory.append(summary)
                        combat_memory.clear()
                        data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                    break

                # 3. PATH B: CREATIVE (The AI Arbiter)
                elif decision.get('type') == 'CREATIVE':
                    # --- CREATIVE ABILITY GUARD ---
                    consume_name = decision.get('consume_ability')
                    if consume_name:
                        ability_found = False
                        for ability in current_actor.abilities:
                            if ability.name.lower() == consume_name.lower():
                                ability_found = True
                                if ability.current_uses <= 0:
                                    msg = f"⚠️ You have no uses of {ability.name} left! You need a {ability.recharge_type.value.replace('_', ' ')}."
                                    print(f"   {msg}")
                                    continue # Skip enemy turn, restart prompt loop
                                # Decrement charge natively
                                ability.current_uses -= 1
                                debug_print(f"   🎟️ Consumed 1 charge of {ability.name}. ({ability.current_uses}/{ability.max_uses} left)")
                                break
                        
                        if not ability_found:
                             # The LLM hallucinated an ability they don't have, OR the user typed an invalid ability
                             msg = f"⚠️ {current_actor.name} does not have the ability: {consume_name}."
                             print(f"   {msg}")
                             continue # Skip enemy turn, restart prompt loop
                    # ------------------------------
                    success, log_msg = handle_creative_intent(decision, user_input, current_actor, party, enemies, llm_service, debug_print, combat_memory=combat_memory, story_memory=story_memory, settings=settings, global_state=global_state)
                    if not success:
                        continue # Skip enemy turn if action is denied
                    elif log_msg:
                        combat_memory.append(log_msg)
                        DataManager.append_to_log(f"   [SYSTEM] {log_msg}")

                # Error handling
                elif decision.get('type') == 'ERROR':
                    print(f"   ❌ Error: {decision.get('message')}")
                    continue # Skip to re-prompt
            
            else:
                # --- 4. ENEMY TURN ---
                print(f"   🔻 Enemy Turn:")
                enemy_logs = EnemyAI.take_single_turn(current_actor, party)
                
                if not enemy_logs:
                    debug_print("   (No active targets)")
                else:
                    # Collect event log for narration
                    full_event_log = ""
                    for log in enemy_logs:
                        debug_print(f"   [SYSTEM] {log}")
                        full_event_log += log + " "
                        DataManager.append_to_log(f"   [SYSTEM] {log}")
                    
                    # Generate Narration
                    print(f"   thinking...", end="\r")
                    
                    # Context for Narrator (Health Status and short-term memory)
                    toon_context = TOONConverter.convert(party, enemies, global_state)
                    # Build persistent player lore context so the Narrator remembers who the player IS
                    player_context = ""
                    if party:
                        p = party[0]
                        if p.title:
                            player_context += f"\nPLAYER TITLE: {p.title}"
                        if p.lore:
                            player_context += f"\nPLAYER BACKSTORY: {p.lore}"
                    combined_lore = (world_lore + player_context).strip()
                    narration = llm_service.narrate_combat_round(full_event_log, toon_context, combat_memory=combat_memory, story_memory=story_memory, world_lore=combined_lore)
                    
                    print(f"   🗣️  DM: \"{narration}\"")
                    
                    # NEW: Write the generated narrative to the campaign log
                    DataManager.append_to_log(f"[DM] ({current_actor.name}'s Turn) {narration}\n")
                    
                    combat_memory.append(f"Enemy phase: {full_event_log.strip()}")

            queue.advance_turn()
            from src.logic.time_manager import TimeManager
            TimeManager.advance_turn(global_state)

            # --- 4.5 AUTO-SAVE ---
            data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

            # --- 5. CHECK WIN/LOSS CONDITIONS ---
            active_players = [p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
            active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS, Condition.PACIFIED]]

            if not active_players:
                print("\n" + "💀"*20)
                print("DEFEAT - The Party has fallen!")
                print("💀"*20)
                return "DEFEAT"
            
            if not active_enemies:
                print("\n" + "🏆"*20)
                print("VICTORY - All enemies defeated!")
                print("🏆"*20)
                
                # --- AUTO-LOOT LOGIC ---
                looted_items = []
                for e in enemies:
                    if getattr(e, 'inventory', None):
                        looted_items.extend(e.inventory)
                        e.inventory = [] # Clear enemy pockets

                if looted_items and party:
                    main_player = party[0]
                    main_player.inventory.extend(looted_items)
                    print(f"\n💰 [SYSTEM] Auto-Looted: [{', '.join(looted_items)}] from the fallen enemies!")
                    
                    # Force a save to lock in the new fat inventory
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

                if combat_memory:
                    print(f"\n   [System] Summarizing combat for Story Memory...")
                    summary = llm_service.summarize_combat(combat_memory)
                    print(f"   📖 [STORY MEMORY] {summary}")
                    DataManager.append_to_log(f"\n[STORY SUMMARY] {summary}\n")
                    story_memory.append(summary)
                    combat_memory.clear()
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

                return "VICTORY"
        
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
            
    return "EXIT"

if __name__ == "__main__":
    start_combat_loop()
