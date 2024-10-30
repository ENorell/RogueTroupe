import pygame
from typing import Final
import logging

from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from components.character import (
    Character,
    draw_character,
    Aepycamelus,
    Brontotherium,
    Cranioceras,
    Glypto,
    Gorgono,
    Mammoth,
    Phorus,
    Sabre,
    Sloth,
    Trilo,
)
from components.character_slot import (
    CharacterSlot,
    CombatSlot,
    draw_slot,
    generate_characters,
)
from components.drag_dropper import DragDropper, DragDropRenderer
from components.interactable import Button, draw_button

from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT


ENEMY_POOL: Final[list[type[Character]]] = [
    Aepycamelus,
    Brontotherium,
    Cranioceras,
    Glypto,
    Gorgono,
    Mammoth,
    Phorus,
    Sabre,
    Sloth,
    Trilo,
]


class PreparationState(State):
    def __init__(
        self,
        ally_slots: list[CombatSlot],
        bench_slots: list[CharacterSlot],
        enemy_slots: list[CombatSlot],
    ) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.enemy_slots = enemy_slots
        self.drag_dropper = DragDropper(ally_slots + bench_slots)
        self.continue_button = Button((400, 500), "Continue...")

    def start_state(self) -> None:
        logging.info("Entering preparation phase")
        generate_characters(self.enemy_slots, ENEMY_POOL)

    def loop(self, user_input: UserInput) -> None:
        for slot in self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        self.continue_button.refresh(user_input.mouse_position)
        if (
            self.continue_button.is_hovered and user_input.is_mouse1_up
        ) or user_input.is_space_key_down:
            self.next_state = StateChoice.BATTLE
            logging.debug("Continue button clicked, switching states")

        self.drag_dropper.loop(user_input)


class PreparationRenderer(DragDropRenderer):
    background_image = pygame.transform.scale(
        IMAGES[ImageChoice.BACKGROUND_COMBAT_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    )

    def draw_frame(self, preparation_state: PreparationState):
        self.frame.blit(self.background_image, (0, 0))

        super().draw_frame(preparation_state.drag_dropper)

        draw_button(self.frame, preparation_state.continue_button)

        for slot in preparation_state.enemy_slots:
            draw_slot(self.frame, slot)

            scale_ratio = 1.5 if slot.is_hovered else 1
            is_enemy_slot = slot in preparation_state.enemy_slots

            if slot.content:
                draw_character(
                    self.frame,
                    slot.center_coordinate,
                    slot.content,
                    is_enemy_slot,
                    scale_ratio=scale_ratio,
                    slot_is_hovered=slot.is_hovered,
                )

            # Reset defend indicator of enemies
            slot.content.is_defending = False

        # Use the defending indicator to highlight who character will attack
        for slot in preparation_state.ally_slots:
            has_target = False
            if slot.content:
                for enemy_slot in preparation_state.enemy_slots:
                    if enemy_slot.coordinate - slot.coordinate == slot.content.range:
                        has_target = True
                        if slot.is_hovered:
                            enemy_slot.content.is_defending = True
                # if not has_target:
                #     slot.content.is_attacking = True
