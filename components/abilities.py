import logging
import random
from typing import TYPE_CHECKING, Optional
from components.ability_handler import Ability, Delay, TriggerType
if TYPE_CHECKING: # Forward reference
    from character import Character
    from character_slot import CombatSlot

WAITING_DURATION_S = 0.3

# This function hints to the need of some sort of grid class that can hold the slots and calculate distances etc.
def distance_between(slot_a: "CombatSlot", slot_b: "CombatSlot") -> int:
    return abs( slot_a.coordinate - slot_b.coordinate )

def get_character_slot(character: "Character", slots: list["CombatSlot"]) -> "CombatSlot":
    index = [slot.content for slot in slots if slot].index(character)
    return slots[index]

def get_friendly_slots(character: "Character", ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> list["CombatSlot"]:
    return ally_slots if character in [ally_slot.content for ally_slot in ally_slots] else enemy_slots

def get_adversary_slots(character: "Character", ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> list["CombatSlot"]:
    return ally_slots if character in [enemy_slot.content for enemy_slot in enemy_slots] else enemy_slots

def living_characters(slots: list["CombatSlot"]) -> list["Character"]:
    return [slot.content for slot in slots if slot.content and not slot.content.is_dead()]


class BasicAttack(Ability):
    name = "Basic Attack"

    @property
    def target_indicator(self) -> str:
        return f"-{self.caster.damage}"

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        acting_slot = get_character_slot(self.caster, [*ally_slots, *enemy_slots])

        defender_slots: list["CombatSlot"] = enemy_slots if self.caster in [slot.content for slot in
                                                                            ally_slots] else ally_slots
        for target_slot in reversed(defender_slots):  # Prioritize slots farther away?
            if not target_slot.content: continue
            target_candidate = target_slot.content
            if target_candidate.is_dead(): continue
            if not self.caster.range >= distance_between(acting_slot, target_slot): continue

            self.targets.append( target_candidate )

        if not self.targets:
            self.duration = Delay(WAITING_DURATION_S)
            logging.debug(f"{self.caster.name} has no target to attack (range {self.caster.range}).")


    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        victim = self.targets[0]
        logging.debug(f"{self.caster.name} attacks {victim.name} for {self.caster.damage} damage!")
        self.caster.attack()
        victim.do_damage(self.caster.damage, self.caster)



class Rampage(Ability):
    name: str = "Rampage"
    description: str = "Attacking: gain 1 attack"
    trigger_type = TriggerType.TURN_START

    @property
    def target_indicator(self) -> str:
        return "+1 dmg"

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        self.targets.append(self.caster)

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        self.caster.damage += 1
        logging.debug(f"{self.caster.name} uses Rampage, gaining 1 attack.")


class Volley(Ability):
    name: str = "Volley"
    amount: int = 1
    hits: int = 2
    description: str = f"Combat start: {amount} damage to {hits} random enemies"
    trigger_type = TriggerType.COMBAT_START

    @property
    def target_indicator(self) -> str:
        return f"-{self.amount}"

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]):
        defender_slots = enemy_slots if self.caster in [slot.content for slot in ally_slots] else ally_slots

        valid_targets: list["Character"] = [slot.content for slot in defender_slots if
                                            slot.content and not slot.content.is_dead()]

        self.targets: list["Character"] = []
        for _ in range(self.hits):
            target = random.choice(valid_targets)
            self.targets.append(target)

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        for target in self.targets:
            logging.debug(f"{self.caster.name} uses Volley on {target.name}, dealing {self.amount} damage.")
            target.do_damage(self.amount, self.caster)


class Heal(Ability):
    name: str = "Heal"
    description: str = "Attacking: heal lowest health ally by 1"
    trigger_type = TriggerType.ROUND_START
    healing: int = 1

    @property
    def target_indicator(self) -> str:
        return f"+{self.healing}"

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]):
        friendly_slots = enemy_slots if self.caster not in [slot.content for slot in ally_slots] else ally_slots

        damaged_living_allies = [slot.content for slot in friendly_slots if
                                 slot.content and not slot.content.is_dead()
                                 and not slot.content.is_full_health()]

        if damaged_living_allies:
            lowest_health_living_ally = min(damaged_living_allies, key=lambda c: c.health)
            self.targets.append( lowest_health_living_ally )

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        heal_amount = self.healing  # + caster.spell_power
        target = self.targets[0]
        logging.debug(f"{self.caster.name} healed {target.name} for {heal_amount}")
        target.restore_health(heal_amount)


class Reckless(Ability):
    name: str = "Reckless"
    description: str = "Loses 1 health when attacking."
    trigger_type = TriggerType.TURN_START
    damage: int = 1

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        self.targets.append(self.caster)

    @property
    def target_indicator(self) -> str:
        return f"-{self.damage}"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        logging.debug(f"{self.caster.name} uses Reckless, losing 1 health.")
        self.caster.do_damage(self.damage, self.caster)


class Devour(Ability):
    name: str = "Devour"
    description: str = "Gains 1 max health when attacking."
    trigger_type = TriggerType.ATTACK
    amount: int = 1

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        self.targets.append(self.caster)

    @property
    def target_indicator(self) -> str:
        return f"+{self.amount} max hp"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        logging.debug(f"{self.caster.name} uses Devour, raising their max health by {self.amount}.")
        self.caster.raise_max_health(self.amount)



class Enrage(Ability):
    name: str = "Enrage"
    description: str = "Gains 1 damage when damaged."
    trigger_type = TriggerType.DEFEND
    amount: int = 1

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        self.targets.append(self.caster)

    @property
    def target_indicator(self) -> str:
        return f"+{self.amount} dmg"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        logging.debug(f"{self.caster.name} uses Enrage, raising their damage by {self.amount}.")
        self.caster.damage += self.amount


class Parry(Ability):
    name: str = "Parry"
    amount: int = 1
    description: str = f"Parries and deals {amount} damage back to the attacker"
    trigger_type = TriggerType.DEFEND

    @property
    def target_indicator(self) -> str:
        return f"-{self.amount}"

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        assert self.triggerer
        self.targets.append(self.triggerer)

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        target = self.targets[0]
        logging.debug(
            f"{self.caster.name} activates Parry, dealing {self.amount} damage back to {target.name}.")
        target.do_damage(self.amount, self.caster)


class CorpseExplosion(Ability):
    name: str = "Corpse Explosion"
    description: str = "Blows up a corpse at start of turn, damaging enemies."
    trigger_type = TriggerType.TURN_START
    amount: int = 2

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        adversary_slots = get_adversary_slots(self.caster, ally_slots, enemy_slots)

        corpse_slots = [adversary_slot for adversary_slot in adversary_slots if
                        adversary_slot.content and adversary_slot.content.is_dead()]
        if not corpse_slots:
            logging.debug(f"No viable corpses to explode for {self.caster.name}")
            return

        self.corpse_slot = corpse_slots[0]
        assert self.corpse_slot.content
        self.corpse_slot.content.combat_indicator = self.name

        viable_targets = [adversary_slot.content for adversary_slot in adversary_slots if adversary_slot.content and not adversary_slot.content.is_dead()]
        if not viable_targets:
            logging.debug(f"No viable targets to damage for {self.caster.name}")
            return

        self.targets.append(viable_targets[0])

    @property
    def target_indicator(self) -> str:
        return f"-{self.amount}"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        target = self.targets[0]
        logging.debug(f"{self.caster.name}'s corpse explodes, dealing {self.amount} to {target.name}.")
        target.do_damage(self.amount, self.caster)
        self.corpse_slot.content = None  # Crude way to get rid of character. Should be sent to a "graveyard"


class AcidBurst(Ability):
    name: str = "Acid Burst"
    description: str = "Explodes violently after death."
    trigger_type = TriggerType.DEATH
    amount: int = 3

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        adversary_slots = get_adversary_slots(self.caster, ally_slots, enemy_slots)
        viable_targets = [adversary_slot.content for adversary_slot in adversary_slots if adversary_slot.content]
        if not viable_targets:
            logging.debug(f"No viable targets to damage for {self.caster.name}")
            return
        self.targets.append( viable_targets[0] )

    @property
    def target_indicator(self) -> str:
        return f"-{self.amount}"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        target = self.targets[0]
        logging.debug(f"{self.caster.name}'s corpse explodes, dealing {self.amount} to {target.name}.")
        target.do_damage(self.amount, self.caster)


class Inspire(Ability):
    name: str = "Inspire"
    description: str = "Inspire front ally to attack"
    trigger_type = TriggerType.TURN_START

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        if ally_slots[0].content and ally_slots[0].content != self.caster:
            self.targets.append(ally_slots[0].content)

    @property
    def target_indicator(self) -> str:
        return self.name

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        target = self.targets[0]
        logging.debug(f"{self.caster.name} inspires {target.name} to attack.")
        target.attack()


class Potion(Ability):
    name: str = "Potion"
    description: str = "If health below 3, heal to max health"
    trigger_type = TriggerType.TURN_START

    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        if self.caster.health < 3 and self.caster.ability_charges and self.caster.ability_charges > 0:
            self.targets.append(self.caster)

    @property
    def target_indicator(self) -> str:
        return f"full heal"

    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        logging.debug(f"{self.caster.name} uses potion to heal.")
        self.caster.revive()
        self.caster.consume_ability_charge()


# def assassinate(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Deals 3 damage to the highest attack enemy at the start of combat."""
#    #TO FIX
#    # valid_targets = [slot.content for slot in enemies if slot.content and not slot.content.is_dead()]
#    # if valid_targets:
#    #     highest_attack = max(valid_targets, key=lambda enemy: enemy.damage)
#    #     highest_attack.damage_health(3)
#    #     print(f"{character.name} uses Assassinate on {highest_attack.name}, dealing 3 damage.")
#
#
# def solid(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Limits the maximum damage taken to 2 when defending."""
#    #TODO
#
#
# def crippling_blow(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Reduces target's attack by 1 when attacking."""
#    #TODO
#
#
# def blast(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Deals 1 damage to the enemy behind the target when attacking."""
#    #TODO
#
#
# def flying(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Allows the character to always target the last enemy when attacking."""
#    #TODO
#
#
# def fortify(character: "Character", allies: list["CharacterSlot"], enemies: list["CharacterSlot"]) -> None:
#    """Increases all allies' health by 1 at the start of combat."""
#    #TODO
