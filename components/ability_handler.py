from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto
from abilities import TriggerType

class EventType(Enum):
    ATTACK = auto()
    KILL = auto()
    HEAL = auto()

@dataclass
class Event:
    #event_type: EventType
    trigger_type: TriggerType
    source: Unit
    target: Optional[Unit] = None

class EventQueue:
    def __init__(self):
        self.queue: list[Event] = []

    def empty_queue(self) -> None:
        self.queue.clear()

class Unit:
    #ability_type:
    def __init__(self):
        self.health = 10

    def take_damage(self, damage: int):#, event_queue: EventQueue):
        self.health -= damage
        #event_queue.queue.append(Event(TriggerType.DEFEND, self))

    def is_dead(self):
        return self.health <= 0

    def attack(self, damage: int, target: Unit, event_queue: EventQueue):
        target.take_damage(damage)
        event_queue.queue.append(Event(TriggerType.ATTACK, self, target))
        if target.is_dead():
            event_queue.queue.append(Event(TriggerType.KILL, self, target))

class Ability:

    def activate(self, source: Unit, target: Unit, event_queue: EventQueue):

        source.attack(1, target, event_queue)


def event_triggers(unit: Unit, event: Event) -> Optional[Ability]:
    ability_trigger = unit.ability.trigger_type
    match event.trigger_type:
        case TriggerType.ATTACK:
            if event.source == unit and ability_trigger == TriggerType.ATTACK:
                return unit.ability()
            if event.target == unit and ability_trigger == TriggerType.DEFEND:
                return unit.ability()
        case TriggerType.DAMAGE:
            if event.source == unit and ability_trigger == TriggerType.DAMAGE:
                return unit.ability()


class AbilityHandler:
    """
    Handles trigger order for a mix of combat/round start abilities and triggered abilities
    """
    def __init__(self, ally_slots: list[CombatSlot], enemy_slots: list[CombatSlot], planned_abilities: list[Ability], event_queue: EventQueue) -> None:
        self.is_done: bool = False
        self.ally_slots = ally_slots
        self.enemy_slots = enemy_slots
        self.planned_abilities: list[Ability] = planned_abilities
        self.triggered_abilities: list[Ability] = []
        self.current_ability: Optional[Ability] = None
        self.event_queue = event_queue

    def next_ability(self) -> None:
        if not self.planned_abilities:
            self.is_done = True
            return
        self.current_ability = self.planned_abilities.pop(0)

    def queue_triggered_abilities(self):
        for event in self.event_queue.queue:
            for slot in self.ally_slots:
                if not slot.content: continue
                if not slot.content.ability_type: continue
                if not slot.content.ability_type.trigger_type == event.trigger_type: continue
                # Check other types of triggers, e.g., ally attacked?
                ability = slot.content.ability_type(event.source, event.target)
                self.triggered_abilities.append(ability)

        self.event_queue.empty_queue()


    def activate(self) -> None:
        self.queue_triggered_abilities()

        assert self.current_ability
        if not self.current_ability.is_done:
            self.current_ability.activate(self.ally_slots, self.enemy_slots)
            return

        if not is_all_done(self.triggered_abilities):
            run_remaining_abilities(self.triggered_abilities, self.ally_slots, self.enemy_slots)
            return

        self.next_ability()
