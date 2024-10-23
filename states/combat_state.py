from pygame import transform
from typing import Optional, Final
import logging

from core.interfaces import UserInput
from core.renderer import PygameRenderer
from core.state_machine import State, StateChoice
from components.character import Character, draw_character
from components.character_slot import CombatSlot, draw_slot
from components.interactable import Button, draw_button, draw_text
from components.abilities import Ability, TriggerType, Delay, distance_between
from assets.images import IMAGES, ImageChoice
from settings import DISPLAY_HEIGHT, DISPLAY_WIDTH


PAUSE_TIME_S: Final[float] = 1
CHARACTER_HOVER_SCALE_RATIO: Final[float] = 1.5


class AbilityHandler:
    '''
    Handles the execution of abilities regardless of trigger
    '''
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.is_done = False
        self.abilities: dict[Character, Ability] = {}

    def setup_all(self, trigger_type: TriggerType) -> None:
        for slot in self.ally_slots + self.enemy_slots:
            if not slot.content: continue
            self.setup_single(slot.content, trigger_type)
            

    def setup_single(self, caster: Character, trigger_type: TriggerType) -> None:
        if     caster.is_dead(): return
        if not caster.ability_type: return 
        if not caster.ability_type.trigger == trigger_type: return

        self.abilities[caster] = caster.ability_type() # Instantiate the class here, then throw it away when we are done


    def activate(self) -> None:
        for character, ability in self.abilities.items():
            if not ability.is_done:
                ability.activate(character, self.ally_slots, self.enemy_slots)
                return
        self.is_done = True



class BasicAttack(Ability):
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        super().__init__()
        self.acting_slot = acting_slot
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
    
        self.targeting_delay = Delay(1)
        self.victim: Optional[Character] = None
        self.on_attack_ability = AbilityHandler(ally_slots, enemy_slots)
        self.on_defend_ability = AbilityHandler(ally_slots, enemy_slots)

    def determine_target(self, caster: Character) -> None:
        self.on_attack_ability.setup_single(caster, TriggerType.ATTACK)

        defender_slots: list[CombatSlot] = self.ally_slots if self.acting_slot in self.enemy_slots else self.enemy_slots

        for target_slot in reversed( defender_slots ): # Prioritize slots farther away?
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not caster.range >= distance_between(self.acting_slot, target_slot): continue

            target_candidate.is_defending = True
            self.on_defend_ability.setup_single(caster, TriggerType.DEFEND)

            self.victim = target_candidate
            return
        
        logging.debug(f"{caster.name} has no target to attack (range {caster.range}).")
        self.is_done = True

    def activate(self, caster: Character, *_) -> None:
        # Search for target character, stop early if none found
        if not self.victim:
            self.determine_target(caster)
            return
        
        if not self.on_attack_ability.is_done:
            self.on_attack_ability.activate()
            return
        
        if not self.targeting_delay.is_done:
            self.targeting_delay.tick()
            return
        
        if not self.on_defend_ability.is_done:
            self.on_defend_ability.activate()
            return

        self.victim.damage_health(caster.damage)
        self.victim.is_defending = False

        logging.debug(f"{caster.name} attacks {self.victim.name} for {caster.damage} damage!")

        self.is_done = True


class BattleTurn:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.acting_slot = acting_slot
        assert acting_slot.content # We should never be here if it was empty
        self.character: Character = acting_slot.content
        
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        
        self.starting_abilities = AbilityHandler(ally_slots, enemy_slots)
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
        
        self.starting_abilities.setup_single(self.character, TriggerType.TURN_START)


    def end_turn(self) -> None:
        # Potential end of turn effects
        self.is_done = True


    def loop(self) -> None:
        if not self.starting_abilities.is_done:
            self.starting_abilities.activate()
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
        self.starting_abilities = AbilityHandler(ally_slots, enemy_slots)
        self.round_start_delay = Delay(PAUSE_TIME_S)
        self.round_end_delay = Delay(PAUSE_TIME_S)
        self.is_done = False

    def start_round(self) -> None:
        self.slot_turn_order: list[CombatSlot] = create_alternating_turn_order(self.ally_slots, self.enemy_slots)
        assert self.slot_turn_order # Something is wrong if this is empty at start of turn
        self.starting_abilities.setup_all(TriggerType.ROUND_START)
        
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
        self.starting_abilities = AbilityHandler(ally_slots, enemy_slots)

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.round_counter = 0
        self.starting_abilities.setup_all(TriggerType.COMBAT_START)
        
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
