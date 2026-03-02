import os
import sys

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.models.character import Character, Stat, Zone, Condition
from src.services.llm_service import LLMService

# Forcing debug mode ON
os.environ["DEBUG_MODE"] = "True"
import src.engine.game_loop as gl
from src.router.intents import execute_fixed_action, handle_creative_intent

class MockLLMService:
    def get_creative_judgment(self, *args, **kwargs):
        return {
            "allowed": True,
            "reason": "Test reason",
            "check_stat": "PHYS",
            "dc": 10,
            "on_success_condition": None,
            "target_name_guess": "Goblin",
            "consumed_item": None
        }
    def narrate_result(self, *args, **kwargs):
        return "You swing wildly."

def test_debug_mode():
    print("--- Simulating Debug Prints ---")
    player = Character(id="p1", name="Player", role="Fighter", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Sword"])
    enemy = Character(id="e1", name="Goblin", role="Monster", stats={Stat.PHYS: 2}, hp=20, max_hp=20, ac=15, zone=Zone.NEAR, inventory=["Gold Coin"])
    
    # 1. Test Fixed Attack Logging
    print("\n[Testing Fixed Attack Logs]")
    decision_fixed = {'type': 'FIXED', 'command': 'ATTACK', 'target': 'e1'}
    execute_fixed_action('ATTACK', decision_fixed, player, [enemy], gl.debug_print)
    
    # 2. Test Creative Arbiter Logging
    print("\n[Testing Creative Arbiter Logs]")
    decision_creative = {'type': 'CREATIVE', 'description': 'I try to kick the goblin'}
    mock_llm = MockLLMService()
    handle_creative_intent(decision_creative, "I try to kick the goblin", player, [player], [enemy], mock_llm, gl.debug_print)

if __name__ == '__main__':
    test_debug_mode()
