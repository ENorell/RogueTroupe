from pygame import display, time
from typing import Final
from interfaces import Renderer, Loopable
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME

from pygame import display
from typing import Final
from interfaces import Renderer, Loopable
from settings import Vector, DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME
from interactable import draw_text


FPS_SCREEN_POSITION: Final[Vector] = (750,50)


class NoRenderer(Renderer):
    def render(self, loopable: Loopable) -> None:
        pass


class PygameRenderer(Renderer):

    def __init__(self) -> None:
        self.frame = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display.set_caption(GAME_NAME)
        self.fps_clock = time.Clock()  # Second clock with only purpose to record fps...

    def draw_fps(self) -> None:
        self.fps_clock.tick()
        fps = round(self.fps_clock.get_fps())
        draw_text(str(fps), self.frame, center_position=FPS_SCREEN_POSITION, scale_ratio=1.5)

    def render(self, loopable: Loopable) -> None:
        self.draw_frame(loopable)
        self.draw_fps()
        display.update()

    def draw_frame(self, loopable: Loopable):
        ...


class CommandlineRenderer(Renderer):
    def __init__(self) -> None:
        self.ascii_graphic = "----<>----"

    def render(self, loopable: Loopable) -> None:
        print(self.ascii_graphic, end='\r')


