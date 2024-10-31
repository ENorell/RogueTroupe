from pygame import draw, Rect

from core.interfaces     import UserInput
from core.engine         import PygameEngine, CommandlineEngine
from core.input_listener import DeafInputListener, PygameInputListener, KeyboardInputListener, CrazyInputListener
from core.renderer       import PygameRenderer, NoRenderer, CommandlineRenderer
from states.game         import NoGame


class MockGame:
    def loop(self, user_input: UserInput):
        self.space = user_input.is_space_key_down

class MockPgRenderer(PygameRenderer):
    def __init__(self, game: MockGame) -> None:
        super().__init__()
        self.game = game

    def draw_frame(self):
        if self.game.space:
            rect = Rect( (100,100), (100,100)  )
            draw.rect(self.frame, (0,0,0), rect )

class MockCliRenderer(CommandlineRenderer):
    def __init__(self, game: MockGame) -> None:
        super().__init__()
        self.game = game

    def render(self) -> None:
        super().render()
        if self.game.space:
            ascii_graphic = "--<OOOO>--"
            print(ascii_graphic, end='\r')

mock_game = MockGame()

engine = CommandlineEngine(
    mock_game,
    MockCliRenderer(mock_game),
    KeyboardInputListener()
)

engine.run()