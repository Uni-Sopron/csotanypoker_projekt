import pygame
from client import NetworkManager
from typing import List, Dict, Any, Tuple, Optional
from colors_and_sizes import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, RED

from end_screen import EndScreen

from waiting_screen import WaitingScreen
from loading_screen import LoadingScreen

from login_screen import LoginScreen
from game_screen import GameScreen


class GameClient:
    def __init__(self) -> None:
        pygame.init()  # Initialize Pygame
        self.window: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )  # width: 1400, height: 800
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        pygame.display.set_caption("Csotány Póker")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # Game state and screens
        self.screen: str = "loading"  # Current screen ("login", "lobby", "waiting", "game", "rejoin_prompt")
        self.rooms: List[Dict[str, Any]] = []
        self.pipa_rect = None  # Rectangle for the checkmark image
        self.x_rect = None
        self.Passzolas = False
        self.atadta = False
        # Handling players and messages
        self.players: List[str] = []  # List of players in the room
        self.message: str = ""  # Message to be displayed
        self.message_display_time: float = 0  # Message display duration

        self.kivalasztott_lap = None

        self.input_text: str = ""
        self.input_active: bool = False
        self.volt_ennel_mar = []
        self.room_input: str = ""
        self.room_active: bool = False
        self.selected_room: Optional[int] = (
            None  # Index of the room selected by the user
        )

        # Handling error messages
        self.login_error: str = ""
        self.error_display_time: float = 0

        # Variables for rejoining screen
        self.rejoin_room_id: Optional[str] = None
        self.rejoin_room_name: Optional[str] = None
        self.yes_button: pygame.Rect = pygame.Rect(250, 350, 100, 50)
        self.no_button: pygame.Rect = pygame.Rect(450, 350, 100, 50)

        # input fields and buttons
        self.input_box: pygame.Rect = pygame.Rect(
            250, 250, 300, 40
        )  # Input field (x, y, width, height)
        self.room_box: pygame.Rect = pygame.Rect(250, 450, 300, 40)
        self.refresh_button: pygame.Rect = pygame.Rect(500, 500, 200, 50)
        self.leave_button: pygame.Rect = pygame.Rect(300, 500, 200, 50)

        # Network communication
        self.network: NetworkManager = NetworkManager(self)
        self.room_id: Optional[str] = None
        self.room_name: str = ""  # Current room name

        self.celzott_jatekos = None  # Target player for the current action

        self.Allitas = None
        self.lenyiloablak_allapot = False

        self.kozepso_lap = None
        self.ellenfel_allitasa = None
        self.sajat_allitas = None
        self.kezben_levo_lapok = None
        self.elotte_levo_kartyak = None
        self.login = None
        self.jatekosadatok = None
        self.aktiv_jatekos = None

        self.keret_szin = RED  # Piros keret a kiválasztott elemhez

    def allat_tipus(self, nev):
        return nev.split("_")[0]

    def run(self) -> None:
        """
        Handles events, updates game state, and screen rendering.
        """

        self.draw_screen()
        pygame.display.update()

        self.network.connect()

        running: bool = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # If the user closes the window
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:  # Mouse click
                    self.handle_mouse_click(event.pos)  # Process click position
                elif event.type == pygame.KEYDOWN:  # Key press
                    self.handle_key_press(event)  # Handle key press

            # Render the current screen
            self.draw_screen()

            pygame.display.update()
            self.clock.tick(FPS)

        self.network.disconnect()
        pygame.quit()

    def handle_mouse_click(self, pos: Tuple) -> None:
        """
        Handles mouse clicks on different screens.

        Args:
            pos (Tuple): Mouse click position with (x, y) coordinates
        """
        if self.screen == "login":
            self.input_active = self.login.handle_mouse_click(pos)

        elif self.screen in ["waiting", "game"]:
            # Handle the leave button
            if self.leave_button.collidepoint(pos) and self.room_id:
                self.network.leave_room(self.room_id)  # Leave the room
                self.room_id = None
                self.room_name = ""
                self.screen = "lobby"
                self.network.get_rooms()

        # Handle player clicks during the game
        if self.screen == "game":
            player_btns = self.get_player_buttons()
            for player, rect in player_btns:
                if rect.collidepoint(pos) and self.room_id:
                    self.network.player_click(self.room_id, player)

        # Handle interactions on the rejoin screen
        elif self.screen == "rejoin_prompt":
            if self.yes_button.collidepoint(pos) and self.rejoin_room_id is not None:
                self.network.send_rejoin_decision(self.rejoin_room_id, True)
                self.rejoin_room_id = None
                self.rejoin_room_name = None
            elif self.no_button.collidepoint(pos) and self.rejoin_room_id is not None:
                self.network.send_rejoin_decision(self.rejoin_room_id, False)
                self.rejoin_room_id = None
                self.rejoin_room_name = None

    def handle_key_press(self, event: pygame.event.Event) -> None:
        """
        Handle key presses based on the game state.

        Args:
            event (pygame.event.Event): The pygame key press event
        """
        if self.screen == "login" and self.input_active:
            self.login.handle_key_press(event)

        elif self.screen == "lobby" and self.room_active:
            if event.key == pygame.K_RETURN:
                if self.room_input:
                    self.network.create_room(self.room_input)  # Create a new room
                    self.room_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.room_input = self.room_input[:-1]
            else:
                self.room_input += event.unicode

    def draw_screen(self) -> None:
        """
        Draw the appropriate screen based on the game state.
        """
        if self.screen == "login":
            self.login = LoginScreen(self)
            self.login.draw()
        elif self.screen == "loading":
            self.loading = LoadingScreen(self)
            self.loading.draw()
        elif self.screen == "waiting":
            self.waiting = WaitingScreen(self)
            self.waiting.draw()
        elif self.screen == "game":
            self.game = GameScreen(self)
            self.game.draw()
        elif self.screen == "rejoin_prompt":
            self.draw_rejoin_prompt()
        elif self.screen == "Jatek_vege":
            self.game_over = EndScreen(self)
            self.game_over.draw()
