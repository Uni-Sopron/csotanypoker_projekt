import pygame
import time

from csotanypoker.client.screens.base_screen import BaseScreen
from csotanypoker.client.drawing_helpers.constans import (
    DARK_GREEN,
    LIGHT_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    RED,
    WHITE,
)

from csotanypoker.client.drawing_helpers.drawing_helpers import (
    _draw_rounded_rect,
    draw_button,
    draw_text,
    create_volume_button_rect,
    draw_sound_volume,
)
from csotanypoker.client.drawing_helpers.image_manager import load_background
from csotanypoker.models.user import this_is_ai_name

class EndScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client = client
        self.auto_leave_timer = 30
        self.start_time = time.time()
        self.hovered_elements = set()
        self.pressed_elements = set()
        self.auto_leave_triggered = False

        self._init_buttons()

    def _init_buttons(self):
        """Gombok pozícióinak beállítása"""
        center_x = self.client.width // 2
        button_y = self.client.height // 2 + 200

        self.leave_button = pygame.Rect(center_x + 100, button_y, 200, 75)
        self.rematch_button = pygame.Rect(center_x - 300, button_y, 200, 75)

    def _update_button_states(self):
        """Gomb állapotok frissítése"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered_elements.clear()
        if not mouse_pressed:
            self.pressed_elements.clear()

        for button_name, button_rect in [
            ("leave", self.leave_button),
            ("rematch", self.rematch_button),
        ]:
            if button_rect.collidepoint(mouse_pos):
                self.hovered_elements.add(button_name)
                if mouse_pressed:
                    self.pressed_elements.add(button_name)

    def _draw_button(self, button_type, rect, text):
        """Általános gomb rajzoló"""
        draw_button(
            surface=self.client.window,
            rect=rect,
            text=text,
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=5,
            is_hovered=button_type in self.hovered_elements,
            is_pressed=button_type in self.pressed_elements,
            hover_color=MIDDLE_GREEN_TRANSPARENT_70,
            pressed_color=LIGHT_GREEN,
        )

    def _draw_voters(self):
        """Szavazók megjelenítése"""
        if not self.client.game_state.voters:
            return

        for i, voter in enumerate(self.client.game_state.voters):
            voter_rect = pygame.Rect(
                200 + (i * 210), self.client.height // 1.7, 200, 50
            )
            _draw_rounded_rect(
                self.client.window, MIDDLE_GREEN_TRANSPARENT_70, voter_rect
            )

            draw_text(
                self.client.window,
                this_is_ai_name(voter),
                DARK_GREEN,
                voter_rect.centerx,
                voter_rect.centery,
                centered=True,
                font="regular",
                font_size=30,
            )

    def _draw_timer(self):
        """Visszaszámlálás megjelenítése"""
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
        elif not self.auto_leave_triggered:
            self.auto_leave_triggered = True
            self.auto_leave()

    def draw(self) -> None:
        load_background(self.client.width, self.client.height, self.client.window)

        self._init_buttons()
        self._update_button_states()

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
                f"{this_is_ai_name(self.client.losing_player_name)} vesztett",
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 3,
                centered=True,
                font="regular",
                font_size=50,
            )

        self._draw_button("leave", self.leave_button, "Szoba elhagyása")
        self._draw_button("rematch", self.rematch_button, "Visszavágó")

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
        self._draw_voters()
        self._draw_timer()
        volume_rect = create_volume_button_rect(
            self.client.width - 40, self.client.height - 40
        )
        draw_sound_volume(
            self.client.window,
            volume_rect.centerx,
            volume_rect.centery,
            "sound",
            self.client._music_manager.sound_effects_volume,
            self.client._music_manager.music_volume,
            center_button=True
        )

    def auto_leave(self) -> None:
        self.client.network.all_players_leave_room(self.client.selected_room.room_id)

    def handle_mouse_click(self, pos):

        if self.leave_button.collidepoint(pos):
            self.client.network.all_players_leave_room(
                self.client.selected_room.room_id
            )
            return True
        elif self.rematch_button.collidepoint(pos):
            self.client.network.vote_rematch(
                self.client.selected_room.room_id, self.client.user.username
            )
            return True

        volume_rect = create_volume_button_rect(
            self.client.width - 40, self.client.height - 40
        )
        if volume_rect.collidepoint(pos):
            return True

        return False 

    def handle_key_press(self, event):
        pass
