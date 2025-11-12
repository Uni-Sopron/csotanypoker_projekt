import pygame
from csotanypoker.client.drawing_helpers.text_manager import handle_continuous_arrow_keys, handle_continuous_backspace, handle_input_text_event, handle_mouse_click_in_input
from csotanypoker.client.screens.base_screen import BaseScreen
from csotanypoker.client.drawing_helpers.constans import (
    RED,
    WHITE,
    DARK_GREEN,
    LIGHT_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    MIDDLE_GREEN_TRANSPARENT_90,
    MIDDLE_GREEN,
)
from csotanypoker.client.drawing_helpers.drawing_helpers import (
    draw_text,
    draw_input_box,
    draw_button,
    get_input_state,
)
from csotanypoker.client.drawing_helpers.image_manager import load_background
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

        self.credits_button_hovered = False
        self.credits_button_pressed = False

        self.input_padding = 15
        self.cursor_blink_interval = 400
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()

        self.username_cursor_pos = 0
        self.password_cursor_pos = 0
        self.username_box = None
        self.password_box = None
        self.login_button = None
        self.register_button = None
        self.credits_button = None

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

        credits_width = 180
        credits_height = 50
        credits_y = self.register_button.bottom + 20
        self.credits_button = pygame.Rect(
            center_x - credits_width // 2,
            credits_y,
            credits_width,
            credits_height,
        )

    def _update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.login_button_hovered = (
            self.login_button.collidepoint(mouse_pos) if self.login_button else False
        )
        self.register_button_hovered = (
            self.register_button.collidepoint(mouse_pos)
            if self.register_button
            else False
        )
        self.credits_button_hovered = (
            self.credits_button.collidepoint(mouse_pos)
            if self.credits_button
            else False
        )

        self.login_button_pressed = self.login_button_hovered and mouse_pressed
        self.register_button_pressed = self.register_button_hovered and mouse_pressed
        self.credits_button_pressed = self.credits_button_hovered and mouse_pressed

    def _draw_error_message(self):
        if self.client.message and self.client.message_display_time > 0:
            error_y = (
                self.credits_button.bottom + 80
                if self.credits_button
                else self.client.height - 100
            )
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

    def update_continuous_input(self):
        """Update continuous input - hívás minden frame-ben"""
        if not self.active_field:
            return


        state = get_input_state(self.active_field)
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        if self.active_field == "username":
            new_text, new_cursor, changed = handle_continuous_backspace(
                state, self.username_text, current_time
            )
            if changed:
                self.username_text = new_text
        elif self.active_field == "password":
            new_text, new_cursor, changed = handle_continuous_backspace(
                state, self.password_text, current_time
            )
            if changed:
                self.password_text = new_text

        text_len = len(self.username_text) if self.active_field == "username" else len(self.password_text)
        new_cursor, changed = handle_continuous_arrow_keys(state, keys, current_time, text_len)
        if changed:
            state.cursor_pos = new_cursor

    def draw(self):
        self._calculate_ui_rects()
        self._update_button_states()
        self._update_cursor_state()

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
            input_id="username",
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
            input_id="password",
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

        draw_button(
            surface=self.client.window,
            rect=self.credits_button,
            text="Készítők",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=25,
            font_type="bold",
            border_width=5,
            is_hovered=self.credits_button_hovered,
            is_pressed=self.credits_button_pressed,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

        self._draw_error_message()

    def handle_mouse_click(self, pos):
        if self.username_box and self.username_box.collidepoint(pos):
            self.active_field = "username"
            state = get_input_state("username")
            cursor_pos = handle_mouse_click_in_input(
                pos,
                self.username_box,
                self.username_text,
                27,
                self.input_padding,
                False,
            )
            if cursor_pos is not None:
                state.cursor_pos = cursor_pos
            return True
        elif self.password_box and self.password_box.collidepoint(pos):
            self.active_field = "password"
            state = get_input_state("password")
            cursor_pos = handle_mouse_click_in_input(
                pos, self.password_box, self.password_text, 27, self.input_padding, True
            )
            if cursor_pos is not None:
                state.cursor_pos = cursor_pos
            return True
        elif self.login_button and self.login_button.collidepoint(pos):
            self.handle_login()
            return True
        elif self.register_button and self.register_button.collidepoint(pos):
            self.handle_register()
            return True
        elif self.credits_button and self.credits_button.collidepoint(pos):
            self.client.credits_menu.show(self.client.width, self.client.height)
            return True
        else:
            self.active_field = None
            return False

    def handle_key_release(self, event):
        """Handle key release events"""
        if not self.active_field:
            return
            
        state = get_input_state(self.active_field)
        
        if event.key == pygame.K_BACKSPACE:
            state.backspace_held = False
        elif event.key == pygame.K_LEFT:
            state.left_held = False
        elif event.key == pygame.K_RIGHT:
            state.right_held = False

    def handle_key_press(self, event):
        if not self.active_field:
            return

        if event.key == pygame.K_RETURN:
            self.handle_login()
            return
        elif event.key == pygame.K_TAB:
            self.active_field = (
                "password" if self.active_field == "username" else "username"
            )
            return

   

        state = get_input_state(self.active_field)

        if self.active_field == "username":
            rect = self.username_box
            new_text, new_cursor, handled = handle_input_text_event(
                event,
                self.username_text,
                state.cursor_pos,
                10,
                rect,
                27,
                self.input_padding,
            )
            if handled:
                self.username_text = new_text
                state.cursor_pos = new_cursor

                if event.key == pygame.K_BACKSPACE:
                    state.backspace_held = True
                    state.last_backspace_time = pygame.time.get_ticks()
                elif event.key == pygame.K_LEFT:
                    state.left_held = True
                    state.last_arrow_time = pygame.time.get_ticks()
                elif event.key == pygame.K_RIGHT:
                    state.right_held = True
                    state.last_arrow_time = pygame.time.get_ticks()

        elif self.active_field == "password":
            rect = self.password_box
            new_text, new_cursor, handled = handle_input_text_event(
                event,
                self.password_text,
                state.cursor_pos,
                20,
                rect,
                27,
                self.input_padding,
                True,
            )
            if handled:
                self.password_text = new_text
                state.cursor_pos = new_cursor

                if event.key == pygame.K_BACKSPACE:
                    state.backspace_held = True
                    state.last_backspace_time = pygame.time.get_ticks()
                elif event.key == pygame.K_LEFT:
                    state.left_held = True
                    state.last_arrow_time = pygame.time.get_ticks()
                elif event.key == pygame.K_RIGHT:
                    state.right_held = True
                    state.last_arrow_time = pygame.time.get_ticks()

    def handle_login(self):
        if not self.username_text.strip():
            self.set_error("A felhasználónév nem lehet üres!")
            return

        if not self.password_text.strip():
            self.set_error("A jelszó nem lehet üres!")
            return
        username = self.username_text.strip().lower()
        ai_names_lower = [name.lower() for name in AI_NAMES]

        if any(ai_name in username for ai_name in ai_names_lower):
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
        username = self.username_text.strip().lower()
        ai_names_lower = [name.lower() for name in AI_NAMES]

        if any(ai_name in username for ai_name in ai_names_lower):
            self.set_error("Az AI nevek nem használhatók felhasználónévként!")
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
