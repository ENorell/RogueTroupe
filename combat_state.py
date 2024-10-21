from interfaces import UserInput
from character import Character, draw_character
from character_slot import CharacterSlot, CombatSlot, draw_slot
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


class BattleTurn:
    def __init__(self, acting_slot: CombatSlot, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], battle_log: list[str]) -> None:
        self.acting_slot = acting_slot
        assert acting_slot.content # We should never be here if it was empty
        self.character: Character = acting_slot.content
        
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.battle_log = battle_log
        self.delay = Delay(TURN_ATTACK_DELAY_TIME_S)
        self.is_done = False
        self.target_character: Optional[Character] = None
        self.post_attack_delay = Delay(1.0)  # Delay after attack or ability
        self.post_attack_phase = False

    def determine_target(self) -> Optional[Character]:
        defender_slots = self.ally_slots if self.acting_slot in self.enemy_slots else self.enemy_slots

        for target_slot in reversed( defender_slots ):
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not self.character.range >= distance_between(self.acting_slot, target_slot): continue

            target_candidate.is_defending = True
            return target_candidate


    def start_turn(self) -> None:
        logging.debug(f"Starting turn for {self.character.name} {"(Ally)" if self.acting_slot in self.ally_slots else "(Enemy)"}")

        if self.character.is_dead():
            logging.debug(f"{self.character.name} is dead, skipping turn")
            self.is_done = True
            return
        
        self.target_character = self.determine_target()

    def end_turn(self) -> None:
        # Potential end of turn effects
        self.is_done = True

    def loop(self) -> None:
        # Delay game slightly before acting
        if not self.delay.is_done:
            self.delay.tick()
            return
        
        # Exit if no viable target is found
        if not self.target_character:
            log_message = f"{self.character.name} has no target to attack (range {self.character.range})."
            self.battle_log.append(log_message)
            logging.debug(log_message)
            self.end_turn()
            return

        # Then execute attack
        self.target_character.damage_health(self.character.damage)
        log_message = f"{self.character.name} attacks {self.target_character.name} for {self.character.damage} damage!"
        self.battle_log.append(log_message)
        logging.debug(log_message)
        self.target_character.is_defending = False
        if self.target_character.is_dead(): logging.debug(f"{self.target_character.name} died")
        
        self.end_turn()
            


class BattleRound:
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], battle_log: list[str], combat_start_abilities_triggered: bool = False) -> None:
        self.battle_log = battle_log
        self.is_done = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order = []
        self.current_turn: Optional[BattleTurn] = None
        self.round_end_delay = Delay(1.5)  # Delay after round ends
        self.round_end_phase = False
        self.ally_turn = True
        self.combat_start_abilities_triggered = combat_start_abilities_triggered

        self.setup_turn_order()

    def setup_combat_start_abilities(self) -> None:
        # Activate abilities triggered at combat start
        if not self.combat_start_abilities_triggered:
            for slot in self.ally_slots + self.enemy_slots:
                if slot.content and slot.content.ability and slot.content.ability.trigger == "combat_start":
                    slot.content.ability.activate(slot.content, self.ally_slots, self.enemy_slots)
                    self.battle_log.append(f"{slot.content.name} uses {slot.content.ability.name}!")
            self.combat_start_abilities_triggered = True

    def setup_turn_order(self) -> None:
        ally_turns = [BattleTurn(slot.content, i, self.ally_slots, self.enemy_slots, self.battle_log) for i, slot in enumerate(self.ally_slots) if slot.content and not slot.content.is_dead()]
        enemy_turns = [BattleTurn(slot.content, i, self.enemy_slots, self.ally_slots, self.battle_log) for i, slot in enumerate(self.enemy_slots) if slot.content and not slot.content.is_dead()]
        self.turn_order = [turn for pair in zip(ally_turns, enemy_turns) for turn in pair] + ally_turns[len(enemy_turns):] + enemy_turns[len(ally_turns):]

    def start_round(self) -> None:
        if not self.combat_start_abilities_triggered:
            self.setup_combat_start_abilities()
        
        self.slot_turn_order: list[CombatSlot] = [slot for slot in self.ally_slots + self.enemy_slots if slot.content and not slot.content.is_dead() ]
        
        self.start_next_turn()
        
    def start_next_turn(self) -> None:
        if not self.slot_turn_order:
            self.end_round()
            return
        
        next_slot = self.slot_turn_order.pop(0)
        assert next_slot.content

        self.current_turn = BattleTurn(next_slot, self.ally_slots, self.enemy_slots, self.battle_log) 
        self.current_turn.start_turn()

    def end_round(self) -> None:
        # Potential end of round effects
        self.cleanup_dead_units()  # Clean up dead units at the end of the round
        self.shift_units_forward()  # Shift units forward to fill empty slots
        self.is_done = True

    def loop(self) -> None:
        assert self.current_turn # Something is wrong if we have gotten here with no turn
        
        if self.current_turn.is_done:
            self.start_next_turn()
            return

        self.current_turn.loop()
    
    def cleanup_dead_units(self) -> None:
        """Remove dead characters from slots after a round."""
        for slot in self.ally_slots + self.enemy_slots:
            if slot.content and slot.content.is_dead():
                character_name = slot.content.name  # Store the character's name before removing
                logging.debug(f"Removing {character_name} from battlefield as they are dead.")
                self.battle_log.append(f"{character_name} has been removed from the battlefield due to being defeated.")
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

    @property
    def is_done(self) -> bool:
        return not self.turn_order and (not self.current_turn or self.current_turn.is_done)


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
        self.battle_log: list[str] = []
        self.combat_start_abilities_triggered = False

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.round_counter = 0
        self.start_new_round()
        
    def start_new_round(self) -> None:
        self.round_counter += 1
        logging.info(f"Starting Round {self.round_counter}")
        self.current_round = BattleRound(self.ally_slots, self.enemy_slots, self.battle_log, self.combat_start_abilities_triggered)
        if not self.combat_start_abilities_triggered:
            self.current_round.setup_combat_start_abilities()
            self.combat_start_abilities_triggered = True
        self.current_round.start_round()

    def is_combat_concluded(self) -> bool:
        return is_everyone_dead(self.ally_slots) or is_everyone_dead(self.enemy_slots)

    def loop(self, user_input: UserInput) -> None:
        self.continue_button.refresh(user_input.mouse_position)

        if self.current_round.is_done:
            self.start_new_round()
            return

        if self.is_combat_concluded():
            if (self.continue_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
                logging.debug("Continue button clicked, switching states")
                revive_ally_characters(self.ally_slots)
                self.next_state = StateChoice.SHOP
            return
            
        self.current_round.loop()


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

        if combat_state.battle_log:
            text_font = font.SysFont(None, 32)
            for i, log_entry in enumerate(combat_state.battle_log[-5:]):
                text_surface = text_font.render(log_entry, True, (255, 255, 255))
                self.frame.blit(text_surface, (30, 160 + i * 32))
