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
    
    def __init__(self, data_path: str = "data/campaign.json"):
        self.data_path = data_path

    def load_game(self, settings: Optional[Dict[str, Any]] = None) -> Tuple[List[Character], List[Character], Deque[str]]:
        """
        Loads the game state from the JSON file.
        Returns: (party_list, enemies_list, event_memory_deque)
        """
        if not settings:
            settings = self.load_settings()
        max_events = settings.get("memory", {}).get("max_history_events", 10)

        if not os.path.exists(self.data_path):
            print(f"❌ Error: Data file not found at {self.data_path}")
            return [], [], deque(maxlen=max_events)

        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                
            party_data = data.get("party", [])
            enemy_data = data.get("enemies", [])
            memory_data = data.get("event_memory", [])
            
            party = [self._create_char(c) for c in party_data]
            enemies = [self._create_char(c) for c in enemy_data]
            
            # Using deque automatically handles the rolling sliding window of max N events.
            event_memory = deque(memory_data, maxlen=max_events)
            
            return party, enemies, event_memory
            
        except Exception as e:
            print(f"❌ Error loading game data: {e}")
            return [], [], deque(maxlen=max_events)
            
    def save_game(self, party: List[Character], enemies: List[Character], event_memory: Optional[Deque[str]] = None):
        """
        Saves the current game state to the JSON file.
        Overwrites existing data.
        """
        data = {
            "party": [p.to_dict() for p in party],
            "enemies": [e.to_dict() for e in enemies],
            "event_memory": list(event_memory) if event_memory else []
        }
        
        try:
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=4)
            # print("💾 Game Saved.") # Optional log
        except Exception as e:
            print(f"❌ Error saving game data: {e}")

    @staticmethod
    def append_to_log(text: str, log_path: str = "data/campaign_log.txt"):
        """Appends a single line of narrative/action history to the continuous campaign log."""
        try:
            with open(log_path, 'a', encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not write to campaign log: {e}")

    @staticmethod
    def clear_log(log_path: str = "data/campaign_log.txt"):
        """Erases the continuous campaign log when starting a New Game/Resetting."""
        try:
            # Overwrite the file with emptiness
            with open(log_path, 'w', encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            pass

    @staticmethod
    def load_settings(filepath: str = "data/settings.json") -> Dict[str, Any]:
        """Loads configuration from JSON, with safe fallback defaults."""
        defaults = {
            "memory": {"max_history_events": 10},
            "engine": {"debug_mode": False, "default_dc": 10, "fuzzy_match_cutoff": 0.4},
            "llm": {"arbiter_model": "gemini-2.5-flash-lite", "narrator_model": "gemini-2.5-flash-lite", "arbiter_temperature": 0.3, "narrator_temperature": 0.7}
        }
        
        settings = {}
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    user_settings = json.load(f)
                
                # Merge defaults with user settings
                for category, options in defaults.items():
                    settings[category] = options.copy()
                    if category in user_settings and isinstance(user_settings[category], dict):
                        settings[category].update(user_settings[category])
            else:
                settings = defaults.copy()
                with open(filepath, 'w') as f:
                    json.dump(settings, f, indent=4)
                    
            return settings
            
        except Exception as e:
            print(f"   ⚠️ Error loading settings: {e}. Using defaults.")
            return defaults

    @staticmethod
    def load_lore(filepath: str = "data/world_lore.txt") -> str:
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
            condition=Condition.NORMAL # Default to normal on load
        )

if __name__ == "__main__":
    # Test Block
    dm = DataManager()
    p, e, m = dm.load_game()
    print(f"Loaded {len(p)} players and {len(e)} enemies. Memory events: {len(m)}")
    if p: print(f"Player 1: {p[0]}")
