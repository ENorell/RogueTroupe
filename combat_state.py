from interfaces import UserInput
from character import Character, draw_character
from character_slot import CharacterSlot, draw_slot
from settings import GAME_FPS
from state_machine import State, StateChoice
from interactable import Button, draw_button, draw_text
from renderer import PygameRenderer
from typing import Optional
import pygame

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
    def __init__(self, character: Character, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot], battle_log: list[str]) -> None:
        self.character = character
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.battle_log = battle_log
        self.delay = Delay(0.5)
        self.is_done = False
        self.target_character: Optional[Character] = None

    def determine_target(self) -> None:
        defenders = self.enemy_slots if self.character in [slot.content for slot in self.ally_slots] else self.ally_slots
        for i in range(len(defenders) - 1, -1, -1):
            defender_slot = defenders[i]
            if defender_slot.content and not defender_slot.content.is_dead() and self.character.range >= i + 1:
                self.target_character = defender_slot.content
                self.target_character.is_defending = True
                return
        self.target_character = None

    def start_turn(self) -> None:
        if self.character.is_dead():
            self.is_done = True
            return
        self.determine_target()

    def loop(self) -> None:
        if not self.target_character or self.delay.is_done:
            if self.target_character:
                self.target_character.damage_health(self.character.damage)
                self.battle_log.append(f"{self.character.name} attacks {self.target_character.name} for {self.character.damage} damage!")
                self.target_character.is_defending = False
            else:
                self.battle_log.append(f"{self.character.name} has no target to attack.")
            self.is_done = True
        else:
            self.delay.tick()


class BattleRound:
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot], battle_log: list[str]) -> None:
        self.turn_order = [BattleTurn(slot.content, ally_slots, enemy_slots, battle_log) for slot in ally_slots + enemy_slots if slot.content and not slot.content.is_dead()]
        self.current_turn: Optional[BattleTurn] = None
        self.is_done = False

    def start_round(self) -> None:
        if self.turn_order:
            self.current_turn = self.turn_order.pop(0)
            self.current_turn.start_turn()
        else:
            self.is_done = True

    def loop(self) -> None:
        if self.current_turn and self.current_turn.is_done:
            self.start_round()
        elif self.current_turn:
            self.current_turn.loop()


def revive_ally_characters(slots: list[CharacterSlot]) -> None:
    for slot in slots:
        if slot.content:
            slot.content.revive()


def is_everyone_dead(slots: list[CharacterSlot]) -> bool:
    return all(slot.content is None or slot.content.is_dead() for slot in slots)


class CombatState(State):
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.continue_button = Button((400, 500), "Continue...")
        self.battle_log: list[str] = []
        self.current_round: Optional[BattleRound] = None

    def start_state(self) -> None:
        self.start_new_round()

    def start_new_round(self) -> None:
        self.current_round = BattleRound(self.ally_slots, self.enemy_slots, self.battle_log)
        self.current_round.start_round()

    def is_combat_concluded(self) -> bool:
        return is_everyone_dead(self.ally_slots) or is_everyone_dead(self.enemy_slots)

    def loop(self, user_input: UserInput) -> None:
        self.continue_button.refresh(user_input.mouse_position)

        if not self.current_round.is_done:
            self.current_round.loop()
        elif self.is_combat_concluded() and self.continue_button.is_hovered and user_input.is_mouse1_up:
            revive_ally_characters(self.ally_slots)
            self.next_state = StateChoice.SHOP
        elif self.current_round.is_done:
            self.start_new_round()


class CombatRenderer(PygameRenderer):
    def draw_frame(self, combat_state: CombatState) -> None:
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
            font = pygame.font.SysFont(None, 32)
            for i, log_entry in enumerate(combat_state.battle_log[-5:]):
                text_surface = font.render(log_entry, True, (255, 255, 255))
                self.frame.blit(text_surface, (30, 160 + i * 32))
