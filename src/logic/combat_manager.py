import random
from typing import List, Optional
from src.models.character import Character, Stat, Condition

class InitiativeQueue:
    """
    Manages turn order in combat by rolling initiative for all combatants
    and cycling through them queue-style.
    """
    def __init__(self, party: List[Character], enemies: List[Character]):
        self.combatants = party + enemies
        self.queue: List[Character] = []
        self.round_number = 1
        self.current_index = 0
        self._roll_initiative()

    def _roll_initiative(self):
        """Rolls 1d20 + PHYS bonus for all combatants and sorts them."""
        initiatives = []
        for char in self.combatants:
            # We'll use PHYS bonus for initiative for now in 5e Lite
            bonus = char.stats.get(Stat.PHYS, 0)
            roll = random.randint(1, 20) + bonus
            initiatives.append((char, roll))
            
        # Sort descending by roll
        initiatives.sort(key=lambda x: x[1], reverse=True)
        
        # Build pure queue
        self.queue = [char for char, _ in initiatives]
        self.current_index = 0
        
        # Reset turn for the first actor
        if self.queue:
            self.queue[0].reset_turn()
        
        print("\n🎲 --- INITIATIVE ORDER --- 🎲")
        for i, (char, roll) in enumerate(initiatives):
            print(f"{i+1}. {char.name} ({roll})")
        print("----------------------------\n")

    def get_current_actor(self) -> Optional[Character]:
        """Returns the character whose turn it currently is."""
        if not self.queue:
            return None
            
        return self.queue[self.current_index]

    def advance_turn(self):
        """Moves to the next character in the queue."""
        if not self.queue:
            return
            
        self.current_index += 1
        
        # If we reached the end of the queue, reset to top and advance round
        if self.current_index >= len(self.queue):
            self.current_index = 0
            self.round_number += 1
            print(f"\n🔄 --- ROUND {self.round_number} --- 🔄\n")
            
        # Check if the next actor is dead/unconscious. If so, skip their turn.
        next_actor = self.get_current_actor()
        if next_actor and next_actor.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
            self.advance_turn() # Recursively skip until we find someone awake
        elif next_actor:
            next_actor.reset_turn()

    def is_combat_over(self) -> bool:
        """
        Combat is over if all party members are dead, or all enemies are dead.
        Using roles 'Hero' vs 'Monster'/'Villain'.
        """
        # In this prototype, party members are 'Fighter', 'Rogue', etc. (not 'Monster'/'Villain')
        
        party_alive = False
        enemies_alive = False
        
        for char in self.combatants:
            if char.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]:
                if char.role.lower() in ['monster', 'villain', 'robotics engineer']: # Added engineer for demo
                    enemies_alive = True
                else:
                    party_alive = True
                    
        return not (party_alive and enemies_alive)
