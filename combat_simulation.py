from data.input_listener import PygameInputListener
from data.engine import PygameEngine
from data.character import *
from data.character_slot import CharacterSlot, CombatSlot
from data.combat_state import CombatState
from data.preparation_state import PreparationState
from data.shop_state import ShopState, ShopRenderer
from data.game import create_ally_slots, create_enemy_slots, create_bench_slots, GameRenderer
from data.state_machine import StateMachine, State, StateChoice
from data.logger import logging # To get baseconfig and set custom debug level
logging.getLogger().setLevel(logging.DEBUG)


ally_slots:  list[CombatSlot] = create_ally_slots()
enemy_slots: list[CombatSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()

ally_slots[0].content = Velocirougue()
ally_slots[1].content = Pterapike()
ally_slots[2].content = Healamimus()
ally_slots[3].content = Archeryptrx()
enemy_slots[0].content = Spinoswordaus()
enemy_slots[1].content = Healamimus()
enemy_slots[2].content = Spinoswordaus()
enemy_slots[3].content = Spinoswordaus()


combat_state = CombatState(ally_slots, enemy_slots)

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)

shop_state = ShopState(ally_slots, bench_slots)


states: dict[StateChoice, State] = {
    StateChoice.SHOP: shop_state,
    StateChoice.PREPARATION: preparation_state,
    StateChoice.BATTLE: combat_state
    }


state_machine = StateMachine(states, StateChoice.BATTLE)


engine = PygameEngine(
    state_machine,
    GameRenderer(),
    PygameInputListener()
)

engine.run()