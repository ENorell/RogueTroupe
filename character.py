import pygame
from typing import Optional
from settings import Vector, WHITE_COLOR, DEFAULT_TEXT_SIZE, RED_COLOR
from pygame import Surface, Rect, font
from images import ImageChoice, IMAGES
from abc import ABC
from abilities import Ability, volley, assassinate, solid, crippling_blow, heal, blast, parry, flying, rampage, fortify, reckless


class Character(ABC):
    name: str = "Character"
    width_pixels: int = 100
    height_pixels: int = 100
    max_health: int = 5
    damage: int = 2
    range: int = 1
    ability: Optional[Ability] = None
    character_image: ImageChoice
    corpse_image = ImageChoice.CHARACTER_CORPSE

    def __init__(self, is_enemy: bool = False) -> None:
        self.health = self.max_health
        self.is_attacking = False
        self.is_defending = False
        self.is_enemy = is_enemy
        self.target = None
        self.attacker = None

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
    character_image = ImageChoice.CHARACTER_ARCHER

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Volley",
            description="Combat start: 1 damage to 2 random enemies",
            trigger="combat_start",
            action=volley
        )


class Stabiraptor(Character):
    '''An assassin focussed on eliminating dangerous enemies'''
    name: str = "Stabiraptor"
    max_health: int = 3
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_ASSASSIN_RAPTOR

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Assassinate",
            description="Combat start: 3 damage to highest attack enemy",
            trigger="combat_start",
            action=assassinate
        )


class Tankylosaurus(Character):
    '''A tanky blocking unit that can absorb powerful attacks'''
    name: str = "Ankylo"
    max_health: int = 7
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_CLUB

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Solid",
            description="Defending: Max 2 damage taken",
            trigger="defend",
            action=solid
        )


class Macedon(Character):
    '''a balanced fighter, can render enemies unable to attack'''
    name: str = "Macedon"
    max_health: int = 4
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_CREST

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Crippling blow",
            description="Attacking: reduce target attack by 1",
            trigger="attack",
            action=crippling_blow
        )


class Healamimus(Character):
    '''A healer, helps sustain allies'''
    name: str = "Healamimus"
    max_health: int = 4
    damage: int = 1
    range: int = 2
    character_image = ImageChoice.CHARACTER_HEALER

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Heal",
            description="Attacking: heal lowest health ally by 1",
            trigger="attack",
            action=heal
        )


class Dilophmageras(Character):
    '''A long range mage with a penetrating attack'''
    name: str = "Dilophmageras"
    max_health: int = 3
    damage: int = 2
    range: int = 3
    character_image = ImageChoice.CHARACTER_DILOPHMAGE

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Blast",
            description="Attacking: enemy behind takes 1 damage",
            trigger="attack",
            action=blast
        )


class Tripiketops(Character):
    '''A tanky unit that deals damage when attacked'''
    name: str = "Tripiketops"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_PIKEMAN

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Parry",
            description="Defending: attacker takes 1 damage",
            trigger="defend",
            action=parry
        )


class Pterapike(Character):
    '''A versatile unit that targets the enemies back units'''
    name: str = "Pterapike"
    max_health: int = 4
    damage: int = 1
    range: int = 0
    character_image = ImageChoice.CHARACTER_PTERO

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Flying",
            description="Attacking: can always target last enemy",
            trigger="attack",
            action=flying
        )


class Spinoswordaus(Character):
    '''A powerful warrior that becomes lethal as the battle progresses'''
    name: str = "Spinoswordaus"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_SPINO

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Rampage",
            description="Attacking: gain 1 attack",
            trigger="attack",
            action=rampage
        )


class Ateratops(Character):
    '''A mage that enhances allied health'''
    name: str = "Ateratops"
    max_health: int = 3
    damage: int = 2
    range: int = 1  # Melee range
    character_image = ImageChoice.CHARACTER_SUMMONER

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Fortify",
            description="Combat start: allies gain 1 health",
            trigger="combat_start",
            action=fortify
        )


class Velocirougue(Character):
    '''a dual wielding rogue, high damage but hurts self on attack, relies on quick victory'''
    name: str = "Velocirougue"
    max_health: int = 5
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_VELO

    def __init__(self, is_enemy: bool = False) -> None:
        super().__init__(is_enemy)
        self.ability = Ability(
            name="Reckless",
            description="Attacking: lose 1 health",
            trigger="attack",
            action=reckless
        )



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