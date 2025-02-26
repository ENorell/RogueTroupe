from enum import Enum, auto
from typing import Protocol, Any, Optional
import pygame

from components.character_slot import Slot, SlotSystem, SLOT_SIZE_WIDTH
from core.interfaces import UserInput
from core.state_machine import State, StateChoice
from components.interactable import HoverDetector, PygameHoverDetector

from old.chassi import Chassi, ComponentDragDropper, ChassiRenderer, DragdropperState

import pydantic




class RobotType(Enum):
    GAMMA = "gamma"


class RobotConfig(pydantic.BaseModel):
    name: RobotType
    health: int
    points: list[tuple]


class RobotHoverDetector:
    position_offset = pygame.Vector2(-15,-100)
    hit_box_size = pygame.Vector2(100,150)

    def __init__(self, local_origin: pygame.Vector2) -> None: # Why not just pass a Robot?
        self.local_origin: pygame.Vector2 = local_origin
        self.is_hovered: bool = False

    @property
    def hit_box(self) -> pygame.Rect:
        return pygame.Rect(self.local_origin + self.position_offset, self.hit_box_size)

    def detect(self, mouse_position) -> None:
        self.is_hovered = self.hit_box.collidepoint(mouse_position)

    def draw(self, frame: pygame.Surface) -> None:
        color: tuple[int, int, int] = (100,60,10) if self.is_hovered else (0,0,0)
        pygame.draw.rect(frame, color, self.hit_box, width = 2) # Temp


class Robot:
    def __init__(self, position: pygame.Vector2, health: int, chassi: Chassi, hover_detector: RobotHoverDetector) -> None:
        self.position: pygame.Vector2 = position
        self.health: int = health
        self.chassi: Chassi = chassi
        self.hover_detector: RobotHoverDetector = hover_detector

    def draw(self, frame: pygame.Surface) -> None:
        self.chassi.draw(frame)

        self.hover_detector.draw(frame)

    def is_hovered(self, mouse_position: pygame.Vector2) -> bool:
        self.hover_detector.detect(mouse_position)
        self.chassi.get_hovered_cell(mouse_position) # Just to "tag" cell as hovered...
        return self.hover_detector.is_hovered

    def deploy_in(self, slot: Slot) -> None:
        self.position = slot.position
        
        


class RobotFactory:
    def __init__(self, robot_type_to_config: dict[str, dict[str, Any]]) -> None:
        self.robot_type_to_config: dict[str, dict[str, Any]] = robot_type_to_config

    #@classmethod
    #def from_config_file(cls, file_path: str) -> "RobotFactory":
    #    ...

    def build(self, robot_type: RobotType, slot: Slot) -> Robot:
        robot_config = self.robot_type_to_config[robot_type.value]
        
        position = pygame.Vector2(slot.position) #+SLOT_SIZE_WIDTH//2
        health: int = robot_config["health"]

        chassi: Chassi = Chassi.from_points(position, robot_config["points"])

        hover_detector = RobotHoverDetector(position)

        return Robot(position, health, chassi, hover_detector)



class RobotDragDropper:
    """
    Governs the nasty logic needed to drag-drop characters between slots
    """
    def __init__(self, robots: list[Robot]) -> None:
        self.robots: list[Robot] = robots
        self.detached_robot: Optional[Robot] = None
        
        self.state = DragdropperState.HOVERING
        self._mouse_position = pygame.Vector2(0,0)


    def loop(self, user_input: UserInput) -> None:
        self._mouse_position = user_input.mouse_position # Stored to be able to draw later...

        hovered_robot: Optional[Robot] = self.get_hovered_robot(user_input.mouse_position)
        #for robot in self.robots:
        #    if not robot.is_hovered(user_input.mouse_position):
        #        continue
        #    hovered_robot = robot
        #    break

        match self.state:
            case DragdropperState.HOVERING:
                if not (hovered_robot and user_input.is_mouse1_down):
                    return
                self.detached_robot = hovered_robot
                self.state = DragdropperState.DRAGGING

            case DragdropperState.DRAGGING:
                assert self.detached_robot
                self.detached_robot.position.update(user_input.mouse_position) #+= pygame.Vector2(user_input.mouse_position) - self.detached_robot.position # hack to change in place...

                if not user_input.is_mouse1_up:
                    return  # Keep dragging this frame

                if not hovered_robot or hovered_robot == self.detached_robot:
                    self.detached_robot = None
                    self.state = DragdropperState.HOVERING
                    return
                
                hovered_robot.position, self.detached_robot.position = self.detached_robot.position, hovered_robot.position

                self.detached_robot = None
                self.state = DragdropperState.HOVERING
            case _:
                raise Exception(f"Unrecognized state {self.state}")
            
    def get_hovered_robot(self, mouse_position: tuple) -> Optional[Robot]:
        for robot in self.robots:
            if robot.is_hovered(mouse_position):
                return robot
        return None


    def draw(self, frame: pygame.Surface) -> None:
        for robot in self.robots:
            robot.draw(frame)
        #match self.state:
        #    case DragdropperState.HOVERING:
        #        ...
        #    case DragdropperState.DRAGGING:
        #        ...
        #    case _:
        #        raise Exception(f"Unrecognized state {self.state}")


class PhaseChoice(Enum):
    PLAYER_PREPARATION = auto()
    PLAYER_ACT = auto()
    ENEMY_ACT = auto()


class Phase(Protocol):
    is_done: bool
    next_phase_choice: PhaseChoice
    def start_phase(self) -> None:
        ...
    def loop(self, user_input: UserInput) -> None:
        ...
    def draw(self, frame: pygame.Surface) -> None:
        ...
    #def end_phase(self) -> None:
    #    ...


class DragdroppingState(Enum):
    DRAGGING_COMPONENT = auto()
    DRAGGING_CHARACTER = auto()
    HOVERING = auto()

class PlayerPreparationPhase(Phase):
    next_phase_choice = PhaseChoice.PLAYER_ACT

    def __init__(self, slot_system: SlotSystem, robots: list[Robot], component_drag_dropper: ComponentDragDropper, character_drag_dropper: RobotDragDropper) -> None:
        self.slot_system = slot_system
        
        self.robots = robots

        self.component_drag_dropper = component_drag_dropper
        self.character_drag_dropper = character_drag_dropper

        self.is_done: bool = False
        
    def start_phase(self) -> None:
        self.is_done = False

    def loop(self, user_input: UserInput) -> None:
        self.slot_system.check_combat_hover(user_input)

        for robot in self.robots:
            robot.is_hovered(user_input.mouse_position)
            
        self.character_drag_dropper.loop(user_input)
        #self.component_drag_dropper.loop(user_input)

    def draw(self, frame: pygame.Surface) -> None:
        self.slot_system.draw_in_combat(frame)

        self.character_drag_dropper.draw(frame)
        #self.component_drag_dropper.draw(frame)


class PlayerActivatePhaseRenderer:
    
    def draw(self, frame: pygame.Surface, player_activate_phase: "PlayerActivatePhase") -> None:
        command = player_activate_phase.current_command

        for character in self.slot_system.get_ally_characters():
            if character == command.caster:
                character.draw_highlighted()
            else:
                character.draw()

            command.component.draw_highlighted()


class PlayerActivatePhase(Phase):
    def __init__(self, renderer: PlayerActivatePhaseRenderer) -> None:
        self.slot_system = slot_system
        self.renderer = renderer

        self.current_command = None
        self.command_queue = []

        self.is_done = False
        self.next_phase: Phase

    def start_phase(self) -> None:
        self.is_done = False
        self.queue_new_commands()

    def queue_new_commands(self) -> None:
        self.command_queue = []
        ally_characters = self.slot_system.get_ally_characters()
        for character in ally_characters:
            components = character.get_components()
            for component in components:
                command = component.command()
                self.command_queue.append(command)


    def loop(self, user_input: UserInput) -> None:
        assert self.current_command
        if not self.current_command.is_done:
            self.current_command.loop()
            return
        
        if not self.command_queue:
            self.is_done = True
            # Set next state
            return
        
        self.current_command = self.command_queue.pop()

        


#class CombatStateRenderer:
#    def draw(self, frame: pygame.Surface, combat_state: "CombatState") -> None:
#        ...

class EnemyGenerator:
    def generate(self) -> None:
        ...



class CombatState(State):

    def __init__(self, enemy_generator: EnemyGenerator, phase_for_choice: dict[PhaseChoice, Phase], start_phase_choice: PhaseChoice) -> None:
        super().__init__()
        #self.slot_system = slot_system
        #self.renderer = renderer
        self.enemy_generator: EnemyGenerator = enemy_generator
        self.phase_for_choice: dict[PhaseChoice, Phase] = phase_for_choice
        self.current_phase: Phase = phase_for_choice[start_phase_choice]


    def start_state(self) -> None:
        #self.phase = PhaseChoice.PLAYER_ACT
        self.enemy_generator.generate()


    def loop(self, user_input: UserInput) -> None:
        if not self.current_phase.is_done:
            self.current_phase.loop(user_input)
            return
        
        self.switch_phase(self.current_phase.next_phase_choice)
        

    def switch_phase(self, phase_choice: PhaseChoice) -> None:
        self.current_phase = self.phase_for_choice[phase_choice]
        self.current_phase.start_phase()


    def draw(self, frame: pygame.Surface) -> None:
        frame.fill((30,20,60))

        self.current_phase.draw(frame)


### TEST ROOM ###

if __name__ == "__main__":
    #pygame.init()

    from old.chassi import Cell, Point, Chassi, Component, SimpleComponentRenderer, ChassiRenderer

    slot1 = Slot((100,300))
    slot2 = Slot((300,300))

    slot_system = SlotSystem([slot1, slot2],[],[],[],[],[])

    robot_config = {"gamma": {"health": 1, "points": [(0,0), (1,0), (2,0), (0,1), (1,1)] }}
    robot_factory = RobotFactory(robot_type_to_config=robot_config)

    robot1 = robot_factory.build(RobotType.GAMMA, slot1)
    robot2 = robot_factory.build(RobotType.GAMMA, slot2)

    #cell_frame_cells1 = [
    #    Cell.create(Point(0,0)), Cell.create(Point(1,0)), Cell.create(Point(2,0)),
    #    Cell.create(Point(0,1)), Cell.create(Point(1,1))
    #]
    #chassi1 = Chassi(pygame.Vector2(100,100), cell_frame_cells1, ChassiRenderer(), [])

    component1 = Component([Point(0,0)], SimpleComponentRenderer())
    component2 = Component([Point(0,0), Point(1,0)], SimpleComponentRenderer())

    robot1.chassi.add_component_in_any_cell(component1)
    robot2.chassi.add_component_in_any_cell(component2)

    drag_dropper = ComponentDragDropper([robot1.chassi, robot2.chassi])

    character_drag_dropper = RobotDragDropper([robot1, robot2])

    player_preparation_phase = PlayerPreparationPhase(slot_system, [robot1, robot2], drag_dropper, character_drag_dropper)

    phase_for_choice: dict[PhaseChoice, Phase] = {
        PhaseChoice.PLAYER_PREPARATION: player_preparation_phase
        #PhaseChoice.PLAYER_ACT: PlayerActivatePhase(),
        #PhaseChoice.ENEMY_ACT: 
    }

    enemy_generator = EnemyGenerator()

    combat_state = CombatState(enemy_generator, phase_for_choice, PhaseChoice.PLAYER_PREPARATION)
    combat_state.start_state()


    from core.input_listener import PygameInputListener
    from core.renderer import PygameRenderer
    from core.engine import PygameEngine

    class MockRenderer(PygameRenderer):
        def draw_frame(self) -> None:
            
            combat_state.draw(self.frame)

    engine = PygameEngine(
        combat_state,
        MockRenderer(),
        PygameInputListener()
    )

    engine.run()
