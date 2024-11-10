import logging
import pygame
from typing import Optional, Sequence, Final

from components.drag_dropper import DragDropper, draw_drag_dropper
from core.renderer import PygameRenderer
from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from components.character_slot import CharacterSlot, CombatSlot, ShopSlot, draw_slot
from components.interactable import Button, draw_button
from components.character import draw_character
from components.character_pool import generate_characters, CHARACTER_TIERS, TIER_PROBABILITIES
from settings import Vector, DISPLAY_WIDTH, DISPLAY_HEIGHT
from states.shop_state import fight_button_image, TrashButton
from assets.images import IMAGES, ImageChoice


SKIP_BUTTON_POSITION: Final[Vector] = (500,400)


def get_vacant_slot(slots: Sequence[CharacterSlot]) -> Optional[CharacterSlot]:
    for slot in slots:
        if not slot.content:
            return slot


class RewardState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot], reward_slots: list[ShopSlot], trash_slot: CharacterSlot) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.trash_slot = trash_slot
        self.bench_slots = bench_slots
        self.reward_slots = reward_slots
        self.skip_button = Button( SKIP_BUTTON_POSITION, "Skip", fight_button_image )
        self.trash_button = TrashButton.create_below_slot(trash_slot)
        self.drag_dropper = DragDropper(ally_slots + bench_slots + [trash_slot])

    def start_state(self) -> None:
        logging.info("Entering reward phase")
        generate_characters(self.reward_slots, CHARACTER_TIERS, TIER_PROBABILITIES)

    def exit_state(self) -> None:
        self.next_state = StateChoice.PREPARATION

    def loop(self, user_input: UserInput) -> None:
        for slot in self.ally_slots + self.bench_slots + self.reward_slots:
            slot.refresh(user_input.mouse_position)

        for slot in self.reward_slots:
            slot.buy_button.refresh(user_input.mouse_position)
            if not slot.content: continue
            if not (slot.buy_button.is_hovered and user_input.is_mouse1_up): continue

            vacant_slot = get_vacant_slot(self.ally_slots + self.bench_slots)
            if not vacant_slot:
                logging.info("Could not select reward due to lack of space")
                continue

            vacant_slot.content = slot.content
            self.exit_state()
            logging.debug("Reward chosen, switching states")

        self.skip_button.refresh(user_input.mouse_position)
        if (self.skip_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            self.exit_state()
            logging.debug("Skip button clicked, switching states")

        self.drag_dropper.loop(user_input)

        self.trash_button.refresh(user_input.mouse_position)
        if self.trash_button.is_hovered and user_input.is_mouse1_up:
            if not self.trash_slot.content: return
            self.trash_slot.content = None


class RewardRenderer(PygameRenderer):
    background_image = pygame.transform.scale(IMAGES[ImageChoice.BACKGROUND_COMBAT_JUNGLE],
                                              (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def __init__(self, reward_state: RewardState) -> None:
        super().__init__()
        self.reward_state = reward_state

    def draw_frame(self) -> None:
        self.render_reward_state(self.frame, self.reward_state)

    @staticmethod
    def render_reward_state(frame, reward_state: RewardState) -> None:
        frame.blit(RewardRenderer.background_image, (0, 0))

        draw_button(frame, reward_state.skip_button)
        draw_button(frame, reward_state.trash_button)

        for slot in reward_state.reward_slots:
            draw_button(frame, slot.buy_button)

        for slot in reward_state.reward_slots:
            draw_slot(frame, slot)

            scale_ratio = 1.5 if slot.is_hovered else 1

            if not slot.content: continue

            draw_character(frame, slot.center_coordinate, slot.content, is_enemy= False, scale_ratio=scale_ratio, slot_is_hovered=slot.is_hovered)

        draw_drag_dropper(frame, reward_state.drag_dropper)