import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    BLACK,
    FONT_MEDIUM,
    GRAY,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
)
from csotanypoker.client.drawing_helpers import draw_text


Jatek_szabaly = {
    "2": """
Adj át egy kártyát az ellenfélnek és mondd meg mi van rajta (igazat vagy hazugságot).

Az ellenfél eldönti, hogy szerinte igaz-e. 
Ha eltalálja, te kapod vissza a kártyát, ha nem, nála marad. Aki végül megkapja a kártyát, az kezdi a következő kört.

Vesztesz, ha összegyűlik 5 ugyanolyan kártya előtted vagy elfogynak a kártyáid.""",
    "3-6": """
Adj át egy kártyát valakinek és mondd meg mi van rajta (igazat vagy hazugságot). 

A megcélzott játékos eldöntheti, hogy elfogadja és tippel, vagy továbbadja másnak.
Ha valaki tippel és eltalálja, a feladó kapja vissza a kártyát, ha nem, a tippelőnél marad.Aki végül megkapja a kártyát, az kezdi a következő kört. 

Vesztesz, ha összegyűlik 4 ugyanolyan kártya előtted vagy elfogynak a kártyáid.
""",
}


class WaitingScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.logout_button = pygame.Rect(SCREEN_WIDTH // 3, 600, 140, 50)
        self.rules_button = pygame.Rect(SCREEN_WIDTH - 50, 10, 40, 40)
        self.show_rules = False

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
            dot_color = (
                (0, 200, 0)
                if player.name in self.client.active_player_list_name
                else (200, 0, 0)
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

        # Kérdőjel gomb rajzolása
        pygame.draw.rect(self.client.window, GRAY, self.rules_button)
        pygame.draw.rect(self.client.window, BLACK, self.rules_button, 2)
        draw_text(
            self.client.window,
            "?",
            BLACK,
            self.rules_button.centerx,
            self.rules_button.centery,
            centered=True,
            font=font_medium,
        )

        # Játékszabály megjelenítése ha az egér a kérdőjel gombon van
        if self.show_rules:
            self.draw_rules_popup()

    def draw_rules_popup(self):
        popup_width = int(SCREEN_WIDTH * 0.6)
        popup_height = int(SCREEN_HEIGHT * 0.6)
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2

        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

        pygame.draw.rect(self.client.window, (173, 216, 230), popup_rect)

        max_players = getattr(self.client.selected_room, "max_player_count")
        print(f"Max players: {max_players}")
        rules_key = "2" if max_players == 2 else "3-6"
        rules_text = Jatek_szabaly[rules_key]

        title = f"Játékszabály ({rules_key} játékos)"
        draw_text(
            self.client.window,
            title,
            BLACK,
            popup_rect.centerx,
            popup_y + 30,
            centered=True,
            font=pygame.font.Font(None, 40),
        )

       
        font = pygame.font.Font(None, 30)
        lines = []
        raw_lines = rules_text.strip().split("\n")

        for raw_line in raw_lines:
            raw_line = raw_line.strip()

            if not raw_line:
                lines.append("")
                continue

            words = raw_line.split()
            current_line = ""

            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_width = font.size(test_line)[0]

                if text_width <= popup_width - 60:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

      
        line_height = 30
        start_y = popup_y + 80

        for i, line in enumerate(lines):
            if line:  
                draw_text(
                    self.client.window,
                    line,
                    BLACK,
                    popup_x + 30,
                    start_y + i * line_height,
                    centered=False,
                    font=font,
                )

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the waiting screen"""
        if self.client.leave_button.collidepoint(pos):
            # print("Leaving room")
            self.client.network.leave_room()
        elif self.logout_button.collidepoint(pos):
            # print("Logging out")
            self.client.network.logout()

    def handle_mouse_motion(self, pos):
        """Handle mouse motion for rules button hover"""
        self.show_rules = self.rules_button.collidepoint(pos)

    def handle_key_press(self, key):
        pass
