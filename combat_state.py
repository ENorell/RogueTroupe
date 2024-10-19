from interfaces import UserInput
from character import Character, draw_character, draw_text
from character_slot import CharacterSlot, draw_slot
from settings import GAME_FPS
from state_machine import State, StateChoice
from interactable import Button

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
        #self.phases = phases
        self.character = character
        self.is_done = False
        self.delay = Delay(0.5)
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots

    def determine_target(self) -> None:
        relative_enemies: list[CharacterSlot] = self.ally_slots if self.character in [slot.content for slot in self.enemy_slots] else self.enemy_slots
        self.target_character: Character = [slot.content for slot in relative_enemies if slot.content and not slot.content.is_dead()][0]

    def start_turn(self) -> None:
        if self.character.is_dead():
            self.is_done = True
            return
        #Start of turn effects
        self.determine_target()

    def loop(self) -> None:
        if not self.delay.is_done:
            self.delay.tick()
            return
        
        self.target_character.damage_health(self.character.damage)
        self.is_done = True


class BattleRound:
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot] ) -> None:
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.turn_order = self.get_turn_order()
        self.current_turn: BattleTurn = self.turn_order[0]
        self.current_turn.start_turn()
        self.is_done = False


    def get_turn_order(self) -> list[BattleTurn]:
        characters: list[Character] = []
        for slot in self.ally_slots+self.enemy_slots:
            if not slot.content or slot.content.is_dead():
                continue
            characters.append(slot.content)

        return [BattleTurn(character, self.ally_slots, self.enemy_slots) for character in characters]
        

    def start_round(self) -> None:
        pass

    def next_round(self) -> None:
        self.turn_order.remove(self.current_turn)
        if len(self.turn_order) == 0:
            self.is_done = True
            return
        
        self.current_turn = self.turn_order[0]
        self.current_turn.start_turn()

    def loop(self) -> None:
        if self.current_turn.is_done:
            self.next_round()
            return
        
        self.current_turn.loop()


def is_everyone_dead(slots: list[CharacterSlot]):
    characters_alive: list[Character] = [slot.content for slot in slots if slot.content and not slot.content.is_dead() ]
    return not bool( characters_alive )



class CombatState(State):
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:
        super().__init__()
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.continue_button = Button((400,500), "Continue...")

    def start_state(self) -> None:
        self.current_round = BattleRound(self.ally_slots, self.enemy_slots)
        self.current_round.start_round()


    def loop(self, user_input: UserInput) -> None:
        self.continue_button.refresh(user_input.mouse_position)

        if not self.current_round.is_done:
            self.current_round.loop()
            return

        if is_everyone_dead(self.ally_slots):
            if self.continue_button.is_hovered and user_input.is_mouse1_up:
                self.next_state = StateChoice.SHOP
        elif is_everyone_dead(self.enemy_slots):
            if self.continue_button.is_hovered and user_input.is_mouse1_up:
                self.next_state = StateChoice.SHOP
        else:
            self.start_state()
