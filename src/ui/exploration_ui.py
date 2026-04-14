"""
exploration_ui.py — Terminal dashboard for the Exploration and Hub phases.

Renders the current node, player health summary, available exits, and time.
Kept separate from combat dashboard (src/ui/dashboard.py) — no modifications there.
"""
from typing import List, Optional, Any, Dict
from src.models.character import Character, Condition


_EVENT_TYPE_BADGES = {
    "safe":    "🟢 SAFE",
    "combat":  "🔴 COMBAT",
    "boss":    "💀 BOSS",
    "puzzle":  "🟡 PUZZLE",
    "hub":     "🏠 HUB",
}

_PHASE_ICONS = {
    "Morning":   "🌅",
    "Afternoon": "☀️ ",
    "Evening":   "🌇",
    "Night":     "🌙",
}


def render_exploration_dashboard(
    party: List[Character],
    node: dict,
    global_state: Optional[Dict[str, Any]] = None,
    quest_name: str = "",
):
    """
    Renders a clean exploration-mode HUD to the terminal.

    Displays:
      - Quest + current node name + event type badge
      - Player HP / condition summary
      - Available exits (from connected_to)
      - Current time phase
    """
    print("\n" + "─" * 52)

    # ── Quest / Node Header ────────────────────────────────
    event_type = node.get("event_type", "safe")
    badge = _EVENT_TYPE_BADGES.get(event_type, f"[{event_type.upper()}]")
    node_name = node.get("name", "Unknown Location")
    if quest_name:
        print(f"  📍 {quest_name}")
    print(f"  🗺️  {node_name}  {badge}")

    # ── Time ──────────────────────────────────────────────
    if global_state:
        time_data = global_state.get("time", {})
        phase = time_data.get("phase", "Morning")
        icon = _PHASE_ICONS.get(phase, "⏰")
        day = time_data.get("day", 1)
        hour = time_data.get("hour", 8)
        print(f"  {icon} Day {day}, {hour:02d}:00 — {phase}")

    print("─" * 52)

    # ── Party Status ──────────────────────────────────────
    for p in party:
        if p.condition in [Condition.DEAD, Condition.UNCONSCIOUS]:
            status_icon = "💀"
        elif p.hp <= p.max_hp * 0.25:
            status_icon = "🩸"
        elif p.hp <= p.max_hp * 0.5:
            status_icon = "⚠️ "
        else:
            status_icon = "💚"

        # Abilities summary (short form)
        abilities_str = ""
        if p.abilities:
            ab_parts = [f"{a.name}({a.current_uses}/{a.max_uses})" for a in p.abilities]
            abilities_str = f"  | {', '.join(ab_parts)}"

        hp_bar = _make_hp_bar(p.hp, p.max_hp, width=10)
        print(f"  {status_icon} {p.name} [{p.role}] HP:{hp_bar} {p.hp}/{p.max_hp}{abilities_str}")

    print("─" * 52)

    # ── Available Exits ───────────────────────────────────
    connected = node.get("connected_to", [])
    if connected:
        # Try to show the names of connected nodes if they're in the quest data
        # (caller may not pass quest_data, so we just show IDs)
        exits_display = " | ".join(connected)
        print(f"  🚪 Exits: {exits_display}")
    else:
        print(f"  🚪 Exits: None — you are at a dead end.")

    print("─" * 52)


def render_hub_dashboard(
    party: List[Character],
    global_state: Optional[Dict[str, Any]] = None,
    available_quests: Optional[list] = None,
):
    """
    Renders the Hub (Adventurer's Guild) HUD.
    Shows player status, available quests, and quick commands.
    """
    print("\n" + "=" * 52)
    print("  🏠 THE ADVENTURER'S GUILD — Safe Haven")
    print("=" * 52)

    # ── Time ──────────────────────────────────────────────
    if global_state:
        time_data = global_state.get("time", {})
        phase = time_data.get("phase", "Morning")
        icon = _PHASE_ICONS.get(phase, "⏰")
        day = time_data.get("day", 1)
        hour = time_data.get("hour", 8)
        print(f"  {icon} Day {day}, {hour:02d}:00 — {phase}")

    print("─" * 52)

    # ── Party Status ──────────────────────────────────────
    for p in party:
        hp_bar = _make_hp_bar(p.hp, p.max_hp, width=12)
        abilities_str = ""
        if p.abilities:
            ab_parts = [f"{a.name}({a.current_uses}/{a.max_uses})" for a in p.abilities]
            abilities_str = f"\n    Abilities: {', '.join(ab_parts)}"
        print(f"  👤 {p.name} [{p.role}]")
        print(f"     HP: {hp_bar} {p.hp}/{p.max_hp}{abilities_str}")

    print("─" * 52)

    # ── Quest Board ───────────────────────────────────────
    if available_quests:
        print("  📋 QUEST BOARD:")
        for i, q in enumerate(available_quests, 1):
            print(f"    [{i}] {q['name']}")
            if q.get("description"):
                print(f"        {q['description'][:70]}...")
    else:
        print("  📋 QUEST BOARD: No quests available.")

    print("─" * 52)
    print("  Commands: QUEST BOARD | REST | STATUS | INVENTORY | QUIT")
    print("─" * 52)


def _make_hp_bar(current: int, maximum: int, width: int = 10) -> str:
    """Renders an ASCII HP bar: [████░░░░░░]"""
    if maximum <= 0:
        return "[" + "?" * width + "]"
    ratio = max(0.0, min(1.0, current / maximum))
    filled = int(round(ratio * width))
    empty = width - filled
    return "[" + "█" * filled + "░" * empty + "]"
