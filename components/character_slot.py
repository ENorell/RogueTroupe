from pygame import Surface, Rect, draw, transform
from typing import Final, Optional, Sequence, Type
from random import choices,choice
from components.interactable import Interactable,Button
from components.character import Character
from settings import Color, Vector, BLACK_COLOR, DISPLAY_WIDTH
from assets.images import ImageChoice, IMAGES

SCREEN_CENTER: Final[int] = round(DISPLAY_WIDTH / 2)
BATTLE_SLOT_COLOR: Final[Color] = (57, 122, 65)
SLOT_HOVER_WIDTH: Final[int] = 3
NR_BATTLE_SLOTS_PER_TEAM: Final[int] = 4
NR_BENCH_SLOTS_PER_TEAM: Final[int] = 2
DISTANCE_BETWEEN_SLOTS: Final[int] = 15
DISTANCE_CENTER_TO_SLOTS: Final[int] = 75
SLOT_HEIGHT: Final[int] = 400
BENCH_HEIGHT: Final[int] = 500
BENCH_SLOT_COLOR:   Final[Color] = (54, 68, 90)

SHOP_TOP_LEFT_POSITION: Final[Vector] = (170, 320)
SHOP_SLOT_NR_ROWS: Final[int] = 1
SHOP_SLOT_NR_COLS: Final[int] = 4
SHOP_SLOT_DISTANCE_X: Final[int] = 60
SHOP_SLOT_DISTANCE_Y: Final[int] = 80
SHOP_SLOT_COLOR: Final[Color] = (119, 64, 36)

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


def create_ally_slots() -> list[CombatSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER - DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BATTLE_SLOTS_PER_TEAM):
        position_x = first_slot_position - slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        coordinate = NR_BATTLE_SLOTS_PER_TEAM - slot_nr
        slots.append(CombatSlot((position_x, SLOT_HEIGHT), coordinate, BATTLE_SLOT_COLOR))
    return slots


def create_enemy_slots() -> list[CombatSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER + DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BATTLE_SLOTS_PER_TEAM):
        position_x = first_slot_position + slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        coordinate = slot_nr + 1 + NR_BATTLE_SLOTS_PER_TEAM
        slots.append(CombatSlot((position_x, SLOT_HEIGHT), coordinate, BATTLE_SLOT_COLOR))
    return slots


def create_bench_slots() -> list[CharacterSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER - DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BENCH_SLOTS_PER_TEAM):
        position_x = first_slot_position - slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        slots.append(CharacterSlot((position_x, BENCH_HEIGHT), BENCH_SLOT_COLOR))
    return slots


def create_shop_slots() -> list[ShopSlot]:
    top_left_x, top_left_y = SHOP_TOP_LEFT_POSITION
    slots: list[ShopSlot] = []
    for row in range(SHOP_SLOT_NR_ROWS):
        for col in range(SHOP_SLOT_NR_COLS):
            x_position = top_left_x + col * (
                ShopSlot.width_pixels + SHOP_SLOT_DISTANCE_X
            )
            y_position = top_left_y + row * (
                ShopSlot.height_pixels + SHOP_SLOT_DISTANCE_Y
            )
            slots.append(ShopSlot((x_position, y_position), SHOP_SLOT_COLOR))
    return slots


def create_trash_slot() -> CharacterSlot:
    first_slot_position = SCREEN_CENTER - DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    position_x = first_slot_position - 3 * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
    return CharacterSlot((position_x, BENCH_HEIGHT), BENCH_SLOT_COLOR)


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
