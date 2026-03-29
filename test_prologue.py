import sys
import os
sys.path.append(os.getcwd())

from src.services.llm_service import LLMService

llm = LLMService()
toon = "Name: Jason\nClass: Fighter\nBackground: A brave fighter.\nStats: {'PHYS': 3}"
lore = "A dark fantasy world."

print("Generating...")
res = llm.generate_prologue(toon, lore)
print("\nFINAL OUTPUT:", res)
