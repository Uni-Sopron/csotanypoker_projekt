import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    BLACK,
    FONT_MEDIUM,
    GRAY,
    RED,
    SCREEN_WIDTH,
    WHITE,
)
from csotanypoker.client.drawing_helpers import draw_text


class ReconnectScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

        self.font_medium = pygame.font.Font(None, FONT_MEDIUM)
        self.reconnect_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 500, 140, 50)
        self.rooms_button = pygame.Rect(SCREEN_WIDTH // 2 + 10, 500, 140, 50)
        self.logout_button = pygame.Rect(SCREEN_WIDTH // 3, 600, 140, 50)
        self.reconnect_hover = False
        self.rooms_hover = False

    def draw(self):
        self.client.window.fill(WHITE)

        draw_text(
            self.client.window,
            "Újracsatlakozás",
            BLACK,
            SCREEN_WIDTH // 2,
            100,
            centered=True,
            font=self.font_medium,
        )
        for room in self.client.room_list:
            if room.room_id == self.client.previous_room_id:
                previous_room = room
                break
        if previous_room:
            info_text = "Korábban a következő szobában voltál:"
            draw_text(
                self.client.window,
                info_text,
                BLACK,
                SCREEN_WIDTH // 2,
                220,
                centered=True,
                font=self.font_medium,
            )

            room_name = previous_room.name
            draw_text(
                self.client.window,
                f'"{room_name}"',
                BLACK,
                SCREEN_WIDTH // 2,
                250,
                centered=True,
                font=self.font_medium,
            )

            players_text = f"Játékosok: {previous_room.player_count}/{previous_room.max_player_count}"
            draw_text(
                self.client.window,
                players_text,
                BLACK,
                SCREEN_WIDTH // 2,
                280,
                centered=True,
                font=self.font_medium,
            )

        pygame.draw.rect(self.client.window, GRAY, self.reconnect_button)

        draw_text(
            self.client.window,
            "Újracsatlakozás",
            BLACK,
            self.reconnect_button.centerx,
            self.reconnect_button.centery,
            centered=True,
            font=self.font_medium,
        )

        pygame.draw.rect(self.client.window, GRAY, self.rooms_button)
        draw_text(
            self.client.window,
            "Szoba elhagyása",
            BLACK,
            self.rooms_button.centerx,
            self.rooms_button.centery,
            centered=True,
            font=self.font_medium,
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
        self.rooms_hover = self.rooms_button.collidepoint(mouse_pos)
        if self.client.message:
            draw_text(
                self.client.window,
                self.client.message,
                RED,
                SCREEN_WIDTH // 2,
                500,
                centered=True,
                font=self.font_medium,
            )

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
                    print(f"jatek id.k{previous_room.game_ids}")
                    if previous_room.game_ids == []:
                        self.client.network.rejoin_waiting_room()
                        print("UJRSCSATLAKOZÁS")
                    else:
                        print("A játék már elkezdődött")
                        self.client.network.rejoin_game()

        elif self.rooms_button.collidepoint(pos):
            self.client.network.leave_room()
            self.client.screen = "rooms_screen"
        elif self.logout_button.collidepoint(pos):
            self.client.network.logout()

    def handle_key_press(self, event):
        pass
