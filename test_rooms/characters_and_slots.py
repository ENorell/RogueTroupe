import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from input_listener import DeafInputListener, PygameInputListener
from engine import PygameEngine
from shop_state import ShopState, ShopRenderer, BENCH_SLOT_COLOR
from preparation_state import PreparationState, PreparationRenderer
from character import Stabiraptor
from character_slot import CharacterSlot, CombatSlot, BATTLE_SLOT_COLOR

from logger import logging
logging.getLogger().setLevel(logging.DEBUG)


ally_slots = [
    CombatSlot((25 ,400), 1, BATTLE_SLOT_COLOR),
    CombatSlot((125,400), 2, BATTLE_SLOT_COLOR),
    CombatSlot((225,400), 3, BATTLE_SLOT_COLOR),
    CombatSlot((325,400), 4, BATTLE_SLOT_COLOR)
    ]

bench_slots = [
    CharacterSlot((25 ,525), BENCH_SLOT_COLOR),
    CharacterSlot((125,525), BENCH_SLOT_COLOR)
]

enemy_slots = [
    CombatSlot((425,400), 5, BATTLE_SLOT_COLOR),
    CombatSlot((525,400), 6, BATTLE_SLOT_COLOR),
    CombatSlot((625,400), 7, BATTLE_SLOT_COLOR),
    CombatSlot((725,400), 8, BATTLE_SLOT_COLOR)
    ]

ally_slots[0].content = Stabiraptor()


shop_state = ShopState(ally_slots, bench_slots)
shop_state.start_state()

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)
preparation_state.start_state()

engine = PygameEngine(
    shop_state,
    ShopRenderer(),
    PygameInputListener()
)

engine.run()