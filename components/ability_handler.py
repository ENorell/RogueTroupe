from typing import TYPE_CHECKING, Final, Optional, Self
from enum import Enum
from abc import ABC, abstractmethod
from settings import GAME_FPS
import logging

if TYPE_CHECKING: # Forward reference
    from character import Character
    from character_slot import CombatSlot


ABILITY_DURATION_S: Final[float] = 1


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
    COMBAT_START    = "Combat Start"
    ROUND_START     = "Each Round"
    TURN_START      = "Each Turn"
    ATTACK          = "On Attack"
    DEFEND          = "On Defend"
    DEATH           = "On Death"


class Ability(ABC):
    name: str
    description: str
    trigger_type: TriggerType
    is_done: bool = False

    def __init__(self, caster: "Character") -> None:
        self.caster = caster
        self.triggerer: Optional["Character"] = None
        self.duration = Delay(ABILITY_DURATION_S)
        self.targets: list["Character"] = []
        self.has_searched_targets = False

    @property
    @abstractmethod
    def target_indicator(self) -> str:
        ...

    def highlight_characters(self) -> None:
        self.caster.combat_indicator = self.name if self.targets else "Waiting"
        self.caster.is_attacking = True
        for target in self.targets:
            target.combat_indicator = self.target_indicator
            target.is_defending = True
        self.has_searched_targets = True

    def loop(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        if not self.has_searched_targets:
            self.determine_targets(ally_slots, enemy_slots)
            self.highlight_characters()
            return

        if not self.duration.is_done:
            self.duration.tick()
            return

        if not self.targets:
            logging.debug(f"{self.caster.name} found no viable targets for {self.name}")
            self.finish()
            return

        self.activate(ally_slots, enemy_slots)

        self.finish()

    @abstractmethod
    def determine_targets(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        ...

    def set_triggerer(self, triggerer: Optional["Character"]) -> None:
        self.triggerer = triggerer

    @classmethod
    def from_trigger(cls, caster: "Character", triggerer: Optional["Character"]) -> Self:
        instance = cls(caster)
        instance.set_triggerer(triggerer)
        return instance

    @abstractmethod
    def activate(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> None:
        ...

    def finish(self) -> None:
        for char in self.targets + [self.caster]:
            char.combat_indicator = None
            char.is_attacking = False
            char.is_defending = False
        self.is_done = True


def get_character_ability(character: "Character", trigger_type: TriggerType) -> Optional[Ability]:
    if not character.ability_type: return
    if not character.ability_type.trigger_type == trigger_type: return
    return character.ability_type(character)


def get_trigger_abilities(ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"], trigger_type: TriggerType) -> list[Ability]:
    ability_queue: list[Ability] = []
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if slot.content.is_dead(): continue
        if not slot.content.ability_type: continue
        if not slot.content.ability_type.trigger_type == trigger_type: continue
        ability = slot.content.ability_type(slot.content)
        ability_queue.append(ability)
    return ability_queue


def empty_ability_queue(ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"]) -> list[Ability]:
    ability_queue: list[Ability] = []
    for slot in ally_slots + enemy_slots:
        if not slot.content: continue
        if not slot.content.ability_queue: continue
        ability_queue.extend(slot.content.ability_queue[:])  # Make a shallow copy
        slot.content.ability_queue.clear()  # Empty the queue
    return ability_queue


def is_all_done(abilities: list[Ability]) -> bool:
    for ability in abilities:
        if not ability.is_done:
            return False
    return True


def run_remaining_abilities(abilities: list[Ability], ally_slots: list["CombatSlot"],
                            enemy_slots: list["CombatSlot"]) -> None:
    for ability in abilities:
        if not ability.is_done:
            ability.loop(ally_slots, enemy_slots)


class AbilityHandler:
    """
    Handles trigger order for a mix of combat/round start abilities and triggered abilities
    """

    def __init__(self, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"], planned_abilities: list[Ability]) -> None:
        self.is_done: bool = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.planned_abilities: list[Ability] = planned_abilities
        self.triggered_abilities: list[Ability] = []
        self.current_ability: Optional[Ability] = None

    @classmethod
    def from_trigger(cls, ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"], trigger_type) -> Self:
        planned_abilities = get_trigger_abilities(ally_slots, enemy_slots, trigger_type)
        instance = cls(ally_slots, enemy_slots, planned_abilities)
        instance.next_ability()
        return instance

    @classmethod
    def turn_abilities(cls, caster: "Character", ally_slots: list["CombatSlot"], enemy_slots: list["CombatSlot"],
                       basic_attack: Ability) -> Self:
        starting_ability = get_character_ability(caster, TriggerType.TURN_START)
        planned_abilities: list[Ability] = [starting_ability, basic_attack] if starting_ability else [basic_attack]
        instance = cls(ally_slots, enemy_slots, planned_abilities)
        instance.next_ability()
        return instance

    def next_ability(self) -> None:
        if not self.planned_abilities:
            self.is_done = True
            return
        self.current_ability = self.planned_abilities.pop(0)

    def activate(self) -> None:
        self.triggered_abilities.extend(empty_ability_queue(self.ally_slots, self.enemy_slots))

        assert self.current_ability
        if not self.current_ability.is_done:
            self.current_ability.loop(self.ally_slots, self.enemy_slots)
            return

        if not is_all_done(self.triggered_abilities):
            run_remaining_abilities(self.triggered_abilities, self.ally_slots, self.enemy_slots)
            return

        self.next_ability()
