from enum import Enum
from typing import Protocol, NoReturn

import pygame


class Node(pygame.Vector2):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)



class Rarity(Enum):
    RARE = "Rare"
    COMMON = "Common"




class HoverDetector(Protocol):
    """Abstract interface for all hover detectors."""
    def detect(self, cursor_position: tuple[int, int]) -> bool:
        ...


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