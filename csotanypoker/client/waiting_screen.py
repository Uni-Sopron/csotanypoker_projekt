import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    GREEN,
    LIGHT_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    LIGHTER_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_90,
    RED,
    TITLE_FONT_SIZE,
    WHITE,
    DARK_GREEN,
    JATEKSZABALY,
)
from csotanypoker.client.drawing_helpers import (
    draw_button,
    draw_text,
    load_background,
    draw_image,
    load_image,
    create_logout_button_rect,
    create_rules_button_rect,
    draw_logout_button,
    draw_rules_button,
    draw_rules_popup,
    check_logout_button_interaction,
    check_rules_button_interaction,
    handle_logout_button_click,
    this_is_ai_name,
    wrap_text,
)


class WaitingScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.logout_button = create_logout_button_rect(self.client.height)
        self.leave_button = pygame.Rect(
            self.client.width // 2 - 140, self.client.height - 150, 350, 90
        )
        self.rules_button = create_rules_button_rect(
            self.client.width, self.client.height
        )
        self.plus_button = pygame.Rect(0, 0, 40, 40)
        self.ai_player_button = pygame.Rect(0, 0, 400, 55)
        self.show_rules = False
        self.margin = 30
        self.hovered_elements = set()
        self.pressed_elements = set()

    def _update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered_elements.clear()
        if not mouse_pressed:
            self.pressed_elements.clear()

        is_logout_hovered, is_logout_pressed = check_logout_button_interaction(
            mouse_pos, mouse_pressed, self.logout_button
        )
        if is_logout_hovered:
            self.hovered_elements.add("logout")
        if is_logout_pressed:
            self.pressed_elements.add("logout")

        if self.leave_button.collidepoint(mouse_pos):
            self.hovered_elements.add("leave")
            if mouse_pressed:
                self.pressed_elements.add("leave")

        self.show_rules = check_rules_button_interaction(mouse_pos, self.rules_button)

        if hasattr(self, "ai_player_button") and self.ai_player_button.collidepoint(
            mouse_pos
        ):
            self.hovered_elements.add("ai_player")
            if mouse_pressed:
                self.pressed_elements.add("ai_player")

    def draw(self) -> None:
        """
        Draw the waiting screen.
        """

        self.logout_button = create_logout_button_rect(self.client.height)
        self.leave_button = pygame.Rect(
            self.client.width // 2 - 140, self.client.height - 150, 350, 90
        )
        self.rules_button = create_rules_button_rect(
            self.client.width, self.client.height
        )

        self._update_button_states()

        load_background(self.client.width, self.client.height, self.client.window)

        if self.client.selected_room is not None:
            wrapped_text = wrap_text(
                f"{self.client.room_name} {self.client.selected_room.player_count}/{self.client.selected_room.max_player_count}",
                max_length=20,
            )
            for i, line in enumerate(wrapped_text):
                draw_text(
                    self.client.window,
                    line,
                    DARK_GREEN,
                    self.client.width // 2,
                    self.margin + (i * 30),
                    True,
                    "bold",
                    TITLE_FONT_SIZE,
                )
            draw_text(
                self.client.window,
                f"ID:{self.client.selected_room.room_id}",
                DARK_GREEN,
                250,
                50,
                centered=True,
                font="thin",
                font_size=25,
            )

        draw_text(
            self.client.window,
            f"Várakozás a többi játékosra.",
            DARK_GREEN,
            self.client.width // 2,
            self.margin + 50,
            True,
            "thin",
            30,
        )

        start_y = self.client.height // 5
        start_x = 200

        for i, player in enumerate(self.client.users):
            dot_color = GREEN if player.is_active else RED
            pygame.draw.circle(
                self.client.window,
                dot_color,
                (start_x - 70, start_y + 30),
                17,
            )

            draw_text(
                self.client.window,
                this_is_ai_name(player.username),
                DARK_GREEN,
                start_x,
                start_y,
                font_size=55,
            )
            start_y += 70
            if (
                i == len(self.client.users) - 1
                and len(self.client.users) < self.client.selected_room.max_player_count
            ):
                self.plus_button = pygame.Rect(start_x - 70, start_y + 7, 40, 40)
                self.ai_player_button = pygame.Rect(start_x - 90, start_y, 400, 55)

        if self.client.message and self.client.message_display_time > 0:
            message_lines = wrap_text(self.client.message, 30)

            for i, line in enumerate(message_lines):
                draw_text(
                    self.client.window,
                    line,
                    RED,
                    self.client.width - 200,
                    50 + (i * 30),
                    centered=True,
                    font="thin",
                    font_size=25,
                )

            self.client.message_display_time -= 1

        draw_button(
            surface=self.client.window,
            rect=self.leave_button,
            text="Szoba elhagyása",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=35,
            font_type="bold",
            border_width=5,
            is_hovered="leave" in self.hovered_elements,
            is_pressed="leave" in self.pressed_elements,
            hover_color=MIDDLE_GREEN_TRANSPARENT_90,
            pressed_color=LIGHT_GREEN,
        )
        draw_logout_button(
            self.client.window,
            self.logout_button,
            is_hovered="logout" in self.hovered_elements,
            is_pressed="logout" in self.pressed_elements,
        )
        draw_rules_button(self.client.window, self.rules_button)

        if (
            self.client.selected_room
            and len(self.client.users) < self.client.selected_room.max_player_count
        ):
            draw_button(
                surface=self.client.window,
                rect=self.ai_player_button,
                text="AI játékos hozzáadása",
                text_color=DARK_GREEN,
                background_color=LIGHT_GREEN_TRANSPARENT,
                border_color=MIDDLE_GREEN,
                font_size=25,
                font_type="thin",
                border_width=3,
                is_hovered="ai_player" in self.hovered_elements,
                is_pressed="ai_player" in self.pressed_elements,
                hover_color=MIDDLE_GREEN_TRANSPARENT_90,
                pressed_color=LIGHTER_GREEN,
            )
            plus = load_image(
                "plus", "button", size=(self.plus_button.width, self.plus_button.height)
            )
            draw_image(self.client.window, plus, self.plus_button.x, self.plus_button.y)

        if self.show_rules:
            draw_rules_popup(
                self.client.window,
                self.client.width,
                self.client.height,
                JATEKSZABALY[
                    "2" if self.client.selected_room.max_player_count == 2 else "3-6"
                ],
                self.client.selected_room.max_player_count,
            )

    def handle_mouse_click(self, pos):
        if self.leave_button.collidepoint(pos):
            print("Leaving room")
            self.client.network.leave_room()
            return True
        elif handle_logout_button_click(pos, self.logout_button, self.client.network):
            return True
        elif hasattr(self, "ai_player_button") and self.ai_player_button.collidepoint(
            pos
        ):
            if len(self.client.users) < self.client.selected_room.max_player_count:
                print("AI hozzáadás")
                self.client.network.add_ai_player()
                return True
        elif hasattr(self, "plus_button") and self.plus_button.collidepoint(pos):
            if len(self.client.users) < self.client.selected_room.max_player_count:
                print("AI hozzáadás")

                return True
        return False

    def handle_mouse_motion(self, pos):
        pass

    def handle_key_press(self, key):
        pass
