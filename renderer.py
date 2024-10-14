from pygame import display
from typing import Final
from interfaces import Renderer, Loopable
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME, Color


COLOR_DISPLAY_BACKGROUND: Final[Color] = (0, 27, 58)


class NoRenderer(Renderer):
    def render(self, loopable: Loopable) -> None:
        pass


class PygameRenderer(Renderer):

    def __init__(self) -> None:
        self.frame = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display.set_caption(GAME_NAME)

    def render(self, loopable: Loopable) -> None:

        self.frame.fill(COLOR_DISPLAY_BACKGROUND)

        self.draw_frame(loopable)
        
        display.flip()

    def draw_frame(self, loopable: Loopable):
        ...


class CommandlineRenderer(Renderer):
    def __init__(self) -> None:
        self.ascii_graphic = "----<>----"

    def render(self, loopable: Loopable) -> None:
        print(self.ascii_graphic, end='\r')


