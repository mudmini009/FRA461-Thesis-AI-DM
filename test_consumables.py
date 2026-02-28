import os
import sys
sys.path.append(os.getcwd())

from src.models.character import Character, Stat, Zone, Condition
from src.router.intent_router import classify_intent
from src.router.intents import execute_fixed_action, handle_creative_intent
from src.services.llm_service import LLMService

from dotenv import load_dotenv
load_dotenv()

class MockDebug:
    def __call__(self, *args, **kwargs):
        print("DEBUG:", *args)

def test_items():
    print("--- Setting up test ---")
    player = Character(id="p1", name="Valen the Explorer", role="Fighter", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Can of Redbull (Heals HP)", "Flashbang Grenade", "Longsword"])
    enemy = Character(id="e1", name="Senior Robotics Engineer", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=[])
    
    party = [player]
    enemies = [enemy]
    llm = LLMService()
    debug = MockDebug()
    
    # Test Path A
    print(f"\n[Test 1] Path A (Fixed): Using a potion")
    print(f"Initial Inventory: {player.inventory}")
    input_text = "I drink my redbull"
    print(f"Input: {input_text}")
    from src.models.toon_converter import TOONConverter
    toon = TOONConverter.convert(party, enemies)
    intent = classify_intent(input_text, toon)
    print("Classified intent:", intent)
    cmd = intent.get('command')
    if intent['type'] == 'FIXED' or intent['type'] == 'FIXED_COMBO':
        if not cmd: cmd = 'USE'
        execute_fixed_action(cmd, intent, player, enemies, debug)
    elif intent['type'] == 'CREATIVE':
        handle_creative_intent(intent, input_text, player, party, enemies, llm, debug)
        
    print(f"Resulting Inventory: {player.inventory}")

    # Test Path B
    print(f"\n[Test 2] Path B (Creative): Throwing an explosive")
    print(f"Current Inventory: {player.inventory}")
    input_text = "I twist the cap off the flashbang grenade and hurl it at the ceiling above the engineer to blind him!"
    print(f"Input: {input_text}")
    toon = TOONConverter.convert(party, enemies)
    intent = classify_intent(input_text, toon)
    print("Classified intent:", intent)
    
    if intent['type'] == 'FIXED' or intent['type'] == 'FIXED_COMBO':
        cmd = intent.get('command', 'USE')
        execute_fixed_action(cmd, intent, player, enemies, debug)
    elif intent['type'] == 'CREATIVE':
        handle_creative_intent(intent, input_text, player, party, enemies, llm, debug)
        
    print(f"Final Inventory: {player.inventory}")

if __name__ == '__main__':
    test_items()
