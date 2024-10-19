from state_machine import State, StateChoice
from character import Character, KnightCharacter, WizardCharacter, GoblinCharacter, TrollCharacter
from character_slot import CharacterSlot, generate_characters
from drag_dropper import DragDropper, DragDropRenderer
from interfaces import UserInput
from interactable import Button, draw_button
from typing import Final

from settings import Vector, Color


SHOP_POOL: list[type] = [
    KnightCharacter,
    WizardCharacter,
    GoblinCharacter,
    TrollCharacter
]

SHOP_TOP_LEFT_POSITION: Final[Vector] = (150,100)
SHOP_SLOT_NR_ROWS:  Final[int] = 2
SHOP_SLOT_NR_COLS:  Final[int] = 4
SHOP_SLOT_DISTANCE: Final[int] = 75
SHOP_SLOT_COLOR:    Final[Color] = (119, 64, 36)
BENCH_SLOT_COLOR:   Final[Color] = (54, 68, 90)



def create_shop_slots() -> list[CharacterSlot]:
    top_left_x, top_left_y = SHOP_TOP_LEFT_POSITION
    slots: list[CharacterSlot] = []
    for row in range(SHOP_SLOT_NR_ROWS):
        for col in range(SHOP_SLOT_NR_COLS):
            x_position = top_left_x + col * (CharacterSlot.width_pixels  + SHOP_SLOT_DISTANCE)
            y_position = top_left_y + row * (CharacterSlot.height_pixels + SHOP_SLOT_DISTANCE)
            slot = CharacterSlot((x_position,y_position), SHOP_SLOT_COLOR)
            slots.append(slot)    
    return slots


class ShopState(State):
    def __init__(self, ally_slots: list[CharacterSlot], bench_slots: list[CharacterSlot]) -> None:
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
        if self.start_combat_button.is_hovered and user_input.is_mouse1_up:
            self.next_state = StateChoice.PREPARATION


class ShopRenderer(DragDropRenderer):

    def draw_frame(self, shop: ShopState):
        super().draw_frame(shop.drag_dropper)

        draw_button(self.frame, shop.start_combat_button)
