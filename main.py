from engine import PygameEngine
from game_renderer import GameRenderer
from input_listener import PygameInputListener
from game import Game


if __name__ == '__main__':

    engine = PygameEngine(
        Game(),
        GameRenderer(),
        PygameInputListener()
    )

    engine.run()
