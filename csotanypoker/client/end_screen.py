import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import BLACK, GRAY, WHITE
from csotanypoker.client.drawing_helpers import draw_text


class EndScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client = client

        self.back_button = pygame.Rect(300, 350, 200, 50)
        self.rematch_button = pygame.Rect(300, 420, 200, 50)

    def draw(self) -> None:
        self.client.window.fill(WHITE)

        draw_text(self.client.window, "Játék vége", BLACK, 400, 150, centered=True)

        if self.client.game_state.active_player.name == self.client.username:
            draw_text(self.client.window, "Vesztettél!", BLACK, 400, 250, centered=True)
        else:
            draw_text(self.client.window, "Nyertél!", BLACK, 400, 250, centered=True)

        pygame.draw.rect(self.client.window, GRAY, self.back_button)
        pygame.draw.rect(self.client.window, GRAY, self.rematch_button)

        draw_text(
            self.client.window,
            "Vissza",
            BLACK,
            self.back_button.centerx,
            self.back_button.centery,
            centered=True,
        )
        draw_text(
            self.client.window,
            "Új játék",
            BLACK,
            self.rematch_button.centerx,
            self.rematch_button.centery,
            centered=True,
        )

    def handle_mouse_click(self, pos):
        if self.back_button.collidepoint(pos):
            self.client.network.leave_room()
        elif self.rematch_button.collidepoint(pos):
            self.client.network.rejoin_waiting_room()

    def handle_key_press(self, event):
        pass
