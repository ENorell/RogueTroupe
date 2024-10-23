from pygame import transform
from typing import Optional, Final
import logging

from core.interfaces import UserInput
from core.renderer import PygameRenderer
from core.state_machine import State, StateChoice
from components.character import Character, draw_character
from components.character_slot import CombatSlot, draw_slot
from components.interactable import Button, draw_button, draw_text
from components.abilities import TriggerType, BasicAttack, Delay
from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_HEIGHT, DISPLAY_WIDTH


PAUSE_TIME_S: Final[float] = 0.2
CHARACTER_HOVER_SCALE_RATIO: Final[float] = 1.5


def done_triggering_abilities(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type: TriggerType) -> bool:
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if     slot.content.is_dead(): continue
        if not slot.content.ability: continue 
        if not slot.content.ability.trigger == trigger_type: continue
        if     slot.content.ability.is_done: continue

        slot.content.ability.activate(slot.content, ally_slots, enemy_slots)
        return False # We need to iterate some more
    return True # All abilities are done


def refresh_all_abilities(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type: TriggerType) -> None:
    for character in [slot.content for slot in ally_slots + enemy_slots if slot.content and slot.content.ability and slot.content.ability.trigger == trigger_type]:
        character.refresh_ability()


class BattleTurn:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.acting_slot = acting_slot
        assert acting_slot.content # We should never be here if it was empty
        self.character: Character = acting_slot.content
        
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        
        self.basic_attack = BasicAttack(acting_slot, ally_slots, enemy_slots)

        self.initial_delay = Delay(PAUSE_TIME_S)
        self.post_attack_delay = Delay(PAUSE_TIME_S)  # Delay after attack or ability
        self.is_done = False


    def start_turn(self) -> None:
        logging.debug(f"Starting turn for {self.character.name} {"(Ally)" if self.acting_slot in self.ally_slots else "(Enemy)"}")

        if self.character.is_dead():
            logging.debug(f"{self.character.name} is dead, skipping turn")
            self.end_turn()
            return


    def end_turn(self) -> None:
        # Potential end of turn effects
        self.is_done = True


    def loop(self) -> None:
        if not done_triggering_abilities(self.ally_slots, self.enemy_slots, TriggerType.TURN_START):
            return

        # Then execute attack
        if not self.basic_attack.is_done:
            self.basic_attack.activate(self.character)
            return
        
        # Delay slightly after attack
        if not self.post_attack_delay.is_done:
            self.post_attack_delay.tick()
            return
        
        self.end_turn()
            

def create_alternating_turn_order(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> list[CombatSlot]:
    return [slot for pair in zip(ally_slots, enemy_slots) for slot in pair if slot.content and not slot.content.is_dead()]

def create_simple_turn_order(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> list[CombatSlot]:
    return [slot for slot in ally_slots + enemy_slots if slot.content and not slot.content.is_dead() ]


def cleanup_dead_units(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
    """Remove dead characters from slots after a round."""
    for slot in ally_slots + enemy_slots:
        if slot.content and slot.content.is_dead():
            character_name = slot.content.name  # Store the character's name before removing
            logging.debug(f"Removing {character_name} from battlefield as they are dead.")
            slot.content = None


def shift_units_forward(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
    """Move all units forward to fill empty slots after a round."""
    for slots in [ally_slots, enemy_slots]:
        # Collect all non-empty characters
        non_empty_slots = [slot.content for slot in slots if slot.content is not None]
        
        # Set all slots to None initially
        for slot in slots:
            slot.content = None
        
        # Fill the slots with non-empty characters
        for i, character in enumerate(non_empty_slots):
            slots[i].content = character



class BattleRound:
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order: list[CombatSlot] = []
        self.current_turn: Optional[BattleTurn] = None
        self.round_start_delay = Delay(PAUSE_TIME_S)
        self.round_end_delay = Delay(PAUSE_TIME_S)
        self.is_done = False

    def start_round(self) -> None:
        self.slot_turn_order: list[CombatSlot] = create_alternating_turn_order(self.ally_slots, self.enemy_slots)
        assert self.slot_turn_order # Something is wrong if this is empty at start of turn
        
    def start_next_turn(self) -> None:
        next_slot = self.slot_turn_order.pop(0)
        assert next_slot.content

        self.current_turn = BattleTurn(next_slot, self.ally_slots, self.enemy_slots) 
        self.current_turn.start_turn()

    def end_round(self) -> None:
        cleanup_dead_units(self.ally_slots, self.enemy_slots)  # Clean up dead units at the end of the round
        shift_units_forward(self.ally_slots, self.enemy_slots)  # Shift units forward to fill empty slots
        refresh_all_abilities(self.ally_slots, self.enemy_slots, TriggerType.ROUND_START) # Reset the state of the abilities to be used again later
        refresh_all_abilities(self.ally_slots, self.enemy_slots, TriggerType.TURN_START)
        self.is_done = True
    
    def any_turns_left(self) -> bool:
        return bool(self.slot_turn_order)

    def loop(self) -> None:
        if not done_triggering_abilities(self.ally_slots, self.enemy_slots, TriggerType.ROUND_START):
            return

        if not self.round_start_delay.is_done:
            self.round_start_delay.tick()
            return

        if not self.current_turn: # Allows us to wait for start of round abilities, happens exactly once
            self.start_next_turn()
            return

        if not self.current_turn.is_done:
            self.current_turn.loop()
            return
        
        if self.any_turns_left():
            self.start_next_turn()
            return

        if not self.round_end_delay.is_done:
            self.round_end_delay.tick()
            return

        self.end_round()


def revive_ally_characters(slots: list[CombatSlot]) -> None:
    for slot in slots:
        if slot.content:
            slot.content.revive()
            logging.debug(f"Revived {slot.content.name}")

def is_everyone_dead(slots: list[CombatSlot]) -> bool:
    return all(slot.content is None or slot.content.is_dead() for slot in slots)



class CombatState(State):
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.continue_button = Button((400, 500), "Continue...")
        self.current_round: Optional[BattleRound] = None

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.round_counter = 0
        
    def start_next_round(self) -> None:
        self.round_counter += 1
        logging.info(f"Starting Round {self.round_counter}")
        self.current_round = BattleRound(self.ally_slots, self.enemy_slots)
        self.current_round.start_round()

    def is_combat_concluded(self) -> bool:
        return is_everyone_dead(self.ally_slots) or is_everyone_dead(self.enemy_slots)
    
    def user_exits_combat(self, user_input: UserInput) -> bool:
        self.continue_button.refresh(user_input.mouse_position)
        return (self.continue_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down
    
    def end_combat(self) -> None:
        logging.debug("Continue button clicked, ending combat")
        revive_ally_characters(self.ally_slots)
        self.next_state = StateChoice.SHOP

    def loop(self, user_input: UserInput) -> None:
        if not done_triggering_abilities(self.ally_slots, self.enemy_slots, TriggerType.COMBAT_START):
            return

        if not self.current_round: # Allows us to wait for start of combat abilities, happens exactly once
            self.start_next_round()
            return
        
        if not self.current_round.is_done:
            self.current_round.loop()
            return
        
        if not self.is_combat_concluded():
            self.start_next_round()
            return

        if self.user_exits_combat(user_input):
            self.end_combat()


class CombatRenderer(PygameRenderer): 
    background_image = transform.scale(IMAGES[ImageChoice.BACKGROUND_COMBAT_JUNGLE], (DISPLAY_WIDTH, DISPLAY_HEIGHT))

    def draw_frame(self, combat_state: CombatState) -> None:
        self.frame.blit(self.background_image, (0, 0))

        if combat_state.is_combat_concluded():
            draw_button(self.frame, combat_state.continue_button)
            result_text = "You lost..." if is_everyone_dead(combat_state.ally_slots) else "You won!"
            draw_text(result_text, self.frame, (400, 400))

        for slot in combat_state.ally_slots + combat_state.enemy_slots:
            draw_slot(self.frame, slot)
            if slot.content:
                is_acting = (combat_state.current_round and combat_state.current_round.current_turn and
                             combat_state.current_round.current_turn.character == slot.content and
                             not slot.content.is_dead())
                is_enemy_slot = slot in combat_state.enemy_slots
                scale_ratio = CHARACTER_HOVER_SCALE_RATIO if slot.is_hovered or is_acting else 1

                draw_character(self.frame, slot.center_coordinate, slot.content, is_enemy_slot, scale_ratio, slot.is_hovered)
