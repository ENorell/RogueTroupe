from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class State(ABC):
    """Handles the specific behavior of a certain state"""
    def __init__(self) -> None:
        self.next_state: Optional[Enum] = None

    @property
    def is_done(self) -> bool:
        return bool(self.next_state)

    def cleanup_state(self) -> None:
        self.next_state = None

    #@abstractmethod
    def start_state(self) -> None:
        ...

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def draw(self) -> None:
        ...


class StateMachine(ABC):
    """Handles switching and activation of different states"""
    def __init__(self, states: dict[Enum, State], start_state: Enum) -> None:
        self.states: dict[Enum, State] = states
        self.state: State = states[start_state]

    def switch_state(self, next_state: Enum) -> None:
        self.state.cleanup_state()
        self.state = self.states[next_state]
        self.state.start_state()
        
    def update(self) -> None:
        if self.state.is_done:
            assert self.state.next_state
            self.switch_state(self.state.next_state)

        self.state.update()

    def draw(self) -> None: self.state.draw()
