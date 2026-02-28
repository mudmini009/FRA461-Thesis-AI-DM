from typing import List
from src.models.character import Character, Stat, Condition

def render_dashboard(party: List[Character], enemies: List[Character]):
    print("\n" + "─"*50)
    # Find the active player for Dashboard display (assuming 1 player for now)
    player = next((p for p in party if p.condition not in [Condition.DEAD, Condition.UNCONSCIOUS]), party[0])
    
    stats = f"PHYS:{player.stats.get(Stat.PHYS, 0)} MENT:{player.stats.get(Stat.MENT, 0)} SOC:{player.stats.get(Stat.SOC, 0)}"
    inventory = " | ".join(player.inventory)
    print(f"⚡ {player.name.upper()} | HP: {player.hp}/{player.max_hp} | Zone: {player.zone.name} | Cond: {player.condition.name}")
    print(f"   📊 Stats: {stats}")
    print(f"   🎒 Bag:   [{inventory}]")
    print("─"*50)
    print("TARGETS:")
    for e in enemies:
        if e.condition not in [Condition.DEAD]:
            status_icon = "👹" if e.role == "Monster" else "👽"
            health_status = e.get_health_status()
            print(f"   {status_icon} {e.name:<25} {health_status:<10} [{e.zone.name}] {e.condition.name if e.condition != Condition.NORMAL else ''}")
    print("─"*50)
