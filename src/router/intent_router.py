import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

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
    # --- 1. Automated Weird Test Cases ---
    print("\n" + "="*40)
    print("🧪 RUNNING WEIRD EDGE CASES")
    print("="*40)

    weird_scenarios = [
        "I kiss the goblin on the forehead",              # Social/Creative
        "I throw my boots at the wizard",                 # Improvised Attack (Could be Fixed or Creative, lets see)
        "I drink my health potion",                       # Standard Use (Fixed)
        "I smash the potion bottle on the ground to create glass shards", # Creative Use
        "I run 30 feet towards the door",                 # Standard Move (Fixed)
        "I do a backflip over the table",                 # Stunt (Creative)
        "I cast Fireball centered on myself",             # Standard Cast (Fixed - even if dumb)
        "I inspect the wall for secret buttons"           # Investigation (Creative)
    ]

    for scenario in weird_scenarios:
        result = classify_intent(scenario)
        print(f"🔹 In:  {scenario}")
        print(f"🔸 Out: {result}\n")

    # --- 2. Interactive Loop ---
    print("="*40)
    print("🎮 INTERACTIVE MODE (Type 'exit' to quit)")
    print("="*40)
    
    while True:
        try:
            user_input = input("\nYour Action > ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Shutting down router.")
                break
            
            if not user_input.strip():
                continue

            result = classify_intent(user_input)
            print(f"🤖 Router Decision: {json.dumps(result, indent=2)}")
            
        except KeyboardInterrupt:
            print("\nShutting down router.")
            break
