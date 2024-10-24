from pygame import transform
from typing import Optional, Final, Self
import logging

from core.interfaces import UserInput
from core.renderer import PygameRenderer
from core.state_machine import State, StateChoice
from components.character import Character, draw_character
from components.character_slot import CombatSlot, draw_slot
from components.interactable import Button, draw_button, draw_text
from components.abilities import Ability, TriggerType, Delay, BasicAttack
from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_HEIGHT, DISPLAY_WIDTH


PAUSE_TIME_S: Final[float] = 1
CHARACTER_HOVER_SCALE_RATIO: Final[float] = 1.5



def get_character_ability(character: Character, trigger_type: TriggerType) -> Optional[Ability]:
    if not character.ability_type: return
    if not character.ability_type.trigger == trigger_type: return
    return character.ability_type(character)

def get_trigger_abilities(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type: TriggerType) -> list[Ability]:
    ability_queue: list[Ability] = []
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if     slot.content.is_dead(): continue
        if not slot.content.ability_type: continue 
        if not slot.content.ability_type.trigger == trigger_type: continue
        ability = slot.content.ability_type(slot.content)
        ability_queue.append(ability)
    return ability_queue

def empty_ability_queue(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> list[Ability]:
    ability_queue: list[Ability] = []
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if not slot.content.ability_queue: continue
        ability_queue.extend(slot.content.ability_queue[:]) # Make a shallow copy
        slot.content.ability_queue.clear() # Empty the queue
    return ability_queue


def is_all_done(abilities: list[Ability]) -> bool:
    for ability in abilities:
        if not ability.is_done:
            return False
    return True

def run_remaining_abilities(abilities: list[Ability], ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
    for ability in abilities:
        if not ability.is_done:
            ability.activate(ally_slots, enemy_slots)


class AbilityHandler:
    '''
    Handles trigger order for a mix of combat/round start abilities and triggered abilities
    '''
    
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.is_done: bool = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.planned_abilities: list[Ability] = []
        self.triggered_abilities: list[Ability] = []
        

    @classmethod
    def from_trigger(cls, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type) -> Self:
        instance = cls(ally_slots, enemy_slots)
        instance.planned_abilities = get_trigger_abilities(ally_slots, enemy_slots, trigger_type)
        instance.next_ability()
        return instance
    
    @classmethod
    def from_abilities(cls, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], abilities: list[Ability]) -> Self:
        instance = cls(ally_slots, enemy_slots)
        instance.planned_abilities = abilities
        instance.next_ability()
        return instance
    
    @classmethod
    def turn_abilities(cls, caster: Character, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> Self:
        instance = cls(ally_slots, enemy_slots)
        basic_attack = BasicAttack(caster)
        starting_ability = get_character_ability(caster, TriggerType.TURN_START)
        instance.planned_abilities = [starting_ability, basic_attack] if starting_ability else [basic_attack]
        instance.next_ability()
        return instance

    def next_ability(self) -> None:
        if not self.planned_abilities:
            self.is_done = True
            return
        self.current_ability = self.planned_abilities.pop(0)

    def activate(self) -> None:
        self.triggered_abilities.extend( empty_ability_queue(self.ally_slots, self.enemy_slots) )

        if not self.current_ability.is_done:
            self.current_ability.activate(self.ally_slots, self.enemy_slots)
            return
        
        if not is_all_done(self.triggered_abilities):
            run_remaining_abilities(self.triggered_abilities, self.ally_slots, self.enemy_slots)
            return

        self.next_ability()



class BattleTurn:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.is_done = False
        self.acting_slot = acting_slot
        assert acting_slot.content # We should never be here if it was empty
        self.character: Character = acting_slot.content
        
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        
        self.turn_abilities = AbilityHandler.turn_abilities(self.character, self.ally_slots, self.enemy_slots)

        self.post_attack_delay = Delay(PAUSE_TIME_S)  # Delay after attack or ability

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
        # subscribe to stream of new triggered abilities for characters
        if not self.turn_abilities.is_done:
            self.turn_abilities.activate()
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
        self.is_done = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order: list[CombatSlot] = []
        self.current_turn: Optional[BattleTurn] = None
        self.round_start_delay = Delay(PAUSE_TIME_S)
        self.round_end_delay = Delay(PAUSE_TIME_S)

    def start_round(self) -> None:
        self.slot_turn_order: list[CombatSlot] = create_alternating_turn_order(self.ally_slots, self.enemy_slots)
        assert self.slot_turn_order # Something is wrong if this is empty at start of turn
        self.starting_abilities = AbilityHandler.from_trigger(self.ally_slots, self.enemy_slots, TriggerType.ROUND_START)
        
    def start_next_turn(self) -> None:
        next_slot = self.slot_turn_order.pop(0)
        assert next_slot.content

        self.current_turn = BattleTurn(next_slot, self.ally_slots, self.enemy_slots) 
        self.current_turn.start_turn()

    def end_round(self) -> None:
        cleanup_dead_units(self.ally_slots, self.enemy_slots)  # Clean up dead units at the end of the round
        shift_units_forward(self.ally_slots, self.enemy_slots)  # Shift units forward to fill empty slots
        self.is_done = True
    
    def any_turns_left(self) -> bool:
        return bool(self.slot_turn_order)

    def loop(self) -> None:
        if not self.starting_abilities.is_done:
            self.starting_abilities.activate()
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
        self.starting_abilities = AbilityHandler.from_trigger(self.ally_slots, self.enemy_slots, TriggerType.COMBAT_START) 
        
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
        if not self.starting_abilities.is_done:
            self.starting_abilities.activate()
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
