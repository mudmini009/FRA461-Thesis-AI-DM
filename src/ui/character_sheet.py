"""
src/ui/character_sheet.py

Pure TUI rendering utilities for character and world lore display.
No logic — only terminal output.

Exported:
  - clear_screen()
  - print_slow()
  - render_character_sheet()
  - render_world_lore_preview()
"""
import os
import time
from src.models.character import Stat


# ─────────────────────────────────────────────────────────────
#  Terminal Utilities
# ─────────────────────────────────────────────────────────────
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_slow(text: str, delay: float = 0.005, cinematic: bool = True):
    """
    Prints text character-by-character when cinematic=True.
    Set cinematic=False (via data/config/settings.json engine.cinematic_print)
    for instant output during backend/testing runs.
    """
    if cinematic:
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    else:
        print(text)


# ─────────────────────────────────────────────────────────────
#  Stat Formatting
# ─────────────────────────────────────────────────────────────
def _stat_label(stat: Stat, value: int) -> str:
    sign = "+" if value >= 0 else ""
    return f"{stat.name} {sign}{value}"


def render_stat_block(archetype_data: dict) -> str:
    parts = [_stat_label(s, v) for s, v in archetype_data.get("stats", {}).items()]
    return "  |  ".join(parts) if parts else "(no stats)"


# ─────────────────────────────────────────────────────────────
#  Character Sheet Renderer
# ─────────────────────────────────────────────────────────────
def render_character_sheet(
    name: str,
    archetype: str,
    math: dict,
    title: str = "",
    lore: str = "",
    stat_justification: str = "",
    flavor_trinkets: list = [],
):
    """Renders a D&D-style Character Sheet to the terminal."""
    clear_screen()

    display_class = archetype.capitalize()
    if title:
        display_class += f'  ·  "{title}"'

    print("=" * 58)
    print(f"   CHARACTER SHEET — {name.upper()}")
    print("=" * 58)
    print(f"   Class    : {display_class}")
    print(f"   HP       : {math.get('hp', '?')} / {math.get('max_hp', '?')}")
    print(f"   AC       : {math.get('ac', '?')}")
    print(f"   Stats    : {render_stat_block(math)}")
    print("-" * 58)

    if stat_justification:
        print("   ✦ Destiny:")
        for line in _word_wrap(stat_justification, 52):
            print(f"     {line}")
        print()

    print("   [ INVENTORY ]")
    print(f"   Gear     : {', '.join(math.get('inventory', []))}")
    if flavor_trinkets:
        print(f"   Trinkets : {', '.join(flavor_trinkets)}")
    print()

    if lore:
        print("   [ BACKSTORY ]")
        for line in _word_wrap(lore, 52):
            print(f"   {line}")

    print("=" * 58)


# ─────────────────────────────────────────────────────────────
#  World Lore Preview Renderer
# ─────────────────────────────────────────────────────────────
def render_world_lore_preview(lore_text: str):
    """Renders a structured world lore document to the terminal."""
    clear_screen()
    print("=" * 58)
    print("   WORLD LORE PREVIEW")
    print("=" * 58)
    print()
    print(lore_text)
    print()
    print("=" * 58)


# ─────────────────────────────────────────────────────────────
#  Internal Helpers
# ─────────────────────────────────────────────────────────────
def _word_wrap(text: str, width: int) -> list:
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 <= width:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines
