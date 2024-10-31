from pygame import display, time, Surface
from typing import Final
from abc import ABC, abstractmethod

from core.interfaces import Renderer, Loopable
from components.interactable import draw_text
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME, Vector


FPS_SCREEN_POSITION: Final[Vector] = (750,50)


class NoRenderer(Renderer):
    def render(self) -> None:
        pass


class PygameRenderer(ABC):
    def __init__(self) -> None:
        self.frame = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display.set_caption(GAME_NAME)
        self.fps_clock = time.Clock()  # Second clock with only purpose to record fps...

    def draw_fps(self) -> None:
        self.fps_clock.tick()
        fps = round(self.fps_clock.get_fps())
        draw_text(str(fps), self.frame, center_position=FPS_SCREEN_POSITION, scale_ratio=1.5)

    def render(self) -> None:
        self.draw_frame()
        self.draw_fps()
        display.update()

    @abstractmethod
    def draw_frame(self):
        ...


class CommandlineRenderer(Renderer):
    def __init__(self) -> None:
        self.ascii_graphic = "----<>----"

    def render(self) -> None:
        print(self.ascii_graphic, end='\r')
