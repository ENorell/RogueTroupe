from typing import Self
from pygame import Surface

from core.interfaces import Loopable, UserInput
from core.renderer import PygameRenderer
from core.state_machine import StateMachine, State, StateChoice
from components.character_slot import create_ally_slots, create_enemy_slots, create_bench_slots, create_shop_slots, \
    create_trash_slot, create_reward_slots
from components.stages import StageEnemyGenerator
from states.combat_state import CombatState, CombatRenderer
from states.preparation_state import PreparationState, PreparationRenderer
from states.reward_state import RewardState, RewardRenderer
from states.shop_state import ShopState, ShopRenderer

from settings import DISPLAY_WIDTH


class NoGame(Loopable):
    def loop(self, user_input: UserInput) -> None:
        pass


class Game(StateMachine):

    @classmethod
    def new_game(cls) -> Self:
        enemy_generator = StageEnemyGenerator()

        ally_slots   = create_ally_slots()
        enemy_slots  = create_enemy_slots()
        shop_slots   = create_shop_slots()
        bench_slots  = create_bench_slots()
        trash_slot   = create_trash_slot()
        reward_slots = create_reward_slots()

        shop_state        = ShopState(ally_slots, bench_slots, shop_slots, trash_slot)
        preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots, enemy_generator)
        combat_state      = CombatState(ally_slots, enemy_slots)
        reward_state      = RewardState(ally_slots, bench_slots, reward_slots, trash_slot)

        states: dict[StateChoice, State] = {
            StateChoice.SHOP:           shop_state,
            StateChoice.PREPARATION:    preparation_state,
            StateChoice.BATTLE:         combat_state,
            StateChoice.REWARD:         reward_state
        }

        return cls(states, start_state=StateChoice.SHOP)


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

            case RewardState():
                assert isinstance(state, RewardState)
                RewardRenderer.render_reward_state(frame, state)

            case _:
                raise Exception(f"Unknown state to render: {state}")
