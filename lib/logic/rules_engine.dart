import 'dart:math';
import '../models/game_models.dart';

class RulesEngine {
  static final Random _random = Random();

  /// Parses a dice notation string (e.g., "1d20", "2d6+3") and returns the result.
  static int rollDice(String notation) {
    // Regex to parse: (count)d(faces)(+modifier)?
    final RegExp regex = RegExp(r'^(\d+)d(\d+)(?:([+-])(\d+))?$');
    final Match? match = regex.firstMatch(notation);

    if (match == null) {
      throw ArgumentError('Invalid dice notation: $notation');
    }

    final int count = int.parse(match.group(1)!);
    final int faces = int.parse(match.group(2)!);
    final String? sign = match.group(3);
    final int modifier =
        match.group(4) != null ? int.parse(match.group(4)!) : 0;

    int total = 0;
    for (int i = 0; i < count; i++) {
      total += _random.nextInt(faces) + 1;
    }

    if (sign == '-') {
      total -= modifier;
    } else {
      total += modifier;
    }

    return total;
  }

  /// Resolves an attack from [attacker] to [target].
  /// Returns a map with details of the attack.
  static Map<String, dynamic> resolveAttack(
      Character attacker, Character target,
      {String attackType = 'melee'}) {
    // Step 1: Validate Target
    if (target.condition == Condition.DEAD ||
        target.condition == Condition.UNCONSCIOUS) {
      return {
        'isHit': false,
        'message': 'Target is dead or unconscious!',
        'roll': 0,
        'total': 0,
        'damage': 0,
        'isCrit': false,
        'disadvantage': false,
      };
    }

    // Step 2: Calculate Zone Distance
    int distance = (attacker.zone.index - target.zone.index).abs();

    if (attackType == 'melee' && distance > 0) {
      return {
        'isHit': false,
        'message': 'Target is out of melee range!',
        'roll': 0,
        'total': 0,
        'damage': 0,
        'isCrit': false,
        'disadvantage': false,
      };
    }

    // Step 3: Determine Stat & Damage Dice (Class Specifics)
    Stat attackStat = Stat.PHYS;
    int damageDiceSides = 6;
    int damageDiceCount = 1;
    int weaponBonus = 0;

    switch (attacker.role.toLowerCase()) {
      case 'fighter':
        attackStat = Stat.PHYS;
        damageDiceSides = 8; // Longsword
        break;
      case 'paladin':
        attackStat = Stat.PHYS;
        damageDiceSides = 6;
        damageDiceCount = 2; // Greatsword (2d6)
        break;
      case 'cleric':
        attackStat = Stat.PHYS;
        damageDiceSides = 8; // Warhammer
        break;
      case 'mage':
        if (attackType == 'melee') {
          attackStat = Stat.PHYS;
          damageDiceSides = 6; // Quarterstaff
        } else {
          attackStat = Stat.MENT; // Spell
          damageDiceSides = 10; // Firebolt
        }
        break;
      default:
        // Default fallback
        attackStat = Stat.PHYS;
        damageDiceSides = 6;
        break;
    }

    final int statBonus = attacker.stats[attackStat] ?? 0;

    // Step 4: Determine Disadvantage
    bool hasDisadvantage = (attackType != 'melee' && distance >= 2);

    // Step 5: Roll to Hit
    int roll1 = _random.nextInt(20) + 1;
    int roll2 = _random.nextInt(20) + 1;
    int d20Roll = hasDisadvantage ? min(roll1, roll2) : roll1;

    final int attackTotal = d20Roll + statBonus;
    final bool isCrit = d20Roll == 20;
    final bool isHit = isCrit || (attackTotal >= target.ac);

    // Step 6: Apply Damage
    int damage = 0;
    if (isHit) {
      // Critical hit doubles the dice
      final int actualDiceCount =
          isCrit ? damageDiceCount * 2 : damageDiceCount;

      for (int i = 0; i < actualDiceCount; i++) {
        damage += _random.nextInt(damageDiceSides) + 1;
      }

      damage += statBonus + weaponBonus;

      // Damage cannot be negative
      if (damage < 0) damage = 0;

      // Apply damage to target
      target.takeDamage(damage);
    }

    return {
      'isHit': isHit,
      'roll': d20Roll,
      'total': attackTotal,
      'damage': damage,
      'isCrit': isCrit,
      'disadvantage': hasDisadvantage,
    };
  }

  /// Resolves a skill check for [actor] using [stat] against [dc].
  static bool resolveCheck(Character actor, Stat stat, int dc) {
    final int bonus = actor.stats[stat] ?? 0;
    final int d20Roll = _random.nextInt(20) + 1;
    final int total = d20Roll + bonus;

    return total >= dc;
  }
}
