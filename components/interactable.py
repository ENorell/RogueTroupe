from abc import ABC
from typing import Final
from pygame import Rect, draw, Surface, font, transform

from settings import Vector, Color, BLACK_COLOR, DEFAULT_TEXT_SIZE

BUTTON_COLOR: Final[Color] = (9, 97, 59)

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
        return (x_position + round(self.width_pixels / 2), y_position + self.height_pixels)

    @property
    def center_coordinate(self) -> Vector:
        x_position, y_position = self.position
        return (x_position + round(self.width_pixels / 2), y_position + round(self.height_pixels / 2))

def draw_text(text_content: str, window: Surface, center_position: Vector, scale_ratio: float = 1) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = font.SysFont(name="comicsans", size=font_size)
    text = text_font.render(text_content, 1, BLACK_COLOR)
    (text_size_x, text_size_y) = text.get_size()
    (center_x, center_y) = center_position
    text_topleft_position = (center_x - text_size_x / 2, center_y - text_size_y / 2)

    window.blit(text, text_topleft_position)

class Button(Interactable):
    def __init__(self, position: Vector, text: str, image: Surface = None) -> None:
        super().__init__(position)
        self.text = text
        self.image = image

        if self.image:
            # Set dimensions based on image
            self.width_pixels, self.height_pixels = self.image.get_size()
            self.rect = self.image.get_rect(topleft=position)
        else:
            # Set default dimensions if no image is provided
            self.width_pixels = 150
            self.height_pixels = 50
            self.rect = Rect(position, (self.width_pixels, self.height_pixels))

    def refresh(self, mouse_position: Vector) -> None:
        if self.image:
            # Update hover status using image rect
            self._is_hovered = self.rect.collidepoint(mouse_position)
        else:
            # Use size for non-image buttons
            self._is_hovered = detect_hover_box(self.position, self.size, mouse_position)

def draw_button(frame: Surface, button: Button) -> None:
    if button.image:
        # Scale the image if the button is hovered
        scale_ratio = 1.5 if button.is_hovered else 1
        new_width = round(button.width_pixels * scale_ratio)
        new_height = round(button.height_pixels * scale_ratio)
        scaled_image = transform.scale(button.image, (new_width, new_height))

        # Calculate the new position to keep the button centered correctly after scaling
        new_position = (
            button.position[0] - (new_width - button.width_pixels) // 2,
            button.position[1] - (new_height - button.height_pixels) // 2,
        )

        # Update button rect for accurate collision detection
        button.rect = scaled_image.get_rect(topleft=new_position)

        # Draw the scaled image
        frame.blit(scaled_image, new_position)

    else:
        # Draw a simple rectangle if no image is provided
        rect = Rect(button.position, button.size)
        scale_ratio = 1.5 if button.is_hovered else 1
        rect = rect.scale_by(scale_ratio, scale_ratio)

        draw.rect(frame, BUTTON_COLOR, rect)
        draw_text(button.text, frame, rect.center, scale_ratio=scale_ratio)
