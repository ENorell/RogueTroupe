from states.game import Game, create_enemy_slots, create_ally_slots
from states.combat_state import CombatState
from core.input_listener import CrazyInputListener, NoInputListener

from components.character import Healamimus, Spinoswordaus, Tripiketops, Dilophmageras, Character
from components.abilities import *
from components import character
from components.character_slot import CharacterSlot, CombatSlot
from states.combat_state import BattleTurn, BattleRound, AbilityHandler

# Pytest

def test_game_1000_loops() -> None:
    # Check that the game survives 1000 frames of crazy input without crash
    input_listener = CrazyInputListener()

    test_game = Game()

    for _ in range(1000):
        user_input = input_listener.capture()

        test_game.loop(user_input)

def test_combat_1000_loops() -> None:
    ally_slots = create_ally_slots()
    enemy_slots = create_enemy_slots()
    ally_slots[0].content = character.Macedon()
    ally_slots[1].content = character.Macedon()
    ally_slots[2].content = character.Healamimus()
    ally_slots[3].content = character.Archeryptrx()
    enemy_slots[0].content = character.Dilophmageras()
    enemy_slots[1].content = character.Tripiketops()
    enemy_slots[2].content = character.Tripiketops()
    enemy_slots[3].content = character.Dilophmageras()

    combat_state = CombatState(ally_slots, enemy_slots)
    combat_state.start_state()
    input_listener = NoInputListener()

    for _ in range(1000):
        user_input = input_listener.capture()

        combat_state.loop(user_input)


slot = CombatSlot((0, 0), 0, (0, 0, 0))

def test_character_heal_ability() -> None:
    """
    Test that the round-start healing ability works
    """

    unit = Healamimus()
    slot.content = unit

    unit.lose_health(2)

    assert unit.ability_type

    battle_round = BattleRound([slot], [])

    battle_round.start_round()

    for _ in range(100):
        battle_round.loop()

    assert unit.health == Healamimus.max_health - 1


def test_character_rampage_ability() -> None:

    unit = Spinoswordaus()
    slot.content = unit

    turn = BattleTurn(slot, [slot], [])
    turn.start_turn()

    for _ in range(100):
        turn.loop()

    assert unit.damage == Spinoswordaus.damage + 1


def test_enrage_ability() -> None:
    unit = Tripiketops()

    slot.content = unit

    handler = AbilityHandler.turn_abilities(unit, [slot], [])

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
    assert unit.damage == Tripiketops.damage + 2


def test_corpse_explosion_ability() -> None:
    """
    Test that the on-death ability works
    """
    enemy_slot = CombatSlot((0, 0), 100, (0, 0, 0))
    enemy_character = Spinoswordaus()
    enemy_slot.content = enemy_character

    unit = Dilophmageras()
    slot.content = unit

    turn = BattleTurn(slot, [slot], [enemy_slot])
    turn.start_turn()

    # Kill the character
    unit.do_damage(100, enemy_character)

    for _ in range(100):
        turn.loop()

    assert enemy_character.health == Spinoswordaus.max_health - 3


def test_parry_ability() -> None:

    class ParryCharacter(Character):
        ability_type = Parry
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
    turn = BattleTurn(attack_slot, [slot], [attack_slot])
    turn.start_turn()

    for _ in range(100):
        turn.loop()

    assert attack_character.health == AttackCharacter.max_health - Parry.amount