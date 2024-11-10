import logging
from core.input_listener import PygameInputListener
from core.engine import PygameEngine
from core.renderer import PygameRenderer
from core.state_machine import StateMachine, State, StateChoice
from components.character_pool import *
from components.character_slot import CharacterSlot, CombatSlot, create_shop_slots, ShopSlot, create_trash_slot, \
    create_reward_slots
from states.combat_state import CombatState
from states.preparation_state import PreparationState
from states.reward_state import RewardState
from states.shop_state import ShopState
from states.game import create_ally_slots, create_enemy_slots, create_bench_slots, GameRenderer
from components.stages import StageEnemyGenerator

logging.getLogger().setLevel(logging.DEBUG)


ally_slots:  list[CombatSlot] = create_ally_slots()
enemy_slots: list[CombatSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()
shop_slots: list[ShopSlot] = create_shop_slots()
trash_slot: CharacterSlot = create_trash_slot()
reward_slots: list[ShopSlot] = create_reward_slots()

ally_slots[0].content = Spinoswordaus()
ally_slots[1].content = Macedon()
ally_slots[2].content = Healamimus()
ally_slots[3].content = Archeryptrx()

enemy_slots[0].content = Tankylosaurus()
enemy_slots[1].content = Dilophmageras()
enemy_slots[2].content = Tripiketops()
enemy_slots[3].content = Dilophmageras()

enemy_generator = StageEnemyGenerator()


combat_state = CombatState(ally_slots, enemy_slots)

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots, enemy_generator)

shop_state = ShopState(ally_slots, bench_slots, shop_slots, trash_slot)

reward_state = RewardState(ally_slots, bench_slots, reward_slots, trash_slot)


states: dict[StateChoice, State] = {
    StateChoice.SHOP: shop_state,
    StateChoice.PREPARATION: preparation_state,
    StateChoice.BATTLE: combat_state,
    StateChoice.REWARD: reward_state
    }


state_machine = StateMachine(states, StateChoice.REWARD)

class MockRenderer(PygameRenderer):
    def __init__(self, game: StateMachine):
        super().__init__()
        self.game = game

    def draw_frame(self):
        GameRenderer.render_game(self.frame, self.game.state)


engine = PygameEngine(
    state_machine,
    MockRenderer(state_machine),
    PygameInputListener()
)

engine.run()