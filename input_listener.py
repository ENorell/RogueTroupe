from interfaces import UserInput, InputListener
from pygame import event, QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, K_SPACE, mouse, key
from keyboard import is_pressed


class PygameInputListener(InputListener):
    """
    Collect user input from pygame's built in event queue and functions.
    Requires pygame to be initialized
    """

    def capture(self) -> UserInput:
        self.events = event.get()

        return UserInput(
            self._is_quit(),
            self._is_mouse1_down(),
            self._is_mouse1_up(),
            self._is_space_key_down(),
            self._mouse_position()
        )

    @property
    def event_types(self) -> list[int]:
        return [event.type for event in self.events]

    def _is_quit(self) -> bool:
        return QUIT in self.event_types
    
    def _is_mouse1_down(self) -> bool:
        return MOUSEBUTTONDOWN in self.event_types
    
    def _is_mouse1_up(self) -> bool:
        return MOUSEBUTTONUP in self.event_types
    
    def _is_space_key_down(self) -> bool:
        #key_presses = [event for event in self.events if event.type == KEYDOWN]
        #space_pressed = K_SPACE in [key_press.key for key_press in key_presses]
        space_pressed = key.get_pressed()[K_SPACE]
        return space_pressed

    def _mouse_position(self) -> tuple[int, int]:
        return mouse.get_pos()


class DeafInputListener(InputListener):
    """
    Produces no input for a number of frames, then quits
    """
    def __init__(self) -> None:
        self.frame_counter = 0

    def capture(self) -> UserInput:
        self.frame_counter += 1

        return UserInput(
            is_quit = self.frame_counter >= 100,
            is_mouse1_down = False,
            is_mouse1_up = False,
            is_space_key_down = False,
            mouse_position = (0,0)
        )


class CrazyInputListener(InputListener):
    """
    Goes crazy on the keyboard.
    """
    def __init__(self) -> None:
        self.frame_counter = 0

    def capture(self) -> UserInput:
        self.frame_counter += 1

        return UserInput(
            is_quit = self.frame_counter >= 200,
            is_mouse1_down = 0 < self.frame_counter <= 25,
            is_mouse1_up = 25 < self.frame_counter <= 50,
            is_space_key_down = 50 < self.frame_counter <= 100,
            mouse_position = (0,0)
        )


class KeyboardInputListener(InputListener):
    """
    Listens to keyboard presses using the Keyboard module.
    """

    def capture(self) -> UserInput:

        return UserInput(
            is_quit = is_pressed("q"),
            is_mouse1_down = False,
            is_mouse1_up = False,
            is_space_key_down = is_pressed("space"),
            mouse_position = (0,0)
        )


if __name__ == "__main__":

    listener = KeyboardInputListener()
    print( listener.capture() )