import pygame
from abc import ABC
from typing import Optional
from pygame import Surface, Rect, font

from data.images import ImageChoice, IMAGES
from settings import Vector, WHITE_COLOR, DEFAULT_TEXT_SIZE, RED_COLOR


class Character(ABC):
    name: str = "Character"
    width_pixels: int = 100
    height_pixels: int = 100
    max_health: int = 5
    damage: int = 2
    range: int = 1
    ability_name: Optional[str] = None
    trigger: Optional[str] = None
    character_image: ImageChoice
    corpse_image = ImageChoice.CHARACTER_CORPSE

    def __init__(self, is_enemy: bool = False) -> None:
        self.health = self.max_health
        self.is_attacking = False
        self.is_defending = False
        self.is_enemy = is_enemy

    def damage_health(self, damage: int) -> None:
        self.health = max(self.health - damage, 0)

    def is_dead(self) -> bool:
        return self.health == 0

    def revive(self) -> None:
        self.health = self.max_health


class Archeryptrx(Character):
    '''A simple archer with upfront damage and range'''
    name: str = "Archeryptrx"
    max_health: int = 3
    damage: int = 1
    range: int = 2
    ability_name: Optional[str] = "Volley"
    ability_description: Optional[str] = "Combat start: 1 damage to 2 random enemies"
    trigger: Optional[str] = "combat_start"
    character_image = ImageChoice.CHARACTER_ARCHER


class Stabiraptor(Character):
    '''An assassin focussed on eliminating dangerous enemies'''
    name: str = "Stabiraptor"
    max_health: int = 3
    damage: int = 2
    range: int = 1
    ability_name: Optional[str] = "Assassinate"
    ability_description: Optional[str] = "Combat start: 3 damage to highest attack enemy"
    trigger: Optional[str] = "combat_start"
    character_image = ImageChoice.CHARACTER_ASSASSIN_RAPTOR


class Tankylosaurus(Character):
    '''A tanky blocking unit that can absorb powerful attacks'''
    name: str = "Ankylo"
    max_health: int = 7
    damage: int = 1
    range: int = 1
    ability_name: Optional[str] = "Solid"
    ability_description: Optional[str] = "Defending: Max 2 damage taken"
    trigger: Optional[str] = "defend"
    character_image = ImageChoice.CHARACTER_CLUB


class Macedon(Character):
    '''a balanced fighter, can render enemies unable to attack'''
    name: str = "Macedon"
    max_health: int = 4
    damage: int = 2
    range: int = 1
    ability_name: Optional[str] = "Crippling blow"
    ability_description: Optional[str] = "Attacking: reduce target attack by 1"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_CREST


class Healamimus(Character):
    '''A healer, helps sustain allies'''
    name: str = "Healamimus"
    max_health: int = 4
    damage: int = 1
    range: int = 2
    ability_name: Optional[str] = "Heal"
    ability_description: Optional[str] = "Attacking: heal lowest health ally by 1"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_HEALER


class Dilophmageras(Character):
    '''A long range mage with a penetrating attack'''
    name: str = "Dilophmageras"
    max_health: int = 3
    damage: int = 2
    range: int = 3
    ability_name: Optional[str] = "Blast"
    ability_description: Optional[str] = "Attacking: enemy behind takes 1 damage"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_DILOPHMAGE


class Tripiketops(Character):
    '''A tanky unit that deals damage when attacked'''
    name: str = "Tripiketops"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    ability_name: Optional[str] = "Parry"
    ability_description: Optional[str] = "Defending: attacker takes 1 damage"
    trigger: Optional[str] = "defend"
    character_image = ImageChoice.CHARACTER_PIKEMAN


class Pterapike(Character):
    '''A versatile unit that targets the enemies back units'''
    name: str = "Pterapike"
    max_health: int = 4
    damage: int = 1
    range: int = 0
    ability_name: Optional[str] = "Flying"
    ability_description: Optional[str] = "Attacking: can always target last enemy"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_PTERO


class Spinoswordaus(Character):
    '''A powerful warrior that becomes lethal as the battle progresses'''
    name: str = "Spinoswordaus"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    ability_name: Optional[str] = "Rampage"
    ability_description: Optional[str] = "Attacking: gain 1 attack"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_SPINO


class Ateratops(Character):
    '''A mage that enhances allied health'''
    name: str = "Ateratops"
    max_health: int = 3
    damage: int = 2
    range: int = 1  # Melee range
    ability_name: Optional[str] = "Fortify"
    ability_description: Optional[str] = "Combat start: allies gain 1 health"
    trigger: Optional[str] = "combat_start"
    character_image = ImageChoice.CHARACTER_SUMMONER


class Velocirougue(Character):
    '''a dual weilding rouge, high damage but hurts self on attack, relies on quick victory'''
    name: str = "Velocirougue"
    max_health: int = 5
    damage: int = 3
    range: int = 1
    ability_name: Optional[str] = "Reckless"
    ability_description: Optional[str] = "Attacking: lose 1 health"
    trigger: Optional[str] = "attack"
    character_image = ImageChoice.CHARACTER_VELO


def draw_text(text_content: str, window: Surface, center_position: Vector, scale_ratio: float = 1) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = font.SysFont(name="comicsans", size=font_size)
    text = text_font.render(text_content, 1, WHITE_COLOR)
    (text_size_x, text_size_y) = text.get_size()
    (center_x, center_y) = center_position
    text_topleft_position = (center_x - text_size_x / 2, center_y - text_size_y)
    window.blit(text, text_topleft_position)


def draw_character(frame: Surface, mid_bottom: Vector, character: Character, scale_ratio: float = 1):
    match character.is_dead():
        case True: 
            character_image = IMAGES[character.corpse_image].convert_alpha()
        case False:
            character_image = IMAGES[character.character_image].convert_alpha()
    
    character_image = pygame.transform.scale(character_image, (character.width_pixels, character.height_pixels))
    if character.is_enemy:
        character_image = pygame.transform.flip(character_image, True, False)

    center_x, bottom_y = mid_bottom
    top_left = (center_x - character.width_pixels / 2, bottom_y - character.height_pixels)
    rect = Rect(top_left, (character.width_pixels, character.height_pixels))
    rect = rect.scale_by(scale_ratio, scale_ratio)

    mid_top = (center_x, bottom_y - character.height_pixels)

    # Draw character name
    draw_text(character.name, frame, mid_top, scale_ratio=scale_ratio)

    frame.blit(character_image, rect.topleft)


    if character.is_dead():
        draw_text(f"DEAD", frame, mid_bottom, scale_ratio=scale_ratio)
    else:
        # Draw defending indicator if character is defending
        if character.is_defending:
            red_circle_radius = rect.width // 2
            red_circle_center = (rect.centerx, rect.centery)
            pygame.draw.circle(frame, RED_COLOR, red_circle_center, red_circle_radius, width=5)

        # Draw health and damage text
        health_damage_pos = (mid_bottom[0], mid_bottom[1] + 20)
        draw_text(f"{character.health}/{character.max_health}  {character.damage}", frame, health_damage_pos, scale_ratio=scale_ratio)