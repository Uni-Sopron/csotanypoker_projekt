import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import BLACK, FONT_MEDIUM, GRAY, SCREEN_WIDTH, WHITE
from csotanypoker.client.drawing_helpers import draw_text
import time


class EndScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client = client

        self.back_button = pygame.Rect(300, 350, 200, 50)
        self.rematch_button = pygame.Rect(300, 420, 200, 50)
        self.auto_leave_timer = 30
        self.logout_button = pygame.Rect(SCREEN_WIDTH // 3, 600, 140, 50)
        self.auto_leave_triggered = False

    def draw(self) -> None:
        self.client.window.fill(WHITE)
        font_medium = pygame.font.Font(None, FONT_MEDIUM)
        pygame.draw.rect(self.client.window, GRAY, self.logout_button)
        draw_text(
            self.client.window,
            "Kijelentkezés",
            BLACK,
            self.logout_button.centerx,
            self.logout_button.centery,
            centered=True,
            font=font_medium,
        )
        draw_text(self.client.window, "Játék vége", BLACK, 400, 150, centered=True)

        if self.client.game_state.active_player.name == self.client.username:
            draw_text(self.client.window, "Vesztettél!", BLACK, 400, 250, centered=True)
        else:
            draw_text(self.client.window, "Nyertél!", BLACK, 400, 250, centered=True)

        if self.client.game_state.voters != []:
            for i, voter in enumerate(self.client.game_state.voters):
                draw_text(
                    self.client.window,
                    voter + " szavazott a visszavágóra!",
                    BLACK,
                    650,
                    300 + 20 * i,
                    centered=True,
                )

        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.auto_leave_timer - elapsed_time)

        if remaining_time > 0:
            draw_text(
                self.client.window,
                f"Automatikus kilépés: {int(remaining_time)}s",
                BLACK,
                400,
                500,
                centered=True,
            )
        if remaining_time <= 0 and not self.auto_leave_triggered:
            self.auto_leave_triggered = True
            self.auto_leave()
        pygame.draw.rect(self.client.window, GRAY, self.back_button)
        pygame.draw.rect(self.client.window, GRAY, self.rematch_button)

        draw_text(
            self.client.window,
            "Szoba elhagyása",
            BLACK,
            self.back_button.centerx,
            self.back_button.centery,
            centered=True,
        )
        draw_text(
            self.client.window,
            "Visszavágó",
            BLACK,
            self.rematch_button.centerx,
            self.rematch_button.centery,
            centered=True,
        )

    def auto_leave(self) -> None:
        print("Automatikus kilépés az időzítő lejárta után")
        self.client.network.all_players_leave_room(self.client.room_id)

    def handle_mouse_click(self, pos):
        if self.back_button.collidepoint(pos):
            self.client.network.all_players_leave_room(self.client.room_id)
            # self.client.network.leave_room()
        elif self.rematch_button.collidepoint(pos):
            print("Visszavágó gomb megnyomva")
            print("Szoba ID:", self.client.room_id)

            print(self.client.room_id, self.client.username)
            self.client.network.vote_rematch(self.client.room_id, self.client.username)
        elif self.logout_button.collidepoint(pos):
            print("Kijelentkezés gomb megnyomva")
            self.client.network.logout(self.client.username)

    def handle_key_press(self, event):
        pass
