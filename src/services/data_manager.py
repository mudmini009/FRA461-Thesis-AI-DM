import json
import os
import sys
sys.path.append(os.getcwd()) # Ensure root is in path for standalone execution
from typing import Tuple, List, Dict, Any, Deque, Optional
from collections import deque
from src.models.character import Character, Stat, Zone, Condition

class DataManager:
    """
    Service to handle data loading and persistence for the AI Dungeon Master.
    Responsibility: Read JSON, Convert Types (Strings -> Enums), Return Objects.
    """
    _log_buffer: List[str] = []
    
    def __init__(self, data_path: str = "data/active/campaign_active.json"):
        self.data_path = data_path

    def load_game(self, settings: Optional[Dict[str, Any]] = None) -> Tuple[List[Character], List[Character], Deque[str], Deque[str]]:
        """
        Loads the game state from the JSON file.
        Returns: (party_list, enemies_list, combat_memory_deque, story_memory_deque)
        """
        if not settings:
            settings = self.load_settings()
        max_combat = settings.get("memory", {}).get("max_combat_events", 10)
        max_story = settings.get("memory", {}).get("max_story_events", 5)

        if not os.path.exists(self.data_path):
            print(f"❌ Error: Data file not found at {self.data_path}")
            return [], [], deque(maxlen=max_combat), deque(maxlen=max_story)

        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                
            party_data = data.get("party", [])
            enemy_data = data.get("enemies", [])
            combat_data = data.get("combat_memory",  data.get("event_memory", [])) # Fallback if migrating
            story_data = data.get("story_memory", [])
            
            party = [self._create_char(c) for c in party_data]
            enemies = [self._create_char(c) for c in enemy_data]
            
            # Using deque automatically handles the rolling sliding window of max N events.
            combat_memory = deque(combat_data, maxlen=max_combat)
            story_memory = deque(story_data, maxlen=max_story)
            
            return party, enemies, combat_memory, story_memory
            
        except Exception as e:
            print(f"❌ Error loading game data: {e}")
            return [], [], deque(maxlen=max_combat), deque(maxlen=max_story)
            
    def save_game(self, party: List[Character], enemies: List[Character], combat_memory: Optional[Deque[str]] = None, story_memory: Optional[Deque[str]] = None):
        """
        Saves the current game state to the JSON file.
        Overwrites existing data.
        """
        data = {
            "party": [p.to_dict() for p in party],
            "enemies": [e.to_dict() for e in enemies],
            "combat_memory": list(combat_memory) if combat_memory else [],
            "story_memory": list(story_memory) if story_memory else []
        }
        
        try:
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic Sync: Flush log text alongside JSON state
            DataManager.flush_log()
        except Exception as e:
            print(f"❌ Error saving game data: {e}")

    @staticmethod
    def append_to_log(text: str, log_path: str = "data/active/campaign_log.txt"):
        """Buffers a single line of narrative history to be atomically written during the next save."""
        DataManager._log_buffer.append(text)

    @staticmethod
    def flush_log(log_path: str = "data/active/campaign_log.txt"):
        """Atomically appends buffered logs to disk and forces OS sync to prevent parity desync."""
        if not DataManager._log_buffer:
            return
        try:
            with open(log_path, 'a', encoding="utf-8") as f:
                for text in DataManager._log_buffer:
                    f.write(text + "\n")
                f.flush()
                os.fsync(f.fileno())
            DataManager._log_buffer.clear()
        except Exception as e:
            print(f"   ⚠️ Warning: Could not write to campaign log: {e}")

    @staticmethod
    def clear_log(log_path: str = "data/active/campaign_log.txt"):
        """Erases the continuous campaign log when starting a New Game/Resetting."""
        DataManager._log_buffer.clear()
        try:
            with open(log_path, 'w', encoding="utf-8") as f:
                f.write("")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            pass

    @staticmethod
    def load_settings(filepath: str = "data/config/settings.json") -> Dict[str, Any]:
        """Loads configuration from JSON. If missing, clones from backup or uses defaults."""
        backup_path = "data/config/settings_backup.json"
        defaults = {
            "memory": {"max_combat_events": 10, "max_story_events": 5},
            "engine": {"debug_mode": False, "default_dc": 10, "fuzzy_match_cutoff": 0.4},
            "llm": {"arbiter_model": "gemini-2.5-flash-lite", "narrator_model": "gemini-2.5-flash-lite", "arbiter_temperature": 0.3, "narrator_temperature": 0.7}
        }
        
        # 1. Self-Healing: If settings.json is missing, try to clone from backup
        if not os.path.exists(filepath):
            if os.path.exists(backup_path):
                print(f"🔧 Settings missing. Cloning from {backup_path}...")
                try:
                    import shutil
                    shutil.copy2(backup_path, filepath)
                except Exception as e:
                    print(f"⚠️ Warning: Could not clone settings backup: {e}")
            else:
                # Absolute fallback: Create from hardcoded defaults
                print(f"🔨 No settings and no backup found. Regenerating defaults...")
                try:
                    with open(filepath, 'w') as f:
                        json.dump(defaults, f, indent=4)
                except Exception as e:
                    print(f"⚠️ Warning: Could not create default settings: {e}")

        # 2. Load the file
        settings = {}
        try:
            with open(filepath, 'r') as f:
                user_settings = json.load(f)
            
            # Merge defaults with user settings to ensure missing keys stay valid
            for category, options in defaults.items():
                settings[category] = options.copy()
                if category in user_settings and isinstance(user_settings[category], dict):
                    settings[category].update(user_settings[category])
                    
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {e}. Using defaults.")
            settings = defaults
            
        return settings

    @staticmethod
    def load_lore(filepath: str = "data/active/world_lore.txt") -> str:
        """Loads world building text for the LLM narrator."""
        try:
            with open(filepath, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "A generic dark fantasy world filled with dangerous monsters."
        except Exception as e:
            print(f"   [DEBUG] Error loading lore from {filepath}: {e}")
            return "A generic dark fantasy world filled with dangerous monsters."

    def _create_char(self, data: Dict[str, Any]) -> Character:
        """
        Helper to convert raw JSON dictionary into a strongly-typed Character object.
        CRITICAL: Converts 'stats' keys and 'zone' values to Enums.
        """
        
        # 1. Convert Stats (String keys -> Enum keys)
        # JSON: {"PHYS": 3, "MENT": 0} -> Python: {Stat.PHYS: 3, Stat.MENT: 0}
        raw_stats = data.get("stats", {})
        converted_stats = {}
        
        for key, value in raw_stats.items():
            try:
                # Stat["PHYS"] -> Stat.PHYS
                stat_enum = Stat[key.upper()] 
                converted_stats[stat_enum] = value
            except KeyError:
                print(f"⚠️ Warning: Invalid stat key '{key}' in character {data.get('name')}")

        # 2. Convert Zone (String value -> Enum value)
        # JSON: "NEAR" -> Python: Zone.NEAR
        raw_zone = data.get("zone", "NEAR")
        try:
            zone_enum = Zone[raw_zone.upper()]
        except KeyError:
            zone_enum = Zone.NEAR # Default fallback

        # 3. Create Object
        return Character(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown"),
            role=data.get("role", "Commoner"),
            hp=data.get("hp", 10),
            max_hp=data.get("max_hp", 10),
            ac=data.get("ac", 10),
            stats=converted_stats,
            zone=zone_enum,
            inventory=data.get("inventory", []),
            condition=Condition.NORMAL, # Default to normal on load
            lore=data.get("lore", ""),
            title=data.get("title", ""),
            stat_justification=data.get("stat_justification", "")
        )

if __name__ == "__main__":
    # Test Block
    dm = DataManager()
    p, e, cm, sm = dm.load_game()
    print(f"Loaded {len(p)} players and {len(e)} enemies. Memory events: {len(cm)}")
    if p: print(f"Player 1: {p[0]}")
