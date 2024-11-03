import pygame
import logging
from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from core.renderer import PygameRenderer
from components import character
from components.stages import EnemyGenerator, draw_stage_number
from components.character_slot import CharacterSlot, CombatSlot, draw_slot
from components.drag_dropper import DragDropper, draw_drag_dropper
from components.interactable import Button, draw_button

from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT


class PreparationState(State):
    def __init__(self, ally_slots: list[CombatSlot], bench_slots: list[CharacterSlot], enemy_slots: list[CombatSlot], enemy_generator: EnemyGenerator) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.enemy_slots = enemy_slots
        self.enemy_generator = enemy_generator
        self.drag_dropper = DragDropper(ally_slots + bench_slots)
        self.continue_button = Button((400, 500), "Continue...")

    def start_state(self) -> None:
        logging.info("Entering preparation phase")
        self.enemy_generator.generate(self.enemy_slots)

    def loop(self, user_input: UserInput) -> None:
        for slot in self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        self.continue_button.refresh(user_input.mouse_position)
        if (self.continue_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
            self.next_state = StateChoice.BATTLE
            logging.debug("Continue button clicked, switching states")

        self.drag_dropper.loop(user_input)


class PreparationRenderer(PygameRenderer):
    background_image = pygame.transform.scale(IMAGES[ImageChoice.BACKGROUND_COMBAT_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def __init__(self, preparation_state: PreparationState) -> None:
        super().__init__()
        self.preparation_state = preparation_state

    def draw_frame(self) -> None:
        self.render_preparation_state(self.frame, self.preparation_state)

    @staticmethod
    def render_preparation_state(frame, preparation_state: PreparationState) -> None:
        frame.blit(PreparationRenderer.background_image, (0, 0))

        draw_drag_dropper(frame, preparation_state.drag_dropper)

        draw_button(frame, preparation_state.continue_button )

        draw_stage_number(frame, preparation_state.enemy_generator.stage)

        for slot in preparation_state.enemy_slots:
            draw_slot(frame, slot)

            scale_ratio = 1.5 if slot.is_hovered else 1
            is_enemy_slot = slot in preparation_state.enemy_slots

            if not slot.content: continue

            character.draw_character(frame, slot.center_coordinate, slot.content, is_enemy_slot, scale_ratio = scale_ratio, slot_is_hovered = slot.is_hovered)
            
            #Reset defend indicator of enemies
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
