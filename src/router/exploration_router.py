"""
ExplorationRouter — pure Python command classifier for EXPLORATION phase.

Zero LLM tokens are burned here. All routing is done via keyword matching.
The LLM is only called AFTER the Python guardrail passes, for narration only.

Intent Classifications:
  MOVE       — player wants to travel to a connected node
  LOOK       — player wants to examine the current room
  REST       — player wants to short-rest
  QUEST_BOARD — player wants to see available quests (hub only)
  STATUS     — player wants to see their character sheet
  INVENTORY  — player wants to see their inventory
  EXIT_HUB   — player wants to leave back to hub
  QUIT       — player wants to exit the game
  PUZZLE_ATTEMPT — player is trying to solve a puzzle creatively
  UNKNOWN    — fallback, no LLM burn
"""
import re
from typing import Optional

# ─── Keyword Pattern Sets ──────────────────────────────────────────────────────

_MOVE_KEYWORDS = re.compile(
    r"\b(go|move|travel|walk|head|enter|proceed|step into|advance|push into|charge|run to|sneak into)\b",
    re.IGNORECASE
)
_LOOK_KEYWORDS = re.compile(
    r"\b(look|examine|inspect|search|study|survey|observe|investigate|scan|check out|peer)\b",
    re.IGNORECASE
)
_REST_KEYWORDS = re.compile(
    r"\b(rest|camp|sleep|take a break|sit down|catch my breath|make camp|set up camp)\b",
    re.IGNORECASE
)
_QUEST_BOARD_KEYWORDS = re.compile(
    r"\b(quest|board|job|work|bounty|contract|mission|assignment|task)\b",
    re.IGNORECASE
)
_STATUS_KEYWORDS = re.compile(
    r"\b(status|sheet|character|stats|abilities|health|hp|inventory)\b",
    re.IGNORECASE
)
_INVENTORY_KEYWORDS = re.compile(
    r"\b(inventory|items|bag|pack|carry|equipment|gear|pouch)\b",
    re.IGNORECASE
)
_EXIT_HUB_KEYWORDS = re.compile(
    r"\b(leave|exit|back|return|go back|hub|guild|tavern)\b",
    re.IGNORECASE
)
_QUIT_WORDS = {"quit", "exit game", "q", "quit game"}


def classify_exploration_intent(user_input: str) -> dict:
    """
    Classifies a player's free-text command into an exploration intent dict.
    Returns: {
        "type": str,           # MOVE | LOOK | REST | QUEST_BOARD | STATUS | INVENTORY | EXIT_HUB | QUIT | UNKNOWN
        "raw_target": str      # For MOVE: the text after the move verb (player's target string)
    }
    Zero LLM calls. Pure keyword regex.
    """
    text = user_input.strip()
    lower = text.lower()

    if lower in _QUIT_WORDS:
        return {"type": "QUIT", "raw_target": ""}

    # MOVE — extract the target after the verb
    move_match = _MOVE_KEYWORDS.search(text)
    if move_match:
        # Grab everything after the verb as the raw target
        verb_end = move_match.end()
        raw_target = text[verb_end:].strip()
        # Strip prepositions (to, into, through, towards, down, up, the)
        raw_target = re.sub(r"^(to|into|through|towards|toward|down|up|the|a|an|)\s+", "", raw_target, flags=re.IGNORECASE).strip()
        return {"type": "MOVE", "raw_target": raw_target}

    if _REST_KEYWORDS.search(text):
        return {"type": "REST", "raw_target": ""}

    if _QUEST_BOARD_KEYWORDS.search(text):
        return {"type": "QUEST_BOARD", "raw_target": ""}

    if _LOOK_KEYWORDS.search(text):
        # Check if looking at something specific
        look_match = _LOOK_KEYWORDS.search(text)
        remainder = text[look_match.end():].strip()
        remainder = re.sub(r"^(at|around|the|a|an)\s+", "", remainder, flags=re.IGNORECASE).strip()
        return {"type": "LOOK", "raw_target": remainder}

    if _INVENTORY_KEYWORDS.search(text):
        return {"type": "INVENTORY", "raw_target": ""}

    if _STATUS_KEYWORDS.search(text):
        return {"type": "STATUS", "raw_target": ""}

    if _EXIT_HUB_KEYWORDS.search(text):
        return {"type": "EXIT_HUB", "raw_target": ""}

    return {"type": "UNKNOWN", "raw_target": text}


def classify_exploration_intent_in_context(user_input: str, current_node: dict) -> dict:
    """
    Context-aware wrapper around classify_exploration_intent.

    If we're in an uncleared puzzle node and the input doesn't match
    any standard command, classify it as PUZZLE_ATTEMPT instead of UNKNOWN.
    This lets the player type creative solutions like:
      "I freeze the water to make an ice bridge"
    and have them routed to the Arbiter.
    """
    result = classify_exploration_intent(user_input)

    # If UNKNOWN and we're in an active puzzle, reclassify
    if result["type"] == "UNKNOWN":
        event_type = current_node.get("event_type", "safe")
        is_puzzle = event_type == "puzzle"
        is_uncleared = not current_node.get("cleared", True)
        if is_puzzle and is_uncleared:
            return {"type": "PUZZLE_ATTEMPT", "raw_target": user_input.strip()}

    return result


def get_rest_rejection_message(node: dict) -> Optional[str]:
    """
    Python guardrail for REST commands.
    Returns a rejection message string if REST is not allowed, else None.
    """
    event_type = node.get("event_type", "safe")
    cleared = node.get("cleared", True)

    if event_type in ("combat", "boss") and not cleared:
        return "🛑 [SYSTEM] You cannot rest while enemies are in the room! Defeat them first."
    if event_type == "puzzle":
        return "🛑 [SYSTEM] You can't rest here — the room feels dangerous. Find somewhere safer."
    return None  # REST is allowed


def get_move_rejection_message(raw_target: str, current_node: dict) -> str:
    """
    Returns a deterministic mechanical rejection for an invalid MOVE.
    No LLM involved. Called when resolve_move_target() returns None.
    """
    exits = current_node.get("connected_to", [])
    if not exits:
        return f"🛑 [SYSTEM] There is nowhere to go from here."
    return (
        f"🛑 [SYSTEM] You can't get to '{raw_target}' from here. "
        f"Check the available exits."
    )


if __name__ == "__main__":
    # Quick self-test
    tests = [
        "I walk into the Main Shaft",
        "I go to node_02",
        "look around the room",
        "I want to rest",
        "check the quest board",
        "what's my status",
        "quit",
        "I charge into the darkness",
        "examine the collapsed cart carefully",
    ]
    for t in tests:
        result = classify_exploration_intent(t)
        print(f"  '{t}' -> {result}")
