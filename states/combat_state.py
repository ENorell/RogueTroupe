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


PAUSE_TIME_S: Final[float] = 0.2
CHARACTER_HOVER_SCALE_RATIO: Final[float] = 1.5



def get_character_ability(character: Character, trigger_type: TriggerType) -> Optional[Ability]:
    if not character.ability_type: return
    if not character.ability_type.trigger == trigger_type: return
    return character.ability_type.from_plan(character)

def get_trigger_abilities(ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type: TriggerType) -> list[Ability]:
    ability_queue: list[Ability] = []
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if     slot.content.is_dead(): continue
        if not slot.content.ability_type: continue 
        if not slot.content.ability_type.trigger == trigger_type: continue
        ability = slot.content.ability_type.from_plan(slot.content)
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
    """
    Handles trigger order for a mix of combat/round start abilities and triggered abilities
    """
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], planned_abilities: list[Ability]) -> None:
        self.is_done: bool = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.planned_abilities: list[Ability] = planned_abilities
        self.triggered_abilities: list[Ability] = []
        self.current_ability: Optional[Ability] = None

    @classmethod
    def from_trigger(cls, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], trigger_type) -> Self:
        planned_abilities = get_trigger_abilities(ally_slots, enemy_slots, trigger_type)
        instance = cls(ally_slots, enemy_slots, planned_abilities)
        instance.next_ability()
        return instance
    
    @classmethod
    def turn_abilities(cls, caster: Character, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> Self:
        basic_attack = BasicAttack.from_plan(caster)
        starting_ability = get_character_ability(caster, TriggerType.TURN_START)
        planned_abilities: list[Ability] = [starting_ability, basic_attack] if starting_ability else [basic_attack]
        instance = cls(ally_slots, enemy_slots, planned_abilities)
        instance.next_ability()
        return instance

    def next_ability(self) -> None:
        if not self.planned_abilities:
            self.is_done = True
            return
        self.current_ability = self.planned_abilities.pop(0)

    def activate(self) -> None:
        self.triggered_abilities.extend( empty_ability_queue(self.ally_slots, self.enemy_slots) )

        assert self.current_ability
        if not self.current_ability.is_done:
            self.current_ability.activate(self.ally_slots, self.enemy_slots)
            return
        
        if not is_all_done(self.triggered_abilities):
            run_remaining_abilities(self.triggered_abilities, self.ally_slots, self.enemy_slots)
            return

        self.next_ability()



class BattleTurn:
    def __init__(self, character: Character, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], turn_abilities: AbilityHandler) -> None:
        self.is_done = False
        self.acting_slot = acting_slot
        self.character = character
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_abilities = turn_abilities
        self.post_attack_delay = Delay(PAUSE_TIME_S)  # Delay after attack or ability

    @classmethod
    def start_new_turn(cls, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> Self:
        assert acting_slot.content  # We should never be here if it was empty
        character: Character = acting_slot.content
        turn_abilities: AbilityHandler = AbilityHandler.turn_abilities(character, ally_slots, enemy_slots)
        new_turn = cls(character, acting_slot, ally_slots, enemy_slots, turn_abilities)
        return new_turn

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
    return [slot for pair in zip(ally_slots, enemy_slots) for slot in pair if slot.content and not slot.content.is_dead()] + ally_slots[len(enemy_slots):] + enemy_slots[len(ally_slots):]

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
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], slot_turn_order: list[CombatSlot], starting_abilities: AbilityHandler) -> None:
        self.is_done = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.slot_turn_order: list[CombatSlot] = slot_turn_order
        self.starting_abilities: AbilityHandler = starting_abilities
        self.current_turn: Optional[BattleTurn] = None
        self.round_start_delay = Delay(PAUSE_TIME_S)
        self.round_end_delay = Delay(PAUSE_TIME_S)

    @classmethod
    def start_new_round(cls, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> Self:
        slot_turn_order: list[CombatSlot] = create_alternating_turn_order(ally_slots, enemy_slots)
        assert slot_turn_order # Something is wrong if this is empty, no loving characters?
        starting_abilities = AbilityHandler.from_trigger(ally_slots, enemy_slots, TriggerType.ROUND_START)
        new_round = cls(ally_slots, enemy_slots, slot_turn_order, starting_abilities)
        return new_round

    def start_next_turn(self) -> None:
        next_slot = self.slot_turn_order.pop(0)
        assert next_slot.content

        if next_slot.content.is_dead():
            logging.debug(f"{next_slot.content.name} is dead, skipping turn")
            return # Try again next frame

        self.current_turn = BattleTurn.start_new_turn(next_slot, self.ally_slots, self.enemy_slots)

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
        self.round_counter = 0
        self.starting_abilities: Optional[AbilityHandler] = None

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.starting_abilities = AbilityHandler.from_trigger(self.ally_slots, self.enemy_slots, TriggerType.COMBAT_START) 
        
    def start_next_round(self) -> None:
        self.round_counter += 1
        logging.info(f"Starting Round {self.round_counter}")
        self.current_round = BattleRound.start_new_round(self.ally_slots, self.enemy_slots)

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
        assert self.starting_abilities

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
                is_acting = (combat_state.current_round and
                             combat_state.current_round.current_turn and
                             combat_state.current_round.current_turn.character == slot.content and
                             not slot.content.is_dead()
                             or slot.content.is_attacking)
                is_enemy_slot = slot in combat_state.enemy_slots
                scale_ratio = CHARACTER_HOVER_SCALE_RATIO if slot.is_hovered or is_acting else 1

                draw_character(self.frame, slot.center_coordinate, slot.content, is_enemy_slot, scale_ratio, slot.is_hovered)
