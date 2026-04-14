import os
import json
import glob

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(title: str):
    clear_screen()
    print("=" * 50)
    print(f" {title.center(48)} ")
    print("=" * 50)

def main_menu() -> str:
    draw_header("MAIN MENU")
    print("1. Start New Campaign    (Hub → Quest Board → Dungeon)")
    print("2. Continue Campaign     (Resume from your last save)")
    print("3. Quick Battle          (Dev mode: skip Hub, fight now)")
    print("4. Exit")
    print("-" * 50)

    while True:
        choice = input("Select an option (1-4): ").strip()
        if choice == '1': return 'new'
        if choice == '2': return 'continue'
        if choice == '3': return 'quick_battle'
        if choice == '4': return 'exit'
        print("Invalid choice. Try again.")
    return 'exit'

def recap_menu() -> bool:
    draw_header("CONTINUE JOURNEY")
    print("Save file found.")
    print("Would you like the AI to summarize your previous adventure?")
    print("-" * 50)
    
    while True:
        choice = input("Generate Recap? (Y/N): ").strip().lower()
        if choice in ['y', 'yes', '1']: return True
        if choice in ['n', 'no', '0']: return False
        print("Invalid choice. Try again.")
    return False

def character_creation_menu() -> tuple[str, str]:
    draw_header("CHARACTER CREATION")
    print("1. Select Pre-Made Class (Fast)")
    print("2. Write Custom Biography (AI Extracts Stats)")
    print("-" * 50)
    
    char_type = ""
    while True:
        choice = input("Select an option (1-2): ").strip()
        if choice == '1':
            char_type = 'premade'
            break
        if choice == '2':
            char_type = 'custom'
            break
        print("Invalid choice. Try again.")
        
    if char_type == 'premade':
        print("\nAvailable Pre-Made Templates:")
        files = glob.glob("data/premade/characters/*.json")
        for i, f in enumerate(files):
            basename = os.path.basename(f).replace('.json', '')
            print(f"{i+1}. {basename.capitalize()}")
        
        while True:
            choice = input(f"Choose your class (1-{len(files)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                selected_file = files[int(choice)-1]
                return ('premade', selected_file)
            print("Invalid choice. Try again.")
    else:
        print("\nDescribe your character (e.g., 'A frail but brilliant wizard looking for ancient knowledge').")
        bio = input("Bio: ").strip()
        return ('custom', bio)
    return ('premade', 'fighter')

def world_lore_menu() -> tuple[str, str]:
    draw_header("WORLD LORE")
    print("1. Use Default World Lore")
    print("2. Create Custom World Concept (AI Expands)")
    print("-" * 50)
    
    while True:
        choice = input("Select an option (1-2): ").strip()
        if choice == '1':
            print("\nAvailable Lore Templates:")
            files = glob.glob("data/premade/lore/*.txt")
            if not files:
                print("No lore templates found. Returning to default.")
                return ('default', "")
            for i, f in enumerate(files):
                basename = os.path.basename(f).replace('.txt', '').replace('_', ' ')
                print(f"{i+1}. {basename.title()}")
            
            while True:
                subchoice = input(f"Choose lore (1-{len(files)}): ").strip()
                if subchoice.isdigit() and 1 <= int(subchoice) <= len(files):
                    selected_file = files[int(subchoice)-1]
                    return ('file', selected_file)
                print("Invalid choice. Try again.")
                
        if choice == '2':
            print("\nEnter a short concept (e.g., 'A grimdark floating city ruled by vampires').")
            concept = input("Concept: ").strip()
            return ('custom', concept)
        print("Invalid choice. Try again.")
    return ('default', "")

def get_character_name() -> str:
    draw_header("NAME YOUR HERO")
    while True:
        name = input("Enter character name: ").strip()
        if name:
             return name
        print("Name cannot be empty.")
    return "Hero"
