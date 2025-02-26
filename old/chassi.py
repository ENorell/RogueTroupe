from math import sqrt
from dataclasses import dataclass
from typing import Optional, Final, Self, Protocol
from enum import Enum, auto
import pygame
from core.interfaces import UserInput
from settings import Vector, BLUE_COLOR, GREEN_COLOR, BLACK_COLOR
from assets.images import AssetManager, ImageChoice

CELL_PIXEL_SIZE: Final[int] = 30
CHASSI_RELATIVE_CHARACTER_OFFSET = pygame.Vector2(5,-50)


@dataclass
class Point: #Node?
    x: int
    y: int

    def __eq__(self, other) -> bool:
        return self.x == other.x and self.y == other.y

    def __add__(self, other) -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, multiplier) -> "Point":
        return Point(self.x * multiplier, self.y * multiplier)

    def distance(self, other: "Point") -> float: # just do abs?
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class ComponentRenderer(Protocol):
    """Abstract interface for component renderer"""
    def draw_idle(self, frame: pygame.Surface, position: Vector, component: "Component") -> None:
        ...
    def draw_highlight(self, frame: pygame.Surface, position: Vector, component: "Component") -> None:
        ...
    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: Vector, component: "Component") -> None:
        ...


class AssetComponentRenderer:
    def __init__(self, local_origin: pygame.Vector2, asset_manager: AssetManager, image_choice: ImageChoice) -> None:
        self.local_origin: pygame.Vector2 = local_origin
        self.asset_manager: AssetManager = asset_manager
        self.image_choice: ImageChoice = image_choice

    def draw_idle(self, frame: pygame.Surface) -> None:
        image: pygame.Surface = self.asset_manager[self.image_choice]

        frame.blit(image, self.local_origin)

    def draw_highlight(self, frame: pygame.Surface, position: Vector, component: "Component") -> None:
        ...
    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: Vector, component: "Component") -> None:
        ...


class SimpleComponentRenderer:
    """Concreate implementation that draws a component as a simple group of colored circles"""
    radius: int = CELL_PIXEL_SIZE//2

    def _get_center_pixel(self, origin_position: Vector, attachment_point: Point, cell_point: Point) -> Vector:
        relative_point = cell_point + attachment_point
        position_x, position_y = origin_position
        return position_x + CELL_PIXEL_SIZE * relative_point.x, position_y + CELL_PIXEL_SIZE * relative_point.y

    def _draw_circle_with_boundary(self, frame: pygame.Surface, center_position: Vector) -> None:
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLUE_COLOR)
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLACK_COLOR, width=2)

    def _draw_circle_without_boundary(self, frame: pygame.Surface, center_position: Vector) -> None:
        pygame.draw.circle(frame, center=center_position, radius=self.radius, color=BLUE_COLOR)

    def draw_idle(self, frame: pygame.Surface, position: Vector, component: "Component") -> None:
        assert component.attachment_point
        for point in component.points:
            center_position = self._get_center_pixel(position, component.attachment_point, point)
            self._draw_circle_without_boundary(frame, center_position)

    def draw_highlight(self, frame: pygame.Surface, position: Vector, component: "Component") -> None:
        assert component.attachment_point
        for point in component.points:
            center_position = self._get_center_pixel(position, component.attachment_point, point)
            self._draw_circle_with_boundary(frame, center_position)

    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: Vector, component: "Component") -> None:
        for point in component.points:
            center_position = self._get_center_pixel(mouse_position, Point(0,0), point)
            self._draw_circle_with_boundary(frame, center_position)


class ComponentContent(Protocol):
    is_done: bool
    def activate(self) -> None:
        ...


class Component:
    def __init__(self, points: list[Point], renderer: ComponentRenderer, content: Optional[ComponentContent] = None) -> None:
        self.points: list[Point] = points
        self.content: Optional[ComponentContent] = content # Not implemented
        self.renderer: ComponentRenderer = renderer
        self.attachment_point: Optional[Point] = None
        self.attachment_cells: list["Cell"] = []

    def attach(self, point: Point, cells: list["Cell"]) -> None:
        self.attachment_point = point
        self.attachment_cells = cells

    def deattach(self) -> None:
        self.attachment_point = None
        self.attachment_cells = []

    # draw_in_place
    def draw(self, frame: pygame.Surface, position: Vector) -> None:
        for cell in self.attachment_cells:
            if cell.hover_detector.is_hovered:
                self.renderer.draw_highlight(frame, position, self)
                return
        self.renderer.draw_idle(frame, position, self)

    def draw_on_mouse(self, frame: pygame.Surface, mouse_position: Vector) -> None:
        self.renderer.draw_on_mouse(frame, mouse_position, self)


class CellRenderer(Protocol):
    def draw(self, frame: pygame.Surface, position: Vector, cell: "Cell") -> None:
        ...
    def draw_highlighted(self, frame: pygame.Surface, position: Vector, cell: "Cell") -> None:
        ...


class SimpleCellRenderer:
    def draw(self, frame: pygame.Surface, position: Vector, cell: "Cell") -> None:
        box = get_cell_box(pygame.Vector2(position), cell.point) # position is tuple and rest is Vector2...
        pygame.draw.rect(frame, rect=box, color=BLACK_COLOR, width=2)

    def draw_highlighted(self, frame: pygame.Surface, position: Vector, cell: "Cell") -> None:
        box = get_cell_box(pygame.Vector2(position), cell.point)
        pygame.draw.rect(frame, rect=box, color=GREEN_COLOR)


class CellHoverDetector:
    def __init__(self) -> None:
        self.is_hovered: bool = False

    def detect(self, origin_position: pygame.Vector2, mouse_position: Vector, cell: "Cell") -> bool:
        box = get_cell_box(origin_position, cell.point)
        self.is_hovered = box.collidepoint(mouse_position)
        return self.is_hovered


def get_cell_box(origin_position: pygame.Vector2, cell_point: Point) -> pygame.Rect:
    origin_x, origin_y = origin_position
    cell_position_x = origin_x + cell_point.x * CELL_PIXEL_SIZE - CELL_PIXEL_SIZE/2
    cell_position_y = origin_y + cell_point.y * CELL_PIXEL_SIZE - CELL_PIXEL_SIZE/2
    return pygame.Rect((cell_position_x, cell_position_y), (CELL_PIXEL_SIZE, CELL_PIXEL_SIZE))


@dataclass
class Cell:
    point: Point
    hover_detector: CellHoverDetector
    renderer: CellRenderer
    component: Optional[Component] = None

    def set_content(self, component: Component) -> None:
        self.component = component

    def clear(self) -> None:
        self.component = None

    @property
    def is_vacant(self) -> bool:
        return not bool(self.component)

    def draw(self, frame: pygame.Surface, position: Vector) -> None:
        if self.hover_detector.is_hovered:
            self.renderer.draw_highlighted(frame, position, self)
        else:
            self.renderer.draw(frame, position, self)

    def is_hovered(self, origin_position: pygame.Vector2, mouse_position: Vector) -> bool:
        return self.hover_detector.detect(origin_position+CHASSI_RELATIVE_CHARACTER_OFFSET, mouse_position, self)

    @classmethod
    def create(cls, point: Point) -> "Cell":
        hover_detector = CellHoverDetector()
        renderer = SimpleCellRenderer()
        return cls(point, hover_detector, renderer)


class ChassiRenderer:

    @staticmethod
    def draw(frame: pygame.Surface, chassi: "Chassi") -> None:
        for cell in chassi.cells:
            cell.draw(frame, chassi.local_origin + CHASSI_RELATIVE_CHARACTER_OFFSET)

        for component in chassi.components:
            component.draw(frame, chassi.local_origin + CHASSI_RELATIVE_CHARACTER_OFFSET)


class NoSpaceException(Exception):
    """Raised when attempting to insert a component into a cell where it cannot fit"""
    pass


@dataclass
class Chassi:
    local_origin: pygame.Vector2 #top_left_position
    cells: list[Cell]
    renderer: ChassiRenderer
    components: list[Component]

    def add_cell(self, cell: Cell) -> None:
        assert not self.is_cell_occupied(cell)
        assert self.is_cell_adjacent(cell)
        self.cells.append(cell)

    def is_cell_occupied(self, cell: Cell) -> bool:
        return cell in self.cells

    def is_cell_adjacent(self, cell: Cell) -> bool:
        for frame_cell in self.cells:
            if frame_cell.point.distance(cell.point) <= 1:
                return True
        return False

    def get_cell(self, point: Point) -> Optional[Cell]:
        for cell in self.cells:
            if cell.point == point:
                return cell
        return None

    def get_hovered_cell(self, mouse_position: Vector) -> Optional[Cell]:
        hover_cell: Optional[Cell] = None
        for cell in self.cells:
            if cell.is_hovered(self.local_origin, mouse_position):
                hover_cell = cell
        return hover_cell

    # CellCluster class from above methods?
    
    def add_component_in_any_cell(self, component: Component) -> None:
        for cell in self.cells:
            try:
                self.add_component(cell, component)
                return
            except NoSpaceException: # Weird to catch the error and then raise it again?
                continue
        raise NoSpaceException(f"No vacant cell in {self}")


    def add_component(self, target_cell: Cell, component: Component) -> None:
        assert target_cell in self.cells

        candidate_cells: list[Cell] = []
        for component_point in component.points:
            frame_point = target_cell.point + component_point
            frame_cell = self.get_cell(frame_point)
            if not frame_cell: raise NoSpaceException(f"{component_point} does not exist in {self.cells}")
            if not frame_cell.is_vacant: raise NoSpaceException(f"{frame_cell} is not vacant")
            candidate_cells.append(frame_cell)

        self.components.append(component)
        component.attach(target_cell.point, candidate_cells)
        for candidate_cell in candidate_cells:
            candidate_cell.set_content(component)

    def remove_component(self, component: Component) -> None:
        for cell in self.cells:
            if cell.component == component:
                cell.clear()
        self.components.remove(component)
        component.deattach()

    def draw(self, frame: pygame.Surface) -> None:
        self.renderer.draw(frame, self)

    def get_hovered_component(self, mouse_position: Vector) -> Optional[Component]:
        hovered_cell = self.get_hovered_cell(mouse_position)
        for component in self.components:
            if hovered_cell in component.attachment_cells:
                return component
        return None

    @classmethod
    def from_points(cls, position: pygame.Vector2, points: list[tuple]) -> Self:
        chassi_renderer = ChassiRenderer()
        cells: list[Cell] = [Cell.create(Point(*point)) for point in points]
        return cls(position, cells, chassi_renderer, [])


class DragdropperState(Enum):
    HOVERING = auto()
    DRAGGING = auto()


class ComponentDragDropper:
    def __init__(self, chassis: list[Chassi]) -> None:
        self.chassis: list[Chassi] = chassis
        self.state: DragdropperState = DragdropperState.HOVERING

        self.mouse_position: Vector = (0,0)
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
        for chassi in self.chassis:
            hovered_component = chassi.get_hovered_component(user_input.mouse_position)
            hovered_chassi = chassi
            if hovered_component: break

        if not (hovered_component and user_input.is_mouse1_down):
            return

        assert hovered_chassi and hovered_component.attachment_point
        self.previous_attached_cell = hovered_chassi.get_cell(hovered_component.attachment_point)
        self.previous_attached_chassi = hovered_chassi

        hovered_chassi.remove_component(hovered_component)
        self.detached = hovered_component
        self.state = DragdropperState.DRAGGING

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
        for chassi in self.chassis:
            chassi.draw(frame)

        if not self.state == DragdropperState.DRAGGING:
            return

        assert self.detached
        self.detached.draw_on_mouse(frame, self.mouse_position)

    #@classmethod
    #def from_robots(cls, robots: list["Robot"])








## Make RobotLoader with Pydantic!

### Test Scenario ###

if __name__ == "__main__":

    cell_frame_cells1: list[Cell] = [
        Cell.create(Point(0,0)), Cell.create(Point(1,0)), Cell.create(Point(2,0)),
        Cell.create(Point(0,1)), Cell.create(Point(1,1))
        ]
    chassi1 = Chassi(pygame.Vector2(100,100), cell_frame_cells1, ChassiRenderer(), [])

    cell_frame_cells2: list[Cell] = [
        Cell.create(Point(0,0)), Cell.create(Point(1,0)), Cell.create(Point(2,0)),
        Cell.create(Point(0,1)), Cell.create(Point(1,1)), Cell.create(Point(2,1)),
        Cell.create(Point(0,2))
        ]
    chassi2 = Chassi(pygame.Vector2(300,100), cell_frame_cells2, ChassiRenderer(), [])

    component1 = Component([Point(0,0)],                         SimpleComponentRenderer())
    component2 = Component([Point(0,0), Point(1,0)],             SimpleComponentRenderer())
    component3 = Component([Point(0,0), Point(1,0), Point(0,1)], SimpleComponentRenderer())

    chassi1.add_component(cell_frame_cells1[0], component1)
    chassi1.add_component(cell_frame_cells1[1], component2)
    chassi2.add_component(cell_frame_cells2[1], component3)

    drag_dropper = ComponentDragDropper([chassi1, chassi2])


    from core.input_listener import PygameInputListener
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
