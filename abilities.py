from typing import Callable, Optional
import random

class Ability:
    def __init__(self, name: str, description: str, trigger: str, action: Callable[["Character", list["CharacterSlot"], list["CharacterSlot"]], None]) -> None:
        self.name = name
        self.description = description
        self.trigger = trigger
        self.action = action

    def activate(self, character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
        self.action(character, allies, enemies)

# Ability Actions

def volley(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Deals 1 damage to 2 random enemies at the start of combat."""
    #Working
    valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
    if valid_targets:
        for _ in range(2):
            if valid_targets:
                target = random.choice(valid_targets)
                target.damage_health(1)
                print(f"{character.name} uses Volley on {target.name}, dealing 1 damage.")


def assassinate(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Deals 3 damage to the highest attack enemy at the start of combat."""
    #TO FIX
    # valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
    # if valid_targets:
    #     highest_attack = max(valid_targets, key=lambda enemy: enemy.damage)
    #     highest_attack.damage_health(3)
    #     print(f"{character.name} uses Assassinate on {highest_attack.name}, dealing 3 damage.")


def solid(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Limits the maximum damage taken to 2 when defending."""
    #TODO


def crippling_blow(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Reduces target's attack by 1 when attacking."""
    #TODO

def heal(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Heals the lowest health ally by 1 when attacking."""
    #Working, but targets max health characters
    valid_targets = [slot.content for slot in allies if slot.content and not slot.content.is_dead()]
    if valid_targets:
        lowest_health_ally = min(valid_targets, key=lambda ally: ally.health)
        lowest_health_ally.health = min(lowest_health_ally.health + 1, lowest_health_ally.max_health)
        print(f"{character.name} uses Heal on {lowest_health_ally.name}, healing 1 health.")


def blast(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Deals 1 damage to the enemy behind the target when attacking."""
    #TODO


def parry(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Deals 1 damage to the attacker when defending."""
    #TODO

def flying(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Allows the character to always target the last enemy when attacking."""
    #TODO

def rampage(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Gains 1 attack when attacking."""
    #Working
    character.damage += 1
    print(f"{character.name} uses Rampage, gaining 1 attack.")

def fortify(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Increases all allies' health by 1 at the start of combat."""
    #TODO

def reckless(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
    """Loses 1 health when attacking."""
    #Working
    character.damage_health(1)
    print(f"{character.name} uses Reckless, losing 1 health.")
