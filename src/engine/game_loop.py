import os
import json
import random
from src.models.character import Condition, Character, Stat, Zone
from src.services.llm_service import LLMService
from src.services.data_manager import DataManager
from src.models.toon_converter import TOONConverter
from src.logic.combat_manager import InitiativeQueue
from src.logic.enemy_ai import EnemyAI
from src.logic.enemy_factory import EnemyFactory
from src.ui.dashboard import render_dashboard
from src.router.intent_router import classify_intent
from src.router.intents import execute_fixed_action, handle_creative_intent
from src.logic.rules_engine import RulesEngine
from src.logic.time_manager import TimeManager
from src.services.quest_loader import QuestLoader
from src.router.exploration_router import (
    classify_exploration_intent,
    classify_exploration_intent_in_context,
    classify_exploration_intent_smart,
    get_rest_rejection_message,
    get_move_rejection_message,
)
from src.ui.exploration_ui import render_exploration_dashboard, render_hub_dashboard

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
                            if not success:
                                break

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


# =============================================================================
#  EXPLORATION LOOP  (Point-Crawl Engine)
#  Wraps start_combat_loop() — does NOT modify it.
# =============================================================================

def _inject_enemy_from_bestiary(
    enemy_tag: str,
    enemy_index: int = 1,
    bestiary_path: str = "data/config/bestiary.json",
) -> "Character | None":
    """
    Loads enemy stats from bestiary.json and returns a fresh Character object.
    Pure Python — no LLM.
    """
    try:
        with open(bestiary_path, "r", encoding="utf-8") as f:
            bestiary = json.load(f)
    except Exception as e:
        print(f"   ❌ Could not load bestiary: {e}")
        return None

    tag = enemy_tag.lower().strip()
    if tag not in bestiary:
        tag = list(bestiary.keys())[0]  # fallback to first entry
        print(f"   ⚠️  Enemy tag '{enemy_tag}' not found. Falling back to '{tag}'.")

    raw = bestiary[tag]
    converted_stats = {}
    for k, v in raw.get("stats", {}).items():
        try:
            converted_stats[Stat[k.upper()]] = v
        except KeyError:
            pass

    return Character(
        id=f"e{enemy_index}",
        name=tag.replace("_", " ").title(),
        role="Enemy",
        hp=raw.get("hp", 10),
        max_hp=raw.get("max_hp", 10),
        ac=raw.get("ac", 10),
        stats=converted_stats,
        zone=Zone.FAR,
        inventory=raw.get("inventory", []),
        condition=Condition.NORMAL,
    )


def start_exploration_loop(
    data_path: str = "data/active/campaign_active.json",
    quest_id: str = "sample_dungeon",
    starting_node_id: str = None,
) -> str:
    """
    Point-Crawl Exploration Loop.

    Handles MOVE, LOOK, REST, STATUS, INVENTORY, QUIT commands
    via pure-Python guardrails. LLM is only called for narration
    AFTER a command passes. Combat is delegated entirely to the
    existing start_combat_loop() with zero modifications.

    Returns: 'VICTORY' | 'DEFEAT' | 'EXIT' | 'HUB'
    """
    # ── Load Game State ────────────────────────────────────────
    data_manager = DataManager(data_path)
    settings = data_manager.load_settings()
    world_lore = data_manager.load_lore()
    party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)

    if not party:
        print(f"   ❌ No party data found.")
        return "EXIT"

    try:
        llm_service = LLMService(settings=settings)
    except Exception as e:
        print(f"   ❌ LLM Service failed: {e}")
        return "EXIT"

    # ── Load Quest ─────────────────────────────────────────────
    quest_data = QuestLoader.load_quest(quest_id)
    if not quest_data:
        print(f"   \u274c Quest '{quest_id}' could not be loaded.")
        return "HUB"

    # Template-vs-Instance: overlay saved progress on top of the clean template.
    # New Game  → load_quest_state returns None → fresh template (all visited=False)
    # Continue  → load_quest_state returns saved copy → resumes with progress intact
    saved_instance = data_manager.load_quest_state(quest_id)
    if saved_instance:
        quest_data = saved_instance

    # Resolve starting node.
    # Only reuse a saved node position if it belongs to THIS quest.
    # If the player is arriving from the hub (different quest_id), always use the entrance.
    saved_node = (
        global_state.get("current_node_id")
        if global_state.get("current_quest_id") == quest_id
        else None
    )
    current_node_id = starting_node_id or saved_node or QuestLoader.get_entrance_node_id(quest_data)
    global_state["current_quest_id"] = quest_id
    global_state["current_node_id"] = current_node_id
    global_state["current_phase"] = "EXPLORATION"
    global_state["is_in_combat"] = False

    # ── Read debug mode from settings ─────────────────────
    global DEBUG_MODE
    DEBUG_MODE = settings.get("engine", {}).get("debug_mode", False)

    quest_name = quest_data.get("name", quest_id)
    player = party[0]

    print(f"\n{'='*52}")
    print(f"  🗺️  ENTERING: {quest_name}")
    print(f"{'='*52}")

    DataManager.append_phase_header("EXPLORATION", quest_name)

    # Narrate initial room entry on load
    current_node = QuestLoader.get_node(quest_data, current_node_id)
    if current_node and not current_node.get("visited", False):
        # First ever entry — lore reveal
        QuestLoader.append_lore(current_node.get("lore_fragment"))
        QuestLoader.mark_visited(quest_data, current_node_id)
        data_manager.save_quest_state(quest_id, quest_data)  # Instance save, not template
        world_lore = data_manager.load_lore()  # Reload after appending

    if current_node:
        print("   Generating room description...")
        narration = llm_service.narrate_room_entry(current_node, world_lore, story_memory, quest_data=quest_data)
        print(f"\n   🗣️  DM: \"{narration}\"\n")
        DataManager.append_to_log(f"[EXPLORATION] Entered: {current_node.get('name')}\n[DM] {narration}\n")

    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

    # ── Main Exploration Loop ───────────────────────────────────
    while True:
        try:
            # Reload node on each iteration (may have changed after combat)
            current_node = QuestLoader.get_node(quest_data, global_state["current_node_id"])
            if not current_node:
                print(f"   ❌ Node '{global_state['current_node_id']}' not found in quest data.")
                return "EXIT"

            # ── HUD ──────────────────────────────────────────────
            render_exploration_dashboard(party, current_node, global_state, quest_name, quest_data=quest_data)
            print(f"   Action > ", end="", flush=True)
            user_input = input()

            if not user_input.strip():
                continue

            DataManager.append_to_log(f"[{player.name}] {user_input}")

            # ── Classify (Hybrid: Regex first, LLM fallback for UNKNOWN) ────
            # Handle debug toggle before classification
            if user_input.lower().strip() == 'debug':
                DEBUG_MODE = not DEBUG_MODE
                print(f"   🔧 Debug Mode is now {'ON' if DEBUG_MODE else 'OFF'}")
                continue

            print("   Thinking...", end="\r", flush=True)
            intent = classify_exploration_intent_smart(user_input, current_node, quest_data=quest_data, settings=settings)
            print(" " * 20, end="\r")
            intent_type = intent["type"]
            debug_print(f"   🤖 [Router] type:{intent_type} | target:{intent.get('raw_target', '')}")

            # ─── QUIT ────────────────────────────────────────────
            if intent_type == "QUIT" or user_input.lower() in ["exit", "quit", "q"]:
                data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                return "EXIT"

            # ─── RETURN TO HUB ───────────────────────────────────
            if intent_type == "EXIT_HUB" or user_input.lower() in ["hub", "return to guild", "leave"]:
                # Only allow leaving from the entrance node
                entrance = QuestLoader.get_entrance_node_id(quest_data)
                if global_state["current_node_id"] == entrance:
                    print("   🏠 [SYSTEM] You head back to the Adventurer's Guild.")
                    global_state["current_phase"] = "HUB"
                    global_state["current_quest_id"] = "hub"
                    global_state["current_node_id"] = "hub_main"
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                    return "HUB"
                else:
                    print("   🛑 [SYSTEM] You can't leave from here — find your way back to the entrance first.")
                    continue

            # ─── LOOK / INSPECT ──────────────────────────────────
            elif intent_type == "LOOK":
                print("   Describing the room...", end="\r")
                # Reload world lore in case lore was appended since last look
                world_lore = data_manager.load_lore()
                narration = llm_service.narrate_exploration_look(current_node, world_lore, quest_data=quest_data)
                print(" " * 30, end="\r")
                print(f"\n   🗣️  DM: \"{narration}\"\n")
                DataManager.append_to_log(f"[LOOK] {narration}")

            # ─── REST ────────────────────────────────────────────
            elif intent_type == "REST":
                rejection = get_rest_rejection_message(current_node)
                if rejection:
                    print(f"   {rejection}")
                    DataManager.append_to_log(f"[SYSTEM] REST blocked: {rejection}")
                else:
                    rest_log = TimeManager.apply_short_rest(party, global_state)
                    print(f"   💤 [SYSTEM] {rest_log}")
                    DataManager.append_to_log(f"[SYSTEM] {rest_log}")
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

            # ─── STATUS ──────────────────────────────────────────
            elif intent_type == "STATUS":
                print(f"\n   👤 {player.name} [{player.role}]")
                print(f"      HP: {player.hp}/{player.max_hp}")
                print(f"      AC: {player.ac}")
                if player.abilities:
                    for a in player.abilities:
                        print(f"      {a.name}: {a.current_uses}/{a.max_uses} charges")
                if player.inventory:
                    print(f"      Inventory: {', '.join(player.inventory)}")

            # ─── INVENTORY ───────────────────────────────────────
            elif intent_type == "INVENTORY":
                if player.inventory:
                    print(f"   🎒 {player.name}'s Inventory: {', '.join(player.inventory)}")
                else:
                    print(f"   🎒 Your inventory is empty.")

            # ─── MOVE ────────────────────────────────────────────
            elif intent_type == "MOVE":
                raw_target = intent.get("raw_target", "").strip()
                if not raw_target:
                    print("   ⚠️  Where do you want to go? Name a destination.")
                    continue

                # Python guardrail: resolve target against connected_to
                target_node_id = QuestLoader.resolve_move_target(raw_target, current_node, quest_data)

                if not target_node_id:
                    # REJECTION — no LLM burn
                    rejection_msg = get_move_rejection_message(raw_target, current_node)
                    print(f"   {rejection_msg}")
                    DataManager.append_to_log(f"[SYSTEM] Invalid MOVE blocked: '{raw_target}'")
                    continue

                # ── Item Gating: required_item check ─────────────────
                target_node_data = QuestLoader.get_node(quest_data, target_node_id)
                required_item = (target_node_data or {}).get("required_item")
                if required_item and required_item not in (player.inventory or []):
                    print(f"   🔒 [SYSTEM] This path requires '{required_item}'. Check your inventory.")
                    DataManager.append_to_log(f"[SYSTEM] MOVE blocked: missing '{required_item}'")
                    continue

                # ✅ Valid move — update state
                new_node = QuestLoader.get_node(quest_data, target_node_id)
                if not new_node:
                    print(f"   ❌ [SYSTEM] Node data missing for '{target_node_id}'.")
                    continue

                global_state["current_node_id"] = target_node_id
                print(f"   🚶 [SYSTEM] Moving to: {new_node['name']}...")

                # ── Step 1: Lore reveal + item pickup (FIRST, before anything else) ──
                if not new_node.get("visited", False):
                    QuestLoader.append_lore(new_node.get("lore_fragment"))
                    QuestLoader.mark_visited(quest_data, target_node_id)
                    data_manager.save_quest_state(quest_id, quest_data)  # Instance save, not template
                    world_lore = data_manager.load_lore()  # Reload enriched lore

                    # grants_item: auto-pickup on first visit
                    granted = new_node.get("grants_item")
                    if granted and granted not in (player.inventory or []):
                        player.inventory = player.inventory or []
                        player.inventory.append(granted)
                        print(f"   🎁 [SYSTEM] You found: {granted}")
                        DataManager.append_to_log(f"[ITEM] Found: {granted}")

                # ── Step 2: Room narration ──────────────────────────
                print("   Narrating...", end="\r")
                room_narration = llm_service.narrate_room_entry(new_node, world_lore, story_memory, quest_data=quest_data)
                print(" " * 20, end="\r")
                print(f"\n   🗣️  DM: \"{room_narration}\"\n")
                DataManager.append_to_log(f"[MOVE] -> {new_node['name']}\n[DM] {room_narration}\n")

                # ── Step 3: Event bridge check ───────────────────────
                event_type = new_node.get("event_type", "safe")
                is_combat_node = event_type in ("combat", "boss")
                is_puzzle_node = event_type == "puzzle"
                is_uncleared = not new_node.get("cleared", True)

                # ── Puzzle node: show obstacle, DON'T auto-resolve ───
                if is_puzzle_node and is_uncleared:
                    obstacle = new_node.get("puzzle_obstacle", "An obstacle blocks your path.")
                    default_puzzle_dc = settings.get("exploration", {}).get("default_puzzle_dc", 14)
                    base_dc = new_node.get("puzzle_base_dc", default_puzzle_dc)
                    print(f"\n   🧩 PUZZLE — \"{obstacle}\"")
                    print(f"   💡 Describe how you solve it. (DC {base_dc})")
                    DataManager.append_to_log(f"[PUZZLE] Encountered: {obstacle}")

                elif is_combat_node and is_uncleared:
                    # ── Dynamic enemy via EnemyFactory (new path) ─────
                    enemy_name_from_node = new_node.get("enemy_name")
                    enemy_archetype = new_node.get("enemy_archetype")
                    enemy_attack_flavor = new_node.get("enemy_attack_flavor", "attacks")
                    enemy_tag = new_node.get("enemy_tag", "goblin")

                    if enemy_name_from_node and enemy_archetype:
                        # New path: EnemyFactory (dynamic scaling)
                        display_name = enemy_name_from_node
                        injected_enemy = EnemyFactory.create(
                            archetype=enemy_archetype,
                            player=player,
                            enemy_name=enemy_name_from_node,
                            attack_flavor=enemy_attack_flavor,
                        )
                    else:
                        # Legacy path: bestiary.json (backward compat for sample_dungeon)
                        display_name = enemy_tag.replace("_", " ").title()
                        injected_enemy = _inject_enemy_from_bestiary(enemy_tag)

                    # Generate Initiative / Cold Open narration
                    print("   Generating encounter...", end="\r")
                    encounter_narration = llm_service.narrate_encounter_start(new_node, display_name, world_lore)
                    print(" " * 30, end="\r")
                    print(f"   ⚔️  DM: \"{encounter_narration}\"\n")
                    DataManager.append_to_log(f"[ENCOUNTER] {display_name} in {new_node['name']}\n[DM] {encounter_narration}\n")

                    # Inject enemy into enemies list
                    if injected_enemy:
                        enemies = [injected_enemy]
                    else:
                        print("   ⚠️  No valid enemy found — skipping combat.")
                        continue

                    # Shift phase to COMBAT
                    global_state["current_phase"] = "COMBAT"
                    global_state["is_in_combat"] = True
                    DataManager.append_phase_header("COMBAT", display_name)

                    # Atomic save before handing to combat loop
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

                    # ── Handoff to existing Combat Loop (UNTOUCHED) ────
                    print(f"\n{'⚔️ '*26}")
                    combat_result = start_combat_loop(data_path=data_path)
                    print(f"{'⚔️ '*26}\n")

                    # Reload state after combat (combat loop saves its own data)
                    party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)
                    # Re-inject exploration phase keys (combat loop doesn't know about them)
                    global_state["current_phase"] = "EXPLORATION"
                    global_state["is_in_combat"] = False
                    global_state["current_node_id"] = target_node_id
                    global_state["current_quest_id"] = quest_id

                    # ── Handle Combat Resolution ────────────────────
                    if combat_result == "VICTORY":
                        # cleared is ONLY set here, exclusively after combat victory
                        QuestLoader.mark_cleared(quest_data, target_node_id)
                        data_manager.save_quest_state(quest_id, quest_data)  # Instance save, not template

                        # Post-combat narration
                        world_lore = data_manager.load_lore()
                        print("   Narrating aftermath...", end="\r")
                        cleared_narration = llm_service.narrate_node_cleared(new_node, world_lore)
                        print(" " * 30, end="\r")
                        print(f"\n   🗣️  DM: \"{cleared_narration}\"\n")
                        DataManager.append_to_log(f"[CLEARED] {new_node['name']}\n[DM] {cleared_narration}\n")

                        data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

                        # Check full quest completion
                        if QuestLoader.is_quest_complete(quest_data):
                            print(f"\n{'🏆'*26}")
                            print(f"  QUEST COMPLETE: {quest_name}")
                            print(f"{'🏆'*26}")
                            data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                            return "VICTORY"

                    elif combat_result == "DEFEAT":
                        data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                        return "DEFEAT"

                    elif combat_result == "EXIT":
                        data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                        return "EXIT"

                    # RESTART: stay in exploration loop, fresh state
                    elif combat_result == "RESTART":
                        party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)
                        global_state["current_phase"] = "EXPLORATION"
                        global_state["is_in_combat"] = False
                        global_state["current_node_id"] = target_node_id
                        global_state["current_quest_id"] = quest_id

                else:
                    # Non-combat / cleared node — just save position
                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

            # ─── PUZZLE ATTEMPT ───────────────────────────────────
            elif intent_type == "PUZZLE_ATTEMPT":
                puzzle_obstacle = current_node.get("puzzle_obstacle", "An obstacle blocks your path.")
                default_puzzle_dc = settings.get("exploration", {}).get("default_puzzle_dc", 14)
                base_dc = current_node.get("puzzle_base_dc", default_puzzle_dc)
                action_desc = intent.get("raw_target", user_input)
                DataManager.append_phase_header("PUZZLE", puzzle_obstacle[:40])

                print("   🎲 [SYSTEM] The Arbiter evaluates your approach...", end="\r")
                world_lore = data_manager.load_lore()
                judgment = llm_service.judge_puzzle_attempt(
                    player, puzzle_obstacle, base_dc, action_desc,
                    world_lore, story_memory
                )
                print(" " * 50, end="\r")

                allowed = str(judgment.get("allowed", "true")).lower() in ("true", "1", "yes")
                reason = judgment.get("reason", "")
                check_stat = judgment.get("check_stat", "PHYS").upper()
                modified_dc = int(judgment.get("modified_dc", base_dc))

                if not allowed:
                    print(f"   ❌ [ARBITER] {reason}")
                    print(f"   💡 Try a different approach!")
                    DataManager.append_to_log(f"[PUZZLE] Attempt rejected: {action_desc} — {reason}")
                else:
                    # Roll the dice: 1d20 + stat modifier
                    stat_key = Stat.PHYS
                    if check_stat == "MENT":
                        stat_key = Stat.MENT
                    elif check_stat == "SOC":
                        stat_key = Stat.SOC

                    modifier = player.stats.get(stat_key, 0)
                    roll = random.randint(1, 20)
                    total = roll + modifier

                    print(f"\n   🎯 [ARBITER] \"{reason}\"")
                    print(f"   🎲 Roll: d20({roll}) + {check_stat}({modifier}) = {total}  vs  DC {modified_dc}")

                    if total >= modified_dc:
                        print(f"   ✅ SUCCESS! You overcome the obstacle!")
                        QuestLoader.mark_cleared(quest_data, current_node.get("node_id", global_state["current_node_id"]))
                        data_manager.save_quest_state(quest_id, quest_data)

                        # Narrate success
                        narration = llm_service.narrate_node_cleared(current_node, world_lore, cleared_by="puzzle")
                        print(f"\n   🗣️  DM: \"{narration}\"\n")
                        DataManager.append_to_log(f"[PUZZLE SOLVED] {action_desc} (Roll:{total} vs DC:{modified_dc})\n[DM] {narration}")

                        # Check full quest completion
                        if QuestLoader.is_quest_complete(quest_data):
                            print(f"\n{'🏆'*26}")
                            print(f"  QUEST COMPLETE: {quest_name}")
                            print(f"{'🏆'*26}")
                            data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                            return "VICTORY"
                    else:
                        print(f"   ❌ FAILED. The obstacle remains. Try a different approach!")
                        DataManager.append_to_log(f"[PUZZLE FAILED] {action_desc} (Roll:{total} vs DC:{modified_dc})")

                    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

            # ─── UNKNOWN ─────────────────────────────────────────
            else:
                print("   🤔 [SYSTEM] That's not something you can do here. Try: LOOK, MOVE [destination], REST, STATUS, INVENTORY, or QUIT.")

        except KeyboardInterrupt:
            print("\n   Saving and shutting down...")
            data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
            return "EXIT"

    return "EXIT"


def start_hub_loop(data_path: str = "data/active/campaign_active.json") -> str:
    """
    Hub Loop — The Adventurer's Guild safe zone.

    Presents quest board, rest, status, and quick battle options.
    Delegates to start_exploration_loop() for quests
    and start_combat_loop() directly for Quick Battle.

    Returns: 'EXIT' | 'DEFEAT'
    """
    data_manager = DataManager(data_path)
    settings = data_manager.load_settings()
    world_lore = data_manager.load_lore()
    party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)

    if not party:
        print("   ❌ No character found. Please start a New Game.")
        return "EXIT"

    try:
        llm_service = LLMService(settings=settings)
    except Exception as e:
        print(f"   ❌ LLM Service failed: {e}")
        return "EXIT"

    player = party[0]

    # ── Hub Welcome Narration ──────────────────────────────────
    global_state["current_phase"] = "HUB"
    global_state["current_quest_id"] = "hub"
    global_state["current_node_id"] = "hub_main"
    global_state["is_in_combat"] = False

    print("   Generating Guild welcome...", end="\r")
    # Extract prologue from story_memory if this is a fresh arrival from character creation.
    # The prologue is stored as the first entry prefixed with '[PROLOGUE] '.
    prologue_text = ""
    if story_memory:
        for entry in list(story_memory):
            if str(entry).startswith("[PROLOGUE] "):
                prologue_text = str(entry)[len("[PROLOGUE] "):].strip()
                break

    welcome = llm_service.narrate_hub_welcome(player.name, world_lore, story_memory, prologue_text)
    print(" " * 35, end="\r")
    print(f"\n   🗣️  DM: \"{welcome}\"\n")
    DataManager.append_phase_header("HUB")
    DataManager.append_to_log(f"  🗣️ DM: {welcome}")
    data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

    # ── Hub Loop ───────────────────────────────────────────────
    while True:
        try:
            # Reload to pick up any changes from sub-loops
            party, enemies, combat_memory, story_memory, global_state = data_manager.load_game(settings=settings)
            world_lore = data_manager.load_lore()
            player = party[0] if party else player

            available_quests = QuestLoader.list_available_quests()

            # ── Auto-generate quest board if below threshold ──────────
            exploration_cfg = settings.get("exploration", {})
            quest_board_size = exploration_cfg.get("quest_board_size", 3)
            auto_generate = exploration_cfg.get("auto_generate_quests", True)
            if auto_generate and len(available_quests) < quest_board_size:
                needed = quest_board_size - len(available_quests)
                print(f"   \u2728 [SYSTEM] Generating {needed} new quest(s) for the board...", end="\r")
                try:
                    character_toon = TOONConverter.convert([player], [])
                    bestiary_tags = QuestLoader.list_bestiary_tags()
                    existing_ids = [q["id"] for q in available_quests]
                    new_quests = llm_service.generate_quest_board(
                        character_toon, world_lore, bestiary_tags,
                        num_quests=needed, existing_quest_ids=existing_ids,
                    )
                    for nq in new_quests:
                        # Save a stub quest file so it appears on the board.
                        # The full map is generated on-demand when selected.
                        stub = {
                            "quest_id": nq["quest_id"],
                            "name": nq["name"],
                            "description": nq["description"],
                            "entrance_node": "node_01",
                            "nodes": {},
                            "_meta": {
                                "generated": True,
                                "theme": nq.get("theme", ""),
                                "enemy_tags": nq.get("enemy_tags", []),
                                "num_nodes": nq.get("num_nodes", 4),
                            },
                        }
                        QuestLoader.save_generated_quest(nq["quest_id"], stub)
                    available_quests = QuestLoader.list_available_quests()
                    print(" " * 60, end="\r")
                except Exception as e:
                    print(f"   \u26a0\ufe0f Quest board generation error: {e}")

            render_hub_dashboard(party, global_state, available_quests)

            print("   Action > ", end="", flush=True)
            user_input = input().strip()

            if not user_input:
                continue

            lower = user_input.lower()
            DataManager.append_to_log(f"[{player.name}] (Hub) {user_input}")

            # ── Quit ──────────────────────────────────────────
            if lower in ["quit", "exit", "q"]:
                data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
                return "EXIT"

            # ── Rest (Long Rest in Hub) ────────────────────────
            elif any(kw in lower for kw in ["rest", "sleep", "camp"]):
                rest_log = TimeManager.apply_long_rest(party, global_state)
                print(f"   💤 [SYSTEM] {rest_log}")
                DataManager.append_to_log(f"[SYSTEM] {rest_log}")
                data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)

            # ── Status ────────────────────────────────────────
            elif any(kw in lower for kw in ["status", "character", "sheet", "stats"]):
                print(f"\n   👤 {player.name} [{player.role}]")
                print(f"      HP: {player.hp}/{player.max_hp}  |  AC: {player.ac}")
                if player.abilities:
                    for a in player.abilities:
                        print(f"      {a.name}: {a.current_uses}/{a.max_uses} charges")
                if player.inventory:
                    print(f"      Inventory: {', '.join(player.inventory)}")

            # ── Inventory ─────────────────────────────────────
            elif any(kw in lower for kw in ["inventory", "items", "bag", "pack"]):
                if player.inventory:
                    print(f"   🎒 {player.name}'s Inventory: {', '.join(player.inventory)}")
                else:
                    print("   🎒 Your inventory is empty.")

            # ── Quest Board ───────────────────────────────────────
            elif any(kw in lower for kw in ["quest", "board", "job", "mission", "bounty"]):
                if not available_quests:
                    print("   📋 No quests available right now.")
                    continue
                print("\n   📋 QUEST BOARD:")
                for i, q in enumerate(available_quests, 1):
                    tag = "\u2b50 Pre-made" if q["id"] == "sample_dungeon" else "\u2728 Generated"
                    print(f"      [{i}] {q['name']}  ({tag})")
                    print(f"          {q.get('description', '')}")
                print(f"      [0] Cancel")

                choice = input("\n   Choose quest (number): ").strip()
                if not choice.isdigit():
                    continue
                choice_int = int(choice)
                if choice_int == 0 or choice_int > len(available_quests):
                    continue

                chosen = available_quests[choice_int - 1]
                chosen_id = chosen["id"]
                print(f"\n   ✦ Accepting quest: {chosen['name']}")
                DataManager.append_to_log(f"[QUEST ACCEPTED] {chosen['name']}")

                # Reset any existing progress/save state for this quest so it plays fresh
                data_manager.delete_quest_state(chosen_id)

                # ── Generate map on-demand for procedural quests ──────
                quest_file = QuestLoader.load_quest(chosen_id)
                is_stub = not quest_file.get("nodes") if quest_file else True

                if is_stub:
                    # This is a generated quest stub — build the full map now
                    meta = quest_file.get("_meta", {}) if quest_file else {}
                    quest_summary = {
                        "quest_id": chosen_id,
                        "name": chosen["name"],
                        "description": chosen.get("description", ""),
                        "enemy_tags": meta.get("enemy_tags", ["goblin"]),
                        "num_nodes": meta.get("num_nodes", 4),
                        "theme": meta.get("theme", "adventure"),
                    }
                    print("   🗺️  [SYSTEM] Generating dungeon map...", end="\r")
                    try:
                        bestiary_tags = QuestLoader.list_bestiary_tags()
                        full_map = llm_service.generate_quest_map(
                            quest_summary, world_lore, bestiary_tags
                        )
                        QuestLoader.save_generated_quest(chosen_id, full_map)
                        print(" " * 50, end="\r")
                    except Exception as e:
                        print(f"   \u274c Map generation failed: {e}")
                        continue

                # Launch exploration loop
                result = start_exploration_loop(
                    data_path=data_path,
                    quest_id=chosen_id,
                    starting_node_id=None,  # Use quest entrance
                )

                if result == "EXIT":
                    return "EXIT"
                elif result == "DEFEAT":
                    return "DEFEAT"
                elif result == "VICTORY":
                    print("\n   🎉 Quest complete! Welcome back to the Guild.")
                    # Remove completed quest (protected quests are guarded internally)
                    QuestLoader.delete_quest(chosen_id)
                    DataManager.append_to_log(f"[QUEST COMPLETE] {chosen['name']}")
                # else HUB: just fall back to hub loop naturally

            else:
                print("   🤔 [HUB] Try: QUEST BOARD | REST | STATUS | INVENTORY | QUIT")

        except KeyboardInterrupt:
            print("\n   Saving and shutting down...")
            data_manager.save_game(party, enemies, combat_memory=combat_memory, story_memory=story_memory, global_state=global_state)
            return "EXIT"

    return "EXIT"
