from typing import Callable, Optional
import random
from logger import logging

class Ability:
    def __init__(self, name: str, description: str, trigger: str, action: Callable[["Character", list["CharacterSlot"], list["CharacterSlot"], Optional["Character"]], None]) -> None:
        self.name = name
        self.description = description
        self.trigger = trigger
        self.action = action

    def activate(self, character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
        self.action(character, allies, enemies, target_character)
    
# Ability Actions

def volley(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Deals 1 damage to 2 random enemies at the start of combat."""
    valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
    if valid_targets:
        for _ in range(2):
            if valid_targets:
                target = random.choice(valid_targets)
                target.damage_health(1)
                logging.debug(f"{character.name} uses Volley on {target.name}, dealing 1 damage.")

def assassinate(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Deals 3 damage to the highest attack enemy at the start of combat."""
    valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
    if valid_targets:
        highest_attack_target = max(valid_targets, key=lambda enemy: enemy.damage)
        highest_attack_target.damage_health(3)
        logging.debug(f"{character.name} uses assassinate on {highest_attack_target.name}, dealing 3 damage.")


def solid(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Heals when attacked."""
    target_character.health += 1

    logging.debug(f"{target_character.name}'s heals self.")

def crippling_blow(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Reduces enemy attack by 1 down to 0 min"""
    if target_character: 
        target_character.damage = max(0, target_character.damage - 1)

def heal(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Heals the lowest health ally by 1 when attacking."""
    valid_targets = [slot.content for slot in allies if slot.content and not slot.content.is_dead() and slot.content.health < slot.content.max_health]
    if valid_targets:
        lowest_health_ally = min(valid_targets, key=lambda ally: ally.health)
        lowest_health_ally.health = min(lowest_health_ally.health + 1, lowest_health_ally.max_health)
        logging.debug(f"{character.name} uses Heal on {lowest_health_ally.name}, healing 1 health.")

def blast(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Deals 1 damage to the enemy behind the target when attacking."""
    # Find the index of the target character in the enemies list
    target_index = next((i for i, slot in enumerate(enemies) if slot.content == target_character), None)
    
    if target_index is not None and target_index + 1 < len(enemies):
        # Deal 1 damage to the enemy behind the target
        enemies[target_index + 1].content.damage_health(1)
        logging.debug(f"{character.name} blasts {target_character.name}, dealing 1 damage to {enemies[target_index + 1].content.name} .")


def parry(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Deals 1 damage to the attacker when defending."""
    character.damage_health(1)
    logging.debug(f"{target_character.name} parries, dealing 1 damage to {character.name}")


def flying(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Allows the character to always target the last enemy when attacking."""
    # Get the damage value of the character
    damage = character.damage
    

    for i in range(len(enemies) - 1, -1, -1):
        if enemies[i].content:
            enemies[i].content.damage_health(damage)
            logging.debug(f"{character.name} flies to attack {enemies[i].content.name}")
            return


def rampage(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Gains 1 attack when attacking target."""

    if target_character:
        character.damage += 1
        logging.debug(f"{character.name} uses Rampage, gaining 1 attack.")

def fortify(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Increases all allies' health by 1 at the start of combat."""
    for slot in allies:
        slot.content.health += 1
    logging.debug(f"{character.name} uses fortify to give allies 1 extra health.")


def reckless(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"], target_character: Optional["Character"] = None) -> None:
    """Loses 1 health when attacking."""
    character.damage_health(1)
    logging.debug(f"{character.name} uses Reckless, losing 1 health.")
