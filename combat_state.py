from interfaces import UserInput
from character import Character, draw_character
from character_slot import CharacterSlot, draw_slot
from settings import GAME_FPS, DISPLAY_HEIGHT, DISPLAY_WIDTH
from state_machine import State, StateChoice
from interactable import Button, draw_button, draw_text
from renderer import PygameRenderer
from typing import Optional
from pygame import transform, font
from images import IMAGES, ImageChoice
import logging


class Delay:
    def __init__(self, delay_time_s: float) -> None:
        self.delay_frames = int(delay_time_s * GAME_FPS)
        self.frame_counter = 0

    def tick(self) -> None:
        self.frame_counter += 1

    @property
    def is_done(self) -> bool:
        return self.frame_counter >= self.delay_frames


class BattleTurn:
    def __init__(self, character: Character, character_index: int, attacker_slots: list[CharacterSlot], defender_slots: list[CharacterSlot], battle_log: list[str]) -> None:
        self.character = character
        self.character_index = character_index
        self.attacker_slots = attacker_slots
        self.defender_slots = defender_slots
        self.battle_log = battle_log
        self.delay = Delay(1)
        self.is_done = False
        self.target_character: Optional[Character] = None
        self.post_attack_delay = Delay(1.0)  # Delay after attack or ability
        self.post_attack_phase = False

    def determine_target(self) -> None:
        for i in range(len(self.defender_slots) - 1, -1, -1):
            defender_slot = self.defender_slots[i]
            if defender_slot.content and not defender_slot.content.is_dead() and self.character.range >= i + self.character_index + 1:
                self.target_character = defender_slot.content
                self.target_character.is_defending = True
                return
        self.target_character = None

    def start_turn(self) -> None:
        logging.debug(f"Starting turn for {self.character.name}")
        if self.character.is_dead():
            logging.debug(f"{self.character.name} is dead, skipping turn")
            self.is_done = True
            return

        self.determine_target()

    def loop(self) -> None:
        if self.post_attack_phase:
            if self.post_attack_delay.is_done:
                if self.character.ability and self.character.ability.trigger == "attack":
                    self.character.ability.activate(self.character, self.attacker_slots, self.defender_slots)
                    self.battle_log.append(f"{self.character.name} uses {self.character.ability.name}!")
                self.post_attack_phase = False
                self.is_done = True
            else:
                self.post_attack_delay.tick()
        elif not self.target_character or self.delay.is_done:
            if self.target_character:
                self.target_character.damage_health(self.character.damage)
                log_message = f"{self.character.name} attacks {self.target_character.name} for {self.character.damage} damage!"
                self.battle_log.append(log_message)
                logging.debug(log_message)
                self.target_character.is_defending = False
                self.post_attack_phase = True
            else:
                log_message = f"{self.character.name} has no target to attack."
                self.battle_log.append(log_message)
                logging.debug(log_message)
                self.is_done = True
        else:
            self.delay.tick()


class BattleRound:
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot], battle_log: list[str], combat_start_abilities_triggered: bool = False) -> None:
        self.battle_log = battle_log
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
        #Alternate between each team starting at the front
        ally_turns = [BattleTurn(slot.content, i, self.ally_slots, self.enemy_slots, self.battle_log) for i, slot in enumerate(self.ally_slots) if slot.content and not slot.content.is_dead()]
        enemy_turns = [BattleTurn(slot.content, i, self.enemy_slots, self.ally_slots, self.battle_log) for i, slot in enumerate(self.enemy_slots) if slot.content and not slot.content.is_dead()]
        self.turn_order = [turn for pair in zip(ally_turns, enemy_turns) for turn in pair] + ally_turns[len(enemy_turns):] + enemy_turns[len(ally_turns):]

    def start_round(self) -> None:
        if not self.combat_start_abilities_triggered:
            self.setup_combat_start_abilities()
        if self.turn_order:
            self.current_turn = self.turn_order.pop(0)
            self.current_turn.start_turn()
        else:
            self.cleanup_dead_units()  # Clean up dead units at the end of the round
            self.shift_units_forward()  # Shift units forward to fill empty slots
            self.round_end_phase = True

    def loop(self) -> None:
        if self.round_end_phase:
            if self.round_end_delay.is_done:
                self.round_end_phase = False
                self.is_done = True
            else:
                self.round_end_delay.tick()
        elif self.current_turn and self.current_turn.is_done:
            self.cleanup_dead_units()  # Clean up dead units after each turn is complete
            self.shift_units_forward()  # Shift units forward to fill empty slots
            self.start_round()
        elif self.current_turn:
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


def revive_ally_characters(slots: list[CharacterSlot]) -> None:
    for slot in slots:
        if slot.content:
            slot.content.revive()
            logging.debug(f"Revived {slot.content.name}")


def is_everyone_dead(slots: list[CharacterSlot]) -> bool:
    return all(slot.content is None or slot.content.is_dead() for slot in slots)


class CombatState(State):
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.continue_button = Button((400, 500), "Continue...")
        self.battle_log: list[str] = []
        self.combat_start_abilities_triggered = False

    def start_state(self) -> None:
        self.combat_start_abilities_triggered = False
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

        if self.is_combat_concluded():
            if (self.continue_button.is_hovered and user_input.is_mouse1_up) or user_input.is_space_key_down:
                logging.debug("Continue button clicked, switching states")
                revive_ally_characters(self.ally_slots)
                self.next_state = StateChoice.SHOP
        elif not self.current_round.is_done:
            self.current_round.loop()
        else:
            self.start_new_round()


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
                draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio=1.5 if slot.is_hovered or is_acting else 1)

        if combat_state.battle_log:
            text_font = font.SysFont(None, 32)
            for i, log_entry in enumerate(combat_state.battle_log[-5:]):
                text_surface = text_font.render(log_entry, True, (255, 255, 255))
                self.frame.blit(text_surface, (30, 160 + i * 32))
