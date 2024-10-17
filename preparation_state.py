from interfaces import UserInput
from state_machine import State
from character import Character, KnightCharacter, WizardCharacter, TrollCharacter, GoblinCharacter, draw_character
from character_slot import CharacterSlot, draw_slot
from drag_dropper import DragDropper, DragDropRenderer
from random import choice


ENEMY_POOL: list[Character] = [
    KnightCharacter(),
    WizardCharacter(),
    GoblinCharacter(),
    TrollCharacter()
]


def generate_enemies(slots: list[CharacterSlot]) -> None:
    for slot in slots:
        slot.content = choice(ENEMY_POOL)


class PreparationState(State):
    def __init__(self, ally_slots: list[CharacterSlot], bench_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.bench_slots = bench_slots
        self.enemy_slots = enemy_slots
        self.drag_dropper = DragDropper(ally_slots + bench_slots)

    def start_state(self) -> None:
        generate_enemies(self.enemy_slots)

    def loop(self, user_input: UserInput) -> None:
        for slot in self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        self.drag_dropper.loop(user_input)


class PreparationRenderer(DragDropRenderer):

    def draw_frame(self, preparation_state: PreparationState):
        super().draw_frame(preparation_state.drag_dropper)

        for slot in preparation_state.enemy_slots:
            draw_slot(self.frame, slot)

            scale_ratio = 1.5 if slot.is_hovered else 1

            if slot.content:  draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)
