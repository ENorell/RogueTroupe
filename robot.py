from typing import Protocol, Optional, Final
from collections.abc import Sequence
from enum import Enum, auto
import pathlib

import pygame
import pydantic
import yaml

from settings import Color, BLUE_COLOR, GREEN_COLOR, BLACK_COLOR, GAME_FPS
from pygame_engine import PygameEventHandler, UserEvent, InputHandler, PygameInputHandler, delay_next_frame, SCREEN, CLOCK
from core.state_machine import State, StateMachine


ROBOT_CONFIG_PATH = pathlib.Path("./robot_configs.yaml")
COMPONENT_CONFIG_PATH = pathlib.Path("./component_configs.yaml")
SLOT_ASSET_PATH = pathlib.Path("assets/ui/slot.png")


class Node(pygame.Vector2):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)



# Singleton? Does not have to be global, but should only be one preferably, not mandatory though
class AssetManager:
    def __init__(self) -> None:
        self.path_to_image: dict[pathlib.Path, pygame.Surface] = {}
    
    def load(self, path: pathlib.Path, size: tuple[int, int]) -> pygame.Surface:
        if not path in self.path_to_image:
            image: pygame.Surface = pygame.image.load(path)
            image.convert_alpha() #NOT BEFORE PYGAME INIT
            image = pygame.transform.scale(image, size)
            self.path_to_image[path] = image
        return self.path_to_image[path]
        

class Rarity(Enum):
    RARE = "Rare"
    COMMON = "Common"


class AssetConfig(pydantic.BaseModel):
    path: pydantic.FilePath
    size: tuple[int, int]
    offset: tuple[int, int]


class RobotConfig(pydantic.BaseModel):
    rarity: Rarity
    health: int
    nodes: list[tuple[int, int]]
    asset: AssetConfig


class ComponentConfig(pydantic.BaseModel):
    rarity: Rarity
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
        hover_detector = RobotHoverDetector(position, config.asset.offset, image.get_size())

        return Robot(renderer, position, config.health, chassi, hover_detector)

    def build_in(self, slot: "Slot", config: RobotConfig) -> "Robot":
        robot = self.build(config, pygame.Vector2(slot.position))
        slot.attach_robot(robot)
        #robot.deploy_in(slot)
        return robot

    @classmethod
    def from_yaml_file(cls, config_path: pathlib.Path, asset_manager: AssetManager) -> "RobotFactory":
        with open(config_path, 'r') as file:
            yaml_config: dict = yaml.safe_load(file)

        robot_configs = [RobotConfig(**robot_config) for robot_config in yaml_config.values()]

        return cls(asset_manager, robot_configs)


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
    def __init__(self, position: tuple[int, int], renderer: "SlotRenderer", hover_detector: "SlotHoverDetector") -> None:
        self._position = position
        self._renderer = renderer
        self._hover_detector = hover_detector
        self.attached_robot: Optional[Robot] = None

    @property
    def position(self) -> tuple[int, int]:
        return self._position
    
    def attach_robot(self, robot: "Robot") -> None:
        self.attached_robot = robot
        robot.position = pygame.Vector2(self._position)

    def clear(self) -> None:
        self.attached_robot = None

    def draw(self) -> None: self._renderer.draw(self)

    def draw_highlighted(self) -> None: self._renderer.draw_highlighted(self)

    def is_hovered(self, cursor_position: tuple[int, int]) -> bool: 
        return self._hover_detector.detect(cursor_position)

    @classmethod
    def create(cls, asset_manager: AssetManager, position: tuple[int, int]) -> "Slot":
        image = asset_manager.load(SLOT_ASSET_PATH, (100, 100))
        renderer = SlotRenderer(image)
        hitbox = pygame.Rect(position -pygame.Vector2(image.get_size())/2, image.get_size())
        hover_detector = SlotHoverDetector(hitbox)
        return Slot(position, renderer, hover_detector)


class SlotHoverDetector:
    def __init__(self, hitbox: pygame.Rect) -> None:
        self._hitbox = hitbox

    def detect(self, cursor_position: tuple[int, int]) -> bool:
        return self._hitbox.collidepoint(cursor_position)


class SlotRenderer:
    def __init__(self, image: pygame.Surface) -> None:
        self.image = image

    @property
    def center_offset(self) -> pygame.Vector2:
        return -pygame.Vector2(self.image.get_size())/2

    def draw(self, slot: Slot) -> None:
        SCREEN.blit(self.image, slot._position+self.center_offset)

    def draw_highlighted(self, slot: Slot) -> None:
        outlined_image = draw_outline(self.image)
        SCREEN.blit(outlined_image, slot._position+self.center_offset)


class Robot:
    def __init__(self, renderer: "RobotRenderer", position: pygame.Vector2, health: int, chassi: "Chassi", hover_detector: "RobotHoverDetector") -> None:
        self._hover_detector: RobotHoverDetector = hover_detector
        self._renderer = renderer

        #self.slot: Slot
        self._position: pygame.Vector2 = position
        self.health: int = health
        self.chassi: Chassi = chassi
        

    @property
    def position(self) -> pygame.Vector2:
        return self._position
    
    @position.setter # To always update in-place
    def position(self, new_position: pygame.Vector2) -> None:
        self._position.update(new_position)
        
    def draw(self, cursor_position: tuple[int, int]) -> None:
        if self.is_hovered(cursor_position):
            self._renderer.draw_highlighted(self)
        else:
            self._renderer.draw(self)

        self.chassi.draw(cursor_position)

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

    #def draw(self, frame: pygame.Surface) -> None:
        #color: Color = (100, 60, 10) if self.is_hovered else (0, 0, 0)
        #pygame.draw.rect(frame, color, self.hit_box, width = 2)


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
        

    def draw_in_place(self, cursor_position: tuple[int, int]) -> None:
        for cell in self.attachment_cells:
            if cell.is_hovered(cursor_position):
                self._renderer.draw_in_place_highlight(self)
                return
        self._renderer.draw_in_place(self)

    def draw_on_mouse(self, cursor_position: tuple) -> None:
        self._renderer.draw_on_mouse(cursor_position, self)



class ComponentRenderer(Protocol):
    """Abstract interface for component renderer"""
    def draw_in_place(self, component: "Component") -> None:
        ...
    def draw_in_place_highlight(self, component: "Component") -> None:
        ...
    def draw_on_mouse(self, cursor_position: tuple, component: "Component") -> None:
        ...


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



def get_mask(surface: pygame.Surface) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface).to_surface()
    mask.set_colorkey((0,0,0))
    return mask

def draw_outline(surface: pygame.Surface) -> pygame.Surface:
    outline_offset: int = 2
    mask = get_mask(surface)
    outline = mask.copy()
    outline.blit( mask,   (-outline_offset, 0) )
    outline.blit( mask,   ( outline_offset, 0) )
    outline.blit( mask,   ( 0             ,-outline_offset) )
    outline.blit( mask,   ( 0             , outline_offset) )
    outline.blit(surface, ( 0             , 0) )
    return outline


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
        sprite_outline = draw_outline(self.sprite)
        SCREEN.blit(sprite_outline, position)

    def draw_on_mouse(self, cursor_position: tuple, component: "Component") -> None:
        SCREEN.blit(self.sprite, cursor_position)


class ComponentContent(Protocol):
    #is_done: bool
    def activate(self) -> None:
        ...



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




class Button:
    def __init__(self, position: tuple[int, int], button_drawer: "ButtonDrawer", hover_detector: "HoverDetector") -> None:
        self._position: tuple[int, int] = position
        self._button_drawer: ButtonDrawer = button_drawer
        self._hover_detector: HoverDetector = hover_detector

    @property
    def position(self) -> tuple[int, int]:
        return self._position

    def is_hovered(self, cursor_position: tuple[int, int]) -> bool:
        return self._hover_detector.detect(cursor_position)

    def is_clicked(self, cursor_position: tuple[int, int], cursor_is_pressed: bool) -> bool:
        return self.is_hovered(cursor_position) and cursor_is_pressed

    def draw(self, cursor_position: tuple[int, int]) -> None:
        if self._hover_detector.detect(cursor_position):
            self._button_drawer.draw_hover()
        else:
            self._button_drawer.draw_idle()

    @classmethod
    def create_simple(cls, position: tuple[int, int], text: str, size: tuple[int, int] = (150,50)) -> "Button":
        hover_detector = PygameHoverDetector(pygame.Rect(position, size))
        button_drawer = SimpleButtonDrawer(position, size, text)
        return cls(position, button_drawer, hover_detector)


class HoverDetector(Protocol):
    """Abstract interface for all hover detectors."""
    def detect(self, mouse_position) -> bool:
        ...


class PygameHoverDetector:
    """Concrete hover detector wrapping the pygame API"""
    def __init__(self, box: pygame.Rect):
        self.box = box

    def detect(self, mouse_position) -> bool:
        return self.box.collidepoint(mouse_position)


class ButtonDrawer(Protocol):
    def draw_idle(self) -> None:
        ...
    def draw_hover(self) -> None:
        ...

class SimpleButtonDrawer:
    color: Final[Color] = (9, 97, 59)
    hover_scale_ratio: float = 1.5

    def __init__(self, position: tuple[int, int], size: tuple[int, int], text: str) -> None:
        self.position = position
        self.size = size
        #self.text_drawer = fonts.PygameTextDrawer(position, text)

    @property
    def box(self) -> pygame.Rect:
        return pygame.Rect(self.position, self.size)

    def draw_idle(self) -> None:
        pygame.draw.rect(SCREEN, self.color, self.box)
        #self.text_drawer.draw(frame)

    def draw_hover(self) -> None:
        rect = self.box.scale_by(self.hover_scale_ratio, self.hover_scale_ratio)
        pygame.draw.rect(SCREEN, self.color, rect)
        #self.text_drawer.draw(frame)


## Important distinction between "game objects" and "scenes"
## The Scene interacts and mutates the game objects
## Scenes need to be "driven" with update, but game objects dont



class DragdropperState(Enum):
    HOVERING = auto()
    DRAGGING = auto()


class ComponentDragDropper(State):
    def __init__(self, input_handler: InputHandler, robots: Sequence[Robot], slots: list[Slot]) -> None:
        super().__init__()
        self._input_handler = input_handler
        self.robots = robots
        self.slots = slots
        self.chassis = [robot.chassi for robot in robots]
        self.state: DragdropperState = DragdropperState.HOVERING

        self.next_state_button = Button.create_simple((500, 300),'')
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

        self.next_state_button.draw(self._input_handler.cursor_position)

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
    def __init__(self, input_handler: InputHandler, robots: list[Robot], slots: list[Slot]) -> None:
        super().__init__()
        self._input_handler = input_handler
        self.robots: list[Robot] = robots
        self.slots = slots

        self.next_state_button = Button.create_simple((500, 300),'')
        self.detached_robot: Optional[Robot] = None
        self.detached_slot: Optional[Slot] = None
        self.state = DragdropperState.HOVERING

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
                    self.next_state = StateChoice.COMPONENT
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

        self.next_state_button.draw(self._input_handler.cursor_position)


### Test Scenario ###

if __name__ == "__main__":
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
            (0,2)
        ],
        asset = AssetConfig(
            path = pathlib.Path("./assets/Sprite-0002.png"),
            size = (210,210),
            offset = (0,-15)
        )
    )

    

    robot_factory = RobotFactory(asset_manager, [config1, config2])

    robot_factory2 = RobotFactory.from_yaml_file(ROBOT_CONFIG_PATH, asset_manager)
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

    position2 = pygame.Vector2(400,300)
    robot2 = Robot(
        BoxRobotRenderer(),
        position2,
        1,
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
        )
    )

    component_factory = ComponentFactory(asset_manager, (component_config1,))
    component_factory = ComponentFactory.from_yaml_file(COMPONENT_CONFIG_PATH, asset_manager)

    component0 = component_factory.build(component_config1)

    component1 = component_factory.build(component_factory.configs[0])
    component2 = Component([Node(0,0), Node(1,0)],            SimpleComponentRenderer())
    component3 = Component([Node(0,0), Node(1,0), Node(0,1)], SimpleComponentRenderer())

    robots[1].chassi.add_component(robots[1].chassi.cells[0], component1)
    robots[1].chassi.add_component(robots[1].chassi.cells[2], component2)
    robots[0].chassi.add_component(robots[0].chassi.cells[0], component3)
    robots[2].chassi.add_component(robots[2].chassi.cells[0], component0)

    input_handler = PygameInputHandler()

    drag_dropper = ComponentDragDropper(input_handler, robots, slots)

    robot_drag_dropper = RobotDragDropper(input_handler, robots, slots)

    class StateChoice(Enum):
        COMPONENT = auto()
        ROBOT = auto()

    state_machine = StateMachine({StateChoice.ROBOT: robot_drag_dropper, StateChoice.COMPONENT: drag_dropper}, StateChoice.ROBOT)


    while True:
        
        input_handler.handle_input()

        state_machine.update()

        state_machine.draw()
        
        delay_next_frame()
