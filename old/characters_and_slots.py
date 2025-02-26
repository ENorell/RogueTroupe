from core.input_listener import DeafInputListener, PygameInputListener
from core.engine import PygameEngine
from components.stages import StageEnemyGenerator
from states.shop_state import ShopState, ShopRenderer
from states.preparation_state import PreparationState, PreparationRenderer
from states.reward_state import RewardState, RewardRenderer
from components.character_pool import Stabiraptor
from components.character_slot import CharacterSlot, CombatSlot, BATTLE_SLOT_COLOR, ShopSlot
from core.logger import logging
logging.getLogger().setLevel(logging.DEBUG)


ally_slots = [
    CombatSlot((25 ,400), 1, BATTLE_SLOT_COLOR),
    CombatSlot((125,400), 2, BATTLE_SLOT_COLOR),
    CombatSlot((225,400), 3, BATTLE_SLOT_COLOR),
    CombatSlot((325,400), 4, BATTLE_SLOT_COLOR)
    ]

bench_slots = [
    CharacterSlot((25 ,525), BATTLE_SLOT_COLOR),
    CharacterSlot((125,525), BATTLE_SLOT_COLOR)
]

enemy_slots = [
    CombatSlot((425,400), 5, BATTLE_SLOT_COLOR),
    CombatSlot((525,400), 6, BATTLE_SLOT_COLOR),
    CombatSlot((625,400), 7, BATTLE_SLOT_COLOR),
    CombatSlot((725,400), 8, BATTLE_SLOT_COLOR)
    ]

shop_slots = [
    ShopSlot((225, 300), BATTLE_SLOT_COLOR),
    ShopSlot((325, 300), BATTLE_SLOT_COLOR),
    ShopSlot((425, 300), BATTLE_SLOT_COLOR),
    ShopSlot((525, 300), BATTLE_SLOT_COLOR)
    ]

reward_slots = [
    ShopSlot((225, 300), BATTLE_SLOT_COLOR),
    ShopSlot((325, 300), BATTLE_SLOT_COLOR)
    ]


trash_slot = CharacterSlot((100, 700), BATTLE_SLOT_COLOR)

ally_slots[0].content = Stabiraptor()


shop_state = ShopState(ally_slots, bench_slots, shop_slots, trash_slot)
shop_state.start_state()

enemy_generator = StageEnemyGenerator()

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots, enemy_generator)
preparation_state.start_state()

reward_state = RewardState(ally_slots, bench_slots, reward_slots, trash_slot)
reward_state.start_state()

engine = PygameEngine(
    reward_state,
    RewardRenderer(reward_state),
    PygameInputListener()
)

engine.run()