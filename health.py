from typing import Self, Protocol
from pathlib import Path

import pygame

from pygame_engine import SCREEN
from asset_manager import AssetManager, AssetConfig


FULL_SPRITE_PATH = Path(r"assets\ui\full_heart.png")
EMPTY_SPRITE_PATH = Path(r"assets\ui\empty_heart.png")


class HasPosition(Protocol):
    @property
    def position(self) -> tuple: ...#pygame.Vector2: ...
    #position: pygame.Vector2#tuple


class Health:
    icon_size: tuple = (15,15)
    attachment_offset: tuple = (100, 20)
    sprite_spacing: tuple = (15, 0)

    def __init__(self, max_health: int, empty_sprite: pygame.Surface, full_sprite: pygame.Surface) -> None:
        self.max = max_health
        self.current = max_health

        self.empty_sprite = empty_sprite
        self.full_sprite = full_sprite

    def __iadd__(self, increment: int) -> "Health":
        self.current = min(self.current + increment, self.max)
        return self

    def __isub__(self, increment: int) -> "Health":
        self.current = max(self.current - increment, 0)
        return self


    def draw(self, attached: HasPosition) -> None:

        for health_level in range(self.max):
            position = pygame.Vector2(attached.position) + pygame.Vector2(self.attachment_offset) + health_level*pygame.Vector2(self.sprite_spacing)
            if health_level < self.current:
                SCREEN.blit(self.full_sprite, position)
            else:
                SCREEN.blit(self.empty_sprite, position)

    @classmethod
    def create(cls, asset_manager: AssetManager, health: int) -> Self:
        full_config = AssetConfig(path=FULL_SPRITE_PATH, size=cls.icon_size, offset=(0,0), flip_x=False)
        full_sprite = asset_manager.load(full_config)
        empty_config = AssetConfig(path=EMPTY_SPRITE_PATH, size=cls.icon_size, offset=(0,0), flip_x=False)
        empty_sprite = asset_manager.load(empty_config)
        return cls(health, empty_sprite, full_sprite)


if __name__ == "__main__":
    from pygame_engine import delay_next_frame, PygameInputHandler

    asset_manager = AssetManager()
    
    health = Health.create(asset_manager, 10)

    class B:
        position = (300,300)
    attached = B()

    input_handler = PygameInputHandler()

    while True:
        input_handler.handle_input()

        if input_handler.is_cursor_pressed:
            health-=1

        SCREEN.fill("darkblue")
        health.draw(attached)
        
        delay_next_frame()
