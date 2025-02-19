#import asyncio
import sys
import pygame
from typing import List, NoReturn, Protocol
from dataclasses import dataclass

from pygame.event import Event
from settings import GAME_NAME, GAME_FPS, DISPLAY_WIDTH, DISPLAY_HEIGHT


# Initialize pygame directly at first import and create globals
pygame.init()
CLOCK = pygame.time.Clock()
SCREEN: pygame.Surface = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
pygame.display.set_caption(GAME_NAME)


@dataclass(frozen=True)
class UserEvent:
    is_selection_pressed: bool
    is_selection_released: bool
    is_next_pressed: bool
    cursor_position: tuple[int, int]


class EventHandler(Protocol):
    def capture(self) -> UserEvent: ...
    def _terminate(self) -> NoReturn: ...


class PygameEventHandler:
    """
    Collect user input from pygame's built in event queue and functions.
    Requires pygame to be initialized
    """

    def capture(self) -> UserEvent:
        events: List[Event] = pygame.event.get()
        event_types = [event.type for event in events]

        if pygame.QUIT in event_types: self._terminate()

        return UserEvent(
            is_selection_pressed = pygame.MOUSEBUTTONDOWN in event_types,
            is_selection_released = pygame.MOUSEBUTTONUP in event_types,
            is_next_pressed = pygame.key.get_pressed()[pygame.K_SPACE],
            cursor_position = pygame.mouse.get_pos()
        )
    
    def _terminate(self) -> NoReturn:
        print("Exiting...")
        pygame.quit()
        sys.exit()



class InputHandler(Protocol):
    def handle_input(self) -> None: ...
    @property
    def cursor_position(self) -> tuple[int, int]: ...
    @property
    def is_cursor_pressed(self) -> bool: ...
    @property
    def is_cursor_released(self) -> bool: ...
    @property
    def is_next_pressed(self) -> bool: ...
    def _terminate(self) -> NoReturn: ...


class PygameInputHandler:
    def __init__(self) -> None:
        self._events: List[Event] = []

    def handle_input(self) -> None:
        self._events = pygame.event.get()
        if pygame.QUIT in self.event_types: self._terminate()

    @property
    def event_types(self) -> list[int]: 
        return [event.type for event in self._events]

    @property
    def cursor_position(self) -> tuple[int, int]:
        return pygame.mouse.get_pos()

    @property
    def is_cursor_pressed(self) -> bool:
        return pygame.MOUSEBUTTONDOWN in self.event_types

    @property
    def is_cursor_released(self) -> bool:
        return pygame.MOUSEBUTTONUP in self.event_types

    @property
    def is_next_pressed(self) -> bool:
        return pygame.key.get_pressed()[pygame.K_SPACE]

    def _terminate(self) -> NoReturn:
        print("Exiting...")
        pygame.quit()
        sys.exit()


def delay_next_frame() -> None:
    CLOCK.tick(GAME_FPS)
    pygame.display.update()

#async def main() -> NoReturn:
#
#    game = Game.new_game()
#    graphics = GameRenderer(game) # GameGraphics?
#    event_handler = PygameEventHandler()
#
#    while True:
#        user_input: UserEvent = event_handler.capture()
#
#        game.update(user_input)
#
#        graphics.display(user_input)
#
#        CLOCK.tick(GAME_FPS)
#
#        await asyncio.sleep(0)
#
#
#asyncio.run(main())