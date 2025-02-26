import asyncio
from pathlib import Path

import pygame

from core.state_machine import StateMachine, StateChoice
from pygame_engine import PygameInputHandler, delay_next_frame
from robot import Robot, RobotConfig, RobotFactory, RobotHoverDetector, BoxRobotRenderer, Chassi, ChassiRenderer, Cell, CellHoverDetector, SimpleCellRenderer
from core.interfaces import Node, Rarity
from component import Component, ComponentFactory, ComponentEffect, ComponentConfig, SimpleComponentRenderer
from entities.slot import Slot
from asset_manager import AssetManager, AssetConfig
from health import Health
from robot_dragdropping import RobotDragDropper, ComponentDragDropper
from combat import CombatState
from enemy import EnemySpawner

async def main() -> None:
    
    asset_manager = AssetManager()
    
    slots = [
        Slot.create(asset_manager, (100,250)),
        Slot.create(asset_manager, (100,500)),
        Slot.create(asset_manager, (300,250)),
        Slot.create(asset_manager, (300,500))
    ]

    mothership_config = RobotConfig(
        rarity = Rarity.RARE,
        health = 1,
        nodes = [
            (0,0), (1,0), (2,0),
            (0,1), (1,1), (2,1),
            (0,2), (1,2), (2,2)
        ],
        asset = AssetConfig(
            path = Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (0,-15)
        )
    )
    #mothership_factory = RobotFactory(asset_manager, [mothership_config])
    #mothership_position = pygame.Vector2(200,400)
    #mothership = mothership_factory.build(mothership_config, mothership_position)
    mothership_position = pygame.Vector2(600,250)
    mothership = Robot(
        BoxRobotRenderer(),
        mothership_position,
        Health.create(asset_manager, 1),
        Chassi(ChassiRenderer(), mothership_position, [Cell(mothership_position, Node(*node), CellHoverDetector(), SimpleCellRenderer()) for node in mothership_config.nodes], []),
        RobotHoverDetector(mothership_position, (-35,-175), (100,150))
    )

    robot_factory = RobotFactory.from_yaml_file(asset_manager)
    robots = [
        robot_factory.build_in(slots[0], robot_factory.configs[1]),
        robot_factory.build_in(slots[1], robot_factory.configs[2]),
        robot_factory.build_in(slots[2], robot_factory.configs[3]),
        robot_factory.build_in(slots[3], robot_factory.configs[4])
    ]

    component_config1 = ComponentConfig(
        rarity = Rarity.COMMON,
        nodes = [(0,0), (0,1)],
        asset = AssetConfig(
            path = Path("./assets/gun3.png"),
            size = (30,60),
            offset = (0,0)
        ),
        effect = ComponentEffect(damage=1)
    )

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

    component_dragdrop_state = ComponentDragDropper(input_handler, asset_manager, robots+[mothership], slots)

    robot_dragdrop_state = RobotDragDropper(input_handler, asset_manager, robots, slots, enemy_spawner)

    combat_state = CombatState(asset_manager, input_handler, robots, slots, robot_dragdrop_state.enemy)


    state_machine = StateMachine(
        {
            StateChoice.ROBOT: robot_dragdrop_state, 
            StateChoice.COMPONENT: component_dragdrop_state, 
            StateChoice.COMBAT: combat_state
        }, 
        StateChoice.COMPONENT
        )


    while True:
        
        input_handler.handle_input()

        state_machine.update()

        state_machine.draw()
        
        delay_next_frame()

        await asyncio.sleep(0)


asyncio.run(main())