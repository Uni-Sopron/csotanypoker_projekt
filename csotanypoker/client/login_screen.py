import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import BLACK, FONT_SMALL, GRAY, RED, WHITE
from csotanypoker.client.drawing_helpers import draw_text


class LoginScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)
        self.input_box = pygame.Rect(250, 250, 300, 40)

    def draw(self):
        """Draw the login screen"""
        self.client.window.fill(WHITE)
        draw_text(
            self.client.window, "Add meg a felhasználóneved", BLACK, 400, 150, True
        )

        pygame.draw.rect(self.client.window, GRAY, self.input_box, 2)
        font: pygame.font.Font = pygame.font.Font(None, FONT_SMALL)
        # Draw the input text
        input_surface = font.render(self.client.input_text, True, BLACK)
        self.client.window.blit(
            input_surface,
            (self.input_box.x + 5, self.input_box.y + 5),
        )

        # Display error message if any
        if self.client.login_error and self.client.error_display_time > 0:
            draw_text(self.client.window, self.client.login_error, RED, 400, 320, True)

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on login screen"""
        self.client.input_active = self.input_box.collidepoint(pos)
        return self.client.input_active

    def handle_key_press(self, event):
        """Handle key presses on login screen"""
        if self.client.input_active:
            if event.key == pygame.K_RETURN:  # Enter key pressed
                if self.client.input_text:
                    self.client.network.login(self.client.input_text)
            elif event.key == pygame.K_BACKSPACE:  # Delete
                self.client.input_text = self.client.input_text[:-1]
            else:
                self.client.input_text += event.unicode
