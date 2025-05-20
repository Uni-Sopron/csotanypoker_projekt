from colors_and_sizes import BLACK, WHITE 
from base_screen import BaseScreen
from drawing_helpers import draw_text  


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
        draw_text(self.client.window,"Játék vége", BLACK, 400, 150, True)
        if self.client.game_state.aktiv_jatekos.nev == self.client.username:
            draw_text(self.client.window,"Vesztettél!", BLACK, 400, 250, True)
        else:
            draw_text(self.client.window,"Nyertél!", BLACK, 400, 250, True)

    def handle_key_press(self, event):
        pass

    def handle_mouse_click(self, event):
        pass
