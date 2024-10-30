from typing import Optional
import logging
import pygame
from pygame import Surface, Rect, draw, transform
from components.character_slot import CharacterSlot, ShopSlot, draw_slot
from components.character import draw_character
from core.interfaces import UserInput
from core.renderer import PygameRenderer
from settings import Vector, DEFAULT_HOVER_SCALE_RATIO


def switch_slots(slot_a: CharacterSlot, slot_b: CharacterSlot) -> None:
    slot_a_content = slot_a.content
    slot_b_content = slot_b.content

    slot_a.content = slot_b_content
    slot_b.content = slot_a_content
    logging.debug(f"Switch places between {slot_a_content} and {slot_b_content}")


class DragDropper:
    """
    Governs the nasty logic needed to drag-drop characters between slots
    """
    def __init__(self, slots: list[CharacterSlot], shop_state: "ShopState" = None) -> None:
        self.slots = slots
        self.detached_slot: Optional[CharacterSlot] = None
        self._mouse_position: Optional[Vector] = None
        self.shop_state = shop_state  # Reference to the entire shop state

    @property
    def mouse_position(self) -> Vector:
        assert self._mouse_position
        return self._mouse_position

    def get_hover_slot(self) -> Optional[CharacterSlot]:
        for slot in self.slots:
            if slot.is_hovered:
                return slot

    def loop(self, user_input: UserInput) -> None:
        self._mouse_position = user_input.mouse_position  # Stored to be able to draw later...

        for slot in self.slots:
            slot.refresh(user_input.mouse_position)

        hover_slot: Optional[CharacterSlot] = self.get_hover_slot()

        if self.detached_slot:
            if not user_input.is_mouse1_up:
                return  # Keep dragging this frame

            if not hover_slot or hover_slot == self.detached_slot:
                self.detached_slot = None
                return

            switch_slots(hover_slot, self.detached_slot)

            self.detached_slot = None

        else:
            if hover_slot and user_input.is_mouse1_down:
                if not hover_slot.content:
                    return
                self.detached_slot = hover_slot


class DragDropRenderer(PygameRenderer):
    def draw_frame(self, drag_dropper: DragDropper):

        # Draw the slots first
        for slot in drag_dropper.slots:
            draw_slot(self.frame, slot)
        

        # Draw characters on top of slots, except for the hovered slot
        hovered_slot = None
        for slot in drag_dropper.slots:
            if not slot.content:
                continue

            if slot.is_hovered:
                hovered_slot = slot  # Save the hovered slot for later
                continue

            position = (
                drag_dropper.mouse_position
                if slot is drag_dropper.detached_slot
                else slot.center_coordinate
            )
            scale_ratio = DEFAULT_HOVER_SCALE_RATIO if slot.is_hovered else 1

            draw_character(
                self.frame,
                position,
                slot.content,
                scale_ratio=scale_ratio,
                slot_is_hovered=slot.is_hovered,
            )

        # Draw the hovered slot's character last to ensure its on top
        if hovered_slot:
            position = (
                drag_dropper.mouse_position
                if hovered_slot is drag_dropper.detached_slot
                else hovered_slot.center_coordinate
            )
            assert hovered_slot.content
            draw_character(
                self.frame,
                position,
                hovered_slot.content,
                scale_ratio=DEFAULT_HOVER_SCALE_RATIO,
                slot_is_hovered=True,
            )


