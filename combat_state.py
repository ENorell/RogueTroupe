from interfaces import UserInput
from character import Character, draw_character
from character_slot import CharacterSlot, draw_slot
from settings import GAME_FPS
from state_machine import State, StateChoice
from interactable import Button, draw_button, draw_text
from renderer import PygameRenderer
from typing import Optional
import logging

class BattlePhase: #not used now, but might be necessary later if there are several components to a turn
    
    @property
    def is_done(self) -> bool:
        ...


class Delay:
    def __init__(self, delay_time_s: float) -> None:
        self.delay_time_s = delay_time_s
        self.frame_counter: int = 0

    def tick(self):
        self.frame_counter += 1

    @property    
    def is_done(self) -> bool:
        return self.frame_counter / GAME_FPS >= self.delay_time_s


class BattleTurn:
    def __init__(self, character: Character, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        self.character = character
        self.is_done = False
        self.delay = Delay(0.5)
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots

    def determine_target(self) -> None:
        relative_enemies: list[CharacterSlot] = self.ally_slots if self.character in [slot.content for slot in self.enemy_slots] else self.enemy_slots
        living_enemies = [slot.content for slot in relative_enemies if slot.content and not slot.content.is_dead()]
        self.target_character: Optional[Character] = living_enemies[0] if living_enemies else None

    def start_turn(self) -> None:
        logging.debug(f"Starting turn for {self.character.name}")
        if self.character.is_dead():
            logging.debug(f"{self.character.name} is dead, skipping turn")
            self.is_done = True
            return
        #Start of turn effects
        self.determine_target()

    def loop(self) -> None:
        if not self.delay.is_done:
            self.delay.tick()
            return
        
        if self.target_character:
            logging.debug(f"{self.character.name} attacks {self.target_character.name} for {self.character.damage}")
            self.target_character.damage_health(self.character.damage)
        else:
            logging.debug(f"{self.character.name} found no viable target and skips their turn")
        self.is_done = True


class BattleRound:
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot] ) -> None:
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order = self.get_turn_order()
        self.is_done = False

    def get_turn_order(self) -> list[BattleTurn]:
        living_characters = [slot.content for slot in self.ally_slots + self.enemy_slots if slot.content and not slot.content.is_dead()]
        logging.debug(f"Turn order created for {len(living_characters)} characters")
        return [BattleTurn(character, self.ally_slots, self.enemy_slots) for character in living_characters]

    def start_round(self) -> None:
        self.current_turn: BattleTurn = self.turn_order[0]
        self.current_turn.start_turn()

    def next_turn(self) -> None:
        self.turn_order.remove(self.current_turn)
        if not self.turn_order:
            self.is_done = True
            return
        
        self.current_turn = self.turn_order[0]
        self.current_turn.start_turn()

    def loop(self) -> None:
        if self.current_turn.is_done:
            self.next_turn()
            return
        
        self.current_turn.loop()


def is_everyone_dead(slots: list[CharacterSlot]):
    characters_alive: list[Character] = [slot.content for slot in slots if slot.content and not slot.content.is_dead() ]
    return not bool( characters_alive )

def revive_ally_characters(slots: list[CharacterSlot]) -> None:
    logging.debug(f"Attempting to revive characters in {len(slots)} slots")
    for slot in slots:
        if not slot.content:
            return
        
        slot.content.revive()
        logging.debug(f"Revived {slot.content.name}")


class CombatState(State):
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.continue_button = Button((400,500), "Continue...")

    def start_state(self) -> None:
        logging.info("Starting Combat")
        self.round_counter = 0
        self.start_new_round()
        
    def start_new_round(self) -> None:
        self.round_counter += 1
        logging.info(f"Starting Round {self.round_counter}")
        self.current_round = BattleRound(self.ally_slots, self.enemy_slots)
        self.current_round.start_round()

    def is_combat_concluded(self) -> bool:
        return is_everyone_dead(self.ally_slots) or is_everyone_dead(self.enemy_slots)
    
    def loop(self, user_input: UserInput) -> None:
        self.continue_button.refresh(user_input.mouse_position)

        if not self.current_round.is_done:
            self.current_round.loop()
            return

        if self.is_combat_concluded():
            if self.continue_button.is_hovered and user_input.is_mouse1_up:
                logging.debug("Continue button clicked, switching states")
                revive_ally_characters(self.ally_slots)
                self.next_state = StateChoice.SHOP
        else:
            self.start_new_round()


class CombatRenderer(PygameRenderer):
    def draw_frame(self, combat_state: CombatState):
        if combat_state.is_combat_concluded():
            draw_button(self.frame, combat_state.continue_button )
            conclusion_text = "You lost..." if is_everyone_dead(combat_state.ally_slots) else "You won!"
            draw_text(conclusion_text, self.frame, (400,400))
                        
        for slot in combat_state.ally_slots + combat_state.enemy_slots:
            draw_slot(self.frame, slot)
            
            if not slot.content: continue

            is_acting = combat_state.current_round.current_turn.character == slot.content and not combat_state.current_round.current_turn.character.is_dead()

            scale_ratio = 1.5 if slot.is_hovered or is_acting else 1

            draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)