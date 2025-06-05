import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (BLACK, BLUE, FONT_SMALL, GRAY, RED,
                                          WHITE)
from csotanypoker.client.drawing_helpers import draw_text


class LoginScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

        self.username_box = pygame.Rect(250, 200, 300, 40)
        self.password_box = pygame.Rect(250, 270, 300, 40)

        self.login_button = pygame.Rect(200, 350, 180, 50)
        self.register_button = pygame.Rect(420, 350, 180, 50)

      
        self.active_field = None  

        self.username_text = ""
        self.password_text = ""

        self.login_button_color = GRAY
        self.register_button_color = GRAY
        self.input_border_color = GRAY
        self.active_input_color = BLUE

    def draw(self):
        self.client.window.fill(WHITE)

        draw_text(self.client.window, "Csotány Póker", BLACK, 400, 100, True)
        draw_text(self.client.window, "Felhasználónév:", BLACK, 250, 180, False)
        draw_text(self.client.window, "Jelszó:", BLACK, 250, 250, False)

        username_border_color = (
            self.active_input_color
            if self.active_field == "username"
            else self.input_border_color
        )
        password_border_color = (
            self.active_input_color
            if self.active_field == "password"
            else self.input_border_color
        )

        pygame.draw.rect(self.client.window, WHITE, self.username_box)
        pygame.draw.rect(
            self.client.window, username_border_color, self.username_box, 2
        )

        pygame.draw.rect(self.client.window, WHITE, self.password_box)
        pygame.draw.rect(
            self.client.window, password_border_color, self.password_box, 2
        )

        font = pygame.font.Font(None, FONT_SMALL)

        username_surface = font.render(self.username_text, True, BLACK)
        self.client.window.blit(
            username_surface, (self.username_box.x + 5, self.username_box.y + 5)
        )

        password_display = "*" * len(self.password_text)
        password_surface = font.render(password_display, True, BLACK)
        self.client.window.blit(
            password_surface, (self.password_box.x + 5, self.password_box.y + 5)
        )

        pygame.draw.rect(self.client.window, self.login_button_color, self.login_button)
        pygame.draw.rect(
            self.client.window, self.register_button_color, self.register_button
        )

        draw_text(
            self.client.window,
            "Bejelentkezés",
            BLACK,
            self.login_button.centerx,
            self.login_button.centery,
            True,
        )
        draw_text(
            self.client.window,
            "Regisztráció",
            BLACK,
            self.register_button.centerx,
            self.register_button.centery,
            True,
        )

        if self.client.login_error and self.client.error_display_time > 0:
            draw_text(self.client.window, self.client.login_error, RED, 400, 420, True)

    def handle_mouse_click(self, pos):

        if self.username_box.collidepoint(pos):
            self.active_field = "username"
            return True
        elif self.password_box.collidepoint(pos):
            self.active_field = "password"
            return True
        elif self.login_button.collidepoint(pos):
            self.handle_login()
            return False
        elif self.register_button.collidepoint(pos):
            self.handle_register()
            return False
        else:
            self.active_field = None
            return False

    def handle_key_press(self, event):
        if not self.active_field:
            return

        if event.key == pygame.K_RETURN:  
            self.handle_login()
        elif event.key == pygame.K_TAB: 
            if self.active_field == "username":
                self.active_field = "password"
            else:
                self.active_field = "username"
        elif event.key == pygame.K_BACKSPACE:  
            if self.active_field == "username":
                self.username_text = self.username_text[:-1]
            elif self.active_field == "password":
                self.password_text = self.password_text[:-1]
        else:
         
            if len(event.unicode) == 1 and event.unicode.isprintable():
                if self.active_field == "username":
                    if len(self.username_text) < 20:  
                        self.username_text += event.unicode
                elif self.active_field == "password":
                    if len(self.password_text) < 30:  
                        self.password_text += event.unicode

    def handle_login(self):
        if not self.username_text.strip():
            self.set_error("A felhasználónév nem lehet üres!")
            return

        if not self.password_text.strip():
            self.set_error("A jelszó nem lehet üres!")
            return

        self.client.network.login(self.username_text.strip(), self.password_text)

    def handle_register(self):
        if not self.username_text.strip():
            self.set_error("A felhasználónév nem lehet üres!")
            return

        if not self.password_text.strip():
            self.set_error("A jelszó nem lehet üres!")
            return

        self.client.network.register(self.username_text.strip(), self.password_text)

    def set_error(self, message):
        self.client.login_error = message
        self.client.error_display_time = (
            pygame.time.get_ticks() + 3000
        ) 

    def clear_error(self):
        self.client.login_error = ""
        self.client.error_display_time = 0

    def clear_fields(self):
        self.username_text = ""
        self.password_text = ""
        self.active_field = None
