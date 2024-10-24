from components.character import Tripiketops
from states.combat_state import empty_ability_queue, AbilityHandler
from components.character_slot import CombatSlot
from core.logger import logging
logging.getLogger().setLevel(logging.DEBUG)

char = Tripiketops()

slot = CombatSlot((100,100), 0, (0,0,0))

slot.content = char

char.is_dead()
char.health

char.ability_queue

handler = AbilityHandler.turn_abilities(char, [slot], [])

handler.planned_abilities
handler.triggered_abilities
handler.current_ability

handler.current_ability.is_done

handler.is_done
#handler.triggered_abilities.extend( empty_ability_queue([slot], []) )

handler.activate()

char.damage_health(1)

handler.activate()

char.damage_health(1)

handler.activate()