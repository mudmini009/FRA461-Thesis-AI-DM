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

DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

def start_combat_loop(data_path: str = "data/campaign.json") -> str:
    """
    Main Combat Loop.
    Returns: "RESTART", "VICTORY", "DEFEAT", or "EXIT".
    """
    print("\n" + "="*50)
    print("🎮 AI DM PROTOTYPE: TWO-PATH ARCHITECTURE (PHASE 3)")
    print("="*50)
    
    # --- 0. INITIALIZE SERVICES ---
    try:
        llm_service = LLMService()
        print("✅ LLM Arbiter Online")
    except Exception as e:
        print(f"❌ Failed to load LLM Service: {e}")
        return "EXIT"

    # --- 1. LOAD DATA FROM JSON ---
    data_manager = DataManager(data_path)
    party, enemies = data_manager.load_game()

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
                    global DEBUG_MODE
                    DEBUG_MODE = not DEBUG_MODE
                    print(f"   🔧 Debug Mode is now {'ON' if DEBUG_MODE else 'OFF'}")
                    continue
                if user_input.lower() == 'restart': return "RESTART"
                if user_input.lower() in ['exit', 'quit', 'q']: return "EXIT"
                if not user_input.strip(): continue

                print("   Thinking...", end="\r", flush=True) # Loading effect
                
                # 1. ROUTER: Decide Intent
                current_toon_state = TOONConverter.convert(party, enemies)
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
                            print("   💨 [SYSTEM] You successfully outran the enemies!")
                            debug_print(f"      [Math] Escaped: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                            escaped = True
                        else:
                            print("   🛑 [SYSTEM] The enemy cuts off your escape!")
                            debug_print(f"      [Math] Failed Escape: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                    else:
                        execute_fixed_action(decision.get('command'), decision, current_actor, enemies, debug_print)

                elif decision.get('type') == 'FIXED_COMBO':
                    action_order = decision.get('action_order', ['MOVE', 'ATTACK'])
                    for action in action_order:
                        if action == 'FLEE':
                            result = RulesEngine.resolve_escape(current_actor, enemies)
                            if result['success']:
                                print("   💨 [SYSTEM] You successfully outran the enemies!")
                                debug_print(f"      [Math] Escaped: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                                escaped = True
                                break
                            else:
                                print("   🛑 [SYSTEM] The enemy cuts off your escape!")
                                debug_print(f"      [Math] Failed Escape: Player ({result['player_roll']} + {result['player_bonus']} = {result['player_total']}) vs {result.get('closest_enemy_name', 'None')} ({result['enemy_roll']} + {result['enemy_bonus']} + {result['proximity_modifier']}(Dist) = {result['enemy_total']})")
                        else:
                            execute_fixed_action(action, decision, current_actor, enemies, debug_print)

                if escaped:
                    break

                # 3. PATH B: CREATIVE (The AI Arbiter)
                elif decision.get('type') == 'CREATIVE':
                    success = handle_creative_intent(decision, user_input, current_actor, party, enemies, llm_service, debug_print)
                    if not success:
                        continue # Skip enemy turn if action is denied

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
                    
                    # Generate Narration
                    print(f"   thinking...", end="\r")
                    
                    # Context for Narrator (Health Status)
                    toon_context = TOONConverter.convert(party, enemies)
                    narration = llm_service.narrate_combat_round(full_event_log, toon_context)
                    
                    print(f"   🗣️  DM: \"{narration}\"")

            queue.advance_turn()

            # --- 4.5 AUTO-SAVE ---
            data_manager.save_game(party, enemies)

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
                    data_manager.save_game(party, enemies)

                return "VICTORY"
        
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
            
    return "EXIT"

if __name__ == "__main__":
    start_combat_loop()
