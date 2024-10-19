from renderer import PygameRenderer
from character import draw_character
from character_slot import draw_slot
from game import Game
from shop_state import ShopRenderer, ShopState
from state_machine import State
from combat_state import CombatState
from preparation_state import PreparationRenderer, PreparationState
from interactable import draw_button


class GameRenderer(PygameRenderer):
    def __init__(self) -> None:
        super().__init__()
        self.shop_renderer = ShopRenderer()
        self.prepatation_renderer = PreparationRenderer()

    def draw_frame(self, game: Game):
        match game.state:
            case CombatState():
                draw_button(self.frame, game.state.continue_button )
                        
                for slot in game.state.ally_slots + game.state.enemy_slots:
                    draw_slot(self.frame, slot)
                    
                    if not slot.content: continue

                    is_acting = game.state.current_round.current_turn.character == slot.content and not game.state.current_round.current_turn.character.is_dead()

                    scale_ratio = 1.5 if slot.is_hovered or is_acting else 1

                    draw_character(self.frame, slot.center_coordinate, slot.content, scale_ratio = scale_ratio)

            case PreparationState():
                self.prepatation_renderer.draw_frame(game.state)

            case ShopState():
                self.shop_renderer.draw_frame(game.state)

            case _:
                raise Exception("Unknown state to draw")