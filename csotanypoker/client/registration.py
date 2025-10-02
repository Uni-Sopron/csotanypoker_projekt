import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    RED,
    WHITE,
    DARK_GREEN,
    LIGHT_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    MIDDLE_GREEN_TRANSPARENT_90,
    MIDDLE_GREEN,
)
from csotanypoker.client.drawing_helpers import (
    draw_text,
    load_background,
    draw_input_box,
    validate_text_input,
    draw_button,
    this_is_ai_name,
)
from csotanypoker.models.user import AI_NAMES


class LoginScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)
        self.active_field = None
        self.username_text = ""
        self.password_text = ""

        self.login_button_color = MIDDLE_GREEN
        self.register_button_color = MIDDLE_GREEN
        self.input_border_color = MIDDLE_GREEN_TRANSPARENT_90
        self.active_input_color = MIDDLE_GREEN_TRANSPARENT_70

        self.login_button_hovered = False
        self.register_button_hovered = False
        self.login_button_pressed = False
        self.register_button_pressed = False

        self.input_padding = 15
        self.cursor_blink_interval = 400

    def _update_cursor_state(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > self.cursor_blink_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time

    def _calculate_ui_rects(self):
        center_x = self.client.width // 2
        quarter_height = self.client.height // 4

        self.username_box = pygame.Rect(center_x - 250, quarter_height, 500, 75)
        self.password_box = pygame.Rect(center_x - 250, quarter_height + 85, 500, 75)
        self.login_button = pygame.Rect(
            center_x - 250, self.client.height // 2, 220, 85
        )
        self.register_button = pygame.Rect(
            center_x + 30, self.client.height // 2, 220, 85
        )

    def _update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.login_button_hovered = self.login_button.collidepoint(mouse_pos)
        self.register_button_hovered = self.register_button.collidepoint(mouse_pos)

        self.login_button_pressed = self.login_button_hovered and mouse_pressed
        self.register_button_pressed = self.register_button_hovered and mouse_pressed

    def _draw_error_message(self):
        if self.client.message and self.client.message_display_time > 0:
            error_y = self.register_button.bottom + 150
            draw_text(
                self.client.window,
                self.client.message,
                RED,
                self.client.width // 2,
                error_y,
                True,
                font="bold",
                font_size=40,
            )
            self.client.message_display_time -= 1

    def draw(self):
        self._calculate_ui_rects()
        self._update_button_states()

        load_background(
            self.client.width, self.client.height, self.client.window, type="background"
        )

        draw_text(
            self.client.window,
            "Csótány Póker",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 6,
            True,
            "Bold",
            85,
        )

        draw_input_box(
            surface=self.client.window,
            rect=self.username_box,
            text=self.username_text,
            is_active=(self.active_field == "username"),
            is_password=False,
            background_color=self.input_border_color,
            active_background_color=self.active_input_color,
            border_color=None,
            text_color=WHITE,
            cursor_color=WHITE,
            font_size=27,
            padding=self.input_padding,
            placeholder="Felhasználónév",
            placeholder_color=WHITE,
        )

        draw_input_box(
            surface=self.client.window,
            rect=self.password_box,
            text=self.password_text,
            is_active=(self.active_field == "password"),
            is_password=True,
            background_color=self.input_border_color,
            active_background_color=self.active_input_color,
            border_color=None,
            text_color=WHITE,
            cursor_color=WHITE,
            font_size=27,
            padding=self.input_padding,
            placeholder="Jelszó",
            placeholder_color=WHITE,
        )

        draw_button(
            surface=self.client.window,
            rect=self.login_button,
            text="Bejelentkezés",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered=self.login_button_hovered,
            is_pressed=self.login_button_pressed,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

        draw_button(
            surface=self.client.window,
            rect=self.register_button,
            text="Regisztráció",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered=self.register_button_hovered,
            is_pressed=self.register_button_pressed,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

        self._draw_error_message()

    def handle_mouse_click(self, pos):
        if self.username_box.collidepoint(pos):
            self.active_field = "username"
            return True 
        elif self.password_box.collidepoint(pos):
            self.active_field = "password"
            return True 
        elif self.login_button.collidepoint(pos):
            self.handle_login()
            return True
        elif self.register_button.collidepoint(pos):
            self.handle_register()
            return True
        else:
            self.active_field = None
            return False  

    def handle_key_press(self, event):
        if not self.active_field:
            return

        if event.key == pygame.K_RETURN:
            self.handle_login()
        elif event.key == pygame.K_TAB:
            self.active_field = (
                "password" if self.active_field == "username" else "username"
            )
        elif event.key == pygame.K_BACKSPACE:
            if self.active_field == "username":
                self.username_text = self.username_text[:-1]
            elif self.active_field == "password":
                self.password_text = self.password_text[:-1]
        else:
            if len(event.unicode) == 1 and event.unicode.isprintable():
                if self.active_field == "username":
                    if validate_text_input(
                        self.username_text,
                        event.unicode,
                        self.username_box,
                        13,
                        False,
                        font_size=27,
                        padding=self.input_padding,
                    ):
                        self.username_text += event.unicode
                elif self.active_field == "password":
                    if validate_text_input(
                        self.password_text,
                        event.unicode,
                        self.password_box,
                        20,
                        True,
                        font_size=27,
                        padding=self.input_padding,
                    ):
                        self.password_text += event.unicode

    def handle_login(self):
        if not self.username_text.strip():
            self.set_error("A felhasználónév nem lehet üres!")
            return

        if not self.password_text.strip():
            self.set_error("A jelszó nem lehet üres!")
            return
        if this_is_ai_name(self.username_text.strip()) in AI_NAMES:
            self.set_error("Az AI nevek nem használhatók felhasználónévként!")
            return

        self.client.network.login(self.username_text.strip(), self.password_text)

    def handle_register(self):
        if not self.username_text.strip():
            self.set_error("A felhasználónév nem lehet üres!")
            return
        elif not self.password_text.strip():
            self.set_error("A jelszó nem lehet üres!")
            return

        self.client.network.register(self.username_text.strip(), self.password_text)

    def set_error(self, message):
        self.client.message = message
        self.client.message_display_time = 30

    def clear_error(self):
        self.client.message = ""
        self.client.message_display_time = 0

    def clear_fields(self):
        self.username_text = ""
        self.password_text = ""
        self.active_field = None
