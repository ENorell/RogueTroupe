import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import Loopable, UserInput
from input_listener import DeafInputListener, PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer, draw_character, draw_slot
from game import NoGame

from character import Character, CharacterSlot


class MockGame(Loopable):
    def loop(self, user_input: UserInput) -> None:
        pass

slots = [
    CharacterSlot((25,400)),
    CharacterSlot((125,400)),
    CharacterSlot((225,400)),
    CharacterSlot((325,400))
    ]

character = Character()
character.deploy_in(slots[2])


class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: Loopable):
        for slot in slots:
            draw_slot(self.frame, slot)
        draw_character(self.frame, character)


engine = PygameEngine(
    NoGame(),
    MockRenderer(),
    PygameInputListener()
)

engine.run()