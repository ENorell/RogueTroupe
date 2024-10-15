import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))

from interfaces import Loopable, UserInput
from input_listener import DeafInputListener, PygameInputListener
from engine import PygameEngine
from renderer import PygameRenderer

from character import Character, KnightCharacter, WizardCharacter, draw_character, draw_text
from character_slot import CharacterSlot, draw_slot
from typing import Optional



class MockGame(Loopable):
    def __init__(self) -> None:
        self.detached_slot: Optional[CharacterSlot] = None

        self.slots = [
            CharacterSlot((25 ,400)),
            CharacterSlot((125,400)),
            CharacterSlot((225,400)),
            CharacterSlot((325,400))
            ]
        
        self.bench_slots = [
            CharacterSlot((25 ,150)),
            CharacterSlot((125,150))
        ]

        self.slots[2].content = KnightCharacter()
        self.slots[3].content = WizardCharacter()


    def loop(self, user_input: UserInput) -> None:
        self.user_input = user_input

        hover_slot: Optional[CharacterSlot] = None
        for slot in self.slots + self.bench_slots: 
            slot.refresh(user_input.mouse_position)

            if slot.is_hovered:
                hover_slot = slot

        if self.detached_slot:
            if not user_input.is_mouse1_up: return
            if not hover_slot or hover_slot == self.detached_slot:
                self.detached_slot = None
                return

            hover_content = hover_slot.content
            detached_content = self.detached_slot.content
            assert detached_content
            #if not detached_content:
            #    raise Exception("ops")
            self.detached_slot.content = hover_content
            hover_slot.content = detached_content
            self.detached_slot = None

        else: 
            if hover_slot and user_input.is_mouse1_down:
                if not hover_slot.content: return
                self.detached_slot = hover_slot



class MockRenderer(PygameRenderer):
    def draw_frame(self, loopable: MockGame):
        draw_text(str(bool(loopable.detached_slot)), self.frame, (600,150))
        if loopable.detached_slot: 
            if loopable.detached_slot.content:
                draw_text(loopable.detached_slot.content.name, self.frame, (600,100))
                

        for slot in loopable.slots + loopable.bench_slots:
            draw_slot(self.frame, slot)
            
            if not slot.content: continue

            position = loopable.user_input.mouse_position if slot is loopable.detached_slot else slot.center_coordinate
                

            scale_ratio = 1.5 if slot.is_hovered else 1

            draw_character(self.frame, position, slot.content, scale_ratio = scale_ratio)


engine = PygameEngine(
    MockGame(),
    MockRenderer(),
    PygameInputListener()
)

engine.run()