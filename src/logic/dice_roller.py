import re
import random

def roll_dice(notation: str) -> int:
    """Parses a dice notation string (e.g., "1d20", "2d6+3") and returns the result."""
    # Regex to parse: (count)d(faces)(+modifier)?
    regex = r'^(\d+)d(\d+)(?:([+-])(\d+))?$'
    match = re.match(regex, notation)

    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    count = int(match.group(1))
    faces = int(match.group(2))
    sign = match.group(3)
    modifier = int(match.group(4)) if match.group(4) else 0

    total = 0
    for _ in range(count):
        total += random.randint(1, faces)

    if sign == '-':
        total -= modifier
    else:
        total += modifier

    return total
