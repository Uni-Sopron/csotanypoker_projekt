from abc import ABC, abstractmethod


class BaseScreen(ABC):
    """
    Abstract base class that all game screens will inherit from.
    Defines the common interface that GameClient will use to interact with screens.
    """

    def __init__(self, client):
        """
        Initialize the screen with a reference to the main client.

        Args:
            client: The GameClient instance that manages this screen
        """
        self.client = client

    @abstractmethod
    def draw(self):
        """
        Draw the screen content.
        This method must be implemented by all concrete screen classes.
        """
        pass

    @abstractmethod
    def handle_mouse_click(self, pos):
        """
        Handle mouse clicks on this screen.

        Args:
            pos (tuple): The (x, y) position of the mouse click
        """
        pass

    @abstractmethod
    def handle_key_press(self, event):
        """
        Handle key presses on this screen.

        Args:
            event (pygame.event.Event): The key press event
        """
        pass
