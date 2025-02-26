from typing import Protocol, Optional, Final, TYPE_CHECKING
from collections.abc import Sequence
import pathlib

import pygame
import pydantic
import yaml

from settings import Color, BLUE_COLOR, GREEN_COLOR, BLACK_COLOR, GAME_FPS
from pygame_engine import PygameInputHandler, delay_next_frame, SCREEN, CLOCK, DEFAULT_FONT
from core.interfaces import HoverDetector, InputHandler, Node, Rarity
from asset_manager import AssetManager, AssetConfig
from button import draw_outline
from health import Health

if TYPE_CHECKING:
    from component import Component
    from entities.slot import Slot


ROBOT_CONFIG_PATH = pathlib.Path("./robot_configs.yaml")



class RobotConfig(pydantic.BaseModel):
    asset: AssetConfig
    rarity: Rarity
    health: int
    nodes: list[tuple[int, int]]


class RobotFactory:
    def __init__(self, asset_manager: AssetManager, configs: Sequence[RobotConfig]) -> None:
        self.asset_manager = asset_manager
        self.configs = list(configs)

    def build(self, config: RobotConfig, position: pygame.Vector2) -> "Robot":

        cells = (
            Cell(
                position,
                Node(*node),
                CellHoverDetector(),
                SimpleCellRenderer()
                ) for node in config.nodes
            )
        chassi = Chassi(ChassiRenderer(), position, list(cells), [])

        image = self.asset_manager.load(config.asset)
        renderer = AssetRobotRenderer(image, config.asset.offset)
        hover_detector = RobotHoverDetector(position, config.asset.offset, image.get_size())
        health = Health.create(self.asset_manager, config.health)
        return Robot(renderer, position, health, chassi, hover_detector)

    def build_in(self, slot: "Slot", config: RobotConfig) -> "Robot":
        robot = self.build(config, pygame.Vector2(slot.position))
        slot.attach_robot(robot)
        #robot.deploy_in(slot)
        return robot

    @classmethod
    def from_yaml_file(cls, asset_manager: AssetManager, config_path: pathlib.Path = ROBOT_CONFIG_PATH) -> "RobotFactory":
        with open(config_path, 'r') as file:
            yaml_config: dict = yaml.safe_load(file)

        robot_configs = [RobotConfig(**robot_config) for robot_config in yaml_config.values()]

        return cls(asset_manager, robot_configs)


class Robot:
    def __init__(self, renderer: "RobotRenderer", position: pygame.Vector2, health: Health, chassi: "Chassi", hover_detector: "RobotHoverDetector") -> None:
        self._hover_detector: RobotHoverDetector = hover_detector
        self._renderer = renderer

        self._position: pygame.Vector2 = position
        self.health: Health = health
        self.chassi: Chassi = chassi
        
    @property
    def position(self) -> pygame.Vector2:
        return self._position
    
    @position.setter # To always update in-place
    def position(self, new_position: pygame.Vector2) -> None:
        self._position.update(new_position)
        # Alternative is update other objects here instead of relying on mutability
        
    def draw(self, cursor_position: tuple[int, int]) -> None:
        if self.is_hovered(cursor_position):
            self._renderer.draw_highlighted(self)
        else:
            self._renderer.draw(self)

        self.chassi.draw(cursor_position)

    def draw_highlighted(self) -> None:
        self._renderer.draw_highlighted(self)
        self.chassi.draw(pygame.mouse.get_pos())
        #self.health.draw(self)

    def is_hovered(self, cursor_position: tuple) -> bool:
        return self._hover_detector.detect(cursor_position) # self._hover_detector.is_hovered


class RobotHoverDetector:
    #hit_box_size = pygame.Vector2(100,150)
    #position_offset = pygame.Vector2(-35,-175)

    def __init__(self, reference_position: pygame.Vector2, offset: tuple[int, int], hitbox_size: tuple[int, int]) -> None: # Why not just pass a Robot?
        self.__reference_position: pygame.Vector2 = reference_position
        self._offset = offset
        self._hitbox_size = hitbox_size

    @property
    def hit_box(self) -> pygame.Rect:
        return pygame.Rect(self.__reference_position + self._offset, self._hitbox_size)

    def detect(self, cursor_position) -> bool:
        return self.hit_box.collidepoint(cursor_position)


class RobotRenderer(Protocol):
    def draw(self, robot: Robot) -> None: ...
    def draw_highlighted(self, robot: Robot) -> None: ...


class BoxRobotRenderer:
    def draw(self, robot: Robot) -> None:
        pygame.draw.rect(SCREEN, (0, 0, 0), robot._hover_detector.hit_box)

    def draw_highlighted(self, robot: Robot) -> None:
        pygame.draw.rect(SCREEN, (100, 60, 10), robot._hover_detector.hit_box)


class AssetRobotRenderer:
    def __init__(self, sprite: pygame.Surface, offset: tuple[int,int]) -> None:
        self.sprite = sprite
        self.offset = pygame.Vector2(offset)

    def draw(self, robot: Robot) -> None:
        position = robot.position + self.offset
        SCREEN.blit(self.sprite, position)
        #pygame.draw.circle(SCREEN, color = GREEN_COLOR, center = robot.position, radius = 3)

    def draw_highlighted(self, robot: Robot) -> None:
        position = robot.position + self.offset
        sprite_outlined = draw_outline(self.sprite)
        SCREEN.blit(sprite_outlined, position)



class Cell:
    pixel_size: int = 30

    def __init__(self, reference_position: pygame.Vector2, node: Node, hover_detector: "CellHoverDetector", renderer: "CellRenderer", component: Optional["Component"] = None) -> None:
        self.__reference_position = reference_position
        self._hover_detector: CellHoverDetector = hover_detector
        self._renderer: CellRenderer = renderer

        self.node = node
        self.component: Optional[Component] = component

    def __repr__(self) -> str:
        return f"Cell({self.node.x:.0f},{self.node.y:.0f})"

    @property
    def position(self) -> pygame.Vector2:
        return self.__reference_position + Chassi.relative_cell_origin_position + Cell.pixel_size * self.node
    
    @property
    def center_position(self) -> pygame.Vector2:
        return self.position + pygame.Vector2(0.5, 0.5) * Cell.pixel_size

    def set_content(self, component: "Component") -> None:
        self.component = component

    def clear_content(self) -> None:
        self.component = None

    @property
    def is_vacant(self) -> bool:
        return not bool(self.component)

    def draw(self) -> None: self._renderer.draw(self)
        #if self._hover_detector.detect(user_event.cursor_position, self):
        #    self._renderer.draw_highlighted(self)
        #else:
        #    self._renderer.draw(self)
    
    def draw_highlighted(self) -> None: self._renderer.draw_highlighted(self)

    def is_hovered(self, cursor_position: tuple) -> bool:
        return self._hover_detector.detect(cursor_position, self)


class CellRenderer(Protocol):
    def draw(self, cell: "Cell") -> None:
        ...
    def draw_highlighted(self, cell: "Cell") -> None:
        ...


class SimpleCellRenderer:
    def draw(self, cell: "Cell") -> None:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        pygame.draw.rect(SCREEN, rect=box, color=BLACK_COLOR, width=2)
        #pygame.draw.circle(SCREEN, color = GREEN_COLOR, center = cell.position, radius = 3)

    def draw_highlighted(self, cell: "Cell") -> None:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        pygame.draw.rect(SCREEN, rect=box, color=GREEN_COLOR)


class CellHoverDetector:
    #def __init__(self) -> None:
        #self.is_hovered: bool = False

    def detect(self, cursor_position: tuple, cell: "Cell") -> bool:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        return box.collidepoint(cursor_position)





class Chassi:
    relative_cell_origin_position = pygame.Vector2(-Cell.pixel_size, -5*Cell.pixel_size)

    def __init__(self, renderer: "ChassiRenderer", reference_position: pygame.Vector2, cells: list["Cell"], components: list["Component"]) -> None:
        self._renderer = renderer
        #self.__reference_position = reference_position #Not really necessary
        self.cells = cells
        self.components = components

    def add_cell(self, cell: "Cell") -> None:
        assert not self.is_attached(cell)
        assert self.is_adjacent(cell)
        self.cells.append(cell)

    def is_attached(self, cell: "Cell") -> bool:
        return cell in self.cells

    def is_adjacent(self, cell: "Cell") -> bool:
        for frame_cell in self.cells:
            if (frame_cell.node - cell.node).length() == 1:
                return True
        return False

    def get_cell(self, node: Node) -> Optional["Cell"]:
        for cell in self.cells:
            if cell.node == node:
                return cell
        return None

    def get_hovered_cell(self, cursor_position: tuple) -> Optional["Cell"]:
        hover_cell: Optional[Cell] = None
        for cell in self.cells:
            if cell.is_hovered(cursor_position):
                hover_cell = cell
        return hover_cell

    # CellCluster class from above methods?
    
    def add_component_in_any_cell(self, component: "Component") -> None:
        for cell in self.cells:
            try:
                self.add_component(cell, component)
                return
            except NoSpaceException:
                continue
        raise NoSpaceException(f"No vacant cell in {self}")


    def add_component(self, target_cell: "Cell", component: "Component") -> None:
        assert self.is_attached(target_cell)

        candidate_cells: list[Cell] = []
        for component_node in component.nodes:
            frame_node = target_cell.node + component_node
            frame_cell = self.get_cell(frame_node)
            if not frame_cell: raise NoSpaceException(f"{component_node} does not exist in {self.cells}")
            if not frame_cell.is_vacant: raise NoSpaceException(f"{frame_cell} is not vacant")
            candidate_cells.append(frame_cell)

        self.components.append(component)
        component.attach(target_cell.node, candidate_cells)
        for candidate_cell in candidate_cells:
            candidate_cell.set_content(component)

    def remove_component(self, component: "Component") -> None:
        for cell in self.cells:
            if cell.component == component:
                cell.clear_content()
        self.components.remove(component)
        component.deattach()

    def draw(self, cursor_position: tuple[int, int]) -> None:
        self._renderer.draw(cursor_position, self)
        #pygame.draw.circle(SCREEN, color = BLACK_COLOR, center = self.__reference_position+self.relative_cell_origin_position, radius = 3)

    def get_hovered_component(self, cursor_position: tuple) -> Optional["Component"]:
        hovered_cell = self.get_hovered_cell(cursor_position)
        for component in self.components:
            if hovered_cell in component.attachment_cells:
                return component
        return None



class NoSpaceException(Exception):
    """Raised when attempting to insert a component into a cell where it cannot fit"""
    pass


class ChassiRenderer:

    @staticmethod
    def draw(cursor_position: tuple[int, int], chassi: "Chassi") -> None:
        for cell in chassi.cells:
            if cell.is_hovered(cursor_position):
                cell.draw_highlighted()
            else:
                cell.draw()

        for component in chassi.components:
            component.draw_in_place(cursor_position)




## Important distinction between "game objects" and "scenes"
## The Scene interacts and mutates the game objects
## Scenes need to be "driven" with update, but game objects dont



### Test Scenario ###

if __name__ == "__main__":
    asset_manager = AssetManager()
    
    #slots = [
    #    Slot.create(asset_manager, (100,250)),
    #    Slot.create(asset_manager, (100,500)),
    #    Slot.create(asset_manager, (300,250)),
    #    Slot.create(asset_manager, (300,500))
    #]

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
            (0,2)
        ],
        asset = AssetConfig(
            path = pathlib.Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (0,-15)
        )
    )


    robot_factory = RobotFactory(asset_manager, [config1, config2])
    robot_factory2 = RobotFactory.from_yaml_file(asset_manager)

    robots = [
        robot_factory2.build(robot_factory2.configs[1], pygame.Vector2(500,500)),
        robot_factory2.build(robot_factory2.configs[2], pygame.Vector2(650,200)),
        robot_factory2.build(robot_factory2.configs[3], pygame.Vector2(150,200)),
        robot_factory2.build(robot_factory2.configs[4], pygame.Vector2(150,600))
    ]


    position1 = pygame.Vector2(200,400)
    robot1 = robot_factory.build(config1, position1)

    position2 = pygame.Vector2(400,300)
    robot2 = Robot(
        BoxRobotRenderer(),
        position2,
        Health.create(asset_manager, 1),
        Chassi(ChassiRenderer(), position2, [Cell(position2, Node(*node), CellHoverDetector(), SimpleCellRenderer()) for node in config2.nodes], []),
        RobotHoverDetector(position2, (-35,-175), (100,150))
    )
    
    robot_factory.build(config2, position2)


    input_handler = PygameInputHandler()

    while True:
        
        input_handler.handle_input()

        #state_machine.update()

        SCREEN.fill("darkgray")
        for robot in robots+[robot2]: 
            robot.draw(input_handler.cursor_position)

            if robot.is_hovered(input_handler.cursor_position):
                robot.draw_highlighted()
        
        delay_next_frame()
