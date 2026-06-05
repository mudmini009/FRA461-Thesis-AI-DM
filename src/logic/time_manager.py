from typing import List, Dict, Any
from src.models.character import Character, RechargeType, Stat
import random

class TimeManager:
    """Handles time progression and ability logic during Short and Long rests."""

    @staticmethod
    def _update_phase(hour: int) -> str:
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    @staticmethod
    def apply_short_rest(party: List[Character], global_state: Dict[str, Any]) -> str:
        # Advance time by 1 hour
        time_data = global_state.setdefault("time", {"day": 1, "hour": 8, "phase": "Morning"})
        time_data["hour"] += 1
        if time_data["hour"] >= 24:
            time_data["hour"] = 0
            time_data["day"] += 1
        time_data["phase"] = TimeManager._update_phase(time_data["hour"])

        logs = []
        for p in party:
            # Full Heal (automatic fully heal, no dice rolling)
            old_hp = p.hp
            p.hp = p.max_hp
            actual_heal = p.hp - old_hp
            
            # Reset Short Rest abilities
            restored = []
            for a in p.abilities:
                if a.recharge_type == RechargeType.SHORT_REST and a.current_uses < a.max_uses:
                    a.current_uses = a.max_uses
                    restored.append(a.name)
            
            log = f"{p.name} takes a short rest, recovering {actual_heal} HP."
            if restored:
                log += f" Refreshed: {', '.join(restored)}."
            logs.append(log)
            
        return " ".join(logs)

    @staticmethod
    def apply_long_rest(party: List[Character], global_state: Dict[str, Any]) -> str:
        # Advance time by 8 hours
        time_data = global_state.setdefault("time", {"day": 1, "hour": 8, "phase": "Morning"})
        time_data["hour"] += 8
        if time_data["hour"] >= 24:
            time_data["hour"] = time_data["hour"] % 24
            time_data["day"] += 1
        time_data["phase"] = TimeManager._update_phase(time_data["hour"])

        logs = []
        for p in party:
            # Full Heal
            p.hp = p.max_hp
            
            # Reset ALL abilities
            restored = []
            for a in p.abilities:
                if a.current_uses < a.max_uses:
                    a.current_uses = a.max_uses
                    restored.append(a.name)
            
            log = f"{p.name} takes a long rest, returning to full health."
            if restored:
                log += f" All abilities refreshed."
            logs.append(log)
            
        return " ".join(logs)

    @staticmethod
    def advance_turn(global_state: Dict[str, Any]):
        global_state["turn_counter"] = global_state.get("turn_counter", 0) + 1
