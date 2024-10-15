from typing import Final, TypeAlias

Vector: TypeAlias = tuple[int, int]
Color: TypeAlias = tuple[int,int,int]

GAME_NAME: Final[str] = "Rogue Troupe"
GAME_FPS: Final[int] = 60
DISPLAY_WIDTH:  Final[int] = 800
DISPLAY_HEIGHT: Final[int] = 600

BLACK_COLOR: Final[Color] = (0,0,0)

DEFAULT_TEXT_SIZE: Final[int] = 15