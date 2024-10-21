from interfaces import UserInput
from character import Character, draw_character
from character_slot import CombatSlot, draw_slot
from abilities import Ability, TriggerType
from settings import GAME_FPS, DISPLAY_HEIGHT, DISPLAY_WIDTH
from state_machine import State, StateChoice
from interactable import Button, draw_button, draw_text
from renderer import PygameRenderer
from typing import Optional, Final
from pygame import transform, font
from images import IMAGES, ImageChoice
import logging


TURN_ATTACK_DELAY_TIME_S: Final[float] = 1
CHARACTER_HOVER_SCALE_RATIO: Final[float] = 1.5


class Delay:
    def __init__(self, delay_time_s: float) -> None:
        self.delay_frames = int(delay_time_s * GAME_FPS)
        self.frame_counter = 0

    def tick(self) -> None:
        self.frame_counter += 1

    @property
    def is_done(self) -> bool:
        return self.frame_counter >= self.delay_frames


# This function hints to the need of some sort of grid class that can hold the slots and calculate distances etc. 
def distance_between(slot_a: CombatSlot, slot_b: CombatSlot) -> int:
    return abs( slot_a.coordinate - slot_b.coordinate )


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


class BasicAttack:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.acting_slot = acting_slot
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
    
        self.is_done: bool = False
        self.victim: Optional[Character] = None

    def activate(self, attacker: Character) -> None:
        assert self.victim
        self.victim.damage_health(attacker.damage)
        self.victim.is_defending = False

        logging.debug(f"{attacker.name} attacks {self.victim.name} for {attacker.damage} damage!")
        
        if self.victim.is_dead(): logging.debug(f"{self.victim.name} died")

        self.is_done = True

    def determine_target(self, attacker: Character) -> None:
        defender_slots: list[CombatSlot] = self.ally_slots if self.acting_slot in self.enemy_slots else self.enemy_slots

        for target_slot in reversed( defender_slots ): # Prioritize slots farther away?
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not attacker.range >= distance_between(self.acting_slot, target_slot): continue

            target_candidate.is_defending = True
            
            self.victim = target_candidate
            return
        
        logging.debug(f"{attacker.name} has no target to attack (range {attacker.range}).")


    def target_found(self) -> bool:
        return bool(self.victim)


class BattleTurn:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.acting_slot = acting_slot
        assert acting_slot.content # We should never be here if it was empty
        self.character: Character = acting_slot.content
        
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        
        self.basic_attack = BasicAttack(acting_slot, ally_slots, enemy_slots)

        self.initial_delay = Delay(TURN_ATTACK_DELAY_TIME_S)
        self.post_attack_delay = Delay(TURN_ATTACK_DELAY_TIME_S)  # Delay after attack or ability
        self.is_done = False


    def start_turn(self) -> None:
        logging.debug(f"Starting turn for {self.character.name} {"(Ally)" if self.acting_slot in self.ally_slots else "(Enemy)"}")

        if self.character.is_dead():
            logging.debug(f"{self.character.name} is dead, skipping turn")
            self.end_turn()
            return
        
        self.basic_attack.determine_target(self.character)

    def end_turn(self) -> None:
        # Potential end of turn effects
        self.is_done = True

    def loop(self) -> None:
        if not done_triggering_abilities(self.ally_slots, self.enemy_slots, TriggerType.TURN_START):
            return
        
        # Delay game slightly before acting
        if not self.initial_delay.is_done:
            self.initial_delay.tick()
            return
        
        # Exit if no viable target is found
        if not self.basic_attack.target_found():
            self.end_turn()
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
            


class BattleRound:
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot]) -> None:
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order = []
        self.current_turn: Optional[BattleTurn] = None
        self.round_end_delay = Delay(1.5)
        self.is_done = False

    #def setup_turn_order(self) -> None:
    #    ally_turns = [BattleTurn(slot.content, i, self.ally_slots, self.enemy_slots, self.battle_log) for i, slot in enumerate(self.ally_slots) if slot.content and not slot.content.is_dead()]
    #    enemy_turns = [BattleTurn(slot.content, i, self.enemy_slots, self.ally_slots, self.battle_log) for i, slot in enumerate(self.enemy_slots) if slot.content and not slot.content.is_dead()]
    #    self.turn_order = [turn for pair in zip(ally_turns, enemy_turns) for turn in pair] + ally_turns[len(enemy_turns):] + enemy_turns[len(ally_turns):]

    def start_round(self) -> None:
        self.slot_turn_order: list[CombatSlot] = [slot for slot in self.ally_slots + self.enemy_slots if slot.content and not slot.content.is_dead() ]
        assert self.slot_turn_order # Something is wrong if this is empty att start of turn
        
        self.start_next_turn()
        
    def start_next_turn(self) -> None:
        if not self.slot_turn_order:
            self.end_round()
            return
        
        next_slot = self.slot_turn_order.pop(0)
        assert next_slot.content

        self.current_turn = BattleTurn(next_slot, self.ally_slots, self.enemy_slots) 
        self.current_turn.start_turn()

    def end_round(self) -> None:
        if not self.round_end_delay.is_done:
            self.round_end_delay.tick()
            return

        self.cleanup_dead_units()  # Clean up dead units at the end of the round
        self.shift_units_forward()  # Shift units forward to fill empty slots
        self.is_done = True
    
    def cleanup_dead_units(self) -> None:
        """Remove dead characters from slots after a round."""
        for slot in self.ally_slots + self.enemy_slots:
            if slot.content and slot.content.is_dead():
                character_name = slot.content.name  # Store the character's name before removing
                logging.debug(f"Removing {character_name} from battlefield as they are dead.")
                slot.content = None

    def shift_units_forward(self) -> None:
        """Move all units forward to fill empty slots after a round."""
        for slots in [self.ally_slots, self.enemy_slots]:
            # Collect all non-empty characters
            non_empty_slots = [slot.content for slot in slots if slot.content is not None]
            
            # Set all slots to None initially
            for slot in slots:
                slot.content = None
            
            # Fill the slots with non-empty characters
            for i, character in enumerate(non_empty_slots):
                slots[i].content = character

    def loop(self) -> None:
        if not done_triggering_abilities(self.ally_slots, self.enemy_slots, TriggerType.ROUND_START):
            return

        assert self.current_turn # Something is wrong if we have gotten here with no turn
        
        if not self.current_turn.is_done:
            self.current_turn.loop()
            return

        self.start_next_turn()


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

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.round_counter = 0
        self.start_next_round()
        
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

                draw_character(self.frame, slot.center_coordinate, slot.content, is_enemy_slot, scale_ratio)
