from pygame import display
from typing import Final
from interfaces import Renderer, Loopable
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME, Color

from pygame import display, image, transform
from typing import Final
from interfaces import Renderer, Loopable
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME


BACKGROUND_IMAGE_PATHS: Final[dict] = {
    'SHOP': 'assets/backgrounds/jungle.webp',
    'PREPARATION': 'assets/backgrounds/jungle2.webp',
    'COMBAT': 'assets/backgrounds/jungle3.webp'
}

class NoRenderer(Renderer):
    def render(self, loopable: Loopable) -> None:
        pass


class PygameRenderer(Renderer):

    def __init__(self) -> None:
        self.frame = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display.set_caption(GAME_NAME)
        self.background_images = {
            'SHOP': transform.scale(image.load(BACKGROUND_IMAGE_PATHS['SHOP']), (DISPLAY_WIDTH, DISPLAY_HEIGHT)),
            'PREPARATION': transform.scale(image.load(BACKGROUND_IMAGE_PATHS['PREPARATION']), (DISPLAY_WIDTH, DISPLAY_HEIGHT)),
            'COMBAT': transform.scale(image.load(BACKGROUND_IMAGE_PATHS['COMBAT']), (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        }

    def render(self, loopable: Loopable) -> None:
        self.draw_frame(loopable)
        display.flip()

    def draw_frame(self, loopable: Loopable):
        ...


class CommandlineRenderer(Renderer):
    def __init__(self) -> None:
        self.ascii_graphic = "----<>----"

    def render(self, loopable: Loopable) -> None:
        print(self.ascii_graphic, end='\r')


