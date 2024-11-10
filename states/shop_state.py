from typing import Final
import pygame
import logging
from functools import lru_cache
from typing import Self

from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from core.renderer import PygameRenderer
from components.character_slot import CharacterSlot, CombatSlot, ShopSlot
from components.character_pool import generate_characters, CHARACTER_TIERS, TIER_PROBABILITIES
from components.drag_dropper import DragDropper, draw_drag_dropper
from components.interactable import Button, draw_button
from assets.images import IMAGES, ImageChoice
from settings import Vector, DISPLAY_WIDTH, DISPLAY_HEIGHT, DEFAULT_TEXT_SIZE, BLACK_COLOR, RED_COLOR


STARTING_GOLD: Final[int] = 10
REROLL_COST: Final[int] = 1

# Button settings
REROLL_BUTTON_SIZE = 100
FIGHT_BUTTON_SIZE = 150
REROLL_BUTTON_POSITION = (350, 50)
FIGHT_BUTTON_POSITION = (500, 400)

fight_button_image = pygame.transform.scale(
    IMAGES[ImageChoice.FIGHT_BUTTON], (FIGHT_BUTTON_SIZE, FIGHT_BUTTON_SIZE)
)
reroll_button_image = pygame.transform.scale(
    IMAGES[ImageChoice.REROLL_BUTTON], (REROLL_BUTTON_SIZE, REROLL_BUTTON_SIZE)
)

# Gold icon settings
GOLD_ICON_SIZE = 90
GOLD_ICON_POSITION = (10, 10)
gold_icon_image = pygame.transform.scale(
    IMAGES[ImageChoice.GOLD_ICON], (GOLD_ICON_SIZE, GOLD_ICON_SIZE)
)

GOLD_BACK_WIDTH = 80
GOLD_BACK_HEIGHT = 56
GOLD_BACK_POSITION = (GOLD_ICON_POSITION[0] + 60, GOLD_ICON_POSITION[1] + 16)
gold_back_image = pygame.transform.scale(
    IMAGES[ImageChoice.GOLD_BACK], (GOLD_BACK_WIDTH, GOLD_BACK_HEIGHT)
)


class TrashButton(Button):
    width_pixels = 30
    height_pixels = 40

    @classmethod
    def create_below_slot(cls, slot: CharacterSlot) -> Self:
        slot_x, slot_y = slot.position
        button_x: int = slot_x + slot.width_pixels // 2 - TrashButton.width_pixels // 2
        button_y: int = slot_y + slot.height_pixels + TrashButton.width_pixels // 5

        return cls((button_x, button_y), "Trash")

# Utility functions
@lru_cache(maxsize=128)
def get_cached_font(font_name: str, font_size: int):
    return pygame.font.SysFont(name=font_name, size=font_size)


def switch_slots(slot_a: CharacterSlot, slot_b: CharacterSlot) -> None:
    slot_a.content, slot_b.content = slot_b.content, slot_a.content
    logging.debug(f"Switched slots between {slot_a.content} and {slot_b.content}")


def draw_text(
    text_content: str,
    window: pygame.Surface,
    center_position: Vector,
    scale_ratio: float = 1,
    font_name: str = "pixel_font",
    color: tuple[int, int, int] = BLACK_COLOR,
) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = get_cached_font(font_name, font_size)
    text = text_font.render(text_content, True, color)
    text_topleft_position = (
        center_position[0] - text.get_width() / 2,
        center_position[1] - text.get_height() / 2,
    )
    window.blit(text, text_topleft_position)


class ShopState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot], shop_slots: list[CharacterSlot], trash_slot: CharacterSlot) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.shop_slots = shop_slots
        self.trash_slot = trash_slot
        self.trash_button = TrashButton.create_below_slot(trash_slot)
        self.start_combat_button = Button(
            FIGHT_BUTTON_POSITION, "Start Combat", fight_button_image
        )
        self.reroll_button = Button(
            REROLL_BUTTON_POSITION, "Reroll", reroll_button_image
        )
        self.gold = STARTING_GOLD
        self.drag_dropper       = DragDropper(ally_slots + bench_slots + [trash_slot], self)
        self.drag_dropper_shop  = DragDropper(self.shop_slots, self)

    def reset_gold(self):
        self.gold = STARTING_GOLD

    def start_state(self) -> None:
        generate_characters(self.shop_slots, CHARACTER_TIERS, TIER_PROBABILITIES)

    def is_there_allies(self) -> bool:
        return bool(self.ally_slots)

    def reroll_shop(self) -> None:
        if self.gold >= REROLL_COST:
            self.gold -= REROLL_COST
            generate_characters(self.shop_slots, CHARACTER_TIERS, TIER_PROBABILITIES)

    def loop(self, user_input: UserInput) -> None:
        self.drag_dropper.loop(user_input)
        self.drag_dropper_shop.loop(user_input)

        self.start_combat_button.refresh(user_input.mouse_position)
        if (self.start_combat_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            if not self.is_there_allies(): return
            self.next_state = StateChoice.PREPARATION
            self.reset_gold()

        self.reroll_button.refresh(user_input.mouse_position)
        if self.reroll_button.is_hovered and user_input.is_mouse1_up:
            self.reroll_shop()

        for slot in self.shop_slots:
            slot.buy_button.refresh(user_input.mouse_position)
            if slot.content and slot.buy_button.is_hovered and user_input.is_mouse1_up:
                self.buy_unit(slot)

        self.trash_button.refresh(user_input.mouse_position)
        if self.trash_button.is_hovered and user_input.is_mouse1_up:
            if not self.trash_slot.content: return
            self.trash_slot.content = None


    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def buy_unit(self, buy_slot: ShopSlot) -> None:
        for slot in self.bench_slots + self.ally_slots:
            if slot.content is None and self.spend_gold(3):
                switch_slots(slot, buy_slot)
                break


def draw_gold(shop_frame: pygame.Surface, balance: int):
    gold_text_position = (GOLD_ICON_POSITION[0] + 103, GOLD_ICON_POSITION[1] + 45)
    shop_frame.blit(gold_back_image, GOLD_BACK_POSITION)
    shop_frame.blit(gold_icon_image, GOLD_ICON_POSITION)

    gold_text = f"{balance}"
    text_color = BLACK_COLOR if balance > 0 else RED_COLOR
    draw_text(gold_text, shop_frame, gold_text_position, 3.5, "pixel_font", text_color)


class ShopRenderer(PygameRenderer):
    background_image = pygame.transform.scale(IMAGES[ImageChoice.BACKGROUND_SHOP_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def __init__(self, shop_state: ShopState) -> None:
        super().__init__()
        self.shop_state = shop_state

    def draw_frame(self):
        self.render_shop_state(self.frame, self.shop_state)

    @staticmethod
    def render_shop_state(frame: pygame.Surface, shop_state: ShopState) -> None:
        frame.blit(ShopRenderer.background_image, (0, 0))

        draw_gold(frame, shop_state.gold)

        for slot in shop_state.shop_slots:
            if slot.content:
                draw_button(frame, slot.buy_button)

        draw_button(frame, shop_state.start_combat_button)
        draw_button(frame, shop_state.reroll_button)
        draw_button(frame, shop_state.trash_button)

        draw_drag_dropper(frame, shop_state.drag_dropper_shop)
        draw_drag_dropper(frame, shop_state.drag_dropper)

