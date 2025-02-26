from typing import Optional, Iterable
from collections import deque
from pathlib import Path

import yaml
import pydantic
import pygame

from asset_manager import AssetConfig, AssetManager, draw_outline
from pygame_engine import SCREEN, delay_next_frame, PygameInputHandler, DEFAULT_FONT
from settings import BLACK_COLOR
from health import Health


ENEMY_CONFIG_PATH = Path("enemy_configs.yaml")
ATTACK_SPRITE_PATH = Path("assets/ui/attack.png")
BUFF_SPRITE_PATH = Path(r"assets\ui\crystalicon.webp")


class Attack(pydantic.BaseModel):
    damage: int
    targets: list[tuple[int, int]]

class Buff(pydantic.BaseModel):
    strength: int = 0
    health: int = 0

class Push(pydantic.BaseModel):
    target: tuple[int, int]
    destination: tuple[int, int]

class Action(pydantic.BaseModel):
    name: Optional[str] = None
    attack: Optional[Attack] = None
    buff: Optional[Buff] = None
    push: Optional[Push] = None
    # Other things that might occur in an enemy action

class EnemyConfig(pydantic.BaseModel):
    asset: AssetConfig
    health: int
    actions: list[Action]


class Enemy:
    def __init__(self, renderer: "EnemyRenderer", hover_detector: "EnemyHoverDetector", intent_renderer: "EnemyIntentRenderer", position: tuple[int, int], health: Health, actions: Iterable[Action]) -> None:
        self.health = health
        self.position = position
        self.renderer = renderer
        self.hover_detector = hover_detector
        self.intent_renderer = intent_renderer
        self.actions: deque[Action] = deque(actions)

    def cycle_action(self) -> None:
        self.actions.rotate(-1)

    @property
    def action(self) -> Action:
        return self.actions[0]
    
    def is_hovered(self) -> bool:
        return self.hover_detector.detect()
    
    def draw(self) -> None:
        self.renderer.draw(self)
        self.intent_renderer.draw(self)

    def draw_highlighted(self) -> None:
        self.renderer.draw_highlighted(self)
        self.intent_renderer.draw(self)
        self.health.draw(self)

    def damage(self, amount: int) -> None:
        self.health -= amount


class EnemyRenderer:
    def __init__(self, sprite) -> None:
        self.sprite: pygame.Surface = sprite

    def draw(self, enemy: Enemy) -> None:
        SCREEN.blit(self.sprite, enemy.position)

    def draw_highlighted(self, enemy: Enemy) -> None:
        outlined_sprite = draw_outline(self.sprite)
        SCREEN.blit(outlined_sprite, enemy.position)


class EnemyIntentRenderer:
    enemy_intent_offset = pygame.Vector2(85,-75)
    element_pixel_space = pygame.Vector2(50, 10)
    def __init__(self, attack_sprite: pygame.Surface, buff_sprite: pygame.Surface) -> None:
        self.attack_sprite = attack_sprite
        self.buff_sprite = buff_sprite

    def draw(self, enemy: Enemy) -> None:
        if enemy.action.attack:
            SCREEN.blit(self.attack_sprite, enemy.position+self.enemy_intent_offset)
            damage_numbers = DEFAULT_FONT.render(str(enemy.action.attack.damage), 1, BLACK_COLOR)
            SCREEN.blit(damage_numbers, enemy.position+self.enemy_intent_offset+self.element_pixel_space)
        elif enemy.action.buff:
            SCREEN.blit(self.buff_sprite, enemy.position+self.enemy_intent_offset)
            damage_numbers = DEFAULT_FONT.render("Buffing", 1, BLACK_COLOR)
            SCREEN.blit(damage_numbers, enemy.position+self.enemy_intent_offset+self.element_pixel_space)
        else:
            wait_text = DEFAULT_FONT.render("Waiting...", 1, BLACK_COLOR)
            SCREEN.blit(wait_text, enemy.position+self.enemy_intent_offset)

    @classmethod
    def create(cls, asset_manager: AssetManager) -> "EnemyIntentRenderer":
        attack_sprite_config = AssetConfig(path = ATTACK_SPRITE_PATH, size=(45,45), offset=(0,0), flip_x=False)
        attack_sprite = asset_manager.load(attack_sprite_config)
        buff_sprite_config = AssetConfig(path = BUFF_SPRITE_PATH, size=(45,45), offset=(0,0), flip_x=False)
        buff_sprite = asset_manager.load(buff_sprite_config)
        return cls(attack_sprite, buff_sprite)


class EnemyHoverDetector:

    def __init__(self, hitbox: pygame.Rect) -> None:
        self._hitbox = hitbox

    def detect(self) -> bool:
        return self._hitbox.collidepoint(pygame.mouse.get_pos())


class EnemySpawner:
    def __init__(self, asset_manager: AssetManager, configs: list[EnemyConfig]) -> None:
        self.configs = configs
        self.asset_manager = asset_manager

    def spawn(self, config: EnemyConfig, position: tuple[int, int]) -> Enemy:
        sprite = self.asset_manager.load(config.asset)
        renderer = EnemyRenderer(sprite)
        hover_detector = EnemyHoverDetector(pygame.Rect(position, sprite.get_size()))
        intent_renderer = EnemyIntentRenderer.create(self.asset_manager)
        health = Health.create(self.asset_manager, config.health)
        return Enemy(renderer, hover_detector, intent_renderer, position, health, config.actions)
    
    def spawn_any(self, position: tuple[int, int]) -> Enemy:
        return self.spawn(self.configs[0], position)
    
    @classmethod
    def from_config_file(cls, asset_manager: AssetManager, path: Path = ENEMY_CONFIG_PATH) -> "EnemySpawner":
        with open(path) as file:
            yaml_configs: list = yaml.safe_load(file)

        enemy_configs: list[EnemyConfig] = [EnemyConfig(**enemy_config) for enemy_config in yaml_configs]
        return cls(asset_manager, enemy_configs)




if __name__ == "__main__":
    asset_manager = AssetManager()
    
    spawner = EnemySpawner.from_config_file(asset_manager)

    enemy = spawner.spawn(spawner.configs[0], (100,100))

    input_handler = PygameInputHandler()

    while True:
        
        input_handler.handle_input()

        #enemy.position = input_handler.cursor_position
        if input_handler.is_cursor_pressed:
            enemy.cycle_action()

        SCREEN.fill("darkblue")
        enemy.draw()
        
        delay_next_frame()
