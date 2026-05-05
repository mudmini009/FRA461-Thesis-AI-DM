"""
ExplorationRouter — Hybrid command classifier for EXPLORATION phase.

Architecture:
  1. Regex-first (Zero Token Cost): Simple commands like LOOK, REST, QUIT,
     INVENTORY, STATUS are resolved instantly via pure Python keyword matching.
  2. LLM Fallback (Smart): When the regex returns UNKNOWN, the player's
     natural-language sentence is sent to Flash Lite for semantic classification.
     This lets players type "I'll carefully climb down toward the Grinding Chamber"
     instead of rigid "MOVE node_02".
  3. Puzzle Context: If we're in an active puzzle node and the input is still
     UNKNOWN after both passes, it's reclassified as PUZZLE_ATTEMPT.

Intent Classifications:
  MOVE           — player wants to travel to a connected node
  LOOK           — player wants to examine the current room
  REST           — player wants to short-rest
  QUEST_BOARD    — player wants to see available quests (hub only)
  STATUS         — player wants to see their character sheet
  INVENTORY      — player wants to see their inventory
  EXIT_HUB       — player wants to leave back to hub
  QUIT           — player wants to exit the game
  PUZZLE_ATTEMPT — player is trying to solve a puzzle creatively
  UNKNOWN        — truly unrecognizable input (after both regex AND LLM)
"""
import os
import re
from typing import Optional, Dict, Any, List

import google.generativeai as genai
from dotenv import load_dotenv

from src.models.toon_converter import TOONConverter

load_dotenv()


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


# ─── LLM-Backed Smart Classification ──────────────────────────────────────────

_EXPLORATION_INTENT_MODEL = "gemini-2.5-flash-lite"

_EXPLORATION_SYSTEM_PROMPT = """\
You are a command classifier for a dungeon exploration RPG.
Your ONLY job is to classify the player's input into ONE exploration intent.

VALID INTENT TYPES:
  MOVE           — player wants to travel / go / walk / climb / descend to a location
  LOOK           — player wants to examine, inspect, or observe something
  REST           — player wants to rest, sleep, camp, or take a break
  STATUS         — player wants to see their character stats or health
  INVENTORY      — player wants to check their items / bag / gear
  EXIT_HUB       — player wants to leave the dungeon / return to the guild
  QUIT           — player wants to exit the game entirely
  UNKNOWN        — input is truly unrecognizable or nonsensical

RULES:
1. If the player mentions ANY movement verb (go, walk, climb, descend, head, sneak, crawl, push, run, advance, proceed, enter, step) AND references a location, classify as MOVE.
2. For MOVE, extract the destination name as the "target" value. Match it to the closest AVAILABLE EXIT listed below.
3. If the player just wants to look/examine/inspect, classify as LOOK.
4. If the input is clearly conversational or creative problem-solving (not movement), classify as UNKNOWN so the game can route it elsewhere.

OUTPUT FORMAT (STRICT — 1 line, pipe-separated TOON):
  type:MOVE|target:The Grinding Chamber
  type:LOOK|target:the strange runes
  type:REST|target:
  type:STATUS|target:
  type:UNKNOWN|target:
"""


def _llm_classify_exploration(user_input: str, available_exits: List[str],
                               settings: Optional[Dict[str, Any]] = None) -> Optional[dict]:
    """
    Sends the player's natural-language input to Flash Lite for intent classification.
    Returns a parsed dict {"type": ..., "raw_target": ...} or None on failure.

    This is the LLM "second pass" — only called when regex returns UNKNOWN.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)

        model_name = _EXPLORATION_INTENT_MODEL
        if settings:
            model_name = settings.get("llm", {}).get("arbiter_model", model_name)

        generation_config = {
            "temperature": 0.1,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=_EXPLORATION_SYSTEM_PROMPT,
        )

        exits_str = ", ".join(available_exits) if available_exits else "none"
        prompt = (
            f"AVAILABLE EXITS FROM THIS ROOM: [{exits_str}]\n\n"
            f"PLAYER INPUT:\n{user_input}"
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse TOON response
        parsed = TOONConverter.decode(text)
        intent_type = parsed.get("type", "UNKNOWN").upper()

        # Validate: only accept known types
        valid_types = {"MOVE", "LOOK", "REST", "STATUS", "INVENTORY", "EXIT_HUB", "QUIT", "UNKNOWN"}
        if intent_type not in valid_types:
            return None

        raw_target = parsed.get("target", "")
        return {"type": intent_type, "raw_target": raw_target}

    except Exception:
        # LLM failed — return None so caller falls back to regex result
        return None


def classify_exploration_intent_smart(
    user_input: str,
    current_node: dict,
    quest_data: Optional[dict] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Hybrid Smart Exploration Router.

    Architecture:
      Pass 1 (Regex — Zero Tokens): Try pure Python keyword matching first.
              If regex confidently identifies the intent, return immediately.
      Pass 2 (LLM — Smart): If regex returns UNKNOWN, send the input to
              Flash Lite for semantic classification. The LLM receives the
              list of available exits so it can resolve natural-language
              destinations like "the Grinding Chamber" → node name.
      Pass 3 (Puzzle Context): If still UNKNOWN and we're in a puzzle node,
              reclassify as PUZZLE_ATTEMPT.

    Falls back gracefully to regex-only if:
      - smart_exploration_router is disabled in settings.json
      - LLM call fails for any reason
      - API key is missing
    """
    # ── Pass 1: Regex (always runs first — zero cost) ──────────
    result = classify_exploration_intent(user_input)

    if result["type"] != "UNKNOWN":
        # Regex got a confident match — skip LLM entirely
        return result

    # ── Pass 2: LLM Smart Classification ──────────────────────
    smart_enabled = True
    if settings:
        smart_enabled = settings.get("exploration", {}).get("smart_exploration_router", True)

    if smart_enabled and quest_data:
        # Build available exit names for the LLM prompt
        from src.services.quest_loader import QuestLoader
        connected_ids = current_node.get("connected_to", [])
        available_exits = []
        for nid in connected_ids:
            node = QuestLoader.get_node(quest_data, nid)
            if node:
                available_exits.append(node.get("name", nid))

        llm_result = _llm_classify_exploration(user_input, available_exits, settings)
        if llm_result and llm_result["type"] != "UNKNOWN":
            return llm_result

    # ── Pass 3: Puzzle Context Reclassification ───────────────
    event_type = current_node.get("event_type", "safe")
    is_puzzle = event_type == "puzzle"
    is_uncleared = not current_node.get("cleared", True)
    if is_puzzle and is_uncleared:
        return {"type": "PUZZLE_ATTEMPT", "raw_target": user_input.strip()}

    # ── Final fallback: UNKNOWN ───────────────────────────────
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
