import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import UserInput
from input_listener import PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer
from game_renderer import GameRenderer

from character import KnightCharacter, WizardCharacter, GoblinCharacter, TrollCharacter, Character, draw_character, draw_text
from character_slot import CharacterSlot, draw_slot
from interactable import Button, draw_button
from combat_state import CombatState
from preparation_state import PreparationState
from shop_state import ShopState, ShopRenderer
from game import create_ally_slots, create_enemy_slots, create_bench_slots

from state_machine import StateMachine, State, StateChoice


ally_slots:  list[CharacterSlot] = create_ally_slots()
enemy_slots: list[CharacterSlot] = create_enemy_slots()
bench_slots: list[CharacterSlot] = create_bench_slots()

ally_slots[0].content = KnightCharacter()
ally_slots[1].content = KnightCharacter()
ally_slots[2].content = WizardCharacter()
ally_slots[3].content = WizardCharacter()
enemy_slots[0].content = GoblinCharacter()
enemy_slots[1].content = GoblinCharacter()
enemy_slots[2].content = GoblinCharacter()
enemy_slots[3].content = TrollCharacter()


class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: CombatState):
        
        draw_button(self.frame, loopable.continue_button )
                
        for slot in loopable.ally_slots + loopable.enemy_slots:
            draw_slot(self.frame, slot)
            
            if not slot.content: continue

            is_acting = loopable.current_round.current_turn.character == slot.content and not loopable.current_round.current_turn.character.is_dead()

            scale_ratio = 1.5 if slot.is_hovered or is_acting else 1

            draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)


class MockRenderer2(PygameRenderer):
    def __init__(self) -> None:
        super().__init__()
        self.shop_renderer = ShopRenderer()

    def draw_frame(self, state_machine: StateMachine):
        if isinstance(state_machine.state, CombatState):
            draw_button(self.frame, state_machine.state.continue_button )
                    
            for slot in state_machine.state.ally_slots + state_machine.state.enemy_slots:
                draw_slot(self.frame, slot)
                
                if not slot.content: continue

                is_acting = state_machine.state.current_round.current_turn.character == slot.content and not state_machine.state.current_round.current_turn.character.is_dead()

                scale_ratio = 1.5 if slot.is_hovered or is_acting else 1

                draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)

        elif isinstance(state_machine.state, ShopState):
            self.shop_renderer.draw_frame(state_machine.state)


combat_state = CombatState(ally_slots, enemy_slots)
#combat_state.start_state()

preparation_state = PreparationState(ally_slots, bench_slots, enemy_slots)
#preparation_state.start_state()

shop_state = ShopState(ally_slots, bench_slots)
#shop_state.start_state()

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