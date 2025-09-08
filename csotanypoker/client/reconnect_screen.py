import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    BLACK,
    DARK_GREEN,
    FONT_MEDIUM,
    GRAY,
    LIGHT_GREEN,
    MIDDLE_GREEN,
    WHITE,
)
from csotanypoker.client.drawing_helpers import draw_button, draw_text, load_background


class ReconnectScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

        self.hovered_elements = set()
        self.pressed_elements = set()

        self.font_medium = pygame.font.Font(None, FONT_MEDIUM)
        self.reconnect_button = pygame.Rect(
            self.client.width // 2 - 250, self.client.height // 2, 240, 95
        )
        self.leave_button = pygame.Rect(
            self.client.width // 2 + 30,
            self.client.height // 2.4 + 50 + 50 + 100,
            240,
            95,
        )
        self.logout_button = pygame.Rect(20, self.client.height - 105, 220, 85)

    def draw(self):
        self.reconnect_button = pygame.Rect(
            self.client.width // 2 - 250,
            self.client.height // 2.4 + 50 + 50 + 100,
            240,
            95,
        )
        self.leave_button = pygame.Rect(
            self.client.width // 2 + 30,
            self.client.height // 2.4 + 50 + 50 + 100,
            240,
            95,
        )
        self.logout_button = pygame.Rect(20, self.client.height - 105, 220, 85)
        load_background(self.client.width, self.client.height, self.client.window)

        draw_text(
            self.client.window,
            "Újracsatlakozás",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 7,
            centered=True,
            font="regular",
            font_size=70,
        )
        for room in self.client.room_list:
            if room.room_id == self.client.previous_room_id:
                previous_room = room
                break
        if previous_room:
            draw_text(
                self.client.window,
                f"Jelenlegi szobád: {previous_room.name}",
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 2.4,
                centered=True,
                font="thin",
                font_size=40,
            )

            players_text = f"Aktuális játékosszám: {previous_room.player_count}/{previous_room.max_player_count}"
            draw_text(
                self.client.window,
                players_text,
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 2.4 + 50,
                centered=True,
                font="thin",
                font_size=40,
            )

        if self.client.message:
            draw_text(
                self.client.window,
                self.client.message,
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 2.4 + 50 + 50,
                centered=True,
                font="thin",
                font_size=40,
            )

        draw_button(
            surface=self.client.window,
            rect=self.reconnect_button,
            text="Újracsatlakozás",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered="reconnect" in self.hovered_elements,
            is_pressed="reconnect" in self.pressed_elements,
            hover_color=DARK_GREEN,
            pressed_color=LIGHT_GREEN,
        )

        draw_button(
            surface=self.client.window,
            rect=self.leave_button,
            text="Szoba elhagyása",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered="leave" in self.hovered_elements,
            is_pressed="leave" in self.pressed_elements,
            hover_color=DARK_GREEN,
            pressed_color=LIGHT_GREEN,
        )
        pygame.draw.rect(self.client.window, GRAY, self.logout_button)
        draw_text(
            self.client.window,
            "Kijelentkezés",
            BLACK,
            self.logout_button.centerx,
            self.logout_button.centery,
            centered=True,
            font=self.font_medium,
        )

        mouse_pos = pygame.mouse.get_pos()
        self.reconnect_hover = self.reconnect_button.collidepoint(mouse_pos)
        self._draw_logout_button()

    def handle_mouse_click(self, pos):
        for room in self.client.room_list:
            if room.room_id == self.client.previous_room_id:
                previous_room = room
                break
        if self.reconnect_button.collidepoint(pos):
            if self.client.previous_room_id:
                room_id = self.client.previous_room_id
                if room_id:
                    print("Újracsatlakozás a szobához:", room_id)
                    self.client.network.rejoin_waiting_room()
       
        elif self.leave_button.collidepoint(pos):
            if self.client.message == "A játék elkezdődött":
                
                self.client.network.all_players_leave_room(self.client.room_id)
            else:
                
                self.client.network.leave_room()
            self.client.screen = "rooms_screen"
        elif self.logout_button.collidepoint(pos):
            self.client.network.logout()

    def handle_key_press(self, event):
        pass

    def _draw_logout_button(self):
        """Kijelentkezés gomb rajzolása"""
        draw_button(
            surface=self.client.window,
            rect=self.logout_button,
            text="Kijelentkezés",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered="logout" in self.hovered_elements,
            is_pressed="logout" in self.pressed_elements,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )
