import os
import shutil
import time
from src.ui.menu import main_menu, recap_menu, character_creation_menu, world_lore_menu, get_character_name
from src.services.data_manager import DataManager
from src.services.llm_service import LLMService
from src.models.character import Character, Stat, Zone, Condition
import json

BACKUP_FILE = "data/campaign_backup.json"
ACTIVE_FILE = "data/campaign_active.json"
LOG_FILE = "data/campaign_log.txt"
BESTIARY_FILE = "data/bestiary.json"
ACTIVE_LORE_FILE = "data/world_lore.txt"

HARDCODED_ARCHETYPES = {
    "fighter": {"hp": 20, "max_hp": 20, "ac": 16, "stats": {Stat.PHYS: 3, Stat.MENT: 0, Stat.SOC: -1}, "inventory": ["healing potion", "sword"]},
    "wizard": {"hp": 12, "max_hp": 12, "ac": 11, "stats": {Stat.PHYS: -1, Stat.MENT: 4, Stat.SOC: 0}, "inventory": ["mana potion", "staff"]},
    "rogue": {"hp": 15, "max_hp": 15, "ac": 14, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: 1}, "inventory": ["bomb", "dagger"]},
    "cleric": {"hp": 16, "max_hp": 16, "ac": 15, "stats": {Stat.PHYS: 1, Stat.MENT: 2, Stat.SOC: 1}, "inventory": ["healing potion", "mace"]},
    "ranger": {"hp": 16, "max_hp": 16, "ac": 14, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: 0}, "inventory": ["healing potion", "bow"]}
}

HARDCODED_BESTIARY = {
    "goblin": {"hp": 8, "max_hp": 8, "ac": 12, "stats": {Stat.PHYS: 1, Stat.MENT: -1, Stat.SOC: 0}, "inventory": ["dirty knife"]},
    "bandit": {"hp": 12, "max_hp": 12, "ac": 11, "stats": {Stat.PHYS: 2, Stat.MENT: 0, Stat.SOC: 1}, "inventory": ["healing potion", "iron sword"]},
    "skeleton": {"hp": 10, "max_hp": 10, "ac": 13, "stats": {Stat.PHYS: 1, Stat.MENT: -2, Stat.SOC: -2}, "inventory": ["rusty sword"]},
    "wolf": {"hp": 11, "max_hp": 11, "ac": 13, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: -2}, "inventory": []},
    "cultist": {"hp": 9, "max_hp": 9, "ac": 11, "stats": {Stat.PHYS: 0, Stat.MENT: 2, Stat.SOC: 1}, "inventory": ["dagger", "strange talisman"]}
}

def print_slow(text, delay=0.005):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def initialize_new_game(llm_service: LLMService) -> bool:
    # 1. Reset state
    shutil.copy(BACKUP_FILE, ACTIVE_FILE)
    DataManager.clear_log()
    
    # 2. Character Creation
    char_mode, char_input = character_creation_menu()
    archetype = "fighter"
    
    if char_mode == 'premade' and os.path.exists(char_input):
        char_file = char_input
        archetype = os.path.basename(char_input).replace('.json', '')
    elif char_mode == 'custom':
        print("\n[System] Consulting LLM for Semantic Classification...")
        toon_out = llm_service.extract_character_stats(char_input)
        print(f"   [LLM Decoded]: {toon_out}")
        if 'archetype:' in toon_out:
            parts = toon_out.split('|')
            for p in parts:
                if p.startswith('archetype:'):
                     archetype = str(p.split(':')[1].strip().lower())
        char_file = f"data/premade/characters/{archetype}.json"
        
    # Failsafe fallback if file doesn't exist
    if not os.path.exists(char_file):
        char_file = "data/premade/characters/fighter.json"
        archetype = "fighter"
        
    with open(char_file, 'r', encoding='utf-8') as f:
        base_stats = json.load(f)
        
    # Convert JSON string keys to Enum Stats
    converted_stats = {}
    for k, v in base_stats.get("stats", {}).items():
        try:
            converted_stats[Stat[k.upper()]] = v
        except KeyError:
            pass
            
    player_name = get_character_name()
    
    player = Character(
        id=base_stats.get("id", "player1"),
        name=player_name,
        role=base_stats.get("role", str(archetype).capitalize()),
        hp=base_stats.get("hp", 20),
        max_hp=base_stats.get("max_hp", 20),
        ac=base_stats.get("ac", 10),
        stats=converted_stats,
        zone=Zone[base_stats.get("zone", "NEAR").upper()],
        inventory=base_stats.get("inventory", []),
        condition=Condition[base_stats.get("condition", "NORMAL").upper()]
    )

    # 3. World Lore
    lore_mode, lore_input = world_lore_menu()
    world_lore = ""
    if lore_mode == 'custom':
        print("\n[System] Expanding World Lore...")
        world_lore = llm_service.expand_world_lore(lore_input)
        with open(ACTIVE_LORE_FILE, "w", encoding="utf-8") as f:
            f.write(world_lore)
    elif lore_mode == 'file' and os.path.exists(lore_input):
        with open(lore_input, 'r', encoding='utf-8') as f:
            world_lore = f.read().strip()
        with open(ACTIVE_LORE_FILE, "w", encoding="utf-8") as f:
            f.write(world_lore)
    else:
        # Fallback to default if no file selected
        try:
             with open("data/premade/lore/classic_fantasy.txt", 'r', encoding='utf-8') as f:
                 world_lore = f.read().strip()
        except:
             world_lore = "A generic dark fantasy world filled with dangerous monsters."
             
        with open(ACTIVE_LORE_FILE, "w", encoding="utf-8") as f:
             f.write(world_lore)
        
    # 4. Prologue Generation
    print("\n[System] Generating Prologue (Cold Open)...")
    char_lore = base_stats.get("lore", "A brave adventurer seeking glory and gold.")
    toon_char = f"Name: {player.name}\nClass: {player.role}\nBackground: {char_lore}\nStats: {player.stats}"
    prologue_data = llm_service.generate_prologue(toon_char, world_lore)
    
    prologue_text = prologue_data.get("prologue", "You enter the dungeon... prepare for battle!")
    # Replace any placeholder the LLM may have left for the character name
    for placeholder in ["[Character Name]", "[character name]", "[Name]", "[name]", "[PLAYER]"]:
        prologue_text = prologue_text.replace(placeholder, player.name)
    enemy_tag = prologue_data.get("enemy_type", "goblin").lower()
    
    if not os.path.exists(BESTIARY_FILE):
        print(f"❌ Error: {BESTIARY_FILE} missing! Creating minimal fallback...")
        with open(BESTIARY_FILE, 'w') as f:
            json.dump({"goblin": {"hp": 8, "max_hp": 8, "ac": 12, "stats": {"PHYS": 1, "MENT": -1, "SOC": 0}, "inventory": []}}, f)
            
    with open(BESTIARY_FILE, 'r', encoding='utf-8') as f:
        bestiary = json.load(f)
        
    if enemy_tag not in bestiary:
        enemy_tag = list(bestiary.keys())[0] if bestiary else "goblin"
        
    enemy_stats = bestiary.get(enemy_tag, {})
    
    # Convert enemy stats
    converted_enemy_stats = {}
    for k, v in enemy_stats.get("stats", {}).items():
        try:
            converted_enemy_stats[Stat[k.upper()]] = v
        except KeyError:
            pass
            
    enemy = Character(
        id="e1",
        name=str(enemy_tag).capitalize(),
        role="Enemy",
        hp=enemy_stats.get("hp", 10),
        max_hp=enemy_stats.get("max_hp", 10),
        ac=enemy_stats.get("ac", 10),
        stats=converted_enemy_stats,
        zone=Zone.FAR,
        inventory=enemy_stats.get("inventory", []),
        condition=Condition.NORMAL
    )
    
    # 5. Save Initial State
    dm = DataManager(ACTIVE_FILE)
    dm.save_game(party=[player], enemies=[enemy], combat_memory=None, story_memory=None)
    # Log the prologue so Continue can load it
    DataManager.append_to_log("[PROLOGUE]")
    DataManager.append_to_log(prologue_text.replace('\\n', '\n'))
    DataManager.append_to_log("[END PROLOGUE]\n")
    
    # Narrate the prologue
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 50)
    print_slow(prologue_text.replace('\\n', '\n'), 0.02)
    print("=" * 50)
    print("\n[PRESS ENTER TO START COMBAT]")
    input()
    return True

def run_continue_flow(llm_service: LLMService) -> bool:
    if not os.path.exists(ACTIVE_FILE):
        print("No active save found! Returning to main menu.")
        time.sleep(2)
        return False
        
    do_recap = recap_menu()
    if do_recap:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            if logs:
                print("\n[System] Generating Recap...")
                recap_text = llm_service.generate_recap(logs)
                os.system('cls' if os.name == 'nt' else 'clear')
                print("=" * 50)
                print("PREVIOUSLY ON YOUR ADVENTURE:")
                print_slow(recap_text, 0.02)
                print("=" * 50)
                print("\n[PRESS ENTER TO RESUME]")
                input()
            else:
                print("Log file is empty. Nothing to recap.")
                time.sleep(2)
        except FileNotFoundError:
             print("No log file found to recap.")
             time.sleep(2)
    
    return True

def run_startup() -> bool:
    try:
        llm = LLMService()
    except Exception as e:
        print(f"Error loading LLM: {e}")
        return False
        
    while True:
        choice = main_menu()
        if choice == 'new':
            if initialize_new_game(llm):
                return True
        elif choice == 'continue':
            if run_continue_flow(llm):
                return True
        elif choice == 'exit':
            return False
    return False
