from colors_and_sizes import BLACK, GRAY, WHITE
import pygame
from base_screen import BaseScreen


class WaitingScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)

    def draw(self) -> None:
        """
        Draw the waiting screen.
        """
        self.client.window.fill(WHITE)
        self.draw_text(f"Szoba: {self.client.room_name}", BLACK, 400, 50, True)
        self.draw_text(f"Felhasználónév: {self.client.username}", BLACK, 600, 50, True)
        status = "Várakozás a játékosokra."

        if self.client.selected_room is not None:
            max_players = self.client.rooms[self.client.selected_room]["max_players"]
            if len(self.client.players) == max_players:
                status = "Játék indul!"

        self.draw_text(status, BLACK, 400, 100, True)

        # Display the list of players
        self.draw_text("Játékosok:", BLACK, 50, 150)
        y = 200
        for player in self.client.players:
            self.draw_text(player, BLACK, 60, y)
            y += 40

        # Leave button
        pygame.draw.rect(self.client.window, GRAY, self.client.leave_button)
        self.draw_text(
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
