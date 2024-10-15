from abc import ABC
from typing import Protocol, Optional, Callable
from settings import Vector
from pygame import Rect


class MouseCollider(Protocol):
    
    def is_point_contained(self, point: Vector, top_left: Vector, size: Vector) -> bool:
        ...

class NoMouseCollider:

    def is_point_contained(self, point: Vector, top_left: Vector, size: Vector) -> bool:
        return False
    
class PygameMouseCollider:

    def is_point_contained(self, point: Vector, top_left: Vector, size: Vector) -> bool:
        rectangle = Rect(top_left, size)
        return rectangle.collidepoint( point )


def detect_hover_pygame(position: Vector, size: Vector, mouse_position: Vector) -> bool:
    rectangle = Rect(position, size)
    return rectangle.collidepoint( mouse_position )


def detect_hover_box(top_left: Vector, size: Vector, mouse_position: Vector) -> bool:
    width, height = size
    top_left_x, top_left_y = top_left
    mouse_x, mouse_y = mouse_position
    is_mouse_in_box_x = top_left_x <= mouse_x <= top_left_x + width
    is_mouse_in_box_y = top_left_y <= mouse_y <= top_left_y + height
    return is_mouse_in_box_x and is_mouse_in_box_y


class Interactable(ABC):
    width_pixels: int
    height_pixels: int

    def __init__(self, position: Vector) -> None:
        self._position = position
        self._is_hovered: bool = False

    @property
    def size(self) -> Vector:
        return (self.width_pixels, self.height_pixels)

    @property
    def position(self) -> Vector:
        return self._position

    def refresh(self, mouse_position: Vector) -> None:
        self._is_hovered = detect_hover_box(self.position, self.size, mouse_position)

    @property
    def is_hovered(self) -> bool:
        return self._is_hovered
    
    @property
    def bottom_mid_coordinate(self) -> Vector:
        x_position, y_position = self.position
        return (x_position + round(self.width_pixels/2), y_position + self.height_pixels)
    
    @property
    def center_coordinate(self) -> Vector:
        x_position, y_position = self.position
        return (x_position + round(self.width_pixels/2), y_position + round(self.height_pixels/2) )
