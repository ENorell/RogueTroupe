from pygame import Surface, Rect, draw, transform
from typing import Final, Optional, Sequence
from random import choice

from components.interactable import Interactable
from components.character import Character
from settings import Color, Vector, BLACK_COLOR
from assets.images import ImageChoice, IMAGES

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


class CombatSlot(CharacterSlot):

    def __init__(self, position: Vector, coordinate: int, color: Color) -> None:
        self.coordinate = coordinate
        super().__init__(position, color)


def generate_characters(slots: Sequence[CharacterSlot], character_type_pool: list[type]) -> None:
    for slot in slots:
        character_type = choice(character_type_pool)
        slot.content = character_type()


def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    assert character_slot.position is not None

    slot_rect = Rect(character_slot.position, character_slot.size)


    if character_slot.is_hovered:
        slot_hover_image = IMAGES[ImageChoice.SLOT_HOVER].convert_alpha()
        slot_hover_image = transform.scale(slot_hover_image, slot_rect.size)
        frame.blit(slot_hover_image, slot_rect.topleft)
    else:
        slot_image = IMAGES[ImageChoice.SLOT].convert_alpha()
        slot_image = transform.scale(slot_image, slot_rect.size)
        frame.blit(slot_image, slot_rect.topleft)
