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
    INJURED = "INJURED"
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
            self.condition = Condition.UNCONSCIOUS
        elif self.hp < self.max_hp:
            self.condition = Condition.INJURED
        else:
            self.condition = Condition.NORMAL

    def __str__(self):
        return f"Character(id: {self.id}, name: {self.name}, role: {self.role}, hp: {self.hp}/{self.max_hp}, condition: {self.condition.name}, zone: {self.zone.name})"
