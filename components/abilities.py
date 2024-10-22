from typing import Optional, Protocol, Sequence
import random
from enum import Enum, auto
from abc import ABC, abstractmethod
from settings import GAME_FPS
import logging



class CharacterInterface(Protocol): # Put an interface to avoid circular imports
    damage: int
    name: str
    range: int
    is_defending: bool

    def damage_health(self, damage: int) -> None:
        ...
    def restore_health(self, healing: int) -> None:
        ...
    def is_dead(self) -> bool:
        ...
    def is_full_health(self) -> bool:
        ...
    
    @property
    def health(self) -> int:
        ...

class SlotInterface(Protocol):
    coordinate: int

    @property
    def content(self) -> Optional[CharacterInterface]:
        ...



class Delay:
    def __init__(self, delay_time_s: float) -> None:
        self.delay_time_s = delay_time_s
        self.frame_counter = 0

    def tick(self) -> None:
        self.frame_counter += 1

    @property
    def is_done(self) -> bool:
        return self.frame_counter > self.delay_time_s * GAME_FPS


class TriggerType(Enum):
    COMBAT_START = auto()
    ROUND_START = auto()
    TURN_START = auto()


class Ability(ABC):
    name: str
    description: str
    trigger: TriggerType

    def __init__(self) -> None:
        self.is_done: bool = False

    @abstractmethod
    def activate(self, caster: CharacterInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        ...



# This function hints to the need of some sort of grid class that can hold the slots and calculate distances etc. 
def distance_between(slot_a: SlotInterface, slot_b: SlotInterface) -> int:
    return abs( slot_a.coordinate - slot_b.coordinate )


class BasicAttack(Ability):
    def __init__(self, acting_slot: SlotInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        super().__init__()
        self.acting_slot = acting_slot
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
    
        self.targeting_delay = Delay(1)
        self.victim: Optional[CharacterInterface] = None

    def activate(self, caster: CharacterInterface, *_) -> None:
        # Search for target character, stop early if none found
        if not self.victim:
            self.determine_target(caster)
            return
        
        if not self.targeting_delay.is_done:
            self.targeting_delay.tick()
            return

        self.victim.damage_health(caster.damage)
        self.victim.is_defending = False

        logging.debug(f"{caster.name} attacks {self.victim.name} for {caster.damage} damage!")

        self.is_done = True

    def determine_target(self, caster: CharacterInterface) -> None:
        defender_slots: Sequence[SlotInterface] = self.ally_slots if self.acting_slot in self.enemy_slots else self.enemy_slots

        for target_slot in reversed( defender_slots ): # Prioritize slots farther away?
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not caster.range >= distance_between(self.acting_slot, target_slot): continue

            target_candidate.is_defending = True
            
            self.victim = target_candidate
            return
        
        logging.debug(f"{caster.name} has no target to attack (range {caster.range}).")
        self.is_done = True



class Rampage(Ability):
    name: str = "Rampage"
    description: str = "Attacking: gain 1 attack"
    trigger = TriggerType.TURN_START

    def activate(self, caster: CharacterInterface, *_) -> None:
        caster.damage += 1
        logging.debug(f"{caster.name} uses Rampage, gaining 1 attack.")
        self.is_done = True



class Volley(Ability):
    name: str = "Volley"
    description: str = "Combat start: 1 damage to 2 random enemies"
    trigger = TriggerType.COMBAT_START

    def activate(self, caster: CharacterInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        defender_slots = enemy_slots if caster in [slot.content for slot in ally_slots] else ally_slots

        valid_targets: list[CharacterInterface] = [slot.content for slot in defender_slots if slot.content and not slot.content.is_dead()]
        if not valid_targets:
            logging.debug(f"{caster.name} found No valid enemy targets for Volley")
            self.is_done = True
            return
        
        for _ in range(2):
            target = random.choice(valid_targets)
            logging.debug(f"{caster.name} uses Volley on {target.name}, dealing 1 damage.")
            target.damage_health(1)
        self.is_done = True


class Heal(Ability):
    name: str = "Heal"
    description: str = "Attacking: heal lowest health ally by 1"
    trigger = TriggerType.ROUND_START
    healing: int = 1

    def activate(self, caster: CharacterInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        friendly_slots = enemy_slots if caster not in [slot.content for slot in ally_slots] else ally_slots

        damaged_living_allies = [slot.content for slot in friendly_slots if slot.content and not slot.content.is_dead() and not slot.content.is_full_health()]
        if not damaged_living_allies: 
            logging.debug(f"No viable targets to heal for {caster.name}")
            self.is_done = True
            return
        
        lowest_health_damaged_living_ally = min(damaged_living_allies, key=lambda c: c.health)
        heal_amount = self.healing # + caster.spell_power
        logging.debug(f"{caster.name} healed {lowest_health_damaged_living_ally.name} for {heal_amount}")
        lowest_health_damaged_living_ally.restore_health(heal_amount)
        self.is_done = True


class Reckless(Ability):
    name: str = "Reckless"
    description: str = "Loses 1 health when attacking."
    trigger = TriggerType.TURN_START
    damage: int = 1

    def activate(self, caster: CharacterInterface, *_) -> None:
        logging.debug(f"{caster.name} uses Reckless, losing 1 health.")
        caster.damage_health(self.damage)
        self.is_done = True


#def assassinate(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Deals 3 damage to the highest attack enemy at the start of combat."""
#    #TO FIX
#    # valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
#    # if valid_targets:
#    #     highest_attack = max(valid_targets, key=lambda enemy: enemy.damage)
#    #     highest_attack.damage_health(3)
#    #     print(f"{character.name} uses Assassinate on {highest_attack.name}, dealing 3 damage.")
#
#
#def solid(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Limits the maximum damage taken to 2 when defending."""
#    #TODO
#
#
#def crippling_blow(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Reduces target's attack by 1 when attacking."""
#    #TODO
#
#
#def blast(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Deals 1 damage to the enemy behind the target when attacking."""
#    #TODO
#
#
#def parry(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Deals 1 damage to the attacker when defending."""
#    #TODO
#
#def flying(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Allows the character to always target the last enemy when attacking."""
#    #TODO
#
#
#def fortify(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Increases all allies' health by 1 at the start of combat."""
#    #TODO
