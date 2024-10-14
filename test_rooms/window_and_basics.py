import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from pygame import draw, Rect
from interfaces import UserInput

from engine         import PygameEngine, CommandlineEngine
from input_listener import DeafInputListener, PygameInputListener, KeyboardInputListener, CrazyInputListener
from renderer       import PygameRenderer, NoRenderer, CommandlineRenderer
from game           import NoGame


class MockGame:
    def loop(self, user_input: UserInput):
        self.space = user_input.is_space_key_down

class MockPgRenderer(PygameRenderer):
    def draw_frame(self, loopable: MockGame):
        if loopable.space:
            rect = Rect( (100,100), (100,100)  )
            draw.rect(self.frame, (0,0,0), rect )

class MockCliRenderer(CommandlineRenderer):
    def render(self, loopable: MockGame) -> None:
        super().render(loopable)
        if loopable.space:
            ascii_graphic = "--<OOOO>--"
            print(ascii_graphic, end='\r')


engine = CommandlineEngine(
    MockGame(),
    MockPgRenderer(),
    CrazyInputListener() 
)

engine.run()