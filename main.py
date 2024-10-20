from data.engine import PygameEngine
from data.input_listener import PygameInputListener
from data.game import Game, GameRenderer


if __name__ == '__main__':

    engine = PygameEngine(
        Game(),
        GameRenderer(),
        PygameInputListener()
    )

    engine.run()
