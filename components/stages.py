from typing import Final, Protocol
from abc import ABC, abstractmethod
from random import choice
import pygame
from components.interactable import draw_text
from components import character_pool
from components.character import Character
from components.character_slot import CombatSlot
from settings import BLACK_COLOR, WHITE_COLOR


ENEMY_POOL: Final[list[type[Character]]] = [
    character_pool.Aepycamelus,
    character_pool.Brontotherium,
    character_pool.Cranioceras,
    character_pool.Glypto,
    character_pool.Gorgono,
    character_pool.Mammoth,
    character_pool.Phorus,
    character_pool.Sabre,
    character_pool.Sloth,
    character_pool.Trilo,
]

ENEMY_STAGES: list[list[Character]] = [
    [character_pool.Trilo(),            character_pool.Trilo()],
    [character_pool.Mammoth()],
    [character_pool.Aepycamelus(),      character_pool.Aepycamelus(),   character_pool.Aepycamelus()],
    [character_pool.Sloth(),            character_pool.Sloth(),         character_pool.Sloth()],
    [character_pool.Phorus(),           character_pool.Sabre()],
    [character_pool.Brontotherium(),    character_pool.Cranioceras()],
    [character_pool.Glypto(),           character_pool.Gorgono()]
    ]


class EnemyGenerator(ABC):
    def __init__(self) -> None:
        self.stage: int = 0

    @abstractmethod
    def generate(self, slots: list[CombatSlot]) -> None:
        ...


class RandomEnemyGenerator(EnemyGenerator):
    def generate(self, slots: list[CombatSlot]) -> None:
        for slot in slots:
            character_type = choice(ENEMY_POOL)
            slot.content = character_type()
        self.stage += 1


class StageEnemyGenerator(EnemyGenerator):
    def generate(self, slots: list[CombatSlot]) -> None:
        stage_enemies: list[character.Character] = ENEMY_STAGES[self.stage]
        for enemy_index, enemy in enumerate(stage_enemies):
            slots[enemy_index].content = enemy
        self.stage += 1


def draw_stage_number(frame: pygame.Surface, stage: int) -> None:
    center = (700,525)
    pygame.draw.circle(frame, color=WHITE_COLOR, center = center, radius=25)
    draw_text(str(stage), frame, center_position=center, scale_ratio=2)