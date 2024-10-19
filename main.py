from engine import PygameEngine
from input_listener import PygameInputListener
from game import Game, GameRenderer


if __name__ == '__main__':

    engine = PygameEngine(
        Game(),
        GameRenderer(),
        PygameInputListener()
    )

    engine.run()
