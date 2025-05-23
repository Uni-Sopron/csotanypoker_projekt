from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import BLACK, WHITE
from csotanypoker.client.drawing_helpers import draw_text


class LoadingScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

    def draw(self):
        """Draw the loading screen"""
        self.client.window.fill(WHITE)
        draw_text(self.client.window, "Betöltés...", BLACK, 400, 300, True)
        print("Betöltés...")

    def handle_mouse_click(self, pos):
        """No interaction on loading screen"""
        return False

    def handle_key_press(self, event):
        """No interaction on loading screen"""
        pass
