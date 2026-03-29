from typing import List, Dict, Any
import sys
import os
sys.path.append(os.getcwd())
from src.models.character import Character, Stat

class TOONConverter:
    """
    Converts Game State objects into TOON (Token-Oriented Object Notation) strings.
    Ref: Thesis Section 3.3.1 - Reduces token usage by ~40% vs JSON.
    Standard: key[N]{columns}: followed by CSV-style rows.
    """
    
    @staticmethod
    def convert(players: List[Character], enemies: List[Character]) -> str:
        toon_output = []
        
        # --- 1. CONVERT PLAYERS ---
        # TOON Format: players[N]{id,name,role,hp,zone,phys,ment,soc,items}:
        if players:
            # Header with Length [N] and Fields {x,y,z}
            header = f"players[{len(players)}]{{id,name,role,hp,zone,phys,ment,soc,items}}:"
            toon_output.append(header)
            
            for p in players:
                # Inventory: Flatten list to [Item|Item] string
                items = f"[{'|'.join(p.inventory)}]" if p.inventory else "[]"
                
                # Stats: Force sign formatting (+3, -1)
                phys = f"{p.stats.get(Stat.PHYS, 0):+d}"
                ment = f"{p.stats.get(Stat.MENT, 0):+d}"
                soc =  f"{p.stats.get(Stat.SOC, 0):+d}"
                
                # CSV-style Row
                line = f"  {p.id},{p.name},{p.role},{p.hp}/{p.max_hp},{p.zone.name},{phys},{ment},{soc},{items}"
                toon_output.append(line)
            
            toon_output.append("") # Spacer

        # --- 2. CONVERT ENEMIES ---
        # TOON Format: enemies[N]{id,name,hp,zone,condition}:
        if enemies:
            header = f"enemies[{len(enemies)}]{{id,name,hp,zone,condition}}:"
            toon_output.append(header)
            
            for e in enemies:
                # CSV-style Row
                line = f"  {e.id},{e.name},{e.hp}/{e.max_hp}({e.get_health_status()}),{e.zone.name},{e.condition.name}"
                toon_output.append(line)

        return "\n".join(toon_output)

    @staticmethod
    def decode(toon_string: str) -> Dict[str, Any]:
        """
        Parses a 1-line TOON output string back into a Python dictionary.
        Expected format: key:value|key2:value2
        Handles basic arrays (e.g. action_order:[MOVE,ATTACK])
        """
        result: Dict[str, Any] = {}
        if not toon_string or not isinstance(toon_string, str):
            return result
            
        # Clean up Markdown artifacts if LLM accidentally wrapped it
        toon_string = toon_string.replace('```text', '').replace('```', '').strip()
        
        # Split by the primary delimiter |
        pairs = toon_string.split('|')
        
        for pair in pairs:
            if ':' not in pair:
                continue
                
            key, val = pair.split(':', 1)
            key = key.strip().strip('"').strip("'").lower()
            val = val.strip().strip('"').strip("'")
            
            # Handle Nulls
            if val.lower() == 'null' or val == '':
                result[key] = None
                continue
                
            # Handle Booleans
            if val.lower() == 'true':
                result[key] = True
                continue
            if val.lower() == 'false':
                result[key] = False
                continue
                
            # Handle Integers (e.g. dc: 15)
            if val.isdigit():
                result[key] = int(val)
                continue
                
            # Handle Arrays (e.g. action_order:[MOVE,ATTACK] or [MOVE, ATTACK])
            if val.startswith('[') and val.endswith(']'):
                # remove brackets
                inner = val[1:-1].strip()
                if not inner:
                    result[key] = []
                else:
                    # split by comma, strip spaces and quotes from elements
                    arr = [item.strip().strip('"').strip("'") for item in inner.split(',')]
                    result[key] = arr
                continue
                
            # String fallback
            result[key] = val
            
        return result

if __name__ == "__main__":
    # Internal Test
    from src.models.character import Character, Stat, Zone, Condition
    p1 = Character("p1", "Valen", "Fighter", 20, 20, 16, {Stat.PHYS: 3, Stat.MENT: 0, Stat.SOC: 1}, inventory=["Sword"])
    print("--- TOON OUTPUT PREVIEW ---")
    print(TOONConverter.convert([p1], []))
