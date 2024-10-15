import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import UserInput
from input_listener import PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer

from character import KnightCharacter, WizardCharacter, GoblinCharacter, TrollCharacter, draw_character, draw_text
from character_slot import CharacterSlot, draw_slot
from typing import Optional
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT
from interactable import Interactable

DISTANCE_BETWEEN_SLOTS = 15
DISTANCE_CENTER_TO_SLOTS = 75
SLOT_HEIGHT = round(DISPLAY_HEIGHT / 2)


class Button(Interactable):
    width_pixels: int = 150
    height_pixels: int = 50


class MockGame:
    def __init__(self) -> None:

        self.ally_slots:  list[CharacterSlot] = []
        self.enemy_slots: list[CharacterSlot] = []
        for i in range(4):
            horisontal_postition_allies = round( DISPLAY_WIDTH/2 - DISTANCE_CENTER_TO_SLOTS - i * ( DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels) - CharacterSlot.width_pixels/2)
            self.ally_slots.append( CharacterSlot((horisontal_postition_allies, SLOT_HEIGHT)) )

            horisontal_postition_enemies = round( DISPLAY_WIDTH/2 + DISTANCE_CENTER_TO_SLOTS + i * ( DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels) - CharacterSlot.width_pixels/2)
            self.enemy_slots.append( CharacterSlot((horisontal_postition_enemies, SLOT_HEIGHT)) )

        self.ally_slots[0].content = KnightCharacter()
        self.ally_slots[1].content = KnightCharacter()
        self.ally_slots[2].content = WizardCharacter()
        self.ally_slots[3].content = WizardCharacter()

        self.enemy_slots[0].content = GoblinCharacter()
        self.enemy_slots[1].content = GoblinCharacter()
        self.enemy_slots[2].content = GoblinCharacter()
        self.enemy_slots[3].content = TrollCharacter()

        self.start_combat_button = Button((400,500))

        self.is_combat: bool = False


    def loop(self, user_input: UserInput) -> None:
        self.start_combat_button.refresh(user_input.mouse_position)
        for slot in self.ally_slots + self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        if not self.is_combat and self.start_combat_button.is_hovered and user_input.is_mouse1_down:
            self.is_combat = True

        if not self.is_combat: return

        





from pygame import Surface, Rect, draw
def draw_button(frame: Surface, button: Button) -> None:
    rect = Rect(button.position, button.size)
    draw.ellipse(frame, (9, 97, 59), rect)


class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: MockGame):
        draw_button(self.frame, loopable.start_combat_button )
                
        for slot in loopable.ally_slots + loopable.enemy_slots:
            draw_slot(self.frame, slot)
            
            if not slot.content: continue

            scale_ratio = 1.5 if slot.is_hovered else 1

            draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)


engine = PygameEngine(
    MockGame(),
    MockRenderer(),
    PygameInputListener()
)

engine.run()