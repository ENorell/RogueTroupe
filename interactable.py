from abc import ABC
from typing import Optional, Callable
from settings import Vector


def detect_hover_pygame(position: Vector, size: Vector, mouse_position: Vector) -> bool:
    from pygame import Rect
    rectangle = Rect(position, size)
    return rectangle.collidepoint( mouse_position )


class Interactable(ABC):
    width_pixels: int
    height_pixels: int
    #detect_hover: Callable[[Vector, Vector, Vector], bool] = detect_hover_pygame
    _is_hovered: bool = False

    def __init__(self) -> None:
        self._position: Optional[Vector]

    @property
    def size(self) -> Vector:
        return (self.width_pixels, self.height_pixels)

    @property
    def position(self) -> Optional[Vector]:
        return self._position

    def refresh(self, mouse_position: Vector, detect_hover: Callable[[Vector, Vector, Vector], bool]) -> None:
        if not self.position: return

        self._is_hovered = detect_hover(self.position, self.size, mouse_position)

    @property
    def is_hovered(self) -> bool:
        return self._is_hovered
    