from data.game import Game
from data.input_listener import CrazyInputListener
from data.engine import PygameEngine
# Pytest


def test_pygame_engine() -> None:
    pass


def test_game_1000_loops() -> None:
    mock_input = CrazyInputListener()

    test_game = Game()

    for _ in range(1000):
        input = mock_input.capture()

        test_game.loop(input)