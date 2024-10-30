from typing import Final
from pygame import Surface

from core.interfaces import Loopable, UserInput
from core.renderer import PygameRenderer
from core.state_machine import StateMachine, State, StateChoice
from components.character_slot import CharacterSlot, CombatSlot, BATTLE_SLOT_COLOR
from states.combat_state import CombatState, CombatRenderer
from states.preparation_state import PreparationState, PreparationRenderer
from states.shop_state import ShopState, ShopRenderer, BENCH_SLOT_COLOR

from settings import DISPLAY_WIDTH

NR_BATTLE_SLOTS_PER_TEAM: Final[int] = 4
NR_BENCH_SLOTS_PER_TEAM: Final[int] = 2
DISTANCE_BETWEEN_SLOTS: Final[int] = 15
DISTANCE_CENTER_TO_SLOTS: Final[int] = 75
SLOT_HEIGHT: Final[int] = 400
BENCH_HEIGHT: Final[int] = 500
SCREEN_CENTER: Final[int] = round(DISPLAY_WIDTH / 2)

class NoGame(Loopable):
    def loop(self, user_input: UserInput) -> None:
        pass

def create_ally_slots() -> list[CombatSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER - DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BATTLE_SLOTS_PER_TEAM):
        position_x = first_slot_position - slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        coordinate = NR_BATTLE_SLOTS_PER_TEAM - slot_nr
        slots.append(CombatSlot((position_x, SLOT_HEIGHT), coordinate, BATTLE_SLOT_COLOR))
    return slots

def create_enemy_slots() -> list[CombatSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER + DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BATTLE_SLOTS_PER_TEAM):
        position_x = first_slot_position + slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        coordinate = slot_nr + 1 + NR_BATTLE_SLOTS_PER_TEAM
        slots.append(CombatSlot((position_x, SLOT_HEIGHT), coordinate, BATTLE_SLOT_COLOR))
    return slots

def create_bench_slots() -> list[CharacterSlot]:
    slots = []
    first_slot_position = SCREEN_CENTER - DISTANCE_CENTER_TO_SLOTS - round(CharacterSlot.width_pixels / 2)
    for slot_nr in range(NR_BENCH_SLOTS_PER_TEAM):
        position_x = first_slot_position - slot_nr * (DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels)
        slots.append(CharacterSlot((position_x, BENCH_HEIGHT), BENCH_SLOT_COLOR))
    return slots


class Game(StateMachine):

    def __init__(self) -> None:

        ally_slots  = create_ally_slots()
        enemy_slots = create_enemy_slots()
        bench_slots = create_bench_slots()

        shop_state        = ShopState(ally_slots, bench_slots)
        preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)
        combat_state      = CombatState(ally_slots, enemy_slots)

        states: dict[StateChoice, State] = {
            StateChoice.SHOP: shop_state,
            StateChoice.PREPARATION: preparation_state,
            StateChoice.BATTLE: combat_state
        }

        super().__init__(states, start_state=StateChoice.SHOP)


class GameRenderer(PygameRenderer):
    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game

    def draw_frame(self):
        self.render_game(self.frame, self.game.state)

    @staticmethod
    def render_game(frame: Surface, state: State):
        # Set the appropriate background image based on the game state
        match state:
            case CombatState():
                assert isinstance(state, CombatState)
                CombatRenderer.render_combat_state(frame, state)

            case PreparationState():
                assert isinstance(state, PreparationState)
                PreparationRenderer.render_preparation_state(frame, state)

            case ShopState():
                assert isinstance(state, ShopState)
                ShopRenderer.render_shop_state(frame, state)

            case _:
                raise Exception(f"Unknown state to render: {state}")
