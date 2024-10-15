from interfaces import Loopable, UserInput
from character import Character
from character_slot import CharacterSlot


class NoGame(Loopable):
    def loop(self, user_input: UserInput) -> None:
        pass


class Game(Loopable):

    def __init__(self, characters: list[Character], character_slots: list[CharacterSlot]) -> None:
        self.characters = characters
        self.character_slots = character_slots

    def loop(self, user_input: UserInput) -> None:
        
        pass

