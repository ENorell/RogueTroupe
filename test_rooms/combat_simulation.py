import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from input_listener import PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer

from character import *
from character_slot import CharacterSlot, draw_slot
from interactable import Button, draw_button
from combat_state import CombatState
from preparation_state import PreparationState
from shop_state import ShopState, ShopRenderer
from game import create_ally_slots, create_enemy_slots, create_bench_slots, GameRenderer

from state_machine import StateMachine, State, StateChoice

from logger import logging
logging.getLogger().setLevel(logging.DEBUG)


ally_slots:  list[CharacterSlot] = create_ally_slots()
enemy_slots: list[CharacterSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()

ally_slots[0].content = Velocirougue()
ally_slots[1].content = Pterapike()
ally_slots[2].content = Dilophmageras()
ally_slots[3].content = Stabiraptor()
enemy_slots[0].content = Spinoswordaus()
enemy_slots[1].content = Healamimus()
enemy_slots[2].content = Macedon()
enemy_slots[3].content = Ateratops()


combat_state = CombatState(ally_slots, enemy_slots)

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)

shop_state = ShopState(ally_slots, bench_slots)


states: dict[StateChoice, State] = {
    StateChoice.SHOP: shop_state,
    StateChoice.PREPARATION: preparation_state,
    StateChoice.BATTLE: combat_state
    }


state_machine = StateMachine(states, StateChoice.PREPARATION)


engine = PygameEngine(
    state_machine,
    GameRenderer(),
    PygameInputListener()
)

engine.run()