from engine import PygameEngine
from character import Character, CharacterSlot
from game_renderer import GameRenderer
from input_listener import PygameInputListener
from game import Game




if __name__ == '__main__':

    slot = CharacterSlot((100,100))
    character = Character()
    character.deploy_in(slot)

    game = Game(
        [character],
        [slot]
    )


    engine = PygameEngine(
        game,
        GameRenderer(),
        PygameInputListener()
    )

    engine.run()
