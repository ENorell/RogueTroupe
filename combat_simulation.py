from core.input_listener import PygameInputListener
from core.engine import PygameEngine
from core.renderer import PygameRenderer
from core.state_machine import StateMachine, State, StateChoice
from components.character import *
from components.character_slot import CharacterSlot, CombatSlot, create_shop_slots, ShopSlot, create_trash_slot
from states.combat_state import CombatState
from states.preparation_state import PreparationState
from states.shop_state import ShopState
from states.game import create_ally_slots, create_enemy_slots, create_bench_slots, GameRenderer

logging.getLogger().setLevel(logging.DEBUG)


ally_slots:  list[CombatSlot] = create_ally_slots()
enemy_slots: list[CombatSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()
shop_slots: list[ShopSlot] = create_shop_slots()
trash_slot: CharacterSlot = create_trash_slot()

ally_slots[0].content = Spinoswordaus()
ally_slots[1].content = Macedon()
ally_slots[2].content = Healamimus()
ally_slots[3].content = Archeryptrx()

enemy_slots[0].content = Tankylosaurus()
enemy_slots[1].content = Dilophmageras()
enemy_slots[2].content = Tripiketops()
enemy_slots[3].content = Dilophmageras()


combat_state = CombatState(ally_slots, enemy_slots)

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)

shop_state = ShopState(ally_slots, bench_slots, shop_slots, trash_slot)


states: dict[StateChoice, State] = {
    StateChoice.SHOP: shop_state,
    StateChoice.PREPARATION: preparation_state,
    StateChoice.BATTLE: combat_state
    }


state_machine = StateMachine(states, StateChoice.BATTLE)

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