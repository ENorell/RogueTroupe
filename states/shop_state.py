from typing import Final
from pygame import transform, font, Surface

from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from components.character import Character, Tankylosaurus, Macedon, Healamimus, Dilophmageras, Tripiketops, Velocirougue, Archeryptrx, Alchemixus, Bardomimus, Battlemagodon, Naturalis, Necrorex, Quetza, Krytoraptor, Triceros
from components.character_slot import CharacterSlot, CombatSlot, ShopSlot, generate_characters
from components.drag_dropper import DragDropper, DragDropRenderer
from components.interactable import Button, draw_button
from assets.images import IMAGES, ImageChoice
from settings import Vector, Color, DISPLAY_WIDTH, DISPLAY_HEIGHT, DEFAULT_TEXT_SIZE, BLACK_COLOR
import logging
from functools import lru_cache

SHOP_POOL: list[type[Character]] = [
    Tankylosaurus,
    Macedon,
    Healamimus,
    Dilophmageras,
    Tripiketops,
    Velocirougue,
    Archeryptrx,
    Alchemixus,
    Bardomimus,
    Battlemagodon,
    Naturalis,
    Necrorex,
    Quetza,
    Krytoraptor,
    Triceros
]

SHOP_TOP_LEFT_POSITION: Final[Vector] = (170, 320)
SHOP_SLOT_NR_ROWS: Final[int] = 1
SHOP_SLOT_NR_COLS: Final[int] = 4
SHOP_SLOT_DISTANCE_X: Final[int] = 60
SHOP_SLOT_DISTANCE_Y: Final[int] = 80
SHOP_SLOT_COLOR: Final[Color] = (119, 64, 36)
BENCH_SLOT_COLOR: Final[Color] = (54, 68, 90)

STARTING_GOLD: Final[int] = 10
REROLL_COST: Final[int] = 1

REROLL_BUTTON_SIZE = 100
FIGHT_BUTTON_SIZE = 150
REROLL_BUTTON_POSITION = (350, 50)
FIGHT_BUTTON_POSITION = (500, 400)
fight_button_image = transform.scale(IMAGES[ImageChoice.FIGHT_BUTTON], (FIGHT_BUTTON_SIZE, FIGHT_BUTTON_SIZE))
reroll_button_image = transform.scale(IMAGES[ImageChoice.REROLL_BUTTON], (REROLL_BUTTON_SIZE, REROLL_BUTTON_SIZE))

GOLD_BUTTON_SIZE = 100
GOLD_BUTTON_POSITION = (350, 50)
gold_icon_image = transform.scale(IMAGES[ImageChoice.GOLD_ICON], (GOLD_BUTTON_SIZE, GOLD_BUTTON_SIZE))


def switch_slots(slot_a: CharacterSlot, slot_b: CharacterSlot) -> None:
    slot_a_content = slot_a.content
    slot_b_content = slot_b.content

    slot_a.content = slot_b_content
    slot_b.content = slot_a_content
    logging.debug(f"Switch places between {slot_a_content} and {slot_b_content}")

@lru_cache(maxsize=128)
def get_cached_font(font_name: str, font_size: int):
    return font.SysFont(name=font_name, size=font_size)


def draw_text(text_content: str, window: Surface, center_position: Vector, scale_ratio: float = 1, font_name: str = "pixel_font", color: tuple[int, int, int] = BLACK_COLOR) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = get_cached_font(font_name, font_size)
    text = text_font.render(text_content, True, color)
    text_topleft_position = (center_position[0] - text.get_width() / 2, center_position[1] - text.get_height() / 2)
    window.blit(text, text_topleft_position)

def create_shop_slots() -> list[ShopSlot]:
    top_left_x, top_left_y = SHOP_TOP_LEFT_POSITION
    slots: list[ShopSlot] = []
    for row in range(SHOP_SLOT_NR_ROWS):
        for col in range(SHOP_SLOT_NR_COLS):
            x_position = top_left_x + col * (ShopSlot.width_pixels + SHOP_SLOT_DISTANCE_X)
            y_position = top_left_y + row * (ShopSlot.height_pixels + SHOP_SLOT_DISTANCE_Y)
            slot = ShopSlot((x_position, y_position), SHOP_SLOT_COLOR)
            slots.append(slot)
    return slots


class ShopState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.shop_slots: list[CharacterSlot] = create_shop_slots()
        
        self.start_combat_button = Button(FIGHT_BUTTON_POSITION, "Start Combat", fight_button_image)
        self.reroll_button = Button(REROLL_BUTTON_POSITION, "Reroll", reroll_button_image)
        self.gold = STARTING_GOLD
        #self.drag_dropper = DragDropper(ally_slots + bench_slots + self.shop_slots, self)
        self.drag_dropper = DragDropper(ally_slots + bench_slots, self)
        self.drag_dropper_shop = DragDropper(self.shop_slots, self)

    def reset_gold(self):
        self.gold = 10

    def start_state(self) -> None:
        generate_characters(self.shop_slots, SHOP_POOL)

    def reroll_shop(self) -> None:
        if self.gold >= REROLL_COST:
            self.gold -= REROLL_COST
            generate_characters(self.shop_slots, SHOP_POOL)

    def loop(self, user_input: UserInput) -> None:
        self.drag_dropper.loop(user_input)
        self.drag_dropper_shop.loop(user_input)

        self.start_combat_button.refresh(user_input.mouse_position)
        if (self.start_combat_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            self.next_state = StateChoice.PREPARATION
            self.gold = STARTING_GOLD

        self.reroll_button.refresh(user_input.mouse_position)
        if self.reroll_button.is_hovered and user_input.is_mouse1_up:
            self.reroll_shop()
        
        # Loop through each shop slot to check for buy button press
        for slot in self.shop_slots:
            slot.buy_button.refresh(user_input.mouse_position)
            if slot.buy_button.is_hovered and user_input.is_mouse1_up:
                self.buy_unit(slot)

    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def buy_unit(self, buy_slot: ShopSlot) -> None:
        #Try to add to Bench otherwise add to team
        for slot in self.bench_slots + self.ally_slots:
            if slot.content is None:
                #Check if money to spend
                if self.spend_gold(3):
                    switch_slots(slot, buy_slot)
                    break



class ShopRenderer(DragDropRenderer):
    background_image = transform.scale(IMAGES[ImageChoice.BACKGROUND_SHOP_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def draw_frame(self, shop: ShopState):
        self.frame.blit(self.background_image, (0, 0))


        # Add buy buttons to shop slots
        for slot in shop.shop_slots:
            if slot.content:
                draw_button(self.frame, slot.buy_button)

        draw_button(self.frame, shop.start_combat_button)
        draw_button(self.frame, shop.reroll_button)

        super().draw_frame(shop.drag_dropper_shop)
        super().draw_frame(shop.drag_dropper)
        




        # Draw the current gold amount on the screen
        gold_text = f"Gold: {shop.gold}"
        gold_position = (50, 30)  # You can adjust this position as needed
        gold_color = (255, 215, 0)  # Gold color
        draw_text(gold_text, self.frame, gold_position, 2, "pixel_font", gold_color)
