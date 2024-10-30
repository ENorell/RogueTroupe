from enum import Enum
from pygame import Surface, image


class ImageChoice(Enum):
    BACKGROUND_COMBAT_JUNGLE  = "assets/backgrounds/combat_jungle.webp"
    BACKGROUND_SHOP_JUNGLE    = "assets/backgrounds/shop_jungle.webp"

    CHARACTER_CORPSE          = "assets/corpse-transformed.webp"

    #Characters
    CHARACTER_ARCHER          = "assets/characters/archer-transformed.webp"  
    CHARACTER_ASSASSIN_RAPTOR = "assets/characters/assassinraptor-transformed.webp"
    CHARACTER_CLUB            = "assets/characters/club-transformed.webp"
    CHARACTER_CREST           = "assets/characters/crest-transformed.webp"
    CHARACTER_HEALER          = "assets/characters/healer-transformed.webp"
    CHARACTER_DILOPHMAGE      = "assets/characters/dilophmage-transformed.webp"
    CHARACTER_PIKEMAN         = "assets/characters/pikeman-transformed.webp"
    CHARACTER_PTERO           = "assets/characters/ptero-transformed.webp"
    CHARACTER_SPINO           = "assets/characters/spino-transformed.webp"
    CHARACTER_SUMMONER        = "assets/characters/summoner-transformed.webp"
    CHARACTER_VELO            = "assets/characters/velo-transformed.webp"
    CHARACTER_ALCHEMIST       = "assets/characters/alchemist-transformed.webp"
    CHARACTER_BARD            = "assets/characters/bard-transformed.webp"
    CHARACTER_BATTLE_MAGE     = "assets/characters/battlemage-transformed.webp"
    CHARACTER_NATURE_MAGE     = "assets/characters/nature-transformed.webp"
    CHARACTER_NECROMANCER     = "assets/characters/necro-transformed.webp"
    CHARACTER_QUETZALCOATLUS  = "assets/characters/quetz-transformed.webp"
    CHARACTER_RAPTOR          = "assets/characters/raptor2-transformed.webp"
    CHARACTER_DEFENDER        = "assets/characters/shield-transformed.webp"

    #Enemies
    CHARACTER_AEPYCAMELUS     = "assets/enemies/aepycamelus.webp"
    CHARACTER_BRONTOTHERIUM   = "assets/enemies/brontotherium.webp"
    CHARACTER_CRANIOCERAS     = "assets/enemies/cranioceras.webp"
    CHARACTER_GLYPTO          = "assets/enemies/glypto.webp"
    CHARACTER_GORGONO         = "assets/enemies/gorgonopsid.webp"
    CHARACTER_MAMMOTH         = "assets/enemies/mammoth-transformed.webp"
    CHARACTER_PHORUS          = "assets/enemies/phorusrhacus.webp"
    CHARACTER_SABRE           = "assets/enemies/sabre-transformed.webp"
    CHARACTER_SLOTH           = "assets/enemies/sloth.webp"
    CHARACTER_TRILO           = "assets/enemies/trilobite-transformed.webp"

    #UI images
    CHARACTER_TOOLTIP         = "assets/ui/tooltip.webp"
    SLOT                      = "assets/ui/slot.webp"
    SLOT_HOVER                = "assets/ui/slot-hover.webp"
    COMBAT_TARGET             = "assets/ui/target.png"
    HEALTH_ICON               = "assets/ui/health.webp"
    DAMAGE_ICON               = "assets/ui/attack.webp"
    REROLL_BUTTON             = "assets/ui/reroll.webp"
    FIGHT_BUTTON              = "assets/ui/fight.webp"
    BUY_BUTTON                = "assets/ui/buy.webp"
    GOLD_ICON                 = "assets/ui/gold.webp"
    GOLD_BACK                 = "assets/ui/goldback.webp"

IMAGES: dict[ImageChoice, Surface] = {character_image: image.load(character_image.value) for character_image in ImageChoice}