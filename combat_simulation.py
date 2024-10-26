from core.input_listener import PygameInputListener
from core.engine import PygameEngine
from core.state_machine import StateMachine, State, StateChoice
from core.logger import logging # To get baseconfig and set custom debug level
from components.character import *
from components.character_slot import CharacterSlot, CombatSlot
from states.combat_state import CombatState
from states.preparation_state import PreparationState
from states.shop_state import ShopState, ShopRenderer
from states.game import create_ally_slots, create_enemy_slots, create_bench_slots, GameRenderer

logging.getLogger().setLevel(logging.DEBUG)


ally_slots:  list[CombatSlot] = create_ally_slots()
enemy_slots: list[CombatSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()

ally_slots[0].content = Macedon()
ally_slots[1].content = Macedon()
ally_slots[2].content = Healamimus()
ally_slots[3].content = Archeryptrx()
enemy_slots[0].content = Dilophmageras()
enemy_slots[1].content = Tripiketops()
enemy_slots[2].content = Tripiketops()
enemy_slots[3].content = Dilophmageras()


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