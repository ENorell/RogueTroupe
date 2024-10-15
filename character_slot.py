from interactable import Interactable
from settings import Color, Vector, BLACK_COLOR
from pygame import Surface, Rect, draw
from typing import Final, Optional
from character import Character


SLOT_COLOR: Final[Color] = (9, 97, 59)
SLOT_HOVER_WIDTH: Final[int] = 3


class CharacterSlot(Interactable):
    width_pixels: int = 75
    height_pixels: int = 50
    _content: Optional[Character] = None
    
    def __init__(self, position: Vector) -> None:
        super().__init__(position)
        self._position = position

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, character: Optional[Character]):
        self._content = character


def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    assert character_slot.position is not None

    rect = Rect(character_slot.position, character_slot.size)
    draw.ellipse(frame, SLOT_COLOR, rect)

    if character_slot.is_hovered:
        draw.ellipse(frame, BLACK_COLOR, rect, width=SLOT_HOVER_WIDTH)