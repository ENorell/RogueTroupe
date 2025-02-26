from typing import Protocol, Self
from pathlib import Path

import pygame

from core.interfaces import HoverDetector
from pygame_engine import SCREEN, DEFAULT_FONT
from settings import Color, BLACK_COLOR
from asset_manager import AssetManager, AssetConfig, draw_outline, get_mask

START_COMBAT_BUTTON_PATH = Path(r"assets\ui\fight.png")




class Button:
    def __init__(self, position: tuple[int, int], button_drawer: "ButtonDrawer", hover_detector: "HoverDetector") -> None:
        self._position: tuple[int, int] = position
        self._button_drawer: ButtonDrawer = button_drawer
        self._hover_detector: HoverDetector = hover_detector

    @property
    def position(self) -> tuple[int, int]:
        return self._position

    def is_hovered(self, cursor_position: tuple[int, int]) -> bool:
        return self._hover_detector.detect(cursor_position)

    def is_clicked(self, cursor_position: tuple[int, int], cursor_is_pressed: bool) -> bool:
        return self.is_hovered(cursor_position) and cursor_is_pressed # get mouse just released?

    def draw(self, cursor_position: tuple[int, int], cursor_is_pressed: bool) -> None:
        if not self._hover_detector.detect(cursor_position):
            self._button_drawer.draw_idle()
            return
        if not pygame.mouse.get_pressed()[0]:#cursor_is_pressed:
            self._button_drawer.draw_hover()
            return
        self._button_drawer.draw_click()

    @classmethod
    def create_simple(cls, position: tuple[int, int], text: str, size: tuple[int, int] = (150,50)) -> "Button":
        hover_detector = PygameHoverDetector(pygame.Rect(position, size))
        button_drawer = SimpleButtonDrawer(position, size, text)
        return cls(position, button_drawer, hover_detector)

    @classmethod
    def create_start_combat_button(cls, asset_manager: AssetManager, position: tuple[int, int]) -> Self:
        size = (120,120)
        sprite_config = AssetConfig(path=START_COMBAT_BUTTON_PATH, size=size, offset=(0,0), flip_x=False)
        sprite = asset_manager.load(sprite_config)
        hover_detector = PygameHoverDetector(pygame.Rect(position, size))
        button_drawer = AssetButtonDrawer(position, sprite)

        return cls(position, button_drawer, hover_detector)


class PygameHoverDetector:
    """Concrete hover detector wrapping the pygame API"""
    def __init__(self, box: pygame.Rect):
        self.box = box

    def detect(self, cursor_position: tuple[int, int]) -> bool:
        return self.box.collidepoint(cursor_position)


class ButtonDrawer(Protocol):
    def draw_idle(self) -> None: ...
    def draw_hover(self) -> None: ...
    def draw_click(self) -> None: ...


class SimpleButtonDrawer:
    color: Color = (9, 97, 59)
    hover_scale_ratio: float = 1.5

    def __init__(self, position: tuple[int, int], size: tuple[int, int], text: str) -> None:
        self.position = position
        self.size = size
        #self.text_drawer = fonts.PygameTextDrawer(position, text)
        #text_font = pygame.font.SysFont(name=font_name, size=font_size)
        self.text_image = DEFAULT_FONT.render(text, 1, BLACK_COLOR) # do in draw?

    @property
    def box(self) -> pygame.Rect:
        return pygame.Rect(self.position, self.size)

    def draw_idle(self) -> None:
        pygame.draw.rect(SCREEN, self.color, self.box)
        #self.text_drawer.draw(frame)
        #(text_size_x, text_size_y) = self.text_image.get_size()
        #(center_x, center_y) = self.center_position
        #text_topleft_position = (center_x - text_size_x / 2, center_y - text_size_y / 2)

        SCREEN.blit(self.text_image, self.position)

    def draw_hover(self) -> None:
        rect = self.box.scale_by(self.hover_scale_ratio, self.hover_scale_ratio)
        pygame.draw.rect(SCREEN, self.color, rect)
        #self.text_drawer.draw(frame)
        SCREEN.blit(self.text_image, self.position)

    def draw_click(self) -> None:
        rect = self.box.scale_by(self.hover_scale_ratio, self.hover_scale_ratio)
        pygame.draw.rect(SCREEN, (150,50,50), rect)
        #self.text_drawer.draw(frame)
        SCREEN.blit(self.text_image, self.position)


class AssetButtonDrawer:
    hover_scale_ratio: float = 1.5

    def __init__(self, position: tuple[int, int], sprite: pygame.Surface) -> None:
        self.position = position
        self.sprite = sprite

    def draw_idle(self) -> None:
        SCREEN.blit(self.sprite, self.position)

    def draw_hover(self) -> None:
        sprite_outlined = draw_outline(self.sprite)
        SCREEN.blit(sprite_outlined, self.position)

    def draw_click(self) -> None:
        sprite_masked = get_mask(self.sprite)
        SCREEN.blit(sprite_masked, self.position)






if __name__ == "__main__":
    from pygame_engine import SCREEN, delay_next_frame, PygameInputHandler
    asset_manager = AssetManager()
    
    asset_button = Button.create_start_combat_button(asset_manager, (200,300))

    simple_button = Button.create_simple((500,300), "simple_button")

    input_handler = PygameInputHandler()

    while True:
        
        input_handler.handle_input()

        SCREEN.fill("darkgrey")

        asset_button.draw(input_handler.cursor_position, input_handler.is_cursor_pressed)

        simple_button.draw(input_handler.cursor_position, input_handler.is_cursor_pressed)
        
        delay_next_frame()
