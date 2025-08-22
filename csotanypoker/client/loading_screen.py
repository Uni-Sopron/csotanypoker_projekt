from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import DARK_GREEN
from csotanypoker.client.drawing_helpers import draw_text, load_background


class LoadingScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

    def draw(self):
        """Draw the loading screen"""
        load_background(self.client.width, self.client.height, self.client.window)
        draw_text(
            self.client.window,
            "Betöltés...",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 2,
            True,
            "bold",
            90,
        )

    def handle_mouse_click(self, pos):
        """No interaction on loading screen"""
        pass

    def handle_key_press(self, event):
        """No interaction on loading screen"""
        pass
