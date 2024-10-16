import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import UserInput
from input_listener import PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer

from character import KnightCharacter, WizardCharacter, GoblinCharacter, TrollCharacter, Character, draw_character, draw_text
from character_slot import CharacterSlot, draw_slot
from typing import Optional
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_FPS
from interactable import Interactable

DISTANCE_BETWEEN_SLOTS = 15
DISTANCE_CENTER_TO_SLOTS = 75
SLOT_HEIGHT = round(DISPLAY_HEIGHT / 2)


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
    def __init__(self, character: Character, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot]) -> None:#, phases: list[BattlePhase]) -> None:
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
    def __init__(self, ally_slots: list[CharacterSlot], enemy_slots: list[CharacterSlot] ) -> None:#, turn_order: list[BattleTurn]) -> None:
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



class Button(Interactable):
    width_pixels: int = 150
    height_pixels: int = 50


def is_everyone_dead(slots: list[CharacterSlot]):
    characters_alive: list[Character] = [slot.content for slot in slots if slot.content and not slot.content.is_dead() ]
    return not bool( characters_alive )


class MockGame:
    def __init__(self) -> None:

        self.ally_slots:  list[CharacterSlot] = []
        self.enemy_slots: list[CharacterSlot] = []
        for i in range(4):
            horisontal_postition_allies = round( DISPLAY_WIDTH/2 - DISTANCE_CENTER_TO_SLOTS - i * ( DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels) - CharacterSlot.width_pixels/2)
            self.ally_slots.append( CharacterSlot((horisontal_postition_allies, SLOT_HEIGHT)) )

            horisontal_postition_enemies = round( DISPLAY_WIDTH/2 + DISTANCE_CENTER_TO_SLOTS + i * ( DISTANCE_BETWEEN_SLOTS + CharacterSlot.width_pixels) - CharacterSlot.width_pixels/2)
            self.enemy_slots.append( CharacterSlot((horisontal_postition_enemies, SLOT_HEIGHT)) )

        self.ally_slots[0].content = KnightCharacter()
        self.ally_slots[1].content = KnightCharacter()
        self.ally_slots[2].content = WizardCharacter()
        self.ally_slots[3].content = WizardCharacter()

        self.enemy_slots[0].content = GoblinCharacter()
        self.enemy_slots[1].content = GoblinCharacter()
        self.enemy_slots[2].content = GoblinCharacter()
        self.enemy_slots[3].content = TrollCharacter()

        self.start_combat_button = Button((400,500))

        self.is_combat: bool = False

        self.current_round = BattleRound(self.ally_slots, self.enemy_slots)


    def loop(self, user_input: UserInput) -> None:
        self.start_combat_button.refresh(user_input.mouse_position)
        for slot in self.ally_slots + self.enemy_slots:
            slot.refresh(user_input.mouse_position)

        if not self.is_combat and self.start_combat_button.is_hovered and user_input.is_mouse1_down:
            self.is_combat = True

        if not self.is_combat: return

        if not self.current_round.is_done:
            self.current_round.loop()
            return

        if is_everyone_dead(self.ally_slots):
            print("you lost")
            self.is_combat = False
        elif is_everyone_dead(self.enemy_slots):
            print("you won")
            self.is_combat = False
        else:
            self.current_round = BattleRound(self.ally_slots, self.enemy_slots)
            self.current_round.start_round()




from pygame import Surface, Rect, draw
def draw_button(frame: Surface, button: Button) -> None:
    rect = Rect(button.position, button.size)
    draw.ellipse(frame, (9, 97, 59), rect)


class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: MockGame):
        draw_button(self.frame, loopable.start_combat_button )
                
        for slot in loopable.ally_slots + loopable.enemy_slots:
            draw_slot(self.frame, slot)
            
            if not slot.content: continue

            is_acting = loopable.current_round.current_turn.character == slot.content

            scale_ratio = 1.5 if slot.is_hovered or is_acting else 1

            draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)


engine = PygameEngine(
    MockGame(),
    MockRenderer(),
    PygameInputListener()
)

engine.run()