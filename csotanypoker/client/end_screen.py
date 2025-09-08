import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    DARK_GREEN,
    LIGHT_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    RED,
    WHITE,
)
from csotanypoker.client.drawing_helpers import (
    _draw_rounded_rect,
    draw_button,
    draw_text,
    load_background,
)
import time


class EndScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client = client
        self.leave_button = pygame.Rect(
            self.client.width // 2 + 100, self.client.height // 2 + 200, 200, 75
        )
        self.rematch_button = pygame.Rect(
            self.client.width // 2 - 100, self.client.height // 2 + 200, 200, 75
        )
        self.auto_leave_timer = 30
        self.start_time = time.time()
        self.hovered_elements = set()
        self.pressed_elements = set()
        self.auto_leave_triggered = False

    def _update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered_elements.clear()
        if not mouse_pressed:
            self.pressed_elements.clear()

        if self.leave_button.collidepoint(mouse_pos):
            self.hovered_elements.add("leave")
            if mouse_pressed:
                self.pressed_elements.add("leave")

        if self.rematch_button.collidepoint(mouse_pos):
            self.hovered_elements.add("rematch")
            if mouse_pressed:
                self.pressed_elements.add("rematch")

    def draw_leave_button(self):
        draw_button(
            surface=self.client.window,
            rect=self.leave_button,
            text="Szoba elhagyása",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=5,
            is_hovered="leave" in self.hovered_elements,
            is_pressed="leave" in self.pressed_elements,
            hover_color=MIDDLE_GREEN_TRANSPARENT_70,
            pressed_color=LIGHT_GREEN,
        )

    def draw(self) -> None:
        load_background(self.client.width, self.client.height, self.client.window)
        self.rematch_button = pygame.Rect(
            self.client.width // 2 - 100 - 200, self.client.height // 2 + 200, 200, 75
        )
        self.leave_button = pygame.Rect(
            self.client.width // 2 + 100, self.client.height // 2 + 200, 200, 75
        )

        self.draw_leave_button()
        self.draw_rematch_button()
        draw_text(
            self.client.window,
            "Játék vége",
            DARK_GREEN,
            self.client.width // 2,
            20,
            centered=True,
            font="bold",
            font_size=40,
        )

        draw_text(
            self.client.window,
            self.client.game_over_message,
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 4,
            centered=True,
            font="bold",
            font_size=60,
        )
        if self.client.losing_player_name:
            draw_text(
                self.client.window,
                f"{self.client.losing_player_name} vesztett",
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 3,
                centered=True,
                font="regular",
                font_size=50,
            )

        draw_text(
            self.client.window,
            "Visszavágóra szavaztak:",
            DARK_GREEN,
            100,
            self.client.height // 2,
            centered=False,
            font="regular",
            font_size=30,
        )
        print("szavazok:", self.client.game_state.voters)
        if self.client.game_state.voters != []:
            for i, voter in enumerate(self.client.game_state.voters):
                voters_rect = pygame.Rect(
                    200 + (i * 210), self.client.height // 1.7, 200, 50
                )
                _draw_rounded_rect(
                    self.client.window, MIDDLE_GREEN_TRANSPARENT_70, voters_rect
                )

                draw_text(
                    self.client.window,
                    voter,
                    DARK_GREEN,
                    voters_rect.x + 100,
                    voters_rect.y + 25,
                    centered=True,
                    font="regular",
                    font_size=30,
                )

        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.auto_leave_timer - elapsed_time)

        if remaining_time > 0:
            draw_text(
                self.client.window,
                f"Automatikus kilépés: {int(remaining_time)}s",
                RED,
                self.client.width - 150,
                30,
                centered=True,
            )
        if remaining_time <= 0 and not self.auto_leave_triggered:
            self.auto_leave_triggered = True
            self.auto_leave()

    def draw_rematch_button(self):
        draw_button(
            surface=self.client.window,
            rect=self.rematch_button,
            text="Visszavágó",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=5,
            is_hovered="rematch" in self.hovered_elements,
            is_pressed="rematch" in self.pressed_elements,
            hover_color=MIDDLE_GREEN_TRANSPARENT_70,
            pressed_color=LIGHT_GREEN,
        )

    def auto_leave(self) -> None:
        self.client.network.all_players_leave_room(self.client.room_id)

    def handle_mouse_click(self, pos):
        if self.leave_button.collidepoint(pos):
            self.client.network.all_players_leave_room(self.client.room_id)

            pass
        elif self.rematch_button.collidepoint(pos):
            self.client.network.vote_rematch(
                self.client.room_id, self.client.user.username
            )

    def handle_key_press(self, event):
        pass
