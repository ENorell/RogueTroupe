import json
import random
from core.input_listener import PygameInputListener
from core.renderer import PygameRenderer
from core.engine import PygameEngine
from chassi import (
    Cell,
    Point,
    Chassi,
    Component,
    ComponentRenderer,
    ComponentDragDropper,
)
import pygame

# Define the file path
chassis_path = "./config/chassis.json"
component_path = "./config/components.json"

# Read the JSON files
with open(chassis_path, "r") as f:
    data = json.load(f)
    chassis_options = data["chassis"]

with open(component_path, "r") as f:
    data = json.load(f)
    component_options = data

# Special "shop" and "toolbox" chassis
shop_width = 20
shop_height = 4
toolbox_width = 5
toolbox_height = 4

shop_cells = [Cell.create(Point(x, y)) for y in range(shop_height) for x in range(shop_width)]
toolbox_cells = [Cell.create(Point(x, y)) for y in range(toolbox_height) for x in range(toolbox_width)]

shop_selection = random.sample(component_options, 4)
shop_chassi = Chassi.create_empty((100, 40), shop_cells)

shop_loc = 0
for component_data in shop_selection:
    component_cells = [Point(x, y) for x, y in component_data["coordinates"]]
    component = Component(component_cells, ComponentRenderer())
    shop_chassi.add_component(shop_cells[shop_loc], component)
    shop_loc += 5

chassi_selection = random.sample(chassis_options, 2)
chassi_loc_x = 300
chassis = []

for chassi_data in chassi_selection:
    chassi_cells = [Cell.create(Point(x, y)) for x, y in chassi_data["coordinates"]]
    chassis.append(Chassi.create_empty((chassi_loc_x, 250), chassi_cells))
    chassi_loc_x += 100

toolbox_chassi = Chassi.create_empty((300, 450), toolbox_cells)
drag_dropper = ComponentDragDropper([shop_chassi, toolbox_chassi] + chassis)

class MockRenderer(PygameRenderer):
    def __init__(self):
        super().__init__()
        pygame.font.init()  # Initialize the font module
        self.font = pygame.font.Font(None, 24)  # Set font and size

    def draw_label(self, text: str, position: tuple[int, int], color=(255, 255, 255)) -> None:
        """Draw a text label at the specified position."""
        label = self.font.render(text, True, color)
        self.frame.blit(label, position)

    def draw_frame(self) -> None:
        self.frame.fill((30, 20, 60))

        # Draw labels for the shop, toolbox, and chassis
        self.draw_label("Shop", (20, 50))
        self.draw_label("Toolbox", (300, 420))
        self.draw_label("Unit 1", (300, 200))  # Adjust based on chassis coordinates
        self.draw_label("Unit 2", (400, 200))  # Adjust as needed

        # Draw components
        drag_dropper.draw(self.frame)

engine = PygameEngine(
    drag_dropper,
    MockRenderer(),
    PygameInputListener(),
)

if __name__ == "__main__":
    engine.run()
