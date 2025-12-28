enum Stat {
  PHYS,
  MENT,
  SOC,
}

enum Zone {
  NEAR,
  MID,
  FAR,
}

enum Condition {
  NORMAL,
  INJURED,
  UNCONSCIOUS,
  DEAD,
}

class Character {
  final String id;
  final String name;
  final String role;
  int hp;
  final int maxHp;
  final int ac;
  final Map<Stat, int> stats;
  Zone zone;
  List<String> inventory;
  Condition condition;

  Character({
    required this.id,
    required this.name,
    required this.role,
    required this.hp,
    required this.maxHp,
    required this.ac,
    required this.stats,
    this.zone = Zone.NEAR,
    List<String>? inventory,
    this.condition = Condition.NORMAL,
  }) : inventory = inventory ?? [];

  void takeDamage(int amount) {
    hp -= amount;
    if (hp <= 0) {
      hp = 0;
      condition = Condition.UNCONSCIOUS;
    } else if (hp < maxHp) {
      condition = Condition.INJURED;
    } else {
      condition = Condition.NORMAL;
    }
  }

  @override
  String toString() {
    return 'Character(id: $id, name: $name, role: $role, hp: $hp/$maxHp, condition: $condition, zone: $zone)';
  }
}

class GameState {
  final List<Character> players;
  final List<Character> enemies;
  int turnCount;
  List<String> logs;

  GameState({
    required this.players,
    required this.enemies,
    this.turnCount = 0,
    List<String>? logs,
  }) : logs = logs ?? [];

  @override
  String toString() {
    return 'GameState(turn: $turnCount, players: ${players.length}, enemies: ${enemies.length})';
  }
}
