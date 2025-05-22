from colors_and_sizes import BLACK, GRAY, WHITE
import pygame
from base_screen import BaseScreen
from drawing_helpers import draw_text


class WaitingScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)

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

        if self.client.selected_room is not None:
            max_players = self.client.rooms[self.client.selected_room]["max_players"]
            if len(self.client.game_state.players) == max_players:
                status = "Játék indul!"

        draw_text(self.client.window, status, BLACK, 400, 100, True)

        # Display the list of players
        draw_text(self.client.window, "Játékosok:", BLACK, 50, 150)
        y = 200
        for player in self.client.game_state.players:
            draw_text(self.client.window, player.name, BLACK, 60, y)
            y += 40

        # Leave button
        pygame.draw.rect(self.client.window, GRAY, self.client.leave_button)
        draw_text(
            self.client.window,
            "Szoba elhagyása",
            BLACK,
            self.client.leave_button.centerx,
            self.client.leave_button.centery,
            True,
        )

    def handle_mouse_click(self, pos):
        pass

    def handle_key_press(self, key):
        pass
