import traceback
import pygame
from time import sleep

from data.interfaces import Engine, Loopable, Renderer, InputListener
from settings import GAME_FPS



class PygameEngine(Engine):
    def __init__(self, loopable: Loopable, renderer: Renderer, input_listener: InputListener):
        super().__init__(loopable, renderer, input_listener)
        pygame.init()
        self.clock = pygame.time.Clock()

    def run(self) -> None:
        try:
            super().run()
        except Exception: 
            traceback.print_exc()
            
    def wait_for_next_frame(self) -> None:
        self.clock.tick(GAME_FPS) 
        
    def quit(self) -> None:
        print("Exiting...")
        pygame.quit()


class CommandlineEngine(Engine):
    def wait_for_next_frame(self) -> None:
        sleep(1/GAME_FPS)

    def quit(self) -> None:
        print("Exiting...")


if __name__ == "__main__":
    from game import NoGame
    from renderer import PygameRenderer
    from input_listener import PygameInputListener

    engine = PygameEngine(
        NoGame(),
        PygameRenderer(), 
        PygameInputListener()
        )

    engine.run()