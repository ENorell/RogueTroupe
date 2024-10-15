from typing import Optional, Final
from settings import Vector, Color, BLACK_COLOR, DEFAULT_TEXT_SIZE
from pygame import Surface, Rect, draw, font


CHARACTER_COLOR: Final[Color] = (100, 50 ,230)


class Character:
    name: str = "Character"
    width_pixels: int = 50
    height_pixels: int = 80
    max_health: int = 5
    damage: int = 2
    target: set[int] = {1}

    def __init__(self) -> None:
        self.health = self.max_health

    def damage_health(self, damage: int) -> None:
        self.health = max(self.health - damage, 0)

    def is_dead(self) -> bool:
        return self.health == 0


class KnightCharacter(Character):
    name: str = "Knight"
    width_pixels: int = 60
    height_pixels: int = 70
    max_health: int = 7
    damage: int = 1


class WizardCharacter(Character):
    name: str = "Wizard"
    width_pixels: int = 30
    height_pixels: int = 70
    max_health: int = 3
    damage: int = 3


class GoblinCharacter(Character):
    name: str = "Goblin"
    width_pixels: int = 40
    height_pixels: int = 40
    max_health: int = 4
    damage: int = 1


class TrollCharacter(Character):
    name: str = "Troll"
    width_pixels: int = 50
    height_pixels: int = 80
    max_health: int = 9
    damage: int = 3



def draw_text(text_content: str, window: Surface, center_position: Vector, scale_ratio: float = 1) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = font.SysFont(name = "comicsans", size = font_size)
    text = text_font.render(text_content, 1, BLACK_COLOR)
    (text_size_x, text_size_y) = text.get_size()
    (center_x, center_y) = center_position
    text_topleft_position = (center_x - text_size_x / 2, center_y - text_size_y)

    window.blit(text, text_topleft_position)


def draw_character(frame: Surface, mid_bottom: Vector, character: Character, color_override: Optional[Color] = None, scale_ratio: float = 1):
    color = CHARACTER_COLOR if not color_override else color_override

    center_x, bottom_y = mid_bottom
    top_left = ( center_x - character.width_pixels/2, bottom_y - character.height_pixels )
    rect = Rect(top_left, (character.width_pixels, character.height_pixels))

    rect = rect.scale_by(scale_ratio, scale_ratio)

    draw.rect(frame, color, rect)

    mid_top = (center_x, bottom_y - character.height_pixels)

    draw_text(character.name, frame, mid_top, scale_ratio=scale_ratio)
    draw_text(f"{character.health}/{character.max_health}", frame, mid_bottom, scale_ratio=scale_ratio)
