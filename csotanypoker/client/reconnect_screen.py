import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import DARK_GREEN, LIGHT_GREEN, MIDDLE_GREEN, WHITE
from csotanypoker.client.drawing_helpers import draw_button, draw_text, load_background


class ReconnectScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)
        self.hovered_elements = set()
        self.pressed_elements = set()
        self._init_buttons()

    def _init_buttons(self):
        """Gombok pozícióinak beállítása"""
        center_x = self.client.width // 2
        button_y = self.client.height // 2.4 + 150

        self.reconnect_button = pygame.Rect(center_x - 250, button_y, 240, 95)
        self.leave_button = pygame.Rect(center_x + 30, button_y, 240, 95)
        self.logout_button = pygame.Rect(20, self.client.height - 105, 220, 85)

    def _update_button_states(self):
        """Gomb állapotok frissítése"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered_elements.clear()
        if not mouse_pressed:
            self.pressed_elements.clear()

        buttons = [
            ("reconnect", self.reconnect_button),
            ("leave", self.leave_button),
            ("logout", self.logout_button),
        ]

        for button_name, button_rect in buttons:
            if button_rect.collidepoint(mouse_pos):
                self.hovered_elements.add(button_name)
                if mouse_pressed:
                    self.pressed_elements.add(button_name)

    def _draw_button_with_state(self, button_type, rect, text, font_size=30):
        """Gomb rajzolása állapot alapján"""
        draw_button(
            surface=self.client.window,
            rect=rect,
            text=text,
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=DARK_GREEN,
            font_size=font_size,
            font_type="bold",
            border_width=5,
            is_hovered=button_type in self.hovered_elements,
            is_pressed=button_type in self.pressed_elements,
            hover_color=DARK_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def _draw_room_info(self):
        """Szoba információk megjelenítése"""
        if not self.client.previous_room:
            return

        center_x = self.client.width // 2
        base_y = self.client.height // 2.4

   
        draw_text(
            self.client.window,
            f"Jelenlegi szobád: {self.client.previous_room.name}",
            DARK_GREEN,
            center_x,
            base_y,
            centered=True,
            font="thin",
            font_size=40,
        )


        players_text = (
            f"Aktuális játékosszám: {self.client.previous_room.player_count}/"
            f"{self.client.previous_room.max_player_count}"
        )
        draw_text(
            self.client.window,
            players_text,
            DARK_GREEN,
            center_x,
            base_y + 50,
            centered=True,
            font="thin",
            font_size=40,
        )

    def draw(self):
 
        self._init_buttons()
        self._update_button_states()

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

      
        self._draw_room_info()

        if self.client.message:
            draw_text(
                self.client.window,
                self.client.message,
                DARK_GREEN,
                self.client.width // 2,
                self.client.height // 2.4 + 100,
                centered=True,
                font="thin",
                font_size=40,
            )


        self._draw_button_with_state(
            "reconnect", self.reconnect_button, "Újracsatlakozás"
        )
        self._draw_button_with_state("leave", self.leave_button, "Szoba elhagyása")
        self._draw_button_with_state("logout", self.logout_button, "Kijelentkezés")

    def handle_mouse_click(self, pos):

        if self.reconnect_button.collidepoint(pos):
            self._handle_reconnect()
        elif self.leave_button.collidepoint(pos):
            self._handle_leave_room()
        elif self.logout_button.collidepoint(pos):
            self.client.network.logout()

    def _handle_reconnect(self):

        if self.client.previous_room and self.client.previous_room.room_id:
            self.client.selected_room = self.client.previous_room
            self.client.network.rejoin_waiting_room()

    def _handle_leave_room(self):

        if self.client.message == "A játék elkezdődött":
            self.client.network.all_players_leave_room(
                self.client.previous_room.room_id
            )
        else:
            self.client.network.leave_room()
        self.client.screen = "rooms_screen"

    def handle_key_press(self, event):
        pass
