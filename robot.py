from typing import Protocol, Final, Optional
from collections.abc import Sequence
from enum import Enum, auto
import pathlib

import pygame
import pydantic
import yaml

from settings import Color, BLUE_COLOR, GREEN_COLOR, BLACK_COLOR
from core.input_listener import UserInput


ROBOT_CONFIG_PATH = pathlib.Path("./robot_configs.yaml")
COMPONENT_CONFIG_PATH = pathlib.Path("./component_configs.yaml")


class Node(pygame.Vector2):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)

    #def __bool__(self) -> bool: # Override 0 length vectors equal to False
    #    return True


class Rarity(Enum):
    RARE = "Rare"
    COMMON = "Common"



#class AssetConfig(pydantic.BaseModel):
#    file_path: pydantic.FilePath

# Singleton? Does not have to be global, but should only be one preferably, not mandatory though
class AssetManager:
    #robot_pixel_size: int = 210

    def __init__(self) -> None:
        self.path_to_image: dict[pathlib.Path, pygame.Surface] = {}
    
    def load(self, path: pathlib.Path, size: tuple[int, int]) -> pygame.Surface: #, size: tuple[int, int]
        if not path in self.path_to_image:
            image: pygame.Surface = pygame.image.load(path)
            #image.convert_alpha() #NOT BEFORE PYGAME INIT
            image = pygame.transform.scale(image, size)
            self.path_to_image[path] = image
        return self.path_to_image[path]
        

class AssetConfig(pydantic.BaseModel):
    path: pydantic.FilePath
    size: tuple[int, int]
    offset: tuple[int, int]


class RobotConfig(pydantic.BaseModel):
    rarity: Rarity
    health: int
    nodes: list[tuple[int, int]]
    asset: AssetConfig



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

        image = self.asset_manager.load(config.asset.path, config.asset.size)
        renderer = AssetRobotRenderer(image, config.asset.offset)

        return Robot(renderer, position, config.health, chassi, RobotHoverDetector(position))

    @classmethod
    def from_yaml_file(cls, config_path: pathlib.Path, asset_manager: AssetManager) -> "RobotFactory":
        with open(config_path, 'r') as file:
            yaml_config: dict = yaml.safe_load(file)

        robot_configs = [RobotConfig(**robot_config) for robot_config in yaml_config.values()]

        return cls(asset_manager, robot_configs)





class ComponentConfig(pydantic.BaseModel):
    rarity: Rarity
    nodes: list[tuple[int, int]]
    asset: AssetConfig


class ComponentFactory:
    def __init__(self, asset_manager: AssetManager, configs: Sequence[ComponentConfig]) -> None:
        self.asset_manager = asset_manager
        self.configs = list(configs)

    def build(self, config: ComponentConfig) -> "Component":
        image = self.asset_manager.load(config.asset.path, config.asset.size)

        nodes = [Node(*node) for node in config.nodes]

        renderer = AssetComponentRenderer(image, config.asset.offset)

        return Component(nodes, renderer)

    @classmethod
    def from_yaml_file(cls, config_path: pathlib.Path, asset_manager: AssetManager) -> "ComponentFactory":
        with open(config_path, 'r') as file:
            yaml_config: dict = yaml.safe_load(file)

        configs = [ComponentConfig(**config) for config in yaml_config.values()]

        return cls(asset_manager, configs)


class Slot:
    def __init__(self, position: pygame.Vector2) -> None:
        self.position = position
    

class Robot:
    def __init__(self, renderer: "RobotRenderer", position: pygame.Vector2, health: int, chassi: "Chassi", hover_detector: "RobotHoverDetector") -> None:
        self._hover_detector: RobotHoverDetector = hover_detector
        self._renderer = renderer

        self.position: pygame.Vector2 = position
        self.health: int = health
        self.chassi: Chassi = chassi
        
    def draw(self, frame: pygame.Surface) -> None:
        self._renderer.draw(frame, self)

        self.chassi.draw(frame)

        #self._hover_detector.draw(frame)

    def is_hovered(self, mouse_position: tuple) -> bool:
        self._hover_detector.detect(mouse_position)
        self.chassi.get_hovered_cell(mouse_position) # Just to "tag" cell as hovered...
        return self._hover_detector.is_hovered

    def deploy_in(self, slot: Slot) -> None:
        self.position = slot.position


class RobotHoverDetector:
    hit_box_size = pygame.Vector2(100,150)
    position_offset = pygame.Vector2(-35,-175)

    def __init__(self, reference_position: pygame.Vector2) -> None: # Why not just pass a Robot?
        self.__reference_position: pygame.Vector2 = reference_position
        self.is_hovered: bool = False

    @property
    def hit_box(self) -> pygame.Rect:
        return pygame.Rect(self.__reference_position + self.position_offset, self.hit_box_size)

    def detect(self, mouse_position) -> None:
        self.is_hovered = self.hit_box.collidepoint(mouse_position)

    #def draw(self, frame: pygame.Surface) -> None:
        #color: Color = (100, 60, 10) if self.is_hovered else (0, 0, 0)
        #pygame.draw.rect(frame, color, self.hit_box, width = 2)


class RobotRenderer(Protocol):
    def draw(self, frame: pygame.Surface, robot: Robot) -> None: ...


class BoxRobotRenderer:
    def draw(self, frame: pygame.Surface, robot: Robot) -> None:
        color: Color = (100, 60, 10) if robot._hover_detector.is_hovered else (0, 0, 0)
        pygame.draw.rect(frame, color, robot._hover_detector.hit_box)


class AssetRobotRenderer:

    def __init__(self, sprite: pygame.Surface, offset: tuple[int,int]) -> None:
        self.sprite = sprite
        self.offset = pygame.Vector2(offset)

    def draw(self, frame: pygame.Surface, robot: Robot) -> None:
        position = robot.position + self.offset
        frame.blit(self.sprite, position)
        pygame.draw.circle(frame, color = GREEN_COLOR, center = robot.position, radius = 3)



class Cell:
    pixel_size: int = 30

    def __init__(self, reference_position: pygame.Vector2, node: Node, hover_detector: "CellHoverDetector", renderer: "CellRenderer", component: Optional["Component"] = None) -> None:
        self.__reference_position = reference_position
        self._hover_detector: CellHoverDetector = hover_detector
        self._renderer: CellRenderer = renderer

        self.node = node
        self.component: Optional[Component] = component

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

    def draw(self, frame: pygame.Surface) -> None:
        if self._hover_detector.is_hovered:
            self._renderer.draw_highlighted(frame, self)
        else:
            self._renderer.draw(frame, self)

    def is_hovered(self, mouse_position: tuple) -> bool:
        return self._hover_detector.detect(mouse_position, self)


class CellRenderer(Protocol):
    def draw(self, frame: pygame.Surface, cell: "Cell") -> None:
        ...
    def draw_highlighted(self, frame: pygame.Surface, cell: "Cell") -> None:
        ...


class SimpleCellRenderer:
    def draw(self, frame: pygame.Surface, cell: "Cell") -> None:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        pygame.draw.rect(frame, rect=box, color=BLACK_COLOR, width=2)
        pygame.draw.circle(frame, color = GREEN_COLOR, center = cell.position, radius = 3)

    def draw_highlighted(self, frame: pygame.Surface, cell: "Cell") -> None:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        pygame.draw.rect(frame, rect=box, color=GREEN_COLOR)


class CellHoverDetector:
    def __init__(self) -> None:
        self.is_hovered: bool = False

    def detect(self, mouse_position: tuple, cell: "Cell") -> bool:
        box = pygame.Rect((cell.position.x, cell.position.y), (Cell.pixel_size, Cell.pixel_size))
        self.is_hovered = box.collidepoint(mouse_position)
        return self.is_hovered



class Component:
    def __init__(self, nodes: list[Node], renderer: "ComponentRenderer", content: Optional["ComponentContent"] = None) -> None:
        self._renderer: ComponentRenderer = renderer

        self.nodes: list[Node] = nodes
        self.content: Optional[ComponentContent] = content # Not implemented
        
        self.attachment_node: Optional["Node"] = None
        self.attachment_cells: list["Cell"] = []

    def attach(self, node: Node, cells: list["Cell"]) -> None:
        self.attachment_node = node
        self.attachment_cells = cells

    def deattach(self) -> None:
        self.attachment_point = None
        self.attachment_cells = []

    @property
    def position(self) -> Optional[pygame.Vector2]:
        assert self.attachment_node is not None
        for cell in self.attachment_cells:
            if cell.node == self.attachment_node:
                return cell.position
        return None
        

    def draw_in_place(self, frame: pygame.Surface) -> None:
        for cell in self.attachment_cells:
            if cell._hover_detector.is_hovered:
                self._renderer.draw_in_place_highlight(frame, self)
                return
        self._renderer.draw_in_place(frame, self)

    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: tuple) -> None:
        self._renderer.draw_on_mouse(frame, mouse_position, self)



class ComponentRenderer(Protocol):
    """Abstract interface for component renderer"""
    def draw_in_place(self, frame: pygame.Surface, component: "Component") -> None:
        ...
    def draw_in_place_highlight(self, frame: pygame.Surface, component: "Component") -> None:
        ...
    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: tuple, component: "Component") -> None:
        ...


class SimpleComponentRenderer: # BallComponentRenderer
    """Concrete implementation that draws a component as a simple group of colored circles"""
    radius: int = Cell.pixel_size//2

    def _draw_circle_with_boundary(self, frame: pygame.Surface, center_position: pygame.Vector2) -> None:
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLUE_COLOR)
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLACK_COLOR, width=2)

    def _draw_circle_without_boundary(self, frame: pygame.Surface, center_position: pygame.Vector2) -> None:
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLUE_COLOR)

    def draw_in_place(self, frame: pygame.Surface, component: "Component") -> None:
        for cell in component.attachment_cells:
            self._draw_circle_without_boundary(frame, cell.center_position)

    def draw_in_place_highlight(self, frame: pygame.Surface, component: "Component") -> None:
        for cell in component.attachment_cells:
            self._draw_circle_with_boundary(frame, cell.center_position)

    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: tuple, component: "Component") -> None:
        for node in component.nodes:
            center_position = pygame.Vector2(mouse_position) + node * Cell.pixel_size
            self._draw_circle_with_boundary(frame, center_position)


class AssetComponentRenderer:
    #alignment_vector = pygame.Vector2(-AssetManager.robot_pixel_size//2, -AssetManager.robot_pixel_size)

    def __init__(self, sprite: pygame.Surface, offset: tuple[int, int]) -> None:
        self.sprite = sprite
        self.offset = pygame.Vector2(offset)

    def draw_in_place(self, frame: pygame.Surface, component: "Component") -> None:
        assert component.position is not None
        position = component.position + self.offset
        frame.blit(self.sprite, position)
        pygame.draw.circle(frame, color = GREEN_COLOR, center = component.position, radius = 3)

    def draw_in_place_highlight(self, frame: pygame.Surface, component: "Component") -> None:
        self.draw_in_place(frame, component)

    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: tuple, component: "Component") -> None:
        frame.blit(self.sprite, mouse_position)


class ComponentContent(Protocol):
    #is_done: bool
    def activate(self) -> None:
        ...



class Chassi:
    relative_cell_origin_position = pygame.Vector2(-Cell.pixel_size, -5*Cell.pixel_size)

    def __init__(self, renderer: "ChassiRenderer", reference_position: pygame.Vector2, cells: list["Cell"], components: list["Component"]) -> None:
        self._renderer = renderer
        self.__reference_position = reference_position #Not really necessary
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

    def get_hovered_cell(self, mouse_position: tuple) -> Optional["Cell"]:
        hover_cell: Optional[Cell] = None
        for cell in self.cells:
            if cell.is_hovered(mouse_position):
                hover_cell = cell
        return hover_cell

    # CellCluster class from above methods?
    
    def add_component_in_any_cell(self, component: "Component") -> None:
        for cell in self.cells:
            try:
                self.add_component(cell, component)
                return
            except NoSpaceException: # Weird to catch the error and then raise it again?
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

    def draw(self, frame: pygame.Surface) -> None:
        self._renderer.draw(frame, self)
        pygame.draw.circle(frame, color = BLACK_COLOR, center = self.__reference_position+self.relative_cell_origin_position, radius = 3)

    def get_hovered_component(self, mouse_position: tuple) -> Optional["Component"]:
        hovered_cell = self.get_hovered_cell(mouse_position)
        for component in self.components:
            if hovered_cell in component.attachment_cells:
                return component
        return None



class NoSpaceException(Exception):
    """Raised when attempting to insert a component into a cell where it cannot fit"""
    pass


class ChassiRenderer:

    @staticmethod
    def draw(frame: pygame.Surface, chassi: "Chassi") -> None:
        for cell in chassi.cells:
            cell.draw(frame)

        for component in chassi.components:
            component.draw_in_place(frame)


class DragdropperState(Enum):
    HOVERING = auto()
    DRAGGING = auto()


class ComponentDragDropper:
    def __init__(self, robots: Sequence[Robot]) -> None:
        self.robots = robots
        self.chassis = [robot.chassi for robot in robots]
        self.state: DragdropperState = DragdropperState.HOVERING

        self.mouse_position: tuple = (0, 0)
        self.detached: Optional[Component] = None
        self.previous_attached_cell: Optional[Cell] = None
        self.previous_attached_chassi: Optional[Chassi] = None

    def loop(self, user_input: UserInput) -> None:
        self.mouse_position = user_input.mouse_position # Just to avoid passing user_input to renderer...

        match self.state:
            case DragdropperState.HOVERING:
                self.update_while_hovering(user_input)

            case DragdropperState.DRAGGING:
                self.update_while_dragging(user_input)

    def update_while_hovering(self, user_input: UserInput) -> None:
        hovered_component: Optional[Component] = None
        hovered_chassi: Optional[Chassi] = None
        #for chassi in self.chassis:
        #    hovered_component = chassi.get_hovered_component(user_input.mouse_position)
        #    hovered_chassi = chassi
        #    if hovered_component: break
        hovered_component, hovered_chassi = self.get_hovered_component_and_chassi(user_input.mouse_position)

        if not (hovered_component and user_input.is_mouse1_down):
            return

        assert hovered_chassi and hovered_component.attachment_node is not None
        self.previous_attached_cell = hovered_chassi.get_cell(hovered_component.attachment_node)
        self.previous_attached_chassi = hovered_chassi

        hovered_chassi.remove_component(hovered_component)
        self.detached = hovered_component
        self.state = DragdropperState.DRAGGING

    def get_hovered_component_and_chassi(self, mouse_position: tuple) -> tuple[Optional[Component], Optional[Chassi]]:
        for chassi in self.chassis:
            hovered_component = chassi.get_hovered_component(mouse_position)
            if hovered_component:
                return hovered_component, chassi
        return None, None

    def update_while_dragging(self, user_input: UserInput) -> None:
        hovered_cell: Optional[Cell] = None
        hovered_chassi: Optional[Chassi] = None
        for chassi in self.chassis:
            hovered_chassi = chassi
            hovered_cell = chassi.get_hovered_cell(user_input.mouse_position)
            if hovered_cell: break

        if not user_input.is_mouse1_up:
            return

        if not hovered_cell:
            assert self.previous_attached_cell and self.previous_attached_chassi and self.detached
            self.previous_attached_chassi.add_component(self.previous_attached_cell, self.detached)
            self.state = DragdropperState.HOVERING
            return

        assert hovered_chassi and self.detached
        self.state = DragdropperState.HOVERING

        try:
            hovered_chassi.add_component(hovered_cell, self.detached)
        except NoSpaceException:
            assert self.previous_attached_cell and self.previous_attached_chassi and self.detached
            self.previous_attached_chassi.add_component(self.previous_attached_cell, self.detached)

    def draw(self, frame: pygame.Surface) -> None:
        for robot in self.robots:
            robot.draw(frame)

        if not self.state == DragdropperState.DRAGGING:
            return

        assert self.detached
        self.detached.draw_on_mouse(frame, self.mouse_position)




### Test Scenario ###

if __name__ == "__main__":

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

    asset_manager = AssetManager()

    robot_factory = RobotFactory(asset_manager, [config1, config2])

    robot_factory2 = RobotFactory.from_yaml_file(ROBOT_CONFIG_PATH, asset_manager)
    robot0 = robot_factory2.build(robot_factory2.configs[1], pygame.Vector2(500,500))
    robot4 = robot_factory2.build(robot_factory2.configs[2], pygame.Vector2(650,200))
    robot5 = robot_factory2.build(robot_factory2.configs[3], pygame.Vector2(150,200))
    robot6 = robot_factory2.build(robot_factory2.configs[4], pygame.Vector2(150,600))

    position1 = pygame.Vector2(200,400)
    robot1 = robot_factory.build(config1, position1)

    position2 = pygame.Vector2(400,300)
    robot2 = Robot(
        BoxRobotRenderer(),
        position2,
        1,
        Chassi(ChassiRenderer(), position2, [Cell(position2, Node(*node), CellHoverDetector(), SimpleCellRenderer()) for node in config2.nodes], []),
        RobotHoverDetector(position2)
    )
    
    robot_factory.build(config2, position2)

    component_config1 = ComponentConfig(
        rarity = Rarity.COMMON,
        nodes = [(0,0), (0,1)],
        asset = AssetConfig(
            path = pathlib.Path("./assets/gun3.png"),
            size = (30,60),
            offset = (0,0)
        )
    )

    component_factory = ComponentFactory(asset_manager, (component_config1,))
    component_factory = ComponentFactory.from_yaml_file(COMPONENT_CONFIG_PATH, asset_manager)

    component0 = component_factory.build(component_config1)

    component1 = component_factory.build(component_factory.configs[0])
    component2 = Component([Node(0,0), Node(1,0)],            SimpleComponentRenderer())
    component3 = Component([Node(0,0), Node(1,0), Node(0,1)], SimpleComponentRenderer())

    robot1.chassi.add_component(robot1.chassi.cells[0], component1)
    robot1.chassi.add_component(robot1.chassi.cells[2], component2)
    robot2.chassi.add_component(robot2.chassi.cells[1], component3)
    robot2.chassi.add_component(robot2.chassi.cells[3], component0)

    drag_dropper = ComponentDragDropper([robot1, robot0, robot2, robot4, robot5, robot6])


    from core.input_listener import PygameInputListener, UserInput
    from core.renderer import PygameRenderer
    from core.engine import PygameEngine

    class MockRenderer(PygameRenderer):
        def draw_frame(self) -> None:
            self.frame.fill((30,20,60))

            drag_dropper.draw(self.frame)


    engine = PygameEngine(
        drag_dropper,
        MockRenderer(),
        PygameInputListener()
    )

    engine.run()
