from typing import Final
from pygame import transform

from data.state_machine import State, StateChoice
from data.character import Character, Tankylosaurus, Macedon, Healamimus, Dilophmageras, Tripiketops, Velocirougue, Archeryptrx
from data.character_slot import CharacterSlot, CombatSlot, generate_characters
from data.drag_dropper import DragDropper, DragDropRenderer
from data.interfaces import UserInput
from data.interactable import Button, draw_button
from data.images import IMAGES, ImageChoice
from settings import Vector, Color, DISPLAY_WIDTH, DISPLAY_HEIGHT


SHOP_POOL: list[type[Character]] = [
    Tankylosaurus,
    Macedon,
    Healamimus,
    Dilophmageras,
    Tripiketops,
    Velocirougue,
    Archeryptrx
]

SHOP_TOP_LEFT_POSITION: Final[Vector] = (170,180)
SHOP_SLOT_NR_ROWS:  Final[int] = 2
SHOP_SLOT_NR_COLS:  Final[int] = 4
SHOP_SLOT_DISTANCE_X: Final[int] = 60
SHOP_SLOT_DISTANCE_Y: Final[int] = 80
SHOP_SLOT_COLOR:    Final[Color] = (119, 64, 36)
BENCH_SLOT_COLOR:   Final[Color] = (54, 68, 90)


def create_shop_slots() -> list[CharacterSlot]:
    top_left_x, top_left_y = SHOP_TOP_LEFT_POSITION
    slots: list[CharacterSlot] = []
    for row in range(SHOP_SLOT_NR_ROWS):
        for col in range(SHOP_SLOT_NR_COLS):
            x_position = top_left_x + col * (CharacterSlot.width_pixels  + SHOP_SLOT_DISTANCE_X)
            y_position = top_left_y + row * (CharacterSlot.height_pixels + SHOP_SLOT_DISTANCE_Y)
            slot = CharacterSlot((x_position,y_position), SHOP_SLOT_COLOR)
            slots.append(slot)    
    return slots


class ShopState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.shop_slots: list[CharacterSlot] = create_shop_slots()
        self.drag_dropper = DragDropper(ally_slots + bench_slots + self.shop_slots)
        self.start_combat_button = Button((400,500), "Start Combat")


    def start_state(self) -> None:
        generate_characters(self.shop_slots, SHOP_POOL)


    def loop(self, user_input: UserInput) -> None:
        self.drag_dropper.loop(user_input)

        self.start_combat_button.refresh(user_input.mouse_position)
        if (self.start_combat_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            self.next_state = StateChoice.PREPARATION


class ShopRenderer(DragDropRenderer):
    background_image = transform.scale(IMAGES[ImageChoice.BACKGROUND_SHOP_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def draw_frame(self, shop: ShopState):
        self.frame.blit(self.background_image, (0, 0))

        super().draw_frame(shop.drag_dropper)

        draw_button(self.frame, shop.start_combat_button)
