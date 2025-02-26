import pathlib

import pydantic
import pygame

from settings import WHITE_COLOR

class AssetConfig(pydantic.BaseModel):
    path: pydantic.FilePath
    size: tuple[int, int]
    offset: tuple[int, int]
    flip_x: bool = False


# Singleton? Does not have to be global, but should only be one preferably, not mandatory though
class AssetManager:
    def __init__(self) -> None:
        self.path_to_image: dict[pathlib.Path, pygame.Surface] = {}
    
    def load(self, config: AssetConfig) -> pygame.Surface:
        if not config.path in self.path_to_image:
            image: pygame.Surface = pygame.image.load(config.path)
            image.convert_alpha() #NOT BEFORE PYGAME INIT
            image = pygame.transform.scale(image, config.size)
            self.path_to_image[config.path] = pygame.transform.flip(image, flip_x=config.flip_x, flip_y=False)
        return self.path_to_image[config.path]

# Avoid temptation to make a global here?? Could ensure singleton behavior since its a module...



def get_mask(surface: pygame.Surface, color: tuple[int,int,int] = WHITE_COLOR) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface).to_surface(setcolor=color)
    mask.set_colorkey((0,0,0))
    return mask

def draw_outline(surface: pygame.Surface, color: tuple[int,int,int] = WHITE_COLOR) -> pygame.Surface:
    outline_offset: int = 2
    mask = get_mask(surface, color)
    outline = mask.copy()
    outline.blit( mask,   (-outline_offset, 0) )
    outline.blit( mask,   ( outline_offset, 0) )
    outline.blit( mask,   ( 0             ,-outline_offset) )
    outline.blit( mask,   ( 0             , outline_offset) )
    outline.blit(surface, ( 0             , 0) )
    return outline


if __name__ == '__main__':
    pass