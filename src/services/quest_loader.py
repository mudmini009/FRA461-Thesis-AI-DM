"""
QuestLoader — pure Python service for reading and writing point-crawl quest data.

Responsibilities:
  - Load/save quest node graphs from data/quests/{quest_id}.json
  - Resolve nodes by ID
  - Mark nodes as visited (lore gate) or cleared (combat resolution)
  - Append lore fragments to world_lore.txt (no LLM, pure file I/O)

No LLM calls, no Character objects. This layer is purely mechanical.
"""
import json
import os
from typing import Optional

QUEST_DIR = "data/quests"
LORE_FILE = "data/active/world_lore.txt"


class QuestLoader:

    # ─── Load / Save ──────────────────────────────────────────

    @staticmethod
    def load_quest(quest_id: str) -> Optional[dict]:
        """
        Loads a quest graph from data/quests/{quest_id}.json.
        Returns the full quest dict, or None if not found.
        """
        path = os.path.join(QUEST_DIR, f"{quest_id}.json")
        if not os.path.exists(path):
            print(f"❌ Quest file not found: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading quest '{quest_id}': {e}")
            return None

    @staticmethod
    def save_quest(quest_id: str, quest_data: dict):
        """
        Atomically writes the quest graph back to disk.
        Called after marking visited/cleared to prevent state desync.
        """
        path = os.path.join(QUEST_DIR, f"{quest_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(quest_data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"❌ Error saving quest '{quest_id}': {e}")

    @staticmethod
    def list_available_quests() -> list:
        """
        Returns a list of (quest_id, quest_name) tuples for all quests
        in the quests directory, excluding the hub.
        """
        quests = []
        if not os.path.exists(QUEST_DIR):
            return quests
        for filename in sorted(os.listdir(QUEST_DIR)):
            if filename.endswith(".json") and filename != "hub.json":
                quest_id = filename.replace(".json", "")
                try:
                    path = os.path.join(QUEST_DIR, filename)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    quests.append({
                        "id": quest_id,
                        "name": data.get("name", quest_id),
                        "description": data.get("description", ""),
                    })
                except Exception:
                    pass
        return quests

    # ─── Node Access ──────────────────────────────────────────

    @staticmethod
    def get_node(quest_data: dict, node_id: str) -> Optional[dict]:
        """Returns the node dict for the given node_id, or None if not found."""
        return quest_data.get("nodes", {}).get(node_id)

    @staticmethod
    def get_entrance_node_id(quest_data: dict) -> str:
        """Returns the entrance node id for the quest."""
        return quest_data.get("entrance_node", "")

    # ─── State Mutation ───────────────────────────────────────

    @staticmethod
    def mark_visited(quest_data: dict, node_id: str):
        """
        Sets visited=True on the node.
        Must be called on FIRST ENTRY to any node, before lore appending.
        This is separate from cleared — safe rooms are never 'cleared' by Python.
        """
        node = QuestLoader.get_node(quest_data, node_id)
        if node is not None:
            node["visited"] = True

    @staticmethod
    def mark_cleared(quest_data: dict, node_id: str):
        """
        Sets cleared=True on the node.
        ONLY called after a combat VICTORY return from start_combat_loop().
        Never called on safe/puzzle nodes.
        """
        node = QuestLoader.get_node(quest_data, node_id)
        if node is not None:
            node["cleared"] = True

    # ─── Lore Expansion ───────────────────────────────────────

    @staticmethod
    def append_lore(lore_fragment: Optional[str], lore_path: str = LORE_FILE):
        """
        Appends a lore fragment to the world_lore.txt file.

        Called ONLY when visited transitions False → True.
        Guarded upstream: this is only reached if visited==False, so
        the Infinite Lore Loophole cannot occur.

        If lore_fragment is None or empty, this is a no-op.
        """
        if not lore_fragment:
            return
        try:
            with open(lore_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{lore_fragment.strip()}")
                f.flush()
                os.fsync(f.fileno())
            print(f"   📜 [WORLD] New lore discovered and recorded.")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not append lore fragment: {e}")

    # ─── Connectivity Helpers ─────────────────────────────────

    @staticmethod
    def resolve_move_target(user_target: str, current_node: dict, quest_data: dict) -> Optional[str]:
        """
        Pure Python fuzzy resolver. Attempts to match the player's typed
        target against the connected_to node IDs and their display names.

        Returns the matching node_id string, or None if no valid connection found.
        Uses three-tier matching: exact ID → display name substring → fuzzy.
        All tiers are constrained strictly to nodes in connected_to.
        """
        import difflib

        connected_ids = current_node.get("connected_to", [])
        if not connected_ids:
            return None

        target = user_target.strip().lower()
        if not target:
            return None

        # Build name map: display_name_lower -> node_id
        # Limited exclusively to nodes in connected_to
        name_map = {}
        for nid in connected_ids:
            node = QuestLoader.get_node(quest_data, nid)
            if node:
                name_map[node.get("name", "").lower()] = nid

        # 1. Exact node_id match
        for nid in connected_ids:
            if target == nid.lower():
                return nid

        # 2. Display name exact match
        if target in name_map:
            return name_map[target]

        # 3. Display name substring match (target inside name, not the reverse)
        for display_name, nid in name_map.items():
            if target in display_name:
                return nid

        # 4. Fuzzy match (higher cutoff to prevent false positives)
        matches = difflib.get_close_matches(target, list(name_map.keys()), n=1, cutoff=0.5)
        if matches:
            return name_map[matches[0]]

        return None

    @staticmethod
    def is_quest_complete(quest_data: dict) -> bool:
        """
        Returns True if all combat/boss nodes in the quest are cleared.
        Safe/puzzle nodes are ignored — they are authored cleared=True already.
        """
        for node in quest_data.get("nodes", {}).values():
            if node.get("event_type") in ("combat", "boss") and not node.get("cleared", False):
                return False
        return True


if __name__ == "__main__":
    # Quick smoke-test
    q = QuestLoader.load_quest("sample_dungeon")
    if q:
        print(f"Quest: {q['name']}")
        print(f"Nodes: {list(q['nodes'].keys())}")
        node = QuestLoader.get_node(q, "node_01")
        print(f"Entrance node: {node['name']}")
        print(f"Connected to: {node['connected_to']}")
        resolved = QuestLoader.resolve_move_target("main shaft", node, q)
        print(f"Resolved 'main shaft' -> {resolved}")
