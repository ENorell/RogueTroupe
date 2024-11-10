from components.character import Character
from components import character_pool
from components import abilities
from components.character_slot import CombatSlot
from states.combat_state import BattleTurn, BattleRound, AbilityHandler


slot = CombatSlot((0, 0), 0, (0, 0, 0))

def test_character_heal_ability() -> None:
    """
    Test that the round-start healing ability works
    """

    unit = character_pool.Healamimus()
    slot.content = unit

    unit.lose_health(2)

    assert unit.ability_type

    battle_round = BattleRound.start_new_round([slot], [])

    for _ in range(100):
        battle_round.loop()

    assert unit.health == character_pool.Healamimus.max_health - 1


def test_character_rampage_ability() -> None:

    unit = character_pool.Spinoswordaus()
    slot.content = unit

    turn = BattleTurn.start_new_turn(slot, [slot], [])

    for _ in range(100):
        turn.loop()

    assert unit.damage == character_pool.Spinoswordaus.damage + 1


def test_enrage_ability() -> None:
    unit = character_pool.Tripiketops()

    slot.content = unit

    basic_attack = abilities.BasicAttack(unit)

    handler = AbilityHandler.turn_abilities(unit, [slot], [], basic_attack)

    # start execution of planned ability
    handler.activate()

    # Cause on-damage triggers
    unit.do_damage(1, unit)

    handler.activate()

    unit.do_damage(1, unit)

    # Flush out the triggered abilities
    for _ in range(100):
        handler.activate()

    # Finally should have enraged twice
    assert unit.damage == character_pool.Tripiketops.damage + 2


def test_acid_burst_ability() -> None:
    """
    Test that the on-death ability works
    """
    enemy_slot = CombatSlot((0, 0), 100, (0, 0, 0))
    enemy_character = character_pool.Spinoswordaus()
    enemy_slot.content = enemy_character

    unit = character_pool.Dilophmageras()
    slot.content = unit

    turn = BattleTurn.start_new_turn(slot, [slot], [enemy_slot])

    # Kill the character
    unit.do_damage(100, enemy_character)

    for _ in range(100):
        turn.loop()

    assert enemy_character.health == character_pool.Spinoswordaus.max_health - 3


def test_parry_ability() -> None:

    class ParryCharacter(Character):
        ability_type = abilities.Parry
        damage = 0
        range = 1

    class AttackCharacter(Character):
        damage = 0
        range = 1

    attack_slot = CombatSlot((0, 0), 1, (0, 0, 0))
    attack_character = AttackCharacter()
    attack_slot.content = attack_character

    unit = ParryCharacter()
    slot.content = unit

    # The attacker attacks once and is itself damaged
    turn = BattleTurn.start_new_turn(attack_slot, [slot], [attack_slot])

    for _ in range(150):
        turn.loop()

    assert attack_character.health == AttackCharacter.max_health - abilities.Parry.amount


def test_corpse_explosion_ability() -> None:
    class CasterCharacter(Character):
        range = 0
        ability_type = abilities.CorpseExplosion

    class CorpseCharacter(Character):
        pass

    class VictimCharacter(Character):
        range = 0

    caster_character = CasterCharacter()
    corpse_character = CorpseCharacter()
    victim_character = VictimCharacter()

    caster_slot = CombatSlot((0, 0), 100, (0, 0, 0))
    enemy_slot = CombatSlot((0, 0), 100, (0, 0, 0))

    slot.content = corpse_character
    caster_slot.content = caster_character
    enemy_slot.content = victim_character

    # Make into corpse
    corpse_character.do_damage(CorpseCharacter.max_health, victim_character)

    turn = BattleTurn.start_new_turn(caster_slot, [caster_slot, slot], [enemy_slot])

    for _ in range(150):
        turn.loop()

    assert victim_character.health == VictimCharacter.max_health - abilities.CorpseExplosion.amount
