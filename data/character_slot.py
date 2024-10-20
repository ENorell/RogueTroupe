from pygame import Surface, Rect, draw
from typing import Final, Optional
from random import choice

from data.interactable import Interactable
from data.character import Character
from settings import Color, Vector, BLACK_COLOR

BATTLE_SLOT_COLOR: Final[Color] = (57, 122, 65)
SLOT_HOVER_WIDTH: Final[int] = 3


class CharacterSlot(Interactable):
    width_pixels: int = 75
    height_pixels: int = 50
    _content: Optional[Character] = None
    
    def __init__(self, position: Vector, color: Color) -> None:
        super().__init__(position)
        self._position = position
        self.color = color

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, character: Optional[Character]):
        self._content = character


def generate_characters(slots: list[CharacterSlot], character_type_pool: list[type], is_enemy: bool = False) -> None:
    for slot in slots:
        character_type = choice(character_type_pool)
        slot.content = character_type(is_enemy=is_enemy)


def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    assert character_slot.position is not None

    rect = Rect(character_slot.position, character_slot.size)
    draw.ellipse(frame, character_slot.color, rect)

    if character_slot.is_hovered:
        draw.ellipse(frame, BLACK_COLOR, rect, width=SLOT_HOVER_WIDTH)