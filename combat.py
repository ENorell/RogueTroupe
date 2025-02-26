from typing import Optional, Iterable, Generator

import pygame

from core.interfaces import InputHandler
from core.state_machine import State
from pygame_engine import PygameInputHandler, SCREEN 
from robot import Robot
from component import Component
from entities.slot import Slot
from enemy import Enemy
from button import Button
from asset_manager import AssetManager
from settings import GAME_FPS, RED_COLOR


ACTIVATION_TIME_S = 0.5


class CombatState(State):

    def __init__(self, asset_manager: AssetManager, input_handler: InputHandler, robots: Iterable[Robot], slots: Iterable[Slot], enemy: Enemy) -> None:
        super().__init__()
        self._input_handler = input_handler
        self.enemy: Enemy = enemy
        self.robots = list(robots)
        self.slots = list(slots)

        self.acting_robot: Optional[Robot] = None
        self.acting_component: Optional[Component] = None
        self.start_combat_button = Button.create_start_combat_button(asset_manager, (450, 400))

        self.actions_to_do: Generator = self.await_start_combat()
        self.effects_to_draw: Generator = self.await_start_combat()

    def start_state(self) -> None:
        self.actions_to_do = self.await_start_combat()
        # Create enemy?

    def await_start_combat(self) -> Generator:
        while not self.start_combat_button.is_clicked(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed):
            yield
        self.actions_to_do = self.activate_components()

    def activate_components(self) -> Generator:
        for robot in self.robots:
            self.acting_robot = robot
            for component in robot.chassi.components:
                self.acting_component = component
                if damage := component.effect.damage:
                    self.enemy.damage(damage)
                    self.effects_to_draw = draw_strike(self.enemy.position)
                    delay: Generator = await_delay(ACTIVATION_TIME_S)
                    yield from delay
        self.acting_robot = None
        self.acting_component = None
        
        self.actions_to_do = self.await_end_turn()

    def await_end_turn(self) -> Generator:
        while not self.start_combat_button.is_clicked(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed):
            yield
        self.actions_to_do = self.activate_enemy()

    def activate_enemy(self) -> Generator:
        if attack := self.enemy.action.attack:
            # do damage to robots
            self.effects_to_draw = draw_strike(self.enemy.position, left_to_right=False)
            delay: Generator = await_delay(ACTIVATION_TIME_S)
            yield from delay
        self.enemy.cycle_action()
        self.actions_to_do = self.await_start_combat()


    def update(self) -> None:
        try:
            next(self.actions_to_do)
        except StopIteration:
            pass # Next State?


    def draw(self) -> None:
        SCREEN.fill((30,20,60))

        for slot in self.slots:
            if slot.is_hovered(self._input_handler.cursor_position):
                slot.draw_highlighted()
            else:
                slot.draw()
    
        for robot in self.robots:
            if robot is self.acting_robot:
                robot.draw_highlighted()
            else:
                robot.draw(self._input_handler.cursor_position)
            
        if self.acting_component:
            self.acting_component.draw_highlighted()

        if self.enemy.is_hovered():
            self.enemy.draw_highlighted()
        else:
            self.enemy.draw()

        self.start_combat_button.draw(self._input_handler.cursor_position, self._input_handler.is_cursor_pressed)

        try:
            next(self.effects_to_draw)
        except StopIteration:
            pass # Next State?


def await_delay(seconds: float) -> Generator:
    frames_to_wait = GAME_FPS * seconds
    frames_waited = 0
    while frames_waited < frames_to_wait:
        frames_waited += 1
        yield


def draw_strike(position: tuple, left_to_right: bool = True) -> Generator:
    velocity = pygame.Vector2(50,0) if left_to_right else pygame.Vector2(-50,0)
    passed_frames, activation_frames = 0, GAME_FPS * ACTIVATION_TIME_S
    top_wing = pygame.Vector2(-100,25) if left_to_right else pygame.Vector2(100,25)
    bot_wing = pygame.Vector2(-100,-25) if left_to_right else pygame.Vector2(100,-25)
    while passed_frames < activation_frames:
        tip = position+passed_frames*velocity
        top = tip+top_wing
        bot = tip+bot_wing
        pygame.draw.polygon(SCREEN, RED_COLOR, (tip, bot, top))
        yield
        passed_frames+=1




if __name__ == "__main__":
    from pygame_engine import delay_next_frame
    from robot import RobotFactory
    from component import ComponentFactory
    from enemy import EnemySpawner

    asset_manager = AssetManager()
    
    enemy_spawner = EnemySpawner.from_config_file(asset_manager)

    enemy = enemy_spawner.spawn(enemy_spawner.configs[0], (500,200))

    slot = Slot.create(asset_manager, position=(200,300))

    robot_factory = RobotFactory.from_yaml_file(asset_manager)

    robot = robot_factory.build_in(slot, robot_factory.configs[2])

    component_factory = ComponentFactory.from_yaml_file(asset_manager)

    component1 = component_factory.build(component_factory.configs[0])
    component2 = component_factory.build(component_factory.configs[0])
    component3 = component_factory.build(component_factory.configs[0])
    component4 = component_factory.build(component_factory.configs[0])
    component5 = component_factory.build(component_factory.configs[0])

    robot.chassi.add_component_in_any_cell(component1)
    robot.chassi.add_component_in_any_cell(component2)
    robot.chassi.add_component_in_any_cell(component3)
    robot.chassi.add_component_in_any_cell(component4)
    robot.chassi.add_component_in_any_cell(component5)

    input_handler = PygameInputHandler()

    state = CombatState(asset_manager, input_handler, [robot], [slot], enemy)

    while True:
        
        input_handler.handle_input()

        state.update()

        #SCREEN.fill("darkblue")
        state.draw()
        
        delay_next_frame()
