from interactable import Interactable
from settings import Color, Vector, BLACK_COLOR
from pygame import Surface, Rect, draw
from typing import Final


SLOT_COLOR: Final[Color] = (9, 97, 59)
SLOT_HOVER_WIDTH: Final[int] = 3


class CharacterSlot(Interactable):
    width_pixels: int = 75
    height_pixels: int = 50
    
    def __init__(self, position: Vector) -> None:
        self._position = position



def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    assert character_slot.position is not None

    rect = Rect(character_slot.position, character_slot.size)
    draw.ellipse(frame, SLOT_COLOR, rect)

    if character_slot.is_hovered:
        draw.ellipse(frame, BLACK_COLOR, rect, width=SLOT_HOVER_WIDTH)