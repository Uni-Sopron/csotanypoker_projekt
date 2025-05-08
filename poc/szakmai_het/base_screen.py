import os
import pygame
from abc import ABC, abstractmethod

from colors_and_sizes import FONT_SMALL


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

    def draw_text(self, text, color, x, y, centered=False, font=None):
        if font is None:
            font = pygame.font.Font(None, FONT_SMALL)

        text_surface = font.render(text, True, color)
        if centered:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        self.client.window.blit(text_surface, text_rect)

    def load_image(self, name, scale_ratio=None, size=None, logo=False):
        if logo:
            utvonal = os.path.join("kepek", f"{name}_logo.png")
        else:
            utvonal = os.path.join("kepek", f"{name}.png")

        image = pygame.image.load(utvonal).convert_alpha()

        if scale_ratio is not None:
            eredeti_meret = image.get_size()
            size = (
                int(eredeti_meret[0] * scale_ratio),
                int(eredeti_meret[1] * scale_ratio),
            )

        if size:
            image = pygame.transform.scale(image, size)

        return image

    def draw_image(self, image, x, y, size=None, centered=False):
        if size:
            image = pygame.transform.scale(image, size)
        rect = image.get_rect()
        if centered:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.client.window.blit(image, rect)
