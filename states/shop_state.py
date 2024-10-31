from pygame import transform, Surface
from typing import Self

from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from core.renderer import PygameRenderer
from components.character import Character, Tankylosaurus, Macedon, Healamimus, Dilophmageras, Tripiketops, Velocirougue, Archeryptrx
from components.character_slot import CharacterSlot, CombatSlot, generate_characters
from components.drag_dropper import DragDropper, draw_drag_dropper
from components.interactable import Button, draw_button
from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT


SHOP_POOL: list[type[Character]] = [
    Tankylosaurus,
    Macedon,
    Healamimus,
    Dilophmageras,
    Tripiketops,
    Velocirougue,
    Archeryptrx
]

class TrashButton(Button):
    width_pixels = 50
    height_pixels = 40

    @classmethod
    def create_below_slot(cls, slot: CharacterSlot) -> Self:
        slot_x, slot_y = slot.position
        button_x: int = slot_x + slot.width_pixels // 2 - TrashButton.width_pixels // 2
        button_y: int = slot_y + slot.height_pixels + TrashButton.width_pixels // 5

        return cls((button_x, button_y), "Trash")


class ShopState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot], shop_slots: list[CharacterSlot], trash_slot: CharacterSlot) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.shop_slots = shop_slots
        self.trash_slot = trash_slot
        self.trash_button = TrashButton.create_below_slot(trash_slot)
        self.start_combat_button = Button((400, 500), "Start Combat")
        self.drag_dropper = DragDropper(ally_slots + bench_slots + shop_slots + [trash_slot])


    def start_state(self) -> None:
        generate_characters(self.shop_slots, SHOP_POOL)

    def is_there_allies(self) -> bool:
        return bool(self.ally_slots)

    def loop(self, user_input: UserInput) -> None:
        self.drag_dropper.loop(user_input)

        self.start_combat_button.refresh(user_input.mouse_position)
        if (self.start_combat_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            if not self.is_there_allies(): return
            self.next_state = StateChoice.PREPARATION

        self.trash_button.refresh(user_input.mouse_position)
        if self.trash_button.is_hovered and user_input.is_mouse1_up:
            if not self.trash_slot.content: return
            self.trash_slot.content = None


class ShopRenderer(PygameRenderer):
    background_image = transform.scale(IMAGES[ImageChoice.BACKGROUND_SHOP_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def __init__(self, shop_state: ShopState) -> None:
        super().__init__()
        self.shop_state = shop_state

    def draw_frame(self):
        self.render_shop_state(self.frame, self.shop_state)

    @staticmethod
    def render_shop_state(frame: Surface, shop_state: ShopState) -> None:
        frame.blit(ShopRenderer.background_image, (0, 0))

        draw_drag_dropper(frame, shop_state.drag_dropper)

        draw_button(frame, shop_state.start_combat_button)

        draw_button(frame, shop_state.trash_button)