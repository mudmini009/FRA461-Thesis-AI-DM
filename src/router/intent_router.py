import os
import json
import sys
sys.path.append('.') 
import google.generativeai as genai
from dotenv import load_dotenv

# --- REFRACTORED IMPORTS ---
from src.logic.rules_engine import RulesEngine
from src.models.character import Character, Stat, Zone, Condition
from src.services.llm_service import LLMService
from src.services.data_manager import DataManager
from src.logic.enemy_ai import EnemyAI

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")

# Using the requested model
MODEL_NAME = "gemini-2.5-flash-lite" 

def classify_intent(user_input: str) -> dict:
    """
    Classifies the user input into a JSON object using Gemini.
    """
    if not api_key:
        return {"error": "Missing API Key"}

    genai.configure(api_key=api_key)
    
    # Generation Config for JSON output
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction="""
        You are a purely mechanical decision tree for a TTRPG game.
        Your ONLY job is to classify the player's input into one of two paths:
        
        PATH A (FIXED ACTION) - Standard Game Mechanics:
        The input matches a standard rule-based action found in a game menu.
        - Attack (hitting, shooting, slashing, unarmed strike)
        - Cast Spell (magic, cantrips, scrolls)
        - Move (running, walking, tactical movement, disengaging)
        - Standard Item Use (drinking potion, equipping armor, eating food, lighting torch)
        
        PATH B (CREATIVE ACTION) - Narrative & Improv:
        The input is complex, narrative, social, or uses items in non-standard ways.
        - Physical stunts (tying ropes, flipping tables, jumping off cliffs)
        - Social (persuading, intimidating, lying, flirting, talking)
        - Investigation (examining runes, searching for traps, listening at doors)
        - Unorthodox Item Use (e.g., "I pour the oil on the floor to make him slip")
        
        OUTPUT FORMAT (JSON ONLY):
        For Path A: {"type": "FIXED", "command": "ATTACK" | "CAST" | "MOVE" | "USE", "target": "string or null"}
        For Path B: {"type": "CREATIVE", "description": "short summary of intent"}
        """
    )

    try:
        response = model.generate_content(user_input)
        return json.loads(response.text)
    except Exception as e:
        return {"type": "ERROR", "message": str(e)}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎮 AI DM PROTOTYPE: TWO-PATH ARCHITECTURE (PHASE 2)")
    print("="*50)
    
    # --- 0. INITIALIZE SERVICES ---
    try:
        llm_service = LLMService()
        print("✅ LLM Arbiter Online")
    except Exception as e:
        print(f"❌ Failed to load LLM Service: {e}")
        exit()

    # --- 1. LOAD DATA FROM JSON ---
    data_manager = DataManager()
    party, enemies = data_manager.load_game()

    if not party:
        print("❌ Error: No party data found. Check data/campaign.json")
        exit()

    # Set Active Characters for Testing
    player = party[0]       # Valen
    goblin = enemies[0]     # Goblin Scavenger

    # Keep party and enemies separate for TOON conversion
    # party = party + enemies <--- REMOVED

    print(f"🦸 Player: {player}")
    print(f"👹 Enemy:  {goblin}")

    while True:
        try:
            print(f"\n[{player.name}] Action > ", end="")
            user_input = input()
            if user_input.lower() in ['exit', 'quit', 'q']: break
            if not user_input.strip(): continue

            print("   Thinking...", end="\r") # Loading effect
            
            # 1. ROUTER: Decide Intent
            decision = classify_intent(user_input)
            
            # Clear loading line
            print(" " * 20, end="\r")
            
            print(f"🤖 Intent: {decision.get('type', 'ERROR').ljust(10)} | Command: {decision.get('command', 'N/A')}")

            # 2. PATH A: FIXED RULES (Delegated to RulesEngine)
            if decision.get('type') == 'FIXED':
                
                if decision.get('command') == 'ATTACK':
                    print(f"   ⚔️  Executing Attack Sequence...")
                    result = RulesEngine.resolve_attack(player, goblin)
                    
                    roll_info = f"{result['roll']} + {player.stats[Stat.PHYS]} (Bonus)"
                    
                    if result['is_crit']:
                         print(f"   🔥 CRITICAL HIT! (Natural 20!)")
                    
                    if result['is_hit']:
                        if not result['is_crit']:
                             print(f"   💥 HIT! (Total {result['total']} vs AC {goblin.ac})")
                        print(f"   🩸 Damage Dealt: {result['damage']}")
                        print(f"   📉 Goblin HP: {goblin.hp}/{goblin.max_hp} ({goblin.condition.name})")
                    else:
                        print(f"   🛡️ MISS! (Total {result['total']} vs AC {goblin.ac})")

                elif decision.get('command') == 'MOVE':
                    print("   🏃 Processing Movement Rules... (To be implemented)")
                else:
                    print(f"   ⚙️ Processing {decision.get('command')}... (To be implemented)")

            # 3. PATH B: CREATIVE (The AI Arbiter)
            elif decision.get('type') == 'CREATIVE':
                 description = decision.get('description', user_input)
                 print(f"   🤔 Arbiter Judging: '{description}'")
                 
                 # A. Arbitration
                 judgment = llm_service.get_creative_judgment(party, enemies, player, description)
                 
                 if judgment['allowed']:
                     print(f"   ✅ Allowed! Reason: {judgment['reason']}")
                     
                     stat_str = judgment.get('check_stat', 'PHYS')
                     dc = judgment.get('dc', 10)
                     
                     # Map string to Enum safely
                     try:
                         target_stat = Stat[stat_str]
                     except KeyError:
                         target_stat = Stat.PHYS # Default falllback
                         
                     print(f"   🎲 Rolling Check: {target_stat.value} (DC {dc})")
                     
                     # B. Execution (Rules Engine)
                     success = RulesEngine.resolve_check(player, target_stat, dc)
                     
                     # Get the raw roll just for display (RulesEngine returns bool, but let's assume valid)
                     # For more detail, normally RulesEngine.resolve_check should return dict, but for now we trust the bool.
                     # But wait, to narrate we need the roll. 
                     # Let's peek at the helper or just narrate the success/fail.
                     # The implementation plan said: narrate_result(action, outcome_bool).
                     
                     outcome_text = "PASSED" if success else "FAILED"
                     print(f"   {'🌟' if success else '💀'} Check {outcome_text}!")
                     
                     # --- C. SYMBOLIC GROUNDING (Side Effects) ---
                     # Added logic to update Game State based on Arbiter's Condition
                     if success:
                         condition_str = judgment.get('on_success_condition')
                         target_name = judgment.get('target_name_guess')
                         
                         if condition_str and target_name:
                             # 1. Search for target in party or enemies (Fuzzy Match)
                             found_target = None
                             all_actors = party + enemies
                             for char in all_actors:
                                 if target_name.lower() in char.name.lower():
                                     found_target = char
                                     break
                            
                             # 2. Apply Condition
                             if found_target:
                                 try:
                                     new_condition = Condition[condition_str]
                                     found_target.condition = new_condition
                                     print(f"   ⚠️ STATUS UPDATE: {found_target.name} is now {new_condition.name}!")
                                 except KeyError:
                                     print(f"   ⚠️ Warning: Arbiter returned invalid condition '{condition_str}'")

                     # D. Narration
                     narration = llm_service.narrate_result(description, "Hidden", dc, success)
                     print(f"   🗣️  DM: \"{narration}\"")
                     
                 else:
                     print(f"   🚫 Denied! Reason: {judgment['reason']}")

            # Error handling
            elif decision.get('type') == 'ERROR':
                print(f"   ❌ Error: {decision.get('message')}")
                continue # Skip enemy turn on error

            # --- 4. ENEMY TURN (Side Initiative) ---
            print(f"\n   🔻 Enemy Turn:")
            enemy_logs = EnemyAI.execute_turn(enemies, party)
            
            if not enemy_logs:
                print("   (No active enemies or targets)")
            else:
                for log in enemy_logs:
                    print(f"   {log}")

            # --- 5. CHECK WIN/LOSS CONDITIONS ---
            active_players = [p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
            active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]

            if not active_players:
                print("\n" + "💀"*20)
                print("GAME OVER - The Party has fallen!")
                print("💀"*20)
                break
            
            if not active_enemies:
                print("\n" + "🏆"*20)
                print("VICTORY - All enemies defeated!")
                print("🏆"*20)
                break
        
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
