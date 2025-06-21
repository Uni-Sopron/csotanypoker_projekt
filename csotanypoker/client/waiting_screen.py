import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import BLACK, FONT_MEDIUM, GRAY, SCREEN_WIDTH, WHITE
from csotanypoker.client.drawing_helpers import draw_text


class WaitingScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.logout_button = pygame.Rect(SCREEN_WIDTH // 3, 600, 140, 50)

    def draw(self) -> None:
        """
        Draw the waiting screen.
        """
        self.client.window.fill(WHITE)
        draw_text(
            self.client.window, f"Szoba: {self.client.room_name}", BLACK, 400, 50, True
        )
        draw_text(
            self.client.window,
            f"Felhasználónév: {self.client.username}",
            BLACK,
            600,
            50,
            True,
        )
        status = "Várakozás a játékosokra."
        if self.client.selected_room.password is not None:
            draw_text(
                self.client.window,
                f"Jelszó:{self.client.selected_room.password}",
                BLACK,
                600,
                100,
                True,
            )

        draw_text(self.client.window, status, BLACK, 400, 100, True)
        draw_text(self.client.window, "Játékosok:", BLACK, 50, 150)
        y = 200
        for player in self.client.game_state.players:
            print(player.is_active)
            dot_color = (
                (0, 200, 0) if getattr(player, "is_active", False) else (200, 0, 0)
            )
            pygame.draw.circle(self.client.window, dot_color, (40, y + 10), 8)

            draw_text(self.client.window, player.name, BLACK, 60, y)
            y += 40

        if self.client.message and self.client.message_display_time > 0:
            draw_text(
                self.client.window,
                self.client.message,
                BLACK,
                self.client.window.get_width() // 2,
                self.client.window.get_height() // 2,
                True,
            )
            self.client.message_display_time -= 1

        pygame.draw.rect(self.client.window, GRAY, self.client.leave_button)
        draw_text(
            self.client.window,
            "Szoba elhagyása",
            BLACK,
            self.client.leave_button.centerx,
            self.client.leave_button.centery,
            True,
        )
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

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the waiting screen"""
        if self.client.leave_button.collidepoint(pos):
            # print("Leaving room")
            self.client.network.leave_room()
        elif self.logout_button.collidepoint(pos):
            # print("Logging out")
            self.client.network.logout()

    def handle_key_press(self, key):
        pass
