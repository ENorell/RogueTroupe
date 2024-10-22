from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum, auto

from core.interfaces import UserInput


class StateChoice(Enum):
    SHOP        = auto()
    PREPARATION = auto()
    BATTLE      = auto()


class State(ABC):
    """Handles the specific behavior of a certain state"""
    def __init__(self) -> None:
        self.cleanup_state()

    def is_state_done(self) -> bool:
        return bool(self.next_state)
    
    def go_to_next_state(self, state_choice: StateChoice) -> None:
        self.next_state = state_choice
    
    def get_next_state(self) -> StateChoice:
        if not self.next_state: raise Exception("Trying to switch state without specifying where.")
        return self.next_state

    def cleanup_state(self) -> None:
        self.next_state: Optional[StateChoice] = None

    @abstractmethod
    def start_state(self) -> None:
        ...

    @abstractmethod
    def loop(self, user_input: UserInput) -> None:
        ...


class StateMachine(ABC):
    """Handles switching and activation of different states"""
    def __init__(self, states: dict[StateChoice, State], start_state: StateChoice) -> None:
        self.states = states
        self.state: State = states[start_state]
        self.state.start_state()

    def switch_state(self, next_state: StateChoice) -> None:
        self.state.cleanup_state()
        self.state = self.states[next_state]
        self.state.start_state()
        
    def loop(self, user_input: UserInput) -> None:
        if self.state.is_state_done():
            next_state = self.state.get_next_state()
            self.switch_state(next_state)

        self.state.loop(user_input)
