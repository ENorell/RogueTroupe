from character import CharacterSlot, Character
from pygame import Surface, draw, Rect, display
from typing import Final, TypeAlias, Optional
from interfaces import Renderer, Loopable

from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_NAME

Color: TypeAlias = tuple[int,int,int]

DISPLAY_BACKGROUND_COLOR: Final[tuple] = (0, 27, 58)
SLOT_COLOR: Final[Color] = (9, 97, 59)
CHARACTER_COLOR: Final[Color] = (100, 50 ,230)


class NoRenderer(Renderer):
    def render(self, loopable: Loopable) -> None:
        pass


class PygameRenderer(Renderer):

    def __init__(self) -> None:
        self.frame = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        display.set_caption(GAME_NAME)

    def render(self, loopable: Loopable) -> None:

        self.frame.fill(DISPLAY_BACKGROUND_COLOR)

        self.draw_frame(loopable)
        
        display.flip()

    def draw_frame(self, loopable: Loopable):
        ...


class CommandlineRenderer(Renderer):
    def __init__(self) -> None:
        self.ascii_graphic = "----<>----"

    def render(self, loopable: Loopable) -> None:
        print(self.ascii_graphic, end='\r')


def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    assert character_slot.position is not None

    rect = Rect(character_slot.position, character_slot.size)
    draw.ellipse(frame, SLOT_COLOR, rect)


def draw_character(frame: Surface, character: Character, color_override: Optional[Color] = None):
    color = CHARACTER_COLOR if not color_override else color_override
    if not character.position:
        return

    rect = Rect(character.position, character.size)

    #if character.is_hover():
    #    rect.scale_by(1.5, 1.5)

    draw.rect(frame, color, rect)
