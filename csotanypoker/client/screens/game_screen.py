
import pygame

from csotanypoker.client.drawing_helpers.constans import DARK_GREEN
from csotanypoker.client.drawing_helpers.text_manager import draw_text
from csotanypoker.client.screens.base_screen import BaseScreen
from csotanypoker.client.game_helpers.game_drawer import GameDrawer
from csotanypoker.client.game_helpers.game_mouse_handler import GameMouseHandler
from csotanypoker.client.game_helpers.animation_manager import (
    AnimationManager,
)
from csotanypoker.client.game_helpers.game_state_manager import GameStateManager
from csotanypoker.client.game_helpers.game_button_manager import GameButtonManager
from csotanypoker.client.game_helpers.game_validator import GameValidator

from csotanypoker.client.drawing_helpers.drawing_helpers import (
    create_logout_button_rect,
    create_rules_button_rect,
)
from csotanypoker.client.drawing_helpers.image_manager import load_background, preload_all_images


class GameScreen(BaseScreen):
    """Játék képernyő"""

    def __init__(self, client) -> None:
        super().__init__(client)

        # Manager objektumok
        self.drawer = GameDrawer(self)
        self.mouse_handler = GameMouseHandler(self)
        self.animation_manager = AnimationManager()
        self.state_manager = GameStateManager(self)
        self.button_manager = GameButtonManager(self)
        self.validator = GameValidator(self)

        # Állapot változók
        self.selected_card_frame = None
        self.show_rules = False
        self.show_leave_button = False
        self.adott = False
        self.answer = False

        # Lokális választások
        self.local_question_card = None
        self.local_targeted_player = None
        self.local_active_animal = None
        self.active_animal = None

        # Gombok
        self.logout_button = create_logout_button_rect(self.client.height)
        self.rules_button = create_rules_button_rect(
            self.client.width, self.client.height
        )
        self.leave_button = pygame.Rect(
            self.logout_button.x, self.logout_button.y - 90, 200, 75
        )
        self.pass_button = None
        self.oke_button = None
        self.cross_rect = None
        self.checkmark_rect = None

        self.hovered_elements = set()
        self.pressed_elements = set()

        # Egyéb
        self.last_game_id = None
        self.opponent_player_rects = []
        self.kartya_poziciok = []
        self.animal_button_rects = {}

   
        self._images_preloaded = False

    def _ensure_images_preloaded(self):
        """Képek előtöltése (csak egyszer)"""
        if not self._images_preloaded:
            preload_all_images()
            self._images_preloaded = True

    def draw(self) -> None:
        """Képernyő kirajzolása"""
        self._ensure_images_preloaded()

        if not self._is_game_data_ready():
            self._draw_loading_screen()
            pygame.display.flip()
            return

        self._update_state()

  
        self.button_manager.update_button_rects()
        self.button_manager.update_button_states()

        self.state_manager.set_contextual_message()

        self.drawer.draw_all()

        pygame.display.flip()

    def _is_game_data_ready(self):
        """Ellenőrzi, hogy minden játék adat készen áll-e"""
        if not self.client.game_state:
            return False

        if not self.client.user:
            return False

        if not hasattr(self.client, "visible_player") or not self.client.visible_player:
            return False

        if not self.client.game_state.active_player:
            return False

        if not hasattr(self.client, "opponent_players"):
            return False

        return True

    def _draw_loading_screen(self):
        """Betöltő képernyő rajzolása"""


        load_background(self.client.width, self.client.height, self.client.window)

        draw_text(
            self.client.window,
            "Betöltés...",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 2,
            centered=True,
            font="bold",
            font_size=40,
        )

    def _update_state(self):
        self.state_manager.check_leave_button_visibility()
        current_game_id = getattr(self.client.game_state, "game_id", None)
        self.state_manager.update_on_game_change(current_game_id)
        self.state_manager.update_on_player_change()

    def handle_mouse_click(self, pos):
        """Egér kattintás kezelése"""
        return self.mouse_handler.handle_click(pos)

    def handle_mouse_motion(self, pos):
        """Egér mozgás kezelése"""
        pass

    def handle_key_press(self, event):
        """Billentyű lenyomás kezelése"""
        pass
