import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from input_listener import DeafInputListener, PygameInputListener
from engine import PygameEngine
from shop_state import ShopState, ShopRenderer, BENCH_SLOT_COLOR
from preparation_state import PreparationState, PreparationRenderer
from character import WizardCharacter
from character_slot import CharacterSlot, BATTLE_SLOT_COLOR


ally_slots = [
    CharacterSlot((25 ,400), BATTLE_SLOT_COLOR),
    CharacterSlot((125,400), BATTLE_SLOT_COLOR),
    CharacterSlot((225,400), BATTLE_SLOT_COLOR),
    CharacterSlot((325,400), BATTLE_SLOT_COLOR)
    ]

bench_slots = [
    CharacterSlot((25 ,525), BENCH_SLOT_COLOR),
    CharacterSlot((125,525), BENCH_SLOT_COLOR)
]

enemy_slots = [
    CharacterSlot((425,400), BATTLE_SLOT_COLOR),
    CharacterSlot((525,400), BATTLE_SLOT_COLOR),
    CharacterSlot((625,400), BATTLE_SLOT_COLOR),
    CharacterSlot((725,400), BATTLE_SLOT_COLOR)
    ]

ally_slots[0].content = WizardCharacter()


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