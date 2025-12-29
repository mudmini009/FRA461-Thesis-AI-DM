import random
import re

def roll(expression: str) -> dict:
    """
    Parses a dice string (e.g., '1d20+5', '2d6', 'd8') and rolls it.
    Returns a deterministic Dictionary Object (Stateless).
    """
    # 1. Clean up input (remove spaces, lower case) -> "1d20+5"
    expression = expression.lower().replace(" ", "")
    
    # 2. Regex Magic: Finds 'Count', 'Sides', and 'Modifier'
    # Pattern explanation:
    # ^(\d+)?   -> Optional number at start (Count)
    # d         -> The letter 'd'
    # (\d+)     -> Required number (Sides)
    # ([+-]\d+)?$ -> Optional +/- number at end (Modifier)
    match = re.match(r"^(\d+)?d(\d+)([+-]\d+)?$", expression)
    
    if not match:
        return {"error": f"Invalid dice format: {expression}"}

    count_str, sides_str, mod_str = match.groups()

    # 3. Handle defaults (e.g., "d20" becomes "1d20")
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(mod_str) if mod_str else 0

    # 4. The Physics: Roll the dice
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier

    # 5. Return Data (The "Single Source of Truth" for the UI)
    return {
        "expression": expression,   # e.g., "1d20+5"
        "rolls": rolls,             # e.g., [14]
        "modifier": modifier,       # e.g., 5
        "total": total,             # e.g., 19
        "is_critical": (sides == 20 and 20 in rolls), # Nat 20 check
        "is_fumble": (sides == 20 and 1 in rolls)     # Nat 1 check
    }

if __name__ == "__main__":
    # Quick Test: Run this file directly to see if math works
    print("Testing Dice Engine...")
    print(f"Rolling 1d20+5: {roll('1d20+5')}")
    print(f"Rolling 2d6:    {roll('2d6')}")
