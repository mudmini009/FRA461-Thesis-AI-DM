
import sys
import os
import time
import shutil

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.engine.game_loop import start_combat_loop

BACKUP_FILE = "data/fibo_backup.json"
ACTIVE_FILE = "data/fibo_active.json"

BANNER = r"""
  ______ _____ ____   ____  
 |  ____|_   _|  _ \ / __ \ 
 | |__    | | | |_) | |  | |
 |  __|   | | |  _ <| |  | |
 | |     _| |_| |_) | |__| |
 |_|    |_____|____/ \____/ 
    INSTITUTE OF FIELD ROBOTICS
       AI DUNGEON MASTER
"""

NARRATIVE = [
    "Rumors spoke of a hidden AI treasure deep within the Institute of Field Robotics (FIBO) at KMUTT.",
    "You step into the glass elevator, pressing the button for the restricted top floor.",
    "The gears grind, the lights flicker, and the doors slide open to a forgotten, dimly lit laboratory.",
    "Amongst scattered drone parts and sparking wires, a massive rogue engineer stands guard over a blueprint.",
    "He notices you. The Senior Engineer cracks his knuckles, grabbing a heavy servo motor. It's time to fight!"
]

def print_slow(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print("⚠️  Type 'RESTART' at any time to reset the demo.")
        print("-" * 50)
        
        # 1. Reset Data
        try:
            shutil.copy(BACKUP_FILE, ACTIVE_FILE)
            print("[SYSTEM] 💾 Game Data Reset Successfully. Ready for new player.")
        except FileNotFoundError:
            print(f"❌ Error: Backup file {BACKUP_FILE} not found!")
            time.sleep(5)
            continue
            
        print("-" * 50)
        time.sleep(0.3)
        
        # 2. Play Narrative
        for line in NARRATIVE:
            print_slow(f"📜 {line}")
            time.sleep(0.5)
            
        print("\n[PRESS ENTER TO START COMBAT]")
        input()
        
        # 3. Launch Game Loop
        result = start_combat_loop(data_path=ACTIVE_FILE)
        
        # 4. Handle End Game
        if result == "EXIT":
            print("\n👋 Exiting Demo Launcher...")
            break
        elif result == "RESTART":
            print("\n🔄 Restarting Demo...")
            time.sleep(1)
            continue
        elif result == "VICTORY":
            print("\n🎉 Congratulations! The restricted floor is yours!")
            time.sleep(5)
        elif result == "DEFEAT":
            print("\n💀 Better luck next time, explorer.")
            time.sleep(5)
            
        print("\nResetting for next demo...")
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nlauncher terminated.")
