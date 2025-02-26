from typing import Optional
from pathlib import Path

import pygame

from pygame_engine import SCREEN
from core.interfaces import HoverDetector
from asset_manager import AssetManager, AssetConfig, draw_outline
from robot import Robot


SLOT_ASSET_PATH = Path("assets/ui/slot.png")


class Slot:
    def __init__(self, position: tuple[int, int], renderer: "SlotRenderer", hover_detector: "SlotHoverDetector") -> None:
        self._position = position
        self._renderer = renderer
        self._hover_detector: HoverDetector = hover_detector
        self.attached_robot: Optional[Robot] = None

    @property
    def position(self) -> tuple[int, int]:
        return self._position
    
    def attach_robot(self, robot: "Robot") -> None:
        self.attached_robot = robot
        robot.position = pygame.Vector2(self._position)

    def clear(self) -> None:
        self.attached_robot = None

    def draw(self) -> None: self._renderer.draw(self)

    def draw_highlighted(self) -> None: self._renderer.draw_highlighted(self)

    def is_hovered(self, cursor_position: tuple[int, int]) -> bool: 
        return self._hover_detector.detect(cursor_position)

    @classmethod
    def create(cls, asset_manager: AssetManager, position: tuple[int, int]) -> "Slot":
        config = AssetConfig(path=SLOT_ASSET_PATH, size=(100,100), offset=(0,0), flip_x=False)
        image = asset_manager.load(config)#SLOT_ASSET_PATH, (100, 100))
        renderer = SlotRenderer(image)
        hitbox = pygame.Rect(position -pygame.Vector2(image.get_size())/2, image.get_size())
        hover_detector = SlotHoverDetector(hitbox)
        return Slot(position, renderer, hover_detector)


class SlotHoverDetector:
    def __init__(self, hitbox: pygame.Rect) -> None:
        self._hitbox = hitbox

    def detect(self, cursor_position: tuple[int, int]) -> bool:
        return self._hitbox.collidepoint(cursor_position)


class SlotRenderer:
    def __init__(self, image: pygame.Surface) -> None:
        self.image = image

    @property
    def center_offset(self) -> pygame.Vector2:
        return -pygame.Vector2(self.image.get_size())/2

    def draw(self, slot: Slot) -> None:
        SCREEN.blit(self.image, slot._position+self.center_offset)

    def draw_highlighted(self, slot: Slot) -> None:
        outlined_image = draw_outline(self.image)
        SCREEN.blit(outlined_image, slot._position+self.center_offset)
