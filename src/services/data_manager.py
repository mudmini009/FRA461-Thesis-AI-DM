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

    def load_game(self) -> Tuple[List[Character], List[Character], Deque[str]]:
        """
        Loads the game state from the JSON file.
        Returns: (party_list, enemies_list, event_memory_deque)
        """
        if not os.path.exists(self.data_path):
            print(f"❌ Error: Data file not found at {self.data_path}")
            return [], [], deque(maxlen=10)

        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                
            party_data = data.get("party", [])
            enemy_data = data.get("enemies", [])
            memory_data = data.get("event_memory", [])
            
            party = [self._create_char(c) for c in party_data]
            enemies = [self._create_char(c) for c in enemy_data]
            
            # Using deque automatically handles the rolling sliding window of max 10 events.
            event_memory = deque(memory_data, maxlen=10)
            
            return party, enemies, event_memory
            
        except Exception as e:
            print(f"❌ Error loading game data: {e}")
            return [], [], deque(maxlen=10)
            
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
