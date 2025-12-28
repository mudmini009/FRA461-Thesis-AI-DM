from dataclasses import dataclass, field
from typing import List
from src.models.character import Character

@dataclass
class GameState:
    players: List[Character]
    enemies: List[Character]
    turn_count: int = 0
    logs: List[str] = field(default_factory=list)

    def __str__(self):
        return f"GameState(turn: {self.turn_count}, players: {len(self.players)}, enemies: {len(self.enemies)})"
