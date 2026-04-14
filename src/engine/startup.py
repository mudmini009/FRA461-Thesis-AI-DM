import os
import glob
import time
from src.ui.menu import main_menu, recap_menu
from src.ui.character_sheet import (
    clear_screen, print_slow,
    render_character_sheet, render_world_lore_preview,
)
from src.services.data_manager import DataManager
from src.services.llm_service import LLMService
from src.models.character import Character, Stat, Zone, Condition
import json

ACTIVE_FILE = "data/active/campaign_active.json"
LOG_FILE = "data/active/campaign_log.txt"
BESTIARY_FILE = "data/config/bestiary.json"
ACTIVE_LORE_FILE = "data/active/world_lore.txt"
PREMADE_CHAR_DIR = "data/premade/characters"
PREMADE_LORE_DIR = "data/premade/lore"

# ─────────────────────────────────────────────────────────────
#  HARDCODED MATH TEMPLATES – Python is the ONLY source of truth
#  for hp, ac, stats. Never let the LLM touch these.
# ─────────────────────────────────────────────────────────────
HARDCODED_ARCHETYPES = {
    "fighter": {"hp": 20, "max_hp": 20, "ac": 16, "stats": {Stat.PHYS: 3, Stat.MENT: 0, Stat.SOC: -1}, "inventory": ["Longsword", "Chainmail", "Healing Potion"]},
    "mage":    {"hp": 12, "max_hp": 12, "ac": 11, "stats": {Stat.PHYS: -1, Stat.MENT: 4, Stat.SOC: 0},  "inventory": ["Mana Potion", "Arcane Staff"]},
    "rogue":   {"hp": 15, "max_hp": 15, "ac": 14, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: 1},  "inventory": ["Smoke Bomb", "Twin Daggers"]},
    "cleric":  {"hp": 16, "max_hp": 16, "ac": 15, "stats": {Stat.PHYS: 1, Stat.MENT: 2, Stat.SOC: 1},  "inventory": ["Healing Potion", "Holy Mace"]},
    "ranger":  {"hp": 16, "max_hp": 16, "ac": 14, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: 0},  "inventory": ["Healing Potion", "Longbow"]},
    "paladin": {"hp": 18, "max_hp": 18, "ac": 17, "stats": {Stat.PHYS: 2, Stat.MENT: 1, Stat.SOC: 2},  "inventory": ["Healing Potion", "Holy Sword", "Shield"]},
}

HARDCODED_BESTIARY = {
    "goblin":  {"hp": 8,  "max_hp": 8,  "ac": 12, "stats": {Stat.PHYS: 1, Stat.MENT: -1, Stat.SOC: 0},  "inventory": ["Dirty Knife"]},
    "bandit":  {"hp": 12, "max_hp": 12, "ac": 11, "stats": {Stat.PHYS: 2, Stat.MENT: 0,  Stat.SOC: 1},  "inventory": ["Healing Potion", "Iron Sword"]},
    "skeleton":{"hp": 10, "max_hp": 10, "ac": 13, "stats": {Stat.PHYS: 1, Stat.MENT: -2, Stat.SOC: -2}, "inventory": ["Rusty Sword"]},
    "wolf":    {"hp": 11, "max_hp": 11, "ac": 13, "stats": {Stat.PHYS: 2, Stat.MENT: 1,  Stat.SOC: -2}, "inventory": []},
    "cultist": {"hp": 9,  "max_hp": 9,  "ac": 11, "stats": {Stat.PHYS: 0, Stat.MENT: 2,  Stat.SOC: 1},  "inventory": ["Dagger", "Strange Talisman"]},
}



# ─────────────────────────────────────────────────────────────
#  INTERNAL LOGIC HELPERS  (not rendering — stay in startup.py)
# ─────────────────────────────────────────────────────────────
def _load_cinematic_setting() -> bool:
    try:
        with open("data/config/settings.json", "r", encoding="utf-8") as f:
            return json.load(f).get("engine", {}).get("cinematic_print", True)
    except:
        return True

def _load_archetype_math(archetype: str) -> dict:
    """Always returns safe, hardcoded math. First tries premade JSON, falls back to HARDCODED_ARCHETYPES."""
    json_path = f"{PREMADE_CHAR_DIR}/{archetype}.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        converted = {}
        for k, v in raw.get("stats", {}).items():
            try:
                converted[Stat[k.upper()]] = v
            except KeyError:
                pass
        raw["stats"] = converted
        return raw
    return HARDCODED_ARCHETYPES.get(archetype, HARDCODED_ARCHETYPES["fighter"])





# ─────────────────────────────────────────────────────────────
#  PREMADE CHARACTER SELECTION (with Preview Loop)
# ─────────────────────────────────────────────────────────────
def _select_premade_character() -> tuple:
    """Returns (base_stats_dict, archetype_name) after user confirms a preview."""
    files = sorted(glob.glob(f"{PREMADE_CHAR_DIR}/*.json"))
    if not files:
        return None, "fighter"

    while True:
        clear_screen()
        print("=" * 58)
        print("   SELECT YOUR CLASS")
        print("=" * 58)
        for i, f in enumerate(files):
            name = os.path.basename(f).replace(".json", "").capitalize()
            print(f"   {i+1}. {name}")
        print("   0. Back")
        print("=" * 58)

        choice = input("Choose a class (number): ").strip()
        if choice == "0":
            return None, "fighter"
        if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
            continue

        selected_file = files[int(choice) - 1]
        archetype = os.path.basename(selected_file).replace(".json", "")

        with open(selected_file, "r", encoding="utf-8") as f:
            base_stats = json.load(f)

        math = _load_archetype_math(archetype)
        render_character_sheet(
            name="Your Hero",
            archetype=archetype,
            math=math,
            lore=base_stats.get("lore", ""),
        )
        print()
        print("   [1] Play as this class")
        print("   [2] Back to class list")
        print()
        confirm = input("   Choice: ").strip()
        if confirm == "1":
            return base_stats, archetype
        # else loop back


# ─────────────────────────────────────────────────────────────
#  CUSTOM CHARACTER GENERATION (Hybrid Engine + Edit Loop)
# ─────────────────────────────────────────────────────────────
def _generate_custom_character(llm_service: LLMService) -> tuple:
    """Returns (base_stats_dict, archetype_name, narrative_profile) after user confirms."""
    clear_screen()
    print("=" * 58)
    print("   CUSTOM CHARACTER CREATION")
    print("=" * 58)
    print("   Describe your character in a sentence or two.")
    print("   e.g. \"A blind monk who lost his sight in the shadow wars.\"")
    print("   e.g. \"An arrogant noble who dabbles in forbidden magic.\"")
    print("=" * 58)
    bio = input("\n   Your bio: ").strip()
    if not bio:
        bio = "A mysterious wanderer seeking purpose."

    edit_instructions = ""
    profile = None
    archetype = "fighter"

    while True:
        print("\n   ✦ Consulting the Fates...")
        profile = llm_service.generate_narrative_profile(bio, edit_instructions)
        archetype = profile.get("archetype_tag", "fighter")

        # Fallback if archetype doesn't have a template
        if archetype not in HARDCODED_ARCHETYPES and not os.path.exists(f"{PREMADE_CHAR_DIR}/{archetype}.json"):
            archetype = "fighter"

        math = _load_archetype_math(archetype)

        # Parse flavor trinkets
        raw_trinkets = profile.get("flavor_trinkets", "")
        trinkets = [t.strip() for t in raw_trinkets.split(",") if t.strip()] if raw_trinkets else []

        render_character_sheet(
            name=profile.get("name", "Hero"),
            archetype=archetype,
            math=math,
            title=profile.get("dynamic_title", ""),
            lore=profile.get("lore", ""),
            stat_justification=profile.get("stat_justification", ""),
            flavor_trinkets=trinkets
        )
        print()
        print("   [1] Accept & Continue")
        print("   [2] Reroll Narrative (same bio)")
        print("   [3] Edit Instructions")
        print("   [4] Cancel (choose premade)")
        print()
        action = input("   Choice: ").strip()

        if action == "1":
            # Merge: load base JSON, add narrative fields
            base_stats = _load_archetype_math(archetype).copy()
            base_stats["role"] = archetype.capitalize()
            base_stats["lore"] = profile.get("lore", "")
            base_stats["lore_raw"] = base_stats.get("lore", "")
            return base_stats, archetype, profile

        elif action == "2":
            edit_instructions = ""  # Pure reroll, same bio
            continue

        elif action == "3":
            clear_screen()
            print("   Tell the AI how to adjust the character.")
            print("   e.g. \"Make him use magic instead\" or \"Give her a tragic past\"")
            edit_instructions = input("\n   Edit instructions: ").strip()
            continue

        elif action == "4":
            return None, None, None  # Signal to fall back to premade


# ─────────────────────────────────────────────────────────────
#  WORLD LORE SELECTION (with Preview Loop)
# ─────────────────────────────────────────────────────────────
def _select_world_lore(llm_service: LLMService) -> str:
    """Returns the final world lore string after user confirms."""
    while True:
        clear_screen()
        print("=" * 58)
        print("   WORLD LORE")
        print("=" * 58)
        print("   1. Choose a Preset World")
        print("   2. Create a Custom World (AI Expands)")
        print("=" * 58)
        choice = input("   Choice: ").strip()

        if choice == "1":
            world_lore = _select_premade_lore()
            if world_lore:
                return world_lore

        elif choice == "2":
            world_lore = _generate_custom_lore(llm_service)
            if world_lore:
                return world_lore


def _select_premade_lore() -> str:
    files = sorted(glob.glob(f"{PREMADE_LORE_DIR}/*.txt"))
    if not files:
        return ""

    while True:
        clear_screen()
        print("=" * 58)
        print("   CHOOSE A PRESET WORLD")
        print("=" * 58)
        for i, f in enumerate(files):
            name = os.path.basename(f).replace(".txt", "").replace("_", " ").title()
            print(f"   {i+1}. {name}")
        print("   0. Back")
        print("=" * 58)
        choice = input("   Choose world (number): ").strip()
        if choice == "0":
            return ""
        if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
            continue

        selected = files[int(choice) - 1]
        with open(selected, "r", encoding="utf-8") as f:
            lore_text = f.read().strip()

        render_world_lore_preview(lore_text)
        print("   [1] Use this world")
        print("   [2] Back to world list")
        confirm = input("\n   Choice: ").strip()
        if confirm == "1":
            return lore_text


def _generate_custom_lore(llm_service: LLMService) -> str:
    clear_screen()
    print("=" * 58)
    print("   CREATE A CUSTOM WORLD")
    print("=" * 58)
    print("   Describe your world in a phrase or two.")
    print("   e.g. \"A cyberpunk city built on the ruins of a Thai kingdom.\"")
    print("=" * 58)
    concept = input("\n   Your concept: ").strip()
    if not concept:
        concept = "A dark fantasy world filled with ancient secrets."

    edit_instructions = ""

    while True:
        print("\n   ✦ The Worldbuilder is at work...")
        lore_text = llm_service.expand_world_lore(concept, edit_instructions)

        render_world_lore_preview(lore_text)
        print("   [1] Accept this world")
        print("   [2] Reroll (same concept)")
        print("   [3] Refine (add instructions)")
        print("   [4] Cancel (choose preset)")
        action = input("\n   Choice: ").strip()

        if action == "1":
            return lore_text
        elif action == "2":
            edit_instructions = ""
            continue
        elif action == "3":
            print("   e.g. \"Make it more cyberpunk\" or \"Add Thai mythology\"")
            edit_instructions = input("\n   Refinement: ").strip()
            continue
        elif action == "4":
            return ""  # Signal to fall back


# ─────────────────────────────────────────────────────────────
#  NAME PROMPT
# ─────────────────────────────────────────────────────────────
def _get_character_name(suggested_name: str = "") -> str:
    clear_screen()
    print("=" * 58)
    print("   NAME YOUR HERO")
    print("=" * 58)
    if suggested_name:
        print(f"   The AI suggests: \"{suggested_name}\"")
    print("   (Press Enter to accept the suggestion, or type a new name)")
    print("=" * 58)
    while True:
        name = input("\n   Name: ").strip()
        if not name and suggested_name:
            return suggested_name
        if name:
            return name
        print("   Name cannot be empty.")


# ─────────────────────────────────────────────────────────────
#  MAIN INITIALIZE NEW GAME
# ─────────────────────────────────────────────────────────────
def initialize_new_game(llm_service: LLMService) -> bool:
    DataManager.clear_log()

    # ── STEP 1: CHARACTER CREATION ────────────────────────────
    while True:
        clear_screen()
        print("=" * 58)
        print("   CHARACTER CREATION")
        print("=" * 58)
        print("   1. Choose a Premade Class")
        print("   2. Describe a Custom Character (AI Crafts Your Destiny)")
        print("=" * 58)
        char_choice = ""
        while char_choice not in ["1", "2"]:
            char_choice = input("   Choice: ").strip()

        narrative_profile = {}
        if char_choice == "1":
            base_stats, archetype = _select_premade_character()
            if base_stats: break # Success
        else:
            base_stats, archetype, narrative_profile = _generate_custom_character(llm_service)
            if base_stats: break # Success

    # Ensure archetype math is always loaded from safe source
    math = _load_archetype_math(archetype)

    # ── STEP 2: NAME ──────────────────────────────────────────
    suggested_name = narrative_profile.get("name", "") if narrative_profile else ""
    player_name = _get_character_name(suggested_name)

    # ── STEP 3: BUILD PLAYER CHARACTER (Hybrid Merge) ─────────
    # Math always comes from Python. Lore always comes from the profile or JSON.
    lore_str = narrative_profile.get("lore", base_stats.get("lore", ""))
    title_str = narrative_profile.get("dynamic_title", "")
    stat_just_str = narrative_profile.get("stat_justification", "")
    raw_trinkets = narrative_profile.get("flavor_trinkets", "") if narrative_profile else ""
    trinkets = [t.strip() for t in raw_trinkets.split(",") if t.strip()] if raw_trinkets else []

    # Mechanical inventory from JSON + flavor trinkets appended
    full_inventory = list(math.get("inventory", []))
    full_inventory.extend(trinkets)

    converted_stats = {k: v for k, v in math.get("stats", {}).items()}

    player = Character(
        id="player1",
        name=player_name,
        role=archetype.capitalize(),
        hp=math.get("hp", 20),
        max_hp=math.get("max_hp", 20),
        ac=math.get("ac", 10),
        stats=converted_stats,
        zone=Zone.NEAR,
        inventory=full_inventory,
        condition=Condition.NORMAL,
        lore=lore_str,
        title=title_str,
        stat_justification=stat_just_str
    )

    # ── STEP 4: FINAL CHARACTER SHEET CONFIRMATION ────────────
    render_character_sheet(
        name=player.name,
        archetype=archetype,
        math=math,
        title=title_str,
        lore=lore_str,
        stat_justification=stat_just_str,
        flavor_trinkets=trinkets
    )
    print()
    print("   ✦ Your character is ready.")
    input("   [Press Enter to choose your world...")

    # ── STEP 5: WORLD LORE ────────────────────────────────────
    world_lore = _select_world_lore(llm_service)
    if not world_lore:
        # Absolute fallback
        try:
            with open(f"{PREMADE_LORE_DIR}/classic_fantasy.txt", "r", encoding="utf-8") as f:
                world_lore = f.read().strip()
        except:
            world_lore = "### Atmosphere & Setting\nA dark world of ancient ruin and forgotten gods.\n\n### Key Factions\nThe Empire and the Rebel Underground fight for the surface.\n\n### Magic & Technology\nMagic is rare and unstable; technology is crude iron.\n\n### Looming Threat\nA great darkness stirs beneath the earth."

    with open(ACTIVE_LORE_FILE, "w", encoding="utf-8") as f:
        f.write(world_lore)

    # ── STEP 6: PROLOGUE GENERATION ───────────────────────────
    clear_screen()
    print("=" * 58)
    print("   ✦ The Dungeon Master is setting the stage...")
    print("=" * 58)
    toon_char = f"Name: {player.name}\nClass: {player.role}\nTitle: {title_str}\nBackground: {lore_str or 'A brave adventurer.'}\nStats: {player.stats}"
    prologue_data = llm_service.generate_prologue(toon_char, world_lore)

    prologue_text = prologue_data.get("prologue", "You enter the dungeon... prepare for battle!")
    for placeholder in ["[Character Name]", "[character name]", "[Name]", "[name]", "[PLAYER]"]:
        prologue_text = prologue_text.replace(placeholder, player.name)

    enemy_tag = prologue_data.get("enemy_type", "goblin").lower()

    # ── STEP 7: ENEMY PROVISIONING ────────────────────────────
    if not os.path.exists(BESTIARY_FILE):
        with open(BESTIARY_FILE, "w") as f:
            json.dump({"goblin": {"hp": 8, "max_hp": 8, "ac": 12, "stats": {"PHYS": 1, "MENT": -1, "SOC": 0}, "inventory": []}}, f)

    with open(BESTIARY_FILE, "r", encoding="utf-8") as f:
        bestiary = json.load(f)

    if enemy_tag not in bestiary:
        enemy_tag = list(bestiary.keys())[0] if bestiary else "goblin"

    enemy_stats = bestiary.get(enemy_tag, {})
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

    # ── STEP 8: SAVE STATE ────────────────────────────────────
    dm = DataManager(ACTIVE_FILE)
    DataManager.append_to_log("[PROLOGUE]")
    DataManager.append_to_log(prologue_text.replace('\\n', '\n'))
    DataManager.append_to_log("[END PROLOGUE]\n")
    dm.save_game(party=[player], enemies=[enemy], combat_memory=None, story_memory=None)

    # ── STEP 9: NARRATE THE PROLOGUE ─────────────────────────
    cinematic = _load_cinematic_setting()
    clear_screen()
    print("=" * 50)
    print_slow(prologue_text.replace('\\n', '\n'), delay=0.005, cinematic=cinematic)
    print("=" * 50)
    print("\n[PRESS ENTER TO START COMBAT]")
    input()
    return True


# ─────────────────────────────────────────────────────────────
#  CONTINUE FLOW
# ─────────────────────────────────────────────────────────────
def run_continue_flow(llm_service: LLMService) -> bool:
    if not os.path.exists(ACTIVE_FILE):
        print("No active save found! Returning to main menu.")
        time.sleep(2)
        return False

    do_recap = recap_menu()
    if do_recap:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = f.readlines()
            if logs:
                print("\n[System] Generating Recap...")
                recap_text = llm_service.generate_recap(logs)
                clear_screen()
                print("=" * 50)
                print("PREVIOUSLY ON YOUR ADVENTURE:")
                cinematic = _load_cinematic_setting()
                print_slow(recap_text, delay=0.005, cinematic=cinematic)
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


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
def run_startup() -> tuple:
    """
    Main entry point for the pre-game flow.
    Returns: (ready: bool, mode: str)
      mode can be: 'hub' | 'continue' | 'quick_battle'
    """
    try:
        llm = LLMService()
    except Exception as e:
        print(f"Error loading LLM: {e}")
        return False, "exit"

    while True:
        choice = main_menu()
        if choice == "new":
            if initialize_new_game(llm):
                return True, "hub"
        elif choice == "continue":
            if run_continue_flow(llm):
                return True, "continue"
        elif choice == "quick_battle":
            # Quick battle: just ensure there's a valid save, then return dev mode
            if not os.path.exists(ACTIVE_FILE):
                print("\n⚠️  No save file found for Quick Battle. Starting a new game first...")
                if initialize_new_game(llm):
                    return True, "quick_battle"
            else:
                return True, "quick_battle"
        elif choice == "exit":
            return False, "exit"
    return False, "exit"
