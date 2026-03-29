import os
import sys

# Setup paths — resolve project root from tests/ folder
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.services.llm_service import LLMService

def test_prologue():
    llm = LLMService()
    toon = "Name: TestHero\nClass: Fighter\nBackground: A battle-hardened warrior trained at the imperial academy.\nStats: {PHYS: +3, MENT: +0, SOC: -1}"
    lore = "A dark world where ancient spirits and neon-lit ruins coexist. The jungle hides cursed temples."

    print("Generating Cold Open Prologue...\n")
    res = llm.generate_prologue(toon, lore)

    print("=" * 50)
    print("PROLOGUE:")
    print(res.get("prologue", "(no prologue)"))
    print("=" * 50)
    print(f"ENEMY TYPE: {res.get('enemy_type', '(unknown)')}")

    assert "prologue" in res, "❌ FAIL: No prologue key in response"
    assert "enemy_type" in res, "❌ FAIL: No enemy_type key in response"
    assert res["prologue"] != "You awaken in a dark dungeon. An enemy approaches!", "❌ FAIL: Got fallback prologue — LLM call likely failed"
    print("\n✅ PASS: Prologue generated successfully!")

if __name__ == '__main__':
    test_prologue()
