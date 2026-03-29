import os
import shutil
import time
from src.ui.menu import main_menu, recap_menu, character_creation_menu, world_lore_menu, get_character_name
from src.services.data_manager import DataManager
from src.services.llm_service import LLMService
from src.models.character import Character, Stat, Zone, Condition

BACKUP_FILE = "data/campaign_backup.json"
ACTIVE_FILE = "data/campaign_active.json"
LOG_FILE = "data/campaign_log.txt"

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

def print_slow(text, delay=0.01):
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
    if char_mode == 'premade' and char_input in HARDCODED_ARCHETYPES:
        archetype = str(char_input)
    elif char_mode == 'custom':
        print("\n[System] Consulting LLM for Semantic Classification...")
        toon_out = llm_service.extract_character_stats(char_input)
        print(f"   [LLM Decoded]: {toon_out}")
        if 'archetype:' in toon_out:
            parts = toon_out.split('|')
            for p in parts:
                if p.startswith('archetype:'):
                     identified = str(p.split(':')[1].strip().lower())
                     if identified in HARDCODED_ARCHETYPES:
                         archetype = identified
    
    player_name = get_character_name()
    base_stats = HARDCODED_ARCHETYPES.get(archetype, HARDCODED_ARCHETYPES["fighter"])
    
    player = Character(
        id="player1",
        name=player_name,
        role=str(archetype).capitalize(),
        hp=base_stats["hp"],
        max_hp=base_stats["max_hp"],
        ac=base_stats["ac"],
        stats=base_stats["stats"],
        zone=Zone.NEAR,
        inventory=base_stats["inventory"],
        condition=Condition.NORMAL
    )

    # 3. World Lore
    lore_mode, lore_input = world_lore_menu()
    if lore_mode == 'custom':
        print("\n[System] Expanding World Lore...")
        world_lore = llm_service.expand_world_lore(lore_input)
        # Save custom lore
        with open("data/world_lore_custom.txt", "w", encoding="utf-8") as f:
            f.write(world_lore)
    else:
        world_lore = DataManager.load_lore()
        
    # 4. Prologue Generation
    print("\n[System] Generating Prologue (Cold Open)...")
    toon_char = f"name:{player.name}|class:{player.role}|hp:{player.hp}/{player.max_hp}"
    prologue_data = llm_service.generate_prologue(toon_char, world_lore)
    
    prologue_text = prologue_data.get("prologue", "You enter the dungeon... prepare for battle!")
    enemy_tag = prologue_data.get("enemy_type", "goblin").lower()
    
    if enemy_tag not in HARDCODED_BESTIARY:
        enemy_tag = "goblin"
        
    enemy_stats = HARDCODED_BESTIARY[enemy_tag]
    enemy = Character(
        id="e1",
        name=enemy_tag.capitalize(),
        role="Enemy",
        hp=enemy_stats["hp"],
        max_hp=enemy_stats["max_hp"],
        ac=enemy_stats["ac"],
        stats=enemy_stats["stats"],
        zone=Zone.NEAR,
        inventory=enemy_stats["inventory"],
        condition=Condition.NORMAL
    )
    
    # 5. Save Initial State
    dm = DataManager(ACTIVE_FILE)
    dm.save_game(party=[player], enemies=[enemy], combat_memory=None, story_memory=None)
    
    # Narrate the prologue
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 50)
    print_slow(prologue_text, 0.02)
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
