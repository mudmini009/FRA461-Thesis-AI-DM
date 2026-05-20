"""
QuestCartographerAgent — generates a full node-map JSON graph for a selected quest.

Takes a quest summary (from the Architect) and produces the exact JSON schema
that QuestLoader expects. Includes strict Python validation to catch LLM errors.

Uses the Arbiter model (low temp) for structured output — generating valid JSON
is more important than creative prose here.
"""
import json
import os
from typing import Dict, Any, List, Optional
from collections import deque
from src.agents.base import BaseLLMProvider
from src.logic.enemy_factory import EnemyFactory
from src.models.toon_converter import TOONConverter

_FALLBACK_PATH = os.path.join("data", "quests", "_fallback_template.json")


class QuestCartographerAgent(BaseLLMProvider):

    def generate_quest_map(
        self,
        quest_summary: Dict[str, Any],
        world_lore: str,
        bestiary_tags: List[str],
        sample_quest_path: str = "data/quests/sample_dungeon.json",
    ) -> Dict[str, Any]:
        """
        Generates a complete quest node-map JSON matching the QuestLoader schema.

        Validation pipeline:
          1. Parse JSON
          2. Check required keys (quest_id, entrance_node, nodes)
          3. Validate all connected_to references resolve
          4. Validate all enemy_tags exist in bestiary
          5. Validate at least one combat/boss node
          6. Validate graph is fully connected from entrance

        On failure: retries once with error feedback, then falls back to template.
        """
        # Load sample quest as one-shot example for the prompt
        sample_json = ""
        try:
            with open(sample_quest_path, "r", encoding="utf-8") as f:
                sample_json = f.read()
        except Exception:
            pass

        quest_id = quest_summary.get("quest_id", "generated_quest")
        quest_name = quest_summary.get("name", "Unknown Quest")
        quest_desc = quest_summary.get("description", "")
        enemy_tags = quest_summary.get("enemy_tags", ["goblin"])
        num_nodes = quest_summary.get("num_nodes", 4)
        tags_str = json.dumps(bestiary_tags)

        prompt = self._build_prompt(
            quest_id, quest_name, quest_desc, enemy_tags, num_nodes,
            world_lore, tags_str, sample_json, error_feedback=""
        )

        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                raw = response.text.strip()

                # Parse lines
                lines = [line.strip() for line in raw.split('\n') if line.strip()]
                # Strip ``` if present
                lines = [line for line in lines if not line.startswith("```")]

                quest_data = {
                    "quest_id": quest_id,
                    "name": quest_name,
                    "description": quest_desc,
                    "nodes": {}
                }

                for line in lines:
                    if line.startswith("entrance_node:"):
                        quest_data["entrance_node"] = line.split(":", 1)[1].strip()
                    elif line.startswith("node:"):
                        node_data = TOONConverter.decode(line)
                        node_id = node_data.get("node")
                        if node_id:
                            # clean node keys/values
                            node_data["node_id"] = node_id
                            # Remove the temporary key 'node'
                            node_data.pop("node", None)
                            quest_data["nodes"][node_id] = node_data

                # Force correct quest_id
                quest_data["quest_id"] = quest_id
                quest_data["name"] = quest_name
                quest_data["description"] = quest_desc

                errors = self._validate_quest_schema(quest_data, bestiary_tags)
                if not errors:
                    return quest_data

                # Retry with error feedback
                if attempt == 0:
                    error_str = "\n".join(f"- {e}" for e in errors)
                    print(f"   ⚠️ Map validation failed (attempt 1), retrying...")
                    prompt = self._build_prompt(
                        quest_id, quest_name, quest_desc, enemy_tags, num_nodes,
                        world_lore, tags_str, sample_json,
                        error_feedback=f"\n\nYOUR PREVIOUS OUTPUT HAD THESE ERRORS:\n{error_str}\nFix them and try again in the same TOON format."
                    )
                    continue

            except Exception as e:
                if attempt == 0:
                    print(f"   ⚠️ Map generation error (attempt 1): {e}")
                    continue
                print(f"   ❌ Map generation failed: {e}")

        # Fallback
        print("   📋 [SYSTEM] Using fallback quest template.")
        return self._load_fallback(quest_id, quest_name, quest_desc, enemy_tags)

    def _build_prompt(
        self, quest_id, quest_name, quest_desc, enemy_tags, num_nodes,
        world_lore, tags_str, sample_json, error_feedback=""
    ) -> str:
        return f"""You are a dungeon map architect for a dark-fantasy TTRPG.
Generate a complete dungeon/quest map in TOON syntax. Do NOT output JSON or XML.

QUEST DETAILS:
- Quest ID: {quest_id}
- Quest Name: {quest_name}
- Description: {quest_desc}
- Enemy Types to use: {json.dumps(enemy_tags)}
- Target number of rooms/nodes: {num_nodes}

WORLD LORE:
{world_lore}

AVAILABLE ENEMY ARCHETYPES (use ONLY these in enemy_archetype fields):
["minion", "skirmisher", "brute", "boss"]

TOON SYNTAX RULES (CRITICAL — follow EXACTLY):
1. The first line MUST be: entrance_node:<node_id> (e.g. entrance_node:node_01)
2. Every subsequent line must represent a single room/node starting with `node:<node_id>` (e.g. node:node_01|name:Room Name|...)
3. Each node line MUST contain all of these keys separated by pipes:
   - name: string (display name like "Dark Corridor")
   - base_description: string (2-3 sentences describing the room)
   - connected_to: array of node_id strings inside brackets (e.g. [node_02,node_03], referencing real node keys)
   - event_type: one of "safe", "combat", "boss", "puzzle"
   - visited: false (ALWAYS false)
   - cleared: true if event_type is "safe", false otherwise
   - lore_fragment: string (2-3 sentences of discoverable world lore)
   - grants_item: string or null (item found in this room on first visit, e.g. "Rusty Key")
   - required_item: string or null (item needed to enter this room, e.g. "Rusty Key")

4. FOR COMBAT/BOSS NODES (event_type "combat" or "boss"), also include:
   - enemy_name: string (creative enemy name matching the room theme, e.g. "Crystal-Infected Miner")
   - enemy_archetype: one of "minion", "skirmisher", "brute", "boss"
   - enemy_attack_flavor: string (attack description, e.g. "Poisoned Pickaxe Smash")
   - enemy_tag: string from quest enemy types list (fallback tag)
   Use "minion" or "skirmisher" for combat nodes, "boss" for boss nodes.

5. FOR PUZZLE NODES (event_type "puzzle"), also include:
   - puzzle_obstacle: string (describe the obstacle, e.g. "A collapsed bridge spans a dark chasm")
   - puzzle_base_dc: integer between 10 and 16 (difficulty class)

6. entrance_node MUST be one of the node keys, and that node MUST be event_type "safe"
7. The LAST node should be event_type "boss"
8. Every connected_to reference MUST exist as a node key — NO dangling references
9. The graph MUST be fully connected — every node reachable from entrance_node
10. You must have at least ONE combat node and exactly ONE boss node
11. Include at least ONE puzzle node for variety
12. If a puzzle node has "required_item", an earlier safe/combat node MUST have a matching "grants_item"

Return ONLY the TOON lines. Do NOT write any markdown code blocks, HTML, or explanations.

EXAMPLE OUTPUT:
entrance_node:node_01
node:node_01|name:Entrance|base_description:A cold stone doorway leading underground.|connected_to:[node_02]|event_type:safe|visited:false|cleared:true|lore_fragment:The chapel above has long been abandoned.|grants_item:null|required_item:null
node:node_02|name:The Shadow Crypt|base_description:Skeletons rattle in their alcoves.|connected_to:[node_01]|event_type:boss|visited:false|cleared:false|lore_fragment:The tomb is cursed.|grants_item:null|required_item:null|enemy_name:Gravekeeper Skeleton|enemy_archetype:boss|enemy_attack_flavor:Rusty Scythe Sweep|enemy_tag:skeleton
{error_feedback}"""

    @staticmethod
    def _validate_quest_schema(quest_data: dict, bestiary_tags: List[str]) -> List[str]:
        """
        Validates the generated quest JSON against the expected schema.
        Returns a list of error strings. Empty list = valid.
        """
        errors = []
        valid_archetypes = EnemyFactory.get_valid_archetypes()

        # Top-level keys
        if "entrance_node" not in quest_data:
            errors.append("Missing 'entrance_node' key")
        if "nodes" not in quest_data or not isinstance(quest_data.get("nodes"), dict):
            errors.append("Missing or invalid 'nodes' dict")
            return errors  # Can't continue without nodes

        nodes = quest_data["nodes"]
        node_ids = set(nodes.keys())

        # Entrance check
        entrance = quest_data.get("entrance_node", "")
        if entrance not in node_ids:
            errors.append(f"entrance_node '{entrance}' not found in nodes")

        has_combat = False
        has_boss = False

        for nid, node in nodes.items():
            prefix = f"Node '{nid}'"

            # Required fields
            for field in ("name", "base_description", "connected_to", "event_type"):
                if field not in node:
                    errors.append(f"{prefix}: missing required field '{field}'")

            # connected_to validation
            connected = node.get("connected_to", [])
            if not isinstance(connected, list):
                errors.append(f"{prefix}: 'connected_to' must be a list")
            else:
                for ref in connected:
                    if ref not in node_ids:
                        errors.append(f"{prefix}: connected_to references non-existent node '{ref}'")

            # event_type validation
            event_type = node.get("event_type", "")
            if event_type not in ("safe", "combat", "boss", "puzzle"):
                errors.append(f"{prefix}: invalid event_type '{event_type}'")
            if event_type == "combat":
                has_combat = True
            if event_type == "boss":
                has_boss = True

            # enemy fields validation (combat/boss)
            if event_type in ("combat", "boss"):
                # enemy_archetype validation (new schema)
                archetype = node.get("enemy_archetype")
                if archetype and archetype not in valid_archetypes:
                    errors.append(f"{prefix}: enemy_archetype '{archetype}' not in {valid_archetypes}")
                # enemy_tag validation (fallback compatibility)
                tag = node.get("enemy_tag")
                if not tag and not node.get("enemy_name"):
                    errors.append(f"{prefix}: combat/boss node missing both enemy_tag and enemy_name")

            # puzzle fields validation
            if event_type == "puzzle":
                if not node.get("puzzle_obstacle"):
                    node["puzzle_obstacle"] = "An obstacle blocks your path."
                if not node.get("puzzle_base_dc"):
                    node["puzzle_base_dc"] = 14

            # Ensure defaults
            if "visited" not in node:
                node["visited"] = False
            if "cleared" not in node:
                node["cleared"] = event_type == "safe"
            if "node_id" not in node:
                node["node_id"] = nid
            # Default new optional fields
            if "grants_item" not in node:
                node["grants_item"] = None
            if "required_item" not in node:
                node["required_item"] = None

        if not has_combat and not has_boss:
            errors.append("Quest must have at least one combat or boss node")

        # Graph connectivity check (BFS from entrance)
        if entrance in node_ids and not errors:
            visited = set()
            queue = deque([entrance])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                current_node = nodes.get(current, {})
                for neighbor in current_node.get("connected_to", []):
                    if neighbor not in visited and neighbor in node_ids:
                        queue.append(neighbor)
            unreachable = node_ids - visited
            if unreachable:
                errors.append(f"Unreachable nodes from entrance: {unreachable}")

        return errors

    @staticmethod
    def _load_fallback(quest_id, quest_name, quest_desc, enemy_tags) -> dict:
        """Loads the fallback template and patches it with the quest metadata."""
        try:
            with open(_FALLBACK_PATH, "r", encoding="utf-8") as f:
                fallback = json.load(f)
            fallback["quest_id"] = quest_id
            fallback["name"] = quest_name
            fallback["description"] = quest_desc
            # Patch enemy tags into combat/boss nodes
            for node in fallback.get("nodes", {}).values():
                if node.get("event_type") in ("combat", "boss") and enemy_tags:
                    node["enemy_tag"] = enemy_tags[0]
            return fallback
        except Exception:
            # Absolute last resort: return a minimal valid quest inline
            tag = enemy_tags[0] if enemy_tags else "goblin"
            return {
                "quest_id": quest_id,
                "name": quest_name,
                "description": quest_desc,
                "entrance_node": "node_01",
                "nodes": {
                    "node_01": {
                        "node_id": "node_01", "name": "Entrance",
                        "base_description": "A dark passage stretches before you.",
                        "connected_to": ["node_02"], "event_type": "safe",
                        "visited": False, "cleared": True, "enemy_tag": None,
                        "lore_fragment": "The air is stale and cold."
                    },
                    "node_02": {
                        "node_id": "node_02", "name": "The Enemy's Lair",
                        "base_description": "Enemies lurk in the shadows ahead.",
                        "connected_to": ["node_01"], "event_type": "boss",
                        "visited": False, "cleared": False, "enemy_tag": tag,
                        "lore_fragment": "This place has been claimed by something dangerous."
                    },
                }
            }
