from typing import Optional, Final
from interactable import Interactable
from settings import Vector, Color
from character_slot import CharacterSlot
from pygame import Surface, Rect, draw, Vector2


COLOR_CHARACTER: Final[Color] = (100, 50 ,230)


class Character(Interactable):
    name: str = "Character"
    width_pixels: int = 50
    height_pixels: int = 80
    health: int = 5
    damage: int = 2

    def __init__(self) -> None:
        self.character_slot: Optional[CharacterSlot] = None
        self._position: Optional[Vector] = None

    @property
    def position(self) -> Optional[Vector]:
        return self.character_slot.position if self.character_slot else None

    def deploy_in(self, character_slot: CharacterSlot) -> None:
        self.character_slot = character_slot



def draw_character(frame: Surface, character: Character, color_override: Optional[Color] = None):
    color = COLOR_CHARACTER if not color_override else color_override
    if not character.position:
        return
    
    assert character.character_slot
    assert character.character_slot.position

    slot_center = Rect(character.character_slot.position, character.character_slot.size).center

    character_bottom = Rect(character.position, character.size).midbottom

    alignment = Vector2(slot_center) - Vector2(character_bottom)

    rect = Rect(Vector2(character.position) + alignment, character.size)

    if character.is_hovered:
        rect = rect.scale_by(1.5, 1.5)

    draw.rect(frame, color, rect)
