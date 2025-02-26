from typing import Sequence, Optional, Protocol, TYPE_CHECKING
from pathlib import Path

import pydantic
import pygame
import yaml

from asset_manager import AssetManager, AssetConfig
from core.interfaces import Node, Rarity
from pygame_engine import SCREEN
from settings import BLACK_COLOR, BLUE_COLOR, RED_COLOR
from button import draw_outline

#if TYPE_CHECKING:
from robot import Cell


COMPONENT_CONFIG_PATH = Path("./component_configs.yaml")


class ComponentEffect(pydantic.BaseModel):
    damage: int = 0
    shield: int = 0# another model
    boost: int = 0


class ComponentConfig(pydantic.BaseModel):
    #name: str
    asset: AssetConfig
    rarity: Rarity
    nodes: list[tuple[int, int]]
    effect: ComponentEffect


class ComponentFactory:
    def __init__(self, asset_manager: AssetManager, configs: Sequence[ComponentConfig]) -> None:
        self.asset_manager = asset_manager
        self.configs = list(configs)

    def build(self, config: ComponentConfig) -> "Component":
        image = self.asset_manager.load(config.asset)

        nodes = [Node(*node) for node in config.nodes]

        renderer = AssetComponentRenderer(image, config.asset.offset)

        return Component(nodes, renderer, config.effect)

    @classmethod
    def from_yaml_file(cls, asset_manager: AssetManager, config_path: Path = COMPONENT_CONFIG_PATH) -> "ComponentFactory":
        with open(config_path, 'r') as file:
            yaml_config: list = yaml.safe_load(file)

        configs = [ComponentConfig(**config) for config in yaml_config]

        return cls(asset_manager, configs)



class Component:
    def __init__(self, nodes: list[Node], renderer: "ComponentRenderer", effect: ComponentEffect) -> None:
        self._renderer: ComponentRenderer = renderer

        self.nodes: list[Node] = nodes
        self.effect: ComponentEffect = effect
        
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
        

    def draw_in_place(self, cursor_position: tuple[int, int]) -> None:
        for cell in self.attachment_cells:
            if cell.is_hovered(cursor_position):
                self._renderer.draw_in_place_highlight(self)
                return
        self._renderer.draw_in_place(self)

    def draw_highlighted(self) -> None:
        self._renderer.draw_in_place_highlight(self)

    def draw_on_mouse(self, cursor_position: tuple) -> None:
        self._renderer.draw_on_mouse(cursor_position, self)



class ComponentRenderer(Protocol):
    """Abstract interface for component renderer"""
    def draw_in_place(self, component: "Component") -> None: ...
    def draw_in_place_highlight(self, component: "Component") -> None: ...
    def draw_on_mouse(self, cursor_position: tuple, component: "Component") -> None: ...


class SimpleComponentRenderer: # BallComponentRenderer
    """Concrete implementation that draws a component as a simple group of colored circles"""
    radius: int = Cell.pixel_size//2

    def _draw_circle_with_boundary(self, center_position: pygame.Vector2) -> None:
        pygame.draw.circle(SCREEN, center=center_position, radius=self.radius, color=BLUE_COLOR)
        pygame.draw.circle(SCREEN, center=center_position, radius=self.radius, color=BLACK_COLOR, width=2)

    def _draw_circle_without_boundary(self, center_position: pygame.Vector2) -> None:
        pygame.draw.circle(SCREEN, center=center_position, radius=self.radius, color=BLUE_COLOR)

    def draw_in_place(self, component: "Component") -> None:
        for cell in component.attachment_cells:
            self._draw_circle_without_boundary(cell.center_position)

    def draw_in_place_highlight(self, component: "Component") -> None:
        for cell in component.attachment_cells:
            self._draw_circle_with_boundary(cell.center_position)

    def draw_on_mouse(self, cursor_position: tuple, component: "Component") -> None:
        for node in component.nodes:
            center_position = pygame.Vector2(cursor_position) + node * Cell.pixel_size
            self._draw_circle_with_boundary(center_position)


class AssetComponentRenderer:
    #alignment_vector = pygame.Vector2(-AssetManager.robot_pixel_size//2, -AssetManager.robot_pixel_size)

    def __init__(self, sprite: pygame.Surface, offset: tuple[int, int]) -> None:
        self.sprite = sprite
        self.offset = pygame.Vector2(offset)

    def draw_in_place(self, component: "Component") -> None:
        assert component.position is not None
        position = component.position + self.offset
        SCREEN.blit(self.sprite, position)
        #pygame.draw.circle(SCREEN, color = GREEN_COLOR, center = component.position, radius = 3)

    def draw_in_place_highlight(self, component: "Component") -> None:
        assert component.position is not None
        position = component.position + self.offset
        sprite_outline = draw_outline(self.sprite, RED_COLOR)
        SCREEN.blit(sprite_outline, position)

    def draw_on_mouse(self, cursor_position: tuple, component: "Component") -> None:
        SCREEN.blit(self.sprite, cursor_position)



if __name__ == '__main__':
    from robot import Chassi, ChassiRenderer, CellHoverDetector, CellRenderer, RobotConfig, SimpleCellRenderer
    from pygame_engine import delay_next_frame, PygameInputHandler

    component_config1 = ComponentConfig(
        rarity = Rarity.COMMON,
        nodes = [(0,0), (0,1)],
        asset = AssetConfig(
            path = Path("./assets/gun3.png"),
            size = (30,60),
            offset = (0,0)
        ),
        effect = ComponentEffect()
    )

    asset_manager = AssetManager()

    component_factory = ComponentFactory(asset_manager, (component_config1,))
    component_factory = ComponentFactory.from_yaml_file(asset_manager)

    component0 = component_factory.build(component_config1)

    component1 = component_factory.build(component_factory.configs[0])
    component2 = Component([Node(0,0), Node(1,0)],            SimpleComponentRenderer(), ComponentEffect())
    component3 = Component([Node(0,0), Node(1,0), Node(0,1)], SimpleComponentRenderer(), ComponentEffect())


    config1 = RobotConfig(
        rarity = Rarity.COMMON,
        health = 1,
        nodes = [
            (0,0), 
            (0,1),
            (0,2), (1,2)
        ],
        asset = AssetConfig(
            path = Path("./assets/Sprite-0002.png"),
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
            path = Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (0,-15)
        )
    )

    position2 = pygame.Vector2(400,300)

    chassi = Chassi(ChassiRenderer(), position2, [Cell(position2, Node(*node), CellHoverDetector(), SimpleCellRenderer()) for node in config2.nodes], [])

    chassi.add_component(chassi.cells[0], component1)
    chassi.add_component(chassi.cells[1], component2)
    #chassi.add_component(chassi.cells[5], component3)
    #chassi.add_component(chassi.cells[0], component0)


    input_handler = PygameInputHandler()

    while True:
        
        input_handler.handle_input()

        #state_machine.update()

        SCREEN.fill('darkgray')
        chassi.draw(input_handler.cursor_position)
        
        delay_next_frame()