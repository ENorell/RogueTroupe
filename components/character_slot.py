from pygame import Surface, Rect, draw, transform
from typing import Final, Optional, Sequence, Type
from random import choices,choice
from components.interactable import Interactable,Button
from components.character import Character
from settings import Color, Vector, BLACK_COLOR
from assets.images import ImageChoice, IMAGES

BATTLE_SLOT_COLOR: Final[Color] = (57, 122, 65)
SLOT_HOVER_WIDTH: Final[int] = 3

BUY_BUTTON_WIDTH = 70
BUY_BUTTON_HEIGHT = 55
buy_button_image = transform.scale(IMAGES[ImageChoice.BUY_BUTTON], (BUY_BUTTON_WIDTH, BUY_BUTTON_HEIGHT))


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

class ShopSlot(CharacterSlot):

    def __init__(self, position: Vector, color: Color) -> None:
        super().__init__(position, color)
        self.buy_button = Button((position[0], position[1] -130), "Buy", buy_button_image)
    
    
def generate_characters(slots: Sequence['CharacterSlot'], character_tiers: dict[int, list[Type[Character]]], tier_probabilities: list[float]) -> None:
    for slot in slots:
        # Select tier based on configured probabilities
        selected_tier = choices(list(character_tiers.keys()), weights=tier_probabilities, k=1)[0]
        # Randomly select a character type from the chosen tier
        character_type = choice(character_tiers[selected_tier])
        # Assign character to the slot
        slot.content = character_type()


def draw_slot(frame: Surface, character_slot: CharacterSlot) -> None:
    slot_rect = Rect(character_slot.position, character_slot.size)

    if character_slot.is_hovered:
        slot_image = IMAGES[ImageChoice.SLOT_HOVER].convert_alpha()
        slot_image = transform.scale(slot_image, slot_rect.size)
    else:
        slot_image = IMAGES[ImageChoice.SLOT].convert_alpha()
        slot_image = transform.scale(slot_image, slot_rect.size)
    frame.blit(slot_image, slot_rect.topleft)

