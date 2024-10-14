from renderer import PygameRenderer, draw_slot, draw_character
from game import Game


class GameRenderer(PygameRenderer):

    def draw_frame(self, game: Game):
        for character_slot in game.character_slots:
            draw_slot(self.frame, character_slot)

        for character in game.characters:
            #if character.is_hover()
            draw_character(self.frame, character)


if __name__ == '__main__':
    

    renderer = GameRenderer()

    #renderer.draw_frame(Game())