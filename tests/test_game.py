from states.game import Game
from core.input_listener import CrazyInputListener

from components.character import Healamimus, Spinoswordaus
from components.character_slot import CombatSlot
from states.combat_state import BattleTurn
# Pytest



def test_game_1000_loops() -> None:
    # Check that the game survives 1000 frames of crazy input without crash
    mock_input = CrazyInputListener()

    test_game = Game()

    for _ in range(1000):
        input = mock_input.capture()

        test_game.loop(input)


def test_character_heal_ability() -> None:
    slot = CombatSlot((0,0),0,(0,0,0))
    character = Healamimus()
    slot.content = character

    character.damage_health(2)

    assert character.ability
    character.ability.activate(character, [slot], [])

    assert character.health == Healamimus.max_health-1


def test_character_rampage_ability() -> None:
    slot = CombatSlot((0,0),0,(0,0,0))
    character = Spinoswordaus()
    slot.content = character

    assert character.ability

    turn = BattleTurn(slot, [slot], [])
    turn.start_turn()

    turn.loop()

    assert character.damage == Spinoswordaus.damage+1