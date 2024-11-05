from states.game import Game, create_enemy_slots, create_ally_slots
from states.combat_state import CombatState
from core.input_listener import CrazyInputListener, NoInputListener
from components import character


def test_game_1000_loops() -> None:
    # Check that the game survives 1000 frames of crazy input without crash
    input_listener = CrazyInputListener()

    test_game = Game.new_game()

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
