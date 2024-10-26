from typing import Optional, Protocol, Sequence, Self
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
    combat_indicator: str

    def do_damage(self, amount: int, attacker: Self) -> None:
        ...
    def restore_health(self, healing: int) -> None:
        ...
    def raise_max_health(self, amount: int) -> None:
        ...
    def is_dead(self) -> bool:
        ...
    def is_full_health(self) -> bool:
        ...
    def attack(self) -> None:
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
    ATTACK = auto()
    DEFEND = auto()
    DEATH = auto()


class Ability(ABC):
    name: str
    description: str
    trigger: TriggerType
    is_done: bool = False

    def __init__(self, caster: CharacterInterface, triggerer: Optional[CharacterInterface]) -> None:
        self.caster = caster
        self.triggerer = triggerer

    @classmethod
    def from_plan(cls, caster: CharacterInterface) -> Self:
        return cls(caster, triggerer=None)

    @abstractmethod
    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        ...



# This function hints to the need of some sort of grid class that can hold the slots and calculate distances etc. 
def distance_between(slot_a: SlotInterface, slot_b: SlotInterface) -> int:
    return abs( slot_a.coordinate - slot_b.coordinate )

def get_character_slot(character: CharacterInterface, slots: Sequence[SlotInterface]) -> SlotInterface:
    index = [slot.content for slot in slots if slot].index(character)
    return slots[index]

def get_friendly_slots(character: CharacterInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> Sequence[SlotInterface]:
    return ally_slots if character in [ally_slot.content for ally_slot in ally_slots] else enemy_slots

def get_adversary_slots(character: CharacterInterface, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> Sequence[SlotInterface]:
    return ally_slots if character in [enemy_slot.content for enemy_slot in enemy_slots] else enemy_slots


class BasicAttack(Ability):
    def __init__(self,  caster: CharacterInterface, triggerer: Optional[CharacterInterface]) -> None:
        super().__init__(caster, triggerer)

        self.targeting_delay = Delay(1)
        self.waiting_delay = Delay(0.3)
        self.victim: Optional[CharacterInterface] = None
        self.waiting: bool = False

    def determine_target(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        acting_slot = get_character_slot(self.caster, [*ally_slots, *enemy_slots])

        defender_slots: Sequence[SlotInterface] = enemy_slots if self.caster in [slot.content for slot in ally_slots] else ally_slots

        for target_slot in reversed( defender_slots ): # Prioritize slots farther away?
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not self.caster.range >= distance_between(acting_slot, target_slot): continue

            target_candidate.is_defending = True

            self.victim = target_candidate
            return

        if not self.waiting_delay.is_done:
            self.caster.combat_indicator = "Waiting"
            self.waiting = True
            self.waiting_delay.tick()
            return

        self.caster.combat_indicator = None

        logging.debug(f"{self.caster.name} has no target to attack (range {self.caster.range}).")
        self.is_done = True

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        # Search for target character, stop early if none found
        if not self.victim:
            self.determine_target(ally_slots, enemy_slots)
            return
        
        if self.waiting:
            if not self.waiting_delay.is_done:
                self.caster.combat_indicator = "Waiting"
                self.waiting_delay.tick()
                return
            else:
                self.caster.combat_indicator = None
                self.is_done = True
                self.waiting = False
                return

        self.victim.combat_indicator = f"-{self.caster.damage}"
        self.caster.combat_indicator = "Attack!"

        if not self.targeting_delay.is_done:
            self.targeting_delay.tick()
            return

        logging.debug(f"{self.caster.name} attacks {self.victim.name} for {self.caster.damage} damage!")
        self.caster.attack()

        self.victim.do_damage(self.caster.damage, self.caster)
        self.victim.is_defending = False
        self.victim.combat_indicator = None
        self.caster.combat_indicator = None

        self.is_done = True



class Rampage(Ability):
    name: str = "Rampage"
    description: str = "Attacking: gain 1 attack"
    trigger = TriggerType.TURN_START

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        self.caster.damage += 1
        logging.debug(f"{self.caster.name} uses Rampage, gaining 1 attack.")
        self.is_done = True



class Volley(Ability):
    name: str = "Volley"
    description: str = "Combat start: 1 damage to 2 random enemies"
    trigger = TriggerType.COMBAT_START
    amount: int = 1

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        defender_slots = enemy_slots if self.caster in [slot.content for slot in ally_slots] else ally_slots

        valid_targets: list[CharacterInterface] = [slot.content for slot in defender_slots if slot.content and not slot.content.is_dead()]
        if not valid_targets:
            logging.debug(f"{self.caster.name} found No valid enemy targets for Volley")
            self.is_done = True
            return
        
        for _ in range(2):
            target = random.choice(valid_targets)
            logging.debug(f"{self.caster.name} uses Volley on {target.name}, dealing {self.amount} damage.")
            target.do_damage(self.amount, self.caster)
        self.is_done = True


class Heal(Ability):
    name: str = "Heal"
    description: str = "Attacking: heal lowest health ally by 1"
    trigger = TriggerType.ROUND_START
    healing: int = 1

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        friendly_slots = enemy_slots if self.caster not in [slot.content for slot in ally_slots] else ally_slots

        damaged_living_allies = [slot.content for slot in friendly_slots if slot.content and not slot.content.is_dead() and not slot.content.is_full_health()]
        if not damaged_living_allies: 
            logging.debug(f"No viable targets to heal for {self.caster.name}")
            self.is_done = True
            return
        
        lowest_health_damaged_living_ally = min(damaged_living_allies, key=lambda c: c.health)
        heal_amount = self.healing # + caster.spell_power
        logging.debug(f"{self.caster.name} healed {lowest_health_damaged_living_ally.name} for {heal_amount}")
        lowest_health_damaged_living_ally.restore_health(heal_amount)
        self.is_done = True


class Reckless(Ability):
    name: str = "Reckless"
    description: str = "Loses 1 health when attacking."
    trigger = TriggerType.TURN_START
    damage: int = 1

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        logging.debug(f"{self.caster.name} uses Reckless, losing 1 health.")
        self.caster.do_damage(self.damage, self.caster)
        self.is_done = True


class Devour(Ability):
    name: str = "Reckless"
    description: str = "Gains 1 max health when attacking."
    trigger = TriggerType.ATTACK
    amount: int = 1

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        logging.debug(f"{self.caster.name} uses Devour, raising their max health by {self.amount}.")
        self.caster.raise_max_health(self.amount)
        self.is_done = True


class Enrage(Ability):
    name: str = "Enrage"
    description: str = "Gains 1 damage when damaged."
    trigger = TriggerType.DEFEND
    amount: int = 1

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        logging.debug(f"{self.caster.name} uses Enrage, raising their damage by {self.amount}.")
        self.caster.damage += self.amount
        self.is_done = True


class Parry(Ability):
    name: str = "Parry"
    amount: int = 1
    description: str = f"Parries and deals {amount} damage back to the attacker"
    trigger = TriggerType.DEFEND

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        assert self.triggerer
        logging.debug(f"{self.caster.name} activates thorns, dealing {self.amount} damage back to {self.triggerer.name}.")
        self.triggerer.do_damage(self.amount, self.caster)
        self.is_done = True


class CorpseExplosion(Ability):
    name: str = "Corpse Explosion"
    description: str = "Explodes violently after death."
    trigger = TriggerType.DEATH
    amount: int = 3

    def activate(self, ally_slots: Sequence[SlotInterface], enemy_slots: Sequence[SlotInterface]) -> None:
        adversary_slots = get_adversary_slots(self.caster, ally_slots, enemy_slots)
        viable_targets = [adversary_slot.content for adversary_slot in adversary_slots if adversary_slot.content]
        if not viable_targets:
            logging.debug(f"No viable targets to explode for {self.caster.name}")
            self.is_done = True
            return
        target = viable_targets[0]
        logging.debug(f"{self.caster.name}'s corpse explodes, dealing {self.amount} to {target.name}.")
        target.do_damage(self.amount, self.caster)
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
