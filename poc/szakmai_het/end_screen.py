from colors_and_sizes import BLACK, WHITE  # Adjusted import path

from base_screen import BaseScreen


class EndScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)
        self.client = client

    def draw(self) -> None:
        """
        Draw the game over screen.
        """
        print("Játék vége")
        self.client.window.fill(WHITE)
        self.draw_text("Játék vége", BLACK, 400, 150, True)
        if self.client.aktiv_jatekos == self.client.username:
            self.draw_text("Vesztettél!", BLACK, 400, 250, True)
        else:
            self.draw_text("Nyertél!", BLACK, 400, 250, True)

    def handle_key_press(self, event):
        pass

    def handle_mouse_click(self, event):
        pass
