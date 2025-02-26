from enum import Enum, auto
from typing import Sequence, Optional
import pathlib

import pygame

from pygame_engine import PygameInputHandler, delay_next_frame, SCREEN, CLOCK, DEFAULT_FONT
from core.state_machine import State, StateMachine, StateChoice
from core.interfaces import HoverDetector, InputHandler, Node, Rarity
from asset_manager import AssetManager, AssetConfig
from button import Button
from robot import Robot, Chassi, Cell, NoSpaceException, RobotConfig, RobotFactory, BoxRobotRenderer, ROBOT_CONFIG_PATH, CellHoverDetector, SimpleCellRenderer, ChassiRenderer, RobotHoverDetector
from component import Component, ComponentFactory, ComponentConfig, SimpleComponentRenderer, COMPONENT_CONFIG_PATH
from entities.slot import Slot
from enemy import Enemy, EnemySpawner

class DragdropperState(Enum):
    HOVERING = auto()
    DRAGGING = auto()


class ComponentDragDropper(State):
    def __init__(self, input_handler: InputHandler, asset_manager: AssetManager, robots: Sequence[Robot], slots: list[Slot]) -> None:
        super().__init__()
        self._input_handler = input_handler
        self.robots = robots
        self.slots = slots
        self.chassis = [robot.chassi for robot in robots]
        self.state: DragdropperState = DragdropperState.HOVERING

        self.next_state_button = Button.create_start_combat_button(asset_manager, (450, 400))
        self.detached_component: Optional[Component] = None
        self.previous_attached_cell: Optional[Cell] = None
        self.previous_attached_chassi: Optional[Chassi] = None

    def update(self) -> None:

        match self.state:
            case DragdropperState.HOVERING:
                self.update_while_hovering()

            case DragdropperState.DRAGGING:
                self.update_while_dragging()

    def update_while_hovering(self) -> None:
        if self.next_state_button.is_clicked(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed):
            self.next_state = StateChoice.ROBOT
            return
        
        hovered_component: Optional[Component] = None
        hovered_chassi: Optional[Chassi] = None

        hovered_component, hovered_chassi = self.get_hovered_component_and_chassi(self._input_handler.cursor_position)

        if not (hovered_component and self._input_handler.is_cursor_pressed):
            return

        assert hovered_chassi and hovered_component.attachment_node is not None
        self.previous_attached_cell = hovered_chassi.get_cell(hovered_component.attachment_node)
        self.previous_attached_chassi = hovered_chassi

        hovered_chassi.remove_component(hovered_component)
        self.detached_component = hovered_component
        self.state = DragdropperState.DRAGGING

    def get_hovered_component_and_chassi(self, cursor_position: tuple) -> tuple[Optional[Component], Optional[Chassi]]:
        for chassi in self.chassis:
            hovered_component = chassi.get_hovered_component(cursor_position)
            if hovered_component:
                return hovered_component, chassi
        return None, None

    def update_while_dragging(self) -> None:
        hovered_cell: Optional[Cell] = None
        hovered_chassi: Optional[Chassi] = None
        for chassi in self.chassis:
            hovered_chassi = chassi
            hovered_cell = chassi.get_hovered_cell(self._input_handler.cursor_position)
            if hovered_cell: break

        if not self._input_handler.is_cursor_released:
            return

        if not hovered_cell:
            assert self.previous_attached_cell and self.previous_attached_chassi and self.detached_component
            self.previous_attached_chassi.add_component(self.previous_attached_cell, self.detached_component)
            self.state = DragdropperState.HOVERING
            return

        assert hovered_chassi and self.detached_component
        self.state = DragdropperState.HOVERING

        try:
            hovered_chassi.add_component(hovered_cell, self.detached_component)
        except NoSpaceException:
            assert self.previous_attached_cell and self.previous_attached_chassi and self.detached_component
            self.previous_attached_chassi.add_component(self.previous_attached_cell, self.detached_component)

    def draw(self) -> None:

        SCREEN.fill((30,20,60))

        self.next_state_button.draw(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed)

        for slot in self.slots: slot.draw()

        for robot in self.robots:
            robot.draw(self._input_handler.cursor_position)

        if not self.state == DragdropperState.DRAGGING:
            return

        assert self.detached_component
        self.detached_component.draw_on_mouse(self._input_handler.cursor_position)

        

class RobotDragDropper(State):
    """
    Governs the nasty logic needed to drag-drop characters between slots
    """
    def __init__(self, input_handler: InputHandler, asset_manager: AssetManager, robots: list[Robot], slots: list[Slot], enemy_spawner: EnemySpawner) -> None:
        super().__init__()
        self._input_handler = input_handler
        self.robots: list[Robot] = robots
        self.slots = slots
        self.enemy_spawner = enemy_spawner
        self.enemy = enemy_spawner.spawn_any((500,200))

        self.next_state_button = Button.create_start_combat_button(asset_manager, (450, 400))
        self.detached_robot: Optional[Robot] = None
        self.detached_slot: Optional[Slot] = None
        self.state = DragdropperState.HOVERING

    def start_state(self) -> None:
        self.enemy_spawner.spawn_any((500,200))

    def get_slot_for(self, robot: Robot) -> Slot:
        for slot in self.slots:
            if slot.attached_robot is robot: 
                return slot
        raise Exception("Could not find in which slot robot belongs to.")

    def update(self) -> None:
        hovered_robot: Optional[Robot] = self.get_hovered_robot(self._input_handler.cursor_position)

        match self.state:
            case DragdropperState.HOVERING:
                if self.next_state_button.is_clicked(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed):
                    self.next_state = StateChoice.COMBAT
                    return

                if not (hovered_robot and self._input_handler.is_cursor_pressed):
                    return
                
                self.detached_robot = hovered_robot
                self.detached_slot = self.get_slot_for(hovered_robot)
                self.detached_slot.clear()
                self.state = DragdropperState.DRAGGING

            case DragdropperState.DRAGGING:
                assert self.detached_robot
                assert self.detached_slot
                self.detached_robot.position = pygame.Vector2(self._input_handler.cursor_position)
                hovered_slot = self.get_hovered_slot()

                if not self._input_handler.is_cursor_released:
                    return  # Keep dragging this frame

                if not hovered_slot:
                    self.detached_slot.attach_robot(self.detached_robot)
                    self.detached_robot = None
                    self.detached_slot = None
                    self.state = DragdropperState.HOVERING
                    return
                
                attached_robot = hovered_slot.attached_robot
                if attached_robot:
                    self.detached_slot.attach_robot(attached_robot)
                

                hovered_slot.attach_robot(self.detached_robot)

                self.detached_robot = None
                self.detached_slot = None

                self.state = DragdropperState.HOVERING
            case _:
                raise Exception(f"Unrecognized state {self.state}")
    
    def update_while_hovering(self) -> None:
        ...
            
    def get_hovered_robot(self, cursor_position: tuple) -> Optional[Robot]:
        for robot in self.robots:
            if robot is self.detached_robot: continue
            if robot.is_hovered(cursor_position):
                return robot
        return None
    
    def get_hovered_slot(self) -> Optional[Slot]:
        for slot in self.slots:
            if slot.is_hovered(self._input_handler.cursor_position):
                return slot
        return None


    def draw(self) -> None:
        SCREEN.fill((30,20,60))

        for slot in self.slots:
            if slot.is_hovered(self._input_handler.cursor_position):
                slot.draw_highlighted()
            else:
                slot.draw()
    
        for robot in self.robots:
            if robot is self.detached_robot: continue
            robot.draw(self._input_handler.cursor_position)

        if self.detached_robot: self.detached_robot.draw(self._input_handler.cursor_position)

        if self.enemy.is_hovered():
            self.enemy.draw_highlighted()
        else:
            self.enemy.draw()

        self.next_state_button.draw(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed)





if __name__ == "__main__":
    from component import ComponentEffect
    from health import Health
    asset_manager = AssetManager()
    
    slots = [
        Slot.create(asset_manager, (100,250)),
        Slot.create(asset_manager, (100,500)),
        Slot.create(asset_manager, (300,250)),
        Slot.create(asset_manager, (300,500))
    ]

    config1 = RobotConfig(
        rarity = Rarity.COMMON,
        health = 1,
        nodes = [
            (0,0), 
            (0,1),
            (0,2), (1,2)
        ],
        asset = AssetConfig(
            path = pathlib.Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (-107,-195)
        )
    )

    config2 = RobotConfig(
        rarity = Rarity.RARE,
        health = 1,
        nodes = [
            (0,0), (1,0), (2,0),
            (0,1), (1,1), (2,1),
            (0,2), (1,2), (2,2)
        ],
        asset = AssetConfig(
            path = pathlib.Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (0,-15)
        )
    )

    

    robot_factory = RobotFactory(asset_manager, [config1, config2])

    robot_factory2 = RobotFactory.from_yaml_file(asset_manager)
    robot0 = robot_factory2.build(robot_factory2.configs[1], pygame.Vector2(500,500))
    robot4 = robot_factory2.build(robot_factory2.configs[2], pygame.Vector2(650,200))
    robot5 = robot_factory2.build(robot_factory2.configs[3], pygame.Vector2(150,200))
    robot6 = robot_factory2.build(robot_factory2.configs[4], pygame.Vector2(150,600))

    robots = [
        robot_factory2.build_in(slots[0], robot_factory2.configs[1]),
        robot_factory2.build_in(slots[1], robot_factory2.configs[2]),
        robot_factory2.build_in(slots[2], robot_factory2.configs[3]),
        robot_factory2.build_in(slots[3], robot_factory2.configs[4])
    ]


    position1 = pygame.Vector2(200,400)
    robot1 = robot_factory.build(config1, position1)

    position2 = pygame.Vector2(600,250)
    mothership = Robot(
        BoxRobotRenderer(),
        position2,
        Health.create(asset_manager, 1),
        Chassi(ChassiRenderer(), position2, [Cell(position2, Node(*node), CellHoverDetector(), SimpleCellRenderer()) for node in config2.nodes], []),
        RobotHoverDetector(position2, (-35,-175), (100,150))
    )
    
    robot_factory.build(config2, position2)

    component_config1 = ComponentConfig(
        rarity = Rarity.COMMON,
        nodes = [(0,0), (0,1)],
        asset = AssetConfig(
            path = pathlib.Path("./assets/gun3.png"),
            size = (30,60),
            offset = (0,0)
        ),
        effect = ComponentEffect(damage=1)
    )

    component_factory = ComponentFactory(asset_manager, (component_config1,))
    component_factory = ComponentFactory.from_yaml_file(asset_manager)

    component0 = component_factory.build(component_config1)

    component1 = component_factory.build(component_factory.configs[0])
    component2 = Component([Node(0,0), Node(1,0)],            SimpleComponentRenderer(), ComponentEffect())
    component3 = Component([Node(0,0), Node(1,0), Node(0,1)], SimpleComponentRenderer(), ComponentEffect())

    robots[1].chassi.add_component(robots[1].chassi.cells[0], component1)
    robots[1].chassi.add_component(robots[1].chassi.cells[2], component2)
    robots[0].chassi.add_component(robots[0].chassi.cells[0], component3)
    robots[2].chassi.add_component(robots[2].chassi.cells[0], component0)

    enemy_spawner = EnemySpawner.from_config_file(asset_manager)


    input_handler = PygameInputHandler()

    drag_dropper = ComponentDragDropper(input_handler, asset_manager, robots+[mothership], slots)

    robot_drag_dropper = RobotDragDropper(input_handler, asset_manager, robots, slots, enemy_spawner)


    state_machine = StateMachine({StateChoice.ROBOT: robot_drag_dropper, StateChoice.COMPONENT: drag_dropper}, StateChoice.COMPONENT)


    while True:
        
        input_handler.handle_input()

        state_machine.update()

        state_machine.draw()
        
        delay_next_frame()
