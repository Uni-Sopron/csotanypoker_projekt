from typing import Any, List, Optional, Tuple

import pygame

from csotanypoker.client.client import NetworkManager
from csotanypoker.client.constans import FPS, SCREEN_WIDTH, SCREEN_HEIGHT

# from csotanypoker.client.end_screen import EndScreen
# from csotanypoker.client.game_screen import GameScreen
from csotanypoker.client.loading_screen import LoadingScreen

# from csotanypoker.client.reconnect_screen import ReconnectScreen
from csotanypoker.client.registration import LoginScreen
from csotanypoker.client.rooms_screen import RoomsScreen
# from csotanypoker.client.waiting_screen import WaitingScreen
# from csotanypoker.models.gamestate import GameState


class GameController:
    def __init__(self) -> None:
        pygame.init()  # Initialize Pygame
        # self.game_state = GameState()
        width, height = SCREEN_WIDTH, SCREEN_HEIGHT

        self.window: pygame.Surface = pygame.display.set_mode(
            (width, height), pygame.RESIZABLE
        )
        # olvasd ki az ablak méretét
        self.width = self.window.get_size()[0]
        self.height = self.window.get_size()[1]
        pygame.display.set_caption("Csotány Póker")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.active_player_list_name: List[str] = []  # List of active player names
        self.screen: str = "loading"

        self.pipa_rect = None  # Rectangle for the checkmark image
        self.x_rect = None
        self.IsPassed = False
        self.is_given = False

        self.message: str = ""  # Message to be displayed
        self.message_display_time: float = 0  # Message display duration

        self.input_text: str = ""
        self.input_active: bool = False
        self.visited_players = []
        self.room_input: str = ""
        self.room_active: bool = False
        self.selected_room = None

        self.user = None
        # Handling error messages
        self.login_error: str = ""
        self.error_display_time: float = 0

        self.leave_button: pygame.Rect = pygame.Rect(300, 500, 200, 50)

        # Network communication
        self.network: NetworkManager = NetworkManager(self)
        self.username: str = ""
        self.room_id: Optional[str] = None
        self.room_name: str = ""  # Current room name
        self.room_list = []
        self.statement = None
        self.dropdown_state = False

        self.loading = LoadingScreen(self)
        self.login = LoginScreen(self)
        self.rooms_screen = RoomsScreen(self)
        # self.waiting = WaitingScreen(self)
        # self.game = GameScreen(self)
        # self.game_over = EndScreen(self)
        # self.reconnect_screen = ReconnectScreen(self)

    # @property
    # def game_state(self) -> GameState:
    #     return self._game_state

    # @game_state.setter
    # def game_state(self, value: GameState) -> None:
    #     self._game_state = value

    @property
    def window(self) -> pygame.Surface:
        return self._window

    @window.setter
    def window(self, value: pygame.Surface) -> None:
        self._window = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = value

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = value

    @property
    def clock(self) -> pygame.time.Clock:
        return self._clock

    @clock.setter
    def clock(self, value: pygame.time.Clock) -> None:
        self._clock = value

    @property
    def screen(self) -> str:
        return self._screen

    @screen.setter
    def screen(self, value: str) -> None:
        self._screen = value

    @property
    def pipa_rect(self) -> Optional[pygame.Rect]:
        return self._pipa_rect

    @pipa_rect.setter
    def pipa_rect(self, value: Optional[pygame.Rect]) -> None:
        self._pipa_rect = value

    @property
    def x_rect(self) -> Optional[pygame.Rect]:
        return self._x_rect

    @x_rect.setter
    def x_rect(self, value: Optional[pygame.Rect]) -> None:
        self._x_rect = value

    @property
    def IsPassed(self) -> bool:
        return self._Passzolas

    @IsPassed.setter
    def IsPassed(self, value: bool) -> None:
        self._Passzolas = value

    @property
    def is_given(self) -> bool:
        return self._atadta

    @is_given.setter
    def is_given(self, value: bool) -> None:
        self._atadta = value

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    @property
    def message_display_time(self) -> float:
        return self._message_display_time

    @message_display_time.setter
    def message_display_time(self, value: float) -> None:
        self._message_display_time = value

    @property
    def input_text(self) -> str:
        return self._input_text

    @input_text.setter
    def input_text(self, value: str) -> None:
        self._input_text = value

    @property
    def input_active(self) -> bool:
        return self._input_active

    @input_active.setter
    def input_active(self, value: bool) -> None:
        self._input_active = value

    @property
    def visited_players(self) -> List:
        return self._visited_players

    @visited_players.setter
    def visited_players(self, value: List) -> None:
        self._visited_players = value

    @property
    def room_input(self) -> str:
        return self._room_input

    @room_input.setter
    def room_input(self, value: str) -> None:
        self._room_input = value

    @property
    def room_active(self) -> bool:
        return self._room_active

    @room_active.setter
    def room_active(self, value: bool) -> None:
        self._room_active = value

    @property
    def selected_room(self) -> Optional[int]:
        return self._selected_room

    @selected_room.setter
    def selected_room(self, value: Optional[int]) -> None:
        self._selected_room = value

    @property
    def user(self) -> Any:
        return self._user

    @user.setter
    def user(self, value: Any) -> None:
        self._user = value

    @property
    def login_error(self) -> str:
        return self._login_error

    @login_error.setter
    def login_error(self, value: str) -> None:
        self._login_error = value

    @property
    def error_display_time(self) -> float:
        return self._error_display_time

    @error_display_time.setter
    def error_display_time(self, value: float) -> None:
        self._error_display_time = value

    @property
    def leave_button(self) -> pygame.Rect:
        return self._leave_button

    @leave_button.setter
    def leave_button(self, value: pygame.Rect) -> None:
        self._leave_button = value

    # @property
    # def network(self) -> NetworkManager:
    #     return self._network

    # @network.setter
    # def network(self, value: NetworkManager) -> None:
    #     self._network = value

    @property
    def room_id(self) -> Optional[str]:
        return self._room_id

    @room_id.setter
    def room_id(self, value: Optional[str]) -> None:
        self._room_id = value

    @property
    def room_name(self) -> str:
        return self._room_name

    @room_name.setter
    def room_name(self, value: str) -> None:
        self._room_name = value

    @property
    def statement(self) -> Any:
        return self._statement

    @statement.setter
    def statement(self, value: Any) -> None:
        self._statement = value

    @property
    def dropdown_state(self) -> bool:
        return self._dropdown_state

    @dropdown_state.setter
    def dropdown_state(self, value: bool) -> None:
        self._dropdown_state = value

    # @property
    # def login(self) -> Optional[LoginScreen]:
    #     return self._login

    # @login.setter
    # def login(self, value: Optional[LoginScreen]) -> None:
    #     self._login = value

    @property
    def yes_button(self) -> Any:
        return self._yes_button

    @yes_button.setter
    def yes_button(self, value: Any) -> None:
        self._yes_button = value

    @property
    def no_button(self) -> Any:
        return self._no_button

    @no_button.setter
    def no_button(self, value: Any) -> None:
        self._no_button = value

    @property
    def loading(self) -> Optional[LoadingScreen]:
        return self._loading

    @loading.setter
    def loading(self, value: Optional[LoadingScreen]) -> None:
        self._loading = value

    # @property
    # def waiting(self) -> Optional[WaitingScreen]:
    #     return self._waiting

    # @waiting.setter
    # def waiting(self, value: Optional[WaitingScreen]) -> None:
    #     self._waiting = value

    # @property
    # def game(self) -> Optional[GameScreen]:
    #     return self._game

    # @game.setter
    # def game(self, value: Optional[GameScreen]) -> None:
    #     self._game = value

    # @property
    # def game_over(self) -> Optional[EndScreen]:
    #     return self._game_over

    # @game_over.setter
    # def game_over(self, value: Optional[EndScreen]) -> None:
    #     self._game_over = value
    # def calculate_screen_size(self) -> Tuple[int, int]:
    #     # a monitor alapján add meg mekkora  képernyö de ugy hogy a felsö menüsor látszódjon
    #     info = pygame.display.Info()
    #     screen_width, screen_height = info.current_w, info.current_h - 50
    #     return screen_width, screen_height

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
                if event.type == pygame.QUIT:
                    running = False
                # abalak méretezés:
                elif event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    print(f"Window resized: {self.width}x{self.height}")
                elif event.type == pygame.WINDOWMINIMIZED:
                    print(f"Window minimized: {self.width}x{self.height}")
                elif event.type == pygame.WINDOWMAXIMIZED:
                    self.width = self.window.get_size()[0]
                    self.height = self.window.get_size()[1]
                    print(f"Window maximized: {self.width}x{self.height}")

                elif event.type == pygame.WINDOWRESTORED:
                    self.width = self.window.get_size()[0]
                    self.height = self.window.get_size()[1]
                    print(f"Window restored: {self.width}x{self.height}")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 3]:
                        self.handle_mouse_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event)
                elif event.type == pygame.MOUSEWHEEL:
                    pass
                    self.rooms_screen.handle_mouse_wheel(event)

            # Render the current screen
            self.draw_screen()

            pygame.display.update()
            self.clock.tick(FPS)

        # self.network.disconnect()
        pygame.quit()

    def handle_mouse_click(self, pos: Tuple) -> None:
        """
        Handles mouse clicks on different screens.

        Args:
            pos (Tuple): Mouse click position with (x, y) coordinates
        """

        if self.screen == "login":
            self.input_active = self.login.handle_mouse_click(pos)

        if self.screen == "rooms_screen":
            self.rooms_screen.handle_mouse_click(pos)

        if self.screen == "waiting":
            self.waiting.handle_mouse_click(pos)

        # Handle player clicks during the game
        if self.screen == "game":
            pass
        if self.screen == "reconnect_screen":
            self.reconnect_screen.handle_mouse_click(pos)
        if self.screen == "game_over":
            self.game_over.handle_mouse_click(pos)

    def handle_mouse_motion(self, pos: Tuple) -> None:
        """
        Handles mouse motion on different screens.

        Args:
            pos (Tuple): Mouse position with (x, y) coordinates
        """
        if self.screen == "waiting":
            self.waiting.handle_mouse_motion(pos)

    def handle_key_press(self, event: pygame.event.Event) -> None:
        """
        Handle key presses based on the game state.

        Args:
            event (pygame.event.Event): The pygame key press event
        """
        if self.screen == "login" and self.input_active:
            self.login.handle_key_press(event)

        elif self.screen == "rooms_screen":
            self.rooms_screen.handle_key_press(event)

    def draw_screen(self) -> None:
        """
        Draw the appropriate screen based on the game state.
        """
        if self.screen == "login":
            self.login.draw()
        elif self.screen == "loading":
            self.loading.draw()

        elif self.screen == "rooms_screen":
            self.rooms_screen.draw()

        elif self.screen == "waiting":
            self.waiting.draw()
        elif self.screen == "game":
            self.game.draw()
        elif self.screen == "reconnect_screen":
            self.reconnect_screen.draw()
        elif self.screen == "game_over":
            self.game_over.draw()

    # Minden property metódus itt marad változatlanul...
