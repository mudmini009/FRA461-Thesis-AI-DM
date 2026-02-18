from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional

class Stat(Enum):
    PHYS = "PHYS"
    MENT = "MENT"
    SOC = "SOC"

class Zone(Enum):
    NEAR = "NEAR"
    MID = "MID"
    FAR = "FAR"

class Condition(Enum):
    NORMAL = "NORMAL"
    # INJURED = "INJURED"  <-- REMOVED per validaton request
    UNCONSCIOUS = "UNCONSCIOUS"
    DEAD = "DEAD"
    RESTRAINED = "RESTRAINED"
    PRONE = "PRONE"
    BLINDED = "BLINDED"
    STUNNED = "STUNNED"

@dataclass
class Character:
    id: str
    name: str
    role: str
    hp: int
    max_hp: int
    ac: int
    stats: Dict[Stat, int]
    zone: Zone = Zone.NEAR
    inventory: List[str] = field(default_factory=list)
    condition: Condition = Condition.NORMAL

    def take_damage(self, amount: int):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            # If already dead, stay dead. If not, go unconscious (or dead for NPCs generally)
            if self.condition != Condition.DEAD:
                self.condition = Condition.UNCONSCIOUS
        
        # NOTE: We no longer set 'INJURED' here. 
        # Condition is reserved for tactical states.

    def to_dict(self) -> Dict[str, any]:
        """
        Converts the Character object back to a dictionary for JSON storage.
        """
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "ac": self.ac,
            "stats": {k.name: v for k, v in self.stats.items()}, # Enum key -> String
            "zone": self.zone.name, # Enum -> String
            "inventory": self.inventory,
            "condition": self.condition.name # Enum -> String
        }

    def get_health_status(self) -> str:
        """
        Returns a narrative description of health for the LLM.
        """
        percent = self.hp / self.max_hp
        if percent == 1.0: return "Unscathed"
        if percent > 0.75: return "Scratched"
        if percent > 0.50: return "Injured"
        if percent > 0.25: return "Wounded"
        if percent > 0.0: return "Critical"
        return "Dead"

    def __str__(self):
        return f"Character(id: {self.id}, name: {self.name}, role: {self.role}, hp: {self.hp}/{self.max_hp}, condition: {self.condition.name}, zone: {self.zone.name})"
