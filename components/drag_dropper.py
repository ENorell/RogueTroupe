from typing import Optional

from components.character_slot import CharacterSlot, draw_slot
from components.character import draw_character
from core.interfaces import UserInput
from core.renderer import PygameRenderer
import logging


class DragDropper:
    '''
    Governs the nasty logic needed to drag-drop characters between slots
    '''
    def __init__(self, slots: list[CharacterSlot]) -> None:
        self.slots = slots
        self.detached_slot: Optional[CharacterSlot] = None

    def get_hover_slot(self) -> Optional[CharacterSlot]:
        for slot in self.slots:
            if slot.is_hovered:
                return slot

    def switch_slots(self, slot_a: CharacterSlot, slot_b: CharacterSlot) -> None:
        slot_a_content = slot_a.content
        slot_b_content = slot_b.content

        slot_a.content = slot_b_content
        slot_b.content = slot_a_content
        logging.debug(f"Switch places between {slot_a_content} and {slot_b_content}")
        
    def loop(self, user_input: UserInput) -> None:
        self.user_input = user_input # Stored to be able to draw later...

        for slot in self.slots: 
            slot.refresh(user_input.mouse_position)

        hover_slot: Optional[CharacterSlot] = self.get_hover_slot()

        if self.detached_slot:
            if not user_input.is_mouse1_up: return # Keep dragging this frame

            if not hover_slot or hover_slot == self.detached_slot:
                self.detached_slot = None
                return

            self.switch_slots(hover_slot, self.detached_slot)
            self.detached_slot = None

        else: 
            if hover_slot and user_input.is_mouse1_down:
                if not hover_slot.content: return
                self.detached_slot = hover_slot


class DragDropRenderer(PygameRenderer):

    def draw_frame(self, drag_dropper: DragDropper):

        for slot in drag_dropper.slots:
            draw_slot(self.frame, slot)
        
        #make sure the characters are drawn on top of slots
        for slot in drag_dropper.slots:
            if not slot.content: continue

            position = drag_dropper.user_input.mouse_position if slot is drag_dropper.detached_slot else slot.center_coordinate

            scale_ratio = 1.5 if slot.is_hovered else 1

            draw_character(self.frame, position, slot.content, scale_ratio = scale_ratio)