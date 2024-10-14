from abc import ABC
from typing import Optional, TypeAlias, Callable


Vector: TypeAlias = tuple[int, int]


def detect_hover_pygame(position: Vector, size: Vector, mouse_position: Vector) -> bool:
    from pygame import Rect
    rectangle = Rect(position, size)
    return rectangle.collidepoint( mouse_position )


class Interactable(ABC):
    width_pixels: int
    height_pixels: int
    detect_hover: Callable[[Vector, Vector, Vector], bool] = detect_hover_pygame

    def __init__(self) -> None:
        self._position: Optional[Vector]

    @property
    def size(self) -> Vector:
        return (self.width_pixels, self.height_pixels)

    @property
    def position(self) -> Optional[Vector]:
        return self._position

    def is_hover(self, mouse_position: Vector ) -> bool:
        if not self.position: return False
        return self.detect_hover(self.position, self.size, mouse_position)
    


class CharacterSlot(Interactable):
    width_pixels: int = 75
    height_pixels: int = 50
    
    def __init__(self, position: Vector) -> None:
        self._position = position



class Character(Interactable):
    name: str = "Character"
    width_pixels: int = 50
    height_pixels: int = 80
    health: int = 5
    damage: int = 2

    def __init__(self) -> None:
        self.character_slot: Optional[CharacterSlot] = None
        self._position: Optional[Vector] = None

    @property
    def position(self) -> Optional[Vector]:
        return self.character_slot.position if self.character_slot else None

    def deploy_in(self, character_slot: CharacterSlot) -> None:
        self.character_slot = character_slot



if __name__ == "__main__":
    from interfaces import UserInput
    from engine import PygameEngine
    from renderer import PygameRenderer
    from input_listener import PygameInputListener
    
    class MockGame:
        def __init__(self) -> None:
            self.character = Character()

        def loop(self, user_input: UserInput) -> None:
            pass

    engine = PygameEngine(
        MockGame(),
        PygameRenderer(), 
        PygameInputListener()
        )

    engine.run()