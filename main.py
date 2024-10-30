from core.engine import PygameEngine
from core.input_listener import PygameInputListener
from states.game import Game, GameRenderer


if __name__ == '__main__':
    game = Game()

    engine = PygameEngine(
        game,
        GameRenderer(game),
        PygameInputListener()
    )

    engine.run()
