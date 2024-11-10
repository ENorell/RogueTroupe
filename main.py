import asyncio
import pygame
from core.interfaces import UserInput
from core.input_listener import PygameInputListener
from states.game import Game, GameRenderer
from settings import GAME_FPS

pygame.init()
clock = pygame.time.Clock()

async def main() -> None:

    game = Game.new_game()
    renderer = GameRenderer(game)
    input_listener = PygameInputListener()

    running = True
    while running:
        clock.tick(GAME_FPS)

        user_input: UserInput = input_listener.capture()

        game.loop(user_input)

        renderer.render()

        await asyncio.sleep(0)

        if user_input.is_quit:
            running = False

    print("Exiting...")
    pygame.quit()

asyncio.run(main())