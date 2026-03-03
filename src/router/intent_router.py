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
from src.models.toon_converter import TOONConverter
from src.logic.combat_manager import InitiativeQueue
import difflib

# Load environment variables
load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")

# Using the requested model
MODEL_NAME = "gemini-2.5-flash-lite" 

def classify_intent(user_input: str, toon_context: str) -> dict:
    """
    Classifies the user input into a JSON object using Gemini.
    Provides the current game state in TOON format to help with context.
    """
    if not api_key:
        return {"error": "Missing API Key"}

    genai.configure(api_key=api_key)
    
    # Generation Config for plain text output
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "text/plain",
    }
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction="""
        You are a purely mechanical decision tree for a TTRPG game.
        Your ONLY job is to classify the player's input into one of two paths based on the GAME STATE provided.
        
        PATH A (FIXED ACTION) - Standard Game Mechanics:
        The input matches a standard rule-based action found in a game menu.
        - Attack (hitting, shooting, slashing, unarmed strike)
        - Cast Spell (magic, cantrips, scrolls)
        - Move (running, walking, tactical movement, disengaging)
        - Standard Item Use (drinking potion, equipping armor, eating food, lighting torch)
        - Flee / Escape (running away from combat)
        - Combo (doing a Move AND an Attack/Flee in the same sentence)
        
        PATH B (CREATIVE ACTION) - Narrative & Improv:
        The input is complex, narrative, social, or uses items in non-standard ways.
        - Physical stunts (tying ropes, flipping tables, jumping off cliffs)
        - Social (persuading, intimidating, lying, flirting, talking)
        - Investigation (examining runes, searching for traps, listening at doors)
        - Unorthodox Item Use (e.g., "I pour the oil on the floor to make him slip")
        
        OUTPUT FORMAT (TOON SYNTAX ONLY - 1 LINE STRICT):
        For this performance upgrade, you MUST NOT output JSON. You must output a single line of pipe-separated key:value pairs.
        
        For Path A (Single Action): type:FIXED|command:ATTACK | CAST | MOVE | USE | FLEE|target:e1|attack_type:melee
          - If command is MOVE, "target" MUST be exactly NEAR, MID, or FAR.
          - Example: type:FIXED|command:MOVE|target:MID|attack_type:null
          
        For Path A (Combo Action): type:FIXED_COMBO|move_target:MID|attack_target:e1|attack_type:ranged|action_order:[MOVE,ATTACK]
        
        For Path B: type:CREATIVE|description:short summary of intent
        """
    )

    prompt = f"GAME STATE (TOON):\n{toon_context}\n\nPLAYER INPUT:\n{user_input}"

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        debug_print(f"      [LLM TOON Response]: {text}")
        return TOONConverter.decode(text)
    except Exception as e:
        return {"type": "ERROR", "message": f"Decode Error: {str(e)}"}

def _find_target(target_name_or_id: str, enemies: list) -> Character | None:
    """Helper to resolve target ID using 3-tier matching."""
    if not target_name_or_id:
        return None
        
    target_name_or_id = target_name_or_id.lower().strip()
    active_enemies = [e for e in enemies if e.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]]
    
    # 1. Exact ID Match (Primary)
    for e in active_enemies:
        if e.id.lower() == target_name_or_id:
            return e
            
    # 2. Fuzzy String Match (Fallback for Typos)
    active_names = {e.name.lower(): e for e in active_enemies}
    matches = difflib.get_close_matches(target_name_or_id, active_names.keys(), n=1, cutoff=0.4)
    if matches:
        return active_names[matches[0]]
        
    # 3. Old Substring Match (Last Resort)
    for e in active_enemies:
        if target_name_or_id in e.name.lower():
            return e
            
    return None


