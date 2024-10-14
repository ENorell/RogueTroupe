import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import Loopable, UserInput
from input_listener import DeafInputListener, PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer
from game import NoGame

from character import Character, draw_character
from character_slot import CharacterSlot, draw_slot
from interactable import detect_hover_pygame


slots = [
    CharacterSlot((25,400)),
    CharacterSlot((125,400)),
    CharacterSlot((225,400)),
    CharacterSlot((325,400))
    ]

character = Character()
character.deploy_in(slots[2])


class MockGame(Loopable):
    def loop(self, user_input: UserInput) -> None:
        [slot.refresh(user_input.mouse_position, detect_hover_pygame) for slot in slots]
        
        character.refresh(user_input.mouse_position, detect_hover_pygame)


class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: Loopable):
        for slot in slots:
            draw_slot(self.frame, slot)
        draw_character(self.frame, character)


engine = PygameEngine(
    MockGame(),
    MockRenderer(),
    PygameInputListener()
)

engine.run()