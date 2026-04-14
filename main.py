import sys
import os
import time
import shutil

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.engine.game_loop import start_combat_loop, start_hub_loop
from src.engine.startup import run_startup, ACTIVE_FILE
from src.services.data_manager import DataManager

BANNER = r"""
  ___ _____   ___  _   _ _  _  ___ ___ ___  _  _   __  __   _   ___ _____ ___ ___ 
 /_\ |_   _| |   \| | | | \| |/ __| __/ _ \| \| | |  \/  | /_\ / __|_   _| __| _ \
/ _ \  | |   | |) | |_| | .` | (_ | _| (_) | .` | | |\/| |/ _ \\__ \ | | | _||   /
/_/ \_\|_|   |___/ \___/|_|\_|\___|___\___/|_|\_| |_|  |_/_/ \_\___/ |_| |___|_|_\
                AI DUNGEON MASTER (PHASE 3: MAIN PRODUCTION)
"""


def check_api_setup():
    """First-Time Boot Wizard: Ensures API key exists before crashing."""
    from dotenv import load_dotenv
    load_dotenv()
    
    if "GEMINI_API_KEY" not in os.environ:
        print("\n" + "="*50)
        print("🚨 FIRST TIME SETUP: Missing Gemini API Key! 🚨")
        print("="*50)
        print("It looks like you don't have a Gemini API key set up.")
        print("(Get one for free at: https://aistudio.google.com/app/apikey)\n")
        
        while True:
            api_key = input("Please paste your API key here: ").strip()
            if api_key:
                try:
                    with open(".env", "a") as f:
                        f.write(f"\nGEMINI_API_KEY={api_key}\n")
                    os.environ["GEMINI_API_KEY"] = api_key
                    print("\n✅ API Key saved to .env!")
                    time.sleep(1)
                    break
                except Exception as e:
                    print(f"❌ Failed to write to .env: {e}")
                    sys.exit(1)
            else:
                print("Key cannot be empty. Please try again.")

def main():
    check_api_setup()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print("\u26a0️  Type 'QUIT' at any time to save and exit.")
        print("-" * 50)

        # 1. Run Pre-Game Flow (menu + character creation)
        ready, mode = run_startup()
        if not ready:
            print("\n👋 Exiting Game...")
            break

        # 2. Route based on selected mode
        if mode == "quick_battle":
            # Quick Battle: bypass Hub, drop directly into combat (dev shortcut)
            print("\n🔥 [QUICK BATTLE] Launching direct combat...")
            result = start_combat_loop(data_path=ACTIVE_FILE)
        else:
            # Default: New Campaign or Continue → Hub Loop
            result = start_hub_loop(data_path=ACTIVE_FILE)

        # 3. Handle End State
        if result == "EXIT":
            print("\n👋 Exiting Game...")
            break
        elif result == "RESTART":
            print("\n🔄 Restarting Game...")
            time.sleep(1)
            continue
        elif result == "VICTORY":
            print("\n🎉 Congratulations! You have conquered the dungeon!")
            time.sleep(5)
        elif result == "DEFEAT":
            print("\n💀 Your journey ends here. Better luck next time, hero.")
            time.sleep(5)

        print("\nReturning to main menu...")
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated.")
