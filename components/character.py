from __future__ import annotations
import pygame
from abc import ABC
from typing import Optional
from pygame import Surface, Rect, font

from components.abilities import *
from assets.images import ImageChoice, IMAGES
from settings import Vector, BLACK_COLOR, RED_COLOR, DEFAULT_TEXT_SIZE, WHITE_COLOR
TOOLTIP_WIDTH = 380
TOOLTIP_HEIGHT = 190

RANGE_ICON_HEIGHT = 40
RANGE_ICON_WIDTH = 50
CHARACTER_ICON_SCALE = 1
HEALTH_ICON_SIZE = 30
DAMAGE_ICON_SIZE = 30

# Define a mapping for user-friendly descriptions
TRIGGER_TYPE_DESCRIPTIONS = {
    TriggerType.COMBAT_START: "Combat Start",
    TriggerType.ROUND_START: "Each Round",
    TriggerType.TURN_START: "Each Turn",
}
class Character(ABC):
    name: str = "Character"
    width_pixels: int = 100
    height_pixels: int = 100
    max_health: int = 5
    damage: int = 2
    range: int = 1
    ability_type: Optional[type[Ability]] = None
    ability_charges = None
    character_image: ImageChoice
    corpse_image = ImageChoice.CHARACTER_CORPSE
    tier: int = 0

    def __init__(self) -> None:
        self._health = self.max_health
        self.is_attacking = False
        self.is_defending = False
        self.is_waiting = False
        self.target = None
        self.attacker = None
        self.combat_indicator: Optional[str] = None
        self.ability_queue: list[Ability] = []

    def attack(self) -> None:
        self.queue_ability(TriggerType.ATTACK, attacker=None)

    def do_damage(self, amount: int, attacker: Character) -> None:
        if self.is_dead():
            logging.debug(f"{attacker} attacks {self.name}, but they are already dead")
            return
        self.lose_health(amount)
        if self.health == 0:
            self.die(attacker)
            return
        self.queue_ability(TriggerType.DEFEND, attacker)

    def lose_health(self, damage: int) -> None:
        self._health = max(self._health - damage, 0)

    def queue_ability(self, trigger_type: TriggerType, attacker: Optional[Character]) -> None:
        if not self.ability_type: return
        if not self.ability_type.trigger == trigger_type: return
        ability = self.ability_type(self, attacker)
        self.ability_queue.append(ability)

    def die(self, attacker: 'Character') -> None:
        self.queue_ability(TriggerType.DEATH, attacker)

        if attacker is self: logging.debug(f"{self.name} killed themself")
        else: logging.debug(f"{attacker.name} killed {self.name}")

    def is_dead(self) -> bool:
        return self._health == 0
    
    def restore_health(self, healing: int) -> None:
        self._health = min(self._health + healing, self.max_health)

    def raise_max_health(self, amount: int) -> None:
        self.max_health += amount # Shared between instances?...

    def is_full_health(self) -> bool:
        return self._health == self.max_health

    def revive(self) -> None:
        self._health = self.max_health

    def consume_ability_charge(self) -> None:
        self.ability_charges -= 1

    @property
    def health(self) -> int:
        return self._health

# TIER 1 CHARACTERS
class Pterapike(Character):
    name: str = "Pterapike"
    max_health: int = 4
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_PTERO
    ability_type: Optional[type[Ability]] = None
    tier: int = 1

class Archeryptrx(Character):
    name: str = "Archeryptrx"
    max_health: int = 3
    damage: int = 1
    range: int = 2
    character_image = ImageChoice.CHARACTER_ARCHER
    ability_type: Optional[type[Ability]] = Volley
    tier: int = 1

class Stabiraptor(Character):
    name: str = "Stabiraptor"
    max_health: int = 3
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_ASSASSIN_RAPTOR
    ability_type: Optional[type[Ability]] = None
    tier: int = 1

class Healamimus(Character):
    name: str = "Healamimus"
    max_health: int = 4
    damage: int = 1
    range: int = 2
    character_image = ImageChoice.CHARACTER_HEALER
    ability_type: Optional[type[Ability]] = Heal
    tier: int = 1

class Tripiketops(Character):
    name: str = "Tripiketops"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_PIKEMAN
    ability_type: Optional[type[Ability]] = Enrage
    tier: int = 1

# TIER 2 CHARACTERS
class Tankylosaurus(Character):
    name: str = "Tankylosaurus"
    max_health: int = 7
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_CLUB
    ability_type: Optional[type[Ability]] = Parry
    tier: int = 2

class Macedon(Character):
    name: str = "Macedon"
    max_health: int = 4
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_CREST
    ability_type: Optional[type[Ability]] = Devour
    tier: int = 2

class Velocirougue(Character):
    name: str = "Velocirougue"
    max_health: int = 5
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_VELO
    ability_type: Optional[type[Ability]] = Reckless
    tier: int = 2

class Bardomimus(Character):
    name: str = "Bardomimus"
    max_health: int = 3
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_BARD
    ability_type: Optional[type[Ability]] = Inspire
    tier: int = 2

class Triceros(Character):
    name: str = "Triceros"
    max_health: int = 7
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_DEFENDER
    ability_type: Optional[type[Ability]] = None
    tier: int = 2

# TIER 3 CHARACTERS
class Dilophmageras(Character):
    name: str = "Dilophmageras"
    max_health: int = 3
    damage: int = 2
    range: int = 3
    character_image = ImageChoice.CHARACTER_DILOPHMAGE
    ability_type: Optional[type[Ability]] = AcidBurst
    tier: int = 3

class Ateratops(Character):
    name: str = "Ateratops"
    max_health: int = 3
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_SUMMONER
    ability_type: Optional[type[Ability]] = CorpseExplosion
    tier: int = 3

class Krytoraptor(Character):
    name: str = "Krytoraptor"
    max_health: int = 3
    damage: int = 4
    range: int = 1
    character_image = ImageChoice.CHARACTER_RAPTOR
    ability_type: Optional[type[Ability]] = None
    tier: int = 3

class Naturalis(Character):
    name: str = "Naturalis"
    max_health: int = 4
    damage: int = 1
    range: int = 3
    character_image = ImageChoice.CHARACTER_NATURE_MAGE
    ability_type: Optional[type[Ability]] = None
    tier: int = 3

class Alchemixus(Character):
    name: str = "Alchemixus"
    max_health: int = 6
    damage: int = 1
    range: int = 2
    ability_charges = 1
    character_image = ImageChoice.CHARACTER_ALCHEMIST
    ability_type: Optional[type[Ability]] = Potion
    tier: int = 3

# TIER 4 CHARACTERS
class Spinoswordaus(Character):
    name: str = "Spinoswordaus"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_SPINO
    ability_type: Optional[type[Ability]] = Rampage
    tier: int = 4

class Battlemagodon(Character):
    name: str = "Battlemagodon"
    max_health: int = 5
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_BATTLE_MAGE
    ability_type: Optional[type[Ability]] = None
    tier: int = 4

class Necrorex(Character):
    name: str = "Necrorex"
    max_health: int = 3
    damage: int = 2
    range: int = 2
    character_image = ImageChoice.CHARACTER_NECROMANCER
    ability_type: Optional[type[Ability]] = None
    tier: int = 4

class Quetza(Character):
    name: str = "Quetza"
    max_health: int = 4
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_QUETZALCOATLUS
    ability_type: Optional[type[Ability]] = None
    tier: int = 4


#ENEMIES
class Aepycamelus(Character):
    """A tall, long-necked herbivore with swift kicks"""
    name: str = "Aepycamelus"
    max_health: int = 5
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_AEPYCAMELUS
    ability_type: Optional[type[Ability]] = None


class Brontotherium(Character):
    """A massive beast with a powerful charge"""
    name: str = "Brontotherium"
    max_health: int = 8
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_BRONTOTHERIUM
    ability_type: Optional[type[Ability]] = None


class Cranioceras(Character):
    """A headbutting herbivore with strong defensive abilities"""
    name: str = "Cranioceras"
    max_health: int = 6
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_CRANIOCERAS
    ability_type: Optional[type[Ability]] = None


class Glypto(Character):
    """An armored tank with a heavy tail swipe"""
    name: str = "Glypto"
    max_health: int = 7
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_GLYPTO
    ability_type: Optional[type[Ability]] = None


class Gorgono(Character):
    """A fierce predator with a deadly bite"""
    name: str = "Gorgono"
    max_health: int = 4
    damage: int = 5
    range: int = 1
    character_image = ImageChoice.CHARACTER_GORGONO
    ability_type: Optional[type[Ability]] = None


class Mammoth(Character):
    """A woolly giant with a trunk slam ability"""
    name: str = "Mammoth"
    max_health: int = 9
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_MAMMOTH
    ability_type: Optional[type[Ability]] = None


class Phorus(Character):
    """A fast-running bird with a piercing beak attack"""
    name: str = "Phorus"
    max_health: int = 3
    damage: int = 4
    range: int = 1
    character_image = ImageChoice.CHARACTER_PHORUS
    ability_type: Optional[type[Ability]] = None


class Sabre(Character):
    """A stealthy cat with a sharp bite"""
    name: str = "Sabre"
    max_health: int = 4
    damage: int = 4
    range: int = 1
    character_image = ImageChoice.CHARACTER_SABRE
    ability_type: Optional[type[Ability]] = None


class Sloth(Character):
    """A slow-moving giant with a powerful claw attack"""
    name: str = "Sloth"
    max_health: int = 6
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_SLOTH
    ability_type: Optional[type[Ability]] = None


class Trilo(Character):
    """An ancient armored invertebrate with a hard shell"""
    name: str = "Trilo"
    max_health: int = 5
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_TRILO
    ability_type: Optional[type[Ability]] = None



from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_font(font_name: str, font_size: int):
    return font.SysFont(name=font_name, size=font_size)

def draw_text(text_content: str, window: Surface, center_position: Vector, scale_ratio: float = 1, font_name: str = "pixel_font", color: tuple[int, int, int] = BLACK_COLOR) -> None:
    font_size: int = round(DEFAULT_TEXT_SIZE * scale_ratio)
    text_font = get_cached_font(font_name, font_size)
    text = text_font.render(text_content, True, color)
    text_topleft_position = (center_position[0] - text.get_width() / 2, center_position[1] - text.get_height() / 2)
    window.blit(text, text_topleft_position)

def add_tier_icon_to_character(frame: Surface, character: Character, rect: Rect):
    # Define the tier icon size
    tier_icon_size = 30  # Adjust this size to fit well within the character image

    # Define the mapping of tiers to their respective icons
    tier_icon_mapping = {
        1: ImageChoice.COMMON_TIER_ICON,
        2: ImageChoice.UNCOMMON_TIER_ICON,
        3: ImageChoice.RARE_TIER_ICON,
        4: ImageChoice.LEGENDARY_TIER_ICON
    }
    
    # Get the icon for the character's tier
    tier_icon_key = tier_icon_mapping.get(character.tier, ImageChoice.COMMON_TIER_ICON)
    tier_icon = get_scaled_image(tier_icon_key, (tier_icon_size, tier_icon_size))

    # Calculate the position to place the tier icon (top left corner of the character image)
    tier_icon_position = (rect.left + 5, rect.top + 5)

    # Draw the tier icon onto the frame
    frame.blit(tier_icon, tier_icon_position)

def draw_character(frame: Surface, mid_bottom: Vector, character: Character, is_enemy: bool = False, scale_ratio: float = 1, slot_is_hovered: bool = False):
    character_image, rect = get_character_image(character, mid_bottom, scale_ratio, is_enemy)
    frame.blit(character_image, rect.topleft)
    
    # Add the tier icon to the character image
    add_tier_icon_to_character(frame, character, rect)

    draw_character_status(frame, character, rect, mid_bottom, scale_ratio)

    if slot_is_hovered:
        draw_tooltip(frame, character, mid_bottom, scale_ratio)


@lru_cache(maxsize=128)
def get_scaled_image(image_key: ImageChoice, size: tuple[int, int], flip: bool = False) -> Surface:
    character_image = IMAGES[image_key].convert_alpha()
    character_image = pygame.transform.scale(character_image, size)
    if flip:
        character_image = pygame.transform.flip(character_image, True, False)
    return character_image

def get_character_image(character: Character, mid_bottom: Vector, scale_ratio: float, is_enemy: bool) -> tuple[Surface, Rect]:
    image_key = character.corpse_image if character.is_dead() else character.character_image
    rect = Rect(
        (mid_bottom[0] - character.width_pixels * scale_ratio / 2, mid_bottom[1] - character.height_pixels * scale_ratio),
        (character.width_pixels * scale_ratio, character.height_pixels * scale_ratio)
    )

    character_image = get_scaled_image(image_key, rect.size, flip=is_enemy)
    return character_image, rect

def draw_tooltip(frame: Surface, character: Character, mid_bottom: Vector, scale_ratio: float):
    box_width = TOOLTIP_WIDTH
    box_height = TOOLTIP_HEIGHT

    tooltip_rect = Rect(
        (mid_bottom[0] - box_width / 2, mid_bottom[1] - character.height_pixels - box_height - 40),
        (box_width, box_height)
    )

    # Clamp the tooltip position to ensure it stays within the screen boundaries
    screen_rect = frame.get_rect()
    tooltip_rect.left = max(screen_rect.left, min(tooltip_rect.left, screen_rect.right - tooltip_rect.width))
    tooltip_rect.top = max(screen_rect.top, min(tooltip_rect.top, screen_rect.bottom - tooltip_rect.height))

    tooltip_image = get_scaled_image(ImageChoice.CHARACTER_TOOLTIP, tooltip_rect.size)
    frame.blit(tooltip_image, tooltip_rect.topleft)
    draw_tooltip_text(frame, character, tooltip_rect, scale_ratio)

    # Add tier icon to the top right corner of the tooltip
    tier_icon_size = 80  # Size of the tier icon
    tier_icon_mapping = {
        1: ImageChoice.COMMON_TIER_EGG,
        2: ImageChoice.UNCOMMON_TIER_EGG,
        3: ImageChoice.RARE_TIER_EGG,
        4: ImageChoice.LEGENDARY_TIER_EGG
    }
    tier_icon_key = tier_icon_mapping.get(character.tier, ImageChoice.COMMON_TIER_EGG)
    tier_icon = get_scaled_image(tier_icon_key, (tier_icon_size, tier_icon_size))
    tier_icon_position = (tooltip_rect.right - tier_icon_size - 10, tooltip_rect.top + 10)
    frame.blit(tier_icon, tier_icon_position)

def draw_tooltip_text(frame: Surface, character: Character, tooltip_rect: Rect, scale_ratio: float):
    draw_text(f"{character.name}", frame, (tooltip_rect.left + tooltip_rect.width / 2, tooltip_rect.top + 40), 1.5*scale_ratio, "pixel_font")
    draw_range_icons(frame, character, tooltip_rect, scale_ratio)
    draw_character_ability(frame, character, tooltip_rect, scale_ratio)

def draw_range_icons(frame: Surface, character: Character, tooltip_rect: Rect, scale_ratio: float):
    range_icon = get_scaled_image(ImageChoice.SLOT, (RANGE_ICON_WIDTH, RANGE_ICON_HEIGHT))
    total_range_width = (character.range + 1) * RANGE_ICON_WIDTH
    start_x = tooltip_rect.left + (tooltip_rect.width - total_range_width) / 2
    target_indicator = get_scaled_image(ImageChoice.COMBAT_TARGET, (RANGE_ICON_HEIGHT, RANGE_ICON_HEIGHT))

    range_indicator_offset = 75

    for i in range(character.range + 1):
        range_icon_position = (start_x + i * RANGE_ICON_WIDTH, tooltip_rect.top + range_indicator_offset)
        frame.blit(range_icon, range_icon_position)
        if i != 0:
            frame.blit(target_indicator, (range_icon_position[0] + (RANGE_ICON_WIDTH - RANGE_ICON_HEIGHT) / 2, range_icon_position[1] - RANGE_ICON_HEIGHT / 2))
            draw_text(f"{character.damage}", frame, (range_icon_position[0] + RANGE_ICON_WIDTH / 2 + (RANGE_ICON_WIDTH - RANGE_ICON_HEIGHT) / 2 - 5, range_icon_position[1] + RANGE_ICON_HEIGHT / 2 - 15), scale_ratio * 1.5, font_name="pixel_font")

    if character.range > 0:
        character_icon_size = CHARACTER_ICON_SCALE * RANGE_ICON_WIDTH
        character_image = get_scaled_image(character.character_image, (character_icon_size, character_icon_size))
        frame.blit(character_image, (start_x, tooltip_rect.top + range_indicator_offset - character_icon_size / 2))

def draw_character_ability(frame: Surface, character: Character, tooltip_rect: Rect, scale_ratio: float):
    if character.ability_type:
        ability_text = f"{character.ability_type.name} : {TRIGGER_TYPE_DESCRIPTIONS.get(character.ability_type.trigger, 'Unknown Trigger')}"
        ability_desc = f"{character.ability_type.description}"
        draw_text(ability_text, frame, (tooltip_rect.left + tooltip_rect.width / 2, tooltip_rect.top + 125), scale_ratio, "pixel_font")
        draw_text(ability_desc, frame, (tooltip_rect.left + tooltip_rect.width / 2, tooltip_rect.top + 145), scale_ratio, "pixel_font")
    else:
        draw_text("No Ability", frame, (tooltip_rect.left + tooltip_rect.width / 2, tooltip_rect.top + 125), scale_ratio, "pixel_font")

def draw_character_status(frame: Surface, character: Character, rect: Rect, mid_bottom: Vector, scale_ratio: float):
    if character.is_dead():
        draw_text("DEAD", frame, mid_bottom, scale_ratio, "pixel_font")
    else:
        if character.is_attacking or character.is_defending:
            draw_defending_indicator(frame, rect)
        draw_health_and_damage(frame, character, mid_bottom, scale_ratio)
        if character.combat_indicator:
            draw_text(character.combat_indicator, frame, (mid_bottom[0], rect.top - 20), 2, "pixel_font", color=RED_COLOR)

def draw_defending_indicator(frame: Surface, rect: Rect):
    target_image = get_scaled_image(ImageChoice.COMBAT_TARGET, rect.size)
    frame.blit(target_image, rect.topleft)

def draw_health_and_damage(frame: Surface, character: Character, mid_bottom: Vector, scale_ratio: float):
    health_icon = get_scaled_image(ImageChoice.HEALTH_ICON, (HEALTH_ICON_SIZE, HEALTH_ICON_SIZE))
    health_pos = (mid_bottom[0] - 20 - HEALTH_ICON_SIZE / 2, mid_bottom[1])
    frame.blit(health_icon, health_pos)
    health_text = f"{character.health}"
    draw_text(health_text, frame, (health_pos[0] + HEALTH_ICON_SIZE / 2, health_pos[1] + 0.8 * HEALTH_ICON_SIZE), 2, "pixel_font", color=WHITE_COLOR)

    damage_icon = get_scaled_image(ImageChoice.DAMAGE_ICON, (DAMAGE_ICON_SIZE, DAMAGE_ICON_SIZE))
    damage_pos = (mid_bottom[0] + 20 - DAMAGE_ICON_SIZE / 2, mid_bottom[1])
    frame.blit(damage_icon, damage_pos)
    damage_text = f"{character.damage}"
    draw_text(damage_text, frame, (damage_pos[0] + DAMAGE_ICON_SIZE / 2, damage_pos[1] + 0.8 * DAMAGE_ICON_SIZE), 2, "pixel_font", color=WHITE_COLOR)
