from interfaces import UserInput
from state_machine import State, StateChoice
from character import Character, Character, draw_character, Spinoswordaus, Stabiraptor, Pterapike, Ateratops
from character_slot import CharacterSlot, draw_slot, generate_characters
from drag_dropper import DragDropper, DragDropRenderer
from interactable import Button, draw_button


ENEMY_POOL: list[type] = [
    Spinoswordaus,
    Stabiraptor,
    Pterapike,
    Ateratops
]


class PreparationState(State):
    def __init__(self, ally_slots: list[CharacterSlot], bench_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.enemy_slots = enemy_slots
        self.drag_dropper = DragDropper(ally_slots + bench_slots)
        self.continue_button = Button((400,500), "Continue...")

    def start_state(self) -> None:
        generate_characters(self.enemy_slots, ENEMY_POOL, True)

    def loop(self, user_input: UserInput) -> None:
        for slot in self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        self.continue_button.refresh(user_input.mouse_position)
        if self.continue_button.is_hovered and user_input.is_mouse1_up:
            self.next_state = StateChoice.BATTLE

        self.drag_dropper.loop(user_input)


class PreparationRenderer(DragDropRenderer):

    def draw_frame(self, preparation_state: PreparationState):
        super().draw_frame(preparation_state.drag_dropper)

        draw_button(self.frame, preparation_state.continue_button )

        for slot in preparation_state.enemy_slots:
            draw_slot(self.frame, slot)

            scale_ratio = 1.5 if slot.is_hovered else 1

            if slot.content:  draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)
