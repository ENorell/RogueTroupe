from typing import Type, Sequence, Optional
from random import choices, choice
from components.character import Character
from components.character_slot import CharacterSlot
from assets.images import ImageChoice
from components.ability_handler import Ability
from components import abilities

# Configurable probabilities for each tier
TIER_PROBABILITIES = [0.9, 0.08, 0.015, 0.005]
# Combined tier dictionary for reference


def generate_characters(slots: Sequence[CharacterSlot], character_tiers: dict[int, list[Type[Character]]], tier_probabilities: list[float]) -> None:
    for slot in slots:
        # Select tier based on configured probabilities
        selected_tier = choices(list(character_tiers.keys()), weights=tier_probabilities, k=1)[0]
        # Randomly select a character type from the chosen tier
        character_type = choice(character_tiers[selected_tier])
        # Assign character to the slot
        slot.content = character_type()


# Function to dynamically create CHARACTER_TIERS dictionary
def create_character_tiers() -> dict[int, list[Type[Character]]]:
    character_classes = Character.__subclasses__()
    character_tiers: dict[int, list[Type[Character]]] = {}
    for character_class in character_classes:
        tier = character_class.tier
        if tier == 0:
            continue
        if tier not in character_tiers:
            character_tiers[tier] = []
        character_tiers[tier].append(character_class)
    return character_tiers



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
    ability_type: Optional[type[Ability]] = abilities.Volley
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
    ability_type: Optional[type[Ability]] = abilities.Heal
    tier: int = 1

class Tripiketops(Character):
    name: str = "Tripiketops"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_PIKEMAN
    ability_type: Optional[type[Ability]] = abilities.Enrage
    tier: int = 1

# TIER 2 CHARACTERS
class Tankylosaurus(Character):
    name: str = "Tankylosaurus"
    max_health: int = 7
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_CLUB
    ability_type: Optional[type[Ability]] = abilities.Parry
    tier: int = 2

class Macedon(Character):
    name: str = "Macedon"
    max_health: int = 4
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_CREST
    ability_type: Optional[type[Ability]] = abilities.Devour
    tier: int = 2

class Velocirougue(Character):
    name: str = "Velocirougue"
    max_health: int = 5
    damage: int = 3
    range: int = 1
    character_image = ImageChoice.CHARACTER_VELO
    ability_type: Optional[type[Ability]] = abilities.Reckless
    tier: int = 2

class Bardomimus(Character):
    name: str = "Bardomimus"
    max_health: int = 3
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_BARD
    ability_type: Optional[type[Ability]] = abilities.Inspire
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
    ability_type: Optional[type[Ability]] = abilities.AcidBurst
    tier: int = 3

class Ateratops(Character):
    name: str = "Ateratops"
    max_health: int = 3
    damage: int = 2
    range: int = 1
    character_image = ImageChoice.CHARACTER_SUMMONER
    ability_type: Optional[type[Ability]] = abilities.CorpseExplosion
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
    ability_type: Optional[type[Ability]] = abilities.Potion
    tier: int = 3

# TIER 4 CHARACTERS
class Spinoswordaus(Character):
    name: str = "Spinoswordaus"
    max_health: int = 6
    damage: int = 1
    range: int = 1
    character_image = ImageChoice.CHARACTER_SPINO
    ability_type: Optional[type[Ability]] = abilities.Rampage
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



CHARACTER_TIERS = create_character_tiers()