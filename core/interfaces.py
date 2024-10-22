from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class UserInput:
    is_quit: bool
    is_mouse1_down: bool
    is_mouse1_up: bool
    is_space_key_down: bool
    mouse_position: tuple[int, int]


class InputListener(Protocol):

    def capture(self) -> UserInput:
        ...


class Loopable(Protocol):

    def loop(self, user_input: UserInput) -> None:
        ...


class Renderer(Protocol):
    
    def render(self, loopable: Loopable) -> None:
        ...


class Engine(ABC):
    def __init__(self, loopable: Loopable, renderer: Renderer, input_listener: InputListener):
        self.loopable = loopable
        self.renderer = renderer
        self.input_listener = input_listener
        self.running = True

    def run(self) -> None:
        while self.running:
            self.wait_for_next_frame()

            user_input: UserInput = self.input_listener.capture()

            self.loopable.loop(user_input)

            self.renderer.render(self.loopable)

            if user_input.is_quit: 
                self.running = False

        self.quit()

    @abstractmethod
    def wait_for_next_frame(self) -> None:
        ...

    @abstractmethod
    def quit(self) -> None:
        ...
