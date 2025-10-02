from typing import Any, List, Optional, Tuple, Dict
import socket
import subprocess
import platform

import pygame

from csotanypoker.client.client import NetworkManager
from csotanypoker.client.constans import FPS, SCREEN_WIDTH, SCREEN_HEIGHT

from csotanypoker.client.end_screen import EndScreen
from csotanypoker.client.game_screen import GameScreen
from csotanypoker.client.loading_screen import LoadingScreen
from csotanypoker.client.music_menü import MusicMenu
from csotanypoker.client.reconnect_screen import ReconnectScreen
from csotanypoker.client.registration import LoginScreen
from csotanypoker.client.rooms_screen import RoomsScreen
from csotanypoker.client.waiting_screen import WaitingScreen
from csotanypoker.models.gamestate import ClientGameState
from csotanypoker.models.player import OpponentPlayer, VisiblePlayer
from csotanypoker.client.drawing_helpers import create_volume_button_rect
from csotanypoker.client.music_managger import MusicManager


class GameController:
    def __init__(self) -> None:
        pygame.init()
        self._game_state = ClientGameState()

        self._window: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
        )

        self._width = self._window.get_size()[0]
        self._height = self._window.get_size()[1]
        pygame.display.set_caption("Csotány Póker")
        self._clock: pygame.time.Clock = pygame.time.Clock()

        self._screen: str = "loading"
        self.opponent_players: List[OpponentPlayer] = []

        self.users = []
        self._message: str = ""
        self._message_display_time: float = 0
        self.visible_player: Optional[VisiblePlayer] = None
        self._selected_room = None
        self._user = None

        self._network: NetworkManager = NetworkManager(self)
        self._screens = self._initialize_screens()
        self.volume_level = 1
        self.input_active = False

        self._music_manager = MusicManager()
        self._music_manager.start_background_music()
        self.music_menu = MusicMenu()

    def get_local_ip(self) -> str:
        """
        Automatikusan meghatározza a helyi IP címet több módszerrel
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                print(f"Socket módszerrel talált IP: {local_ip}")
                return local_ip
        except Exception as e:
            print(f"Socket módszer sikertelen: {e}")

        try:
            system = platform.system().lower()

            if system == "windows":
                result = subprocess.run(
                    ["ipconfig"], capture_output=True, text=True, shell=True
                )
                lines = result.stdout.split("\n")

                for i, line in enumerate(lines):
                    if "Wireless LAN adapter" in line or "Wi-Fi" in line:
                        for j in range(i, min(i + 10, len(lines))):
                            if "IPv4" in lines[j] and "192.168." in lines[j]:
                                ip = lines[j].split(":")[-1].strip()
                                if ip.startswith("192.168."):
                                    print(
                                        f"Windows ipconfig módszerrel talált IP: {ip}"
                                    )
                                    return ip

            elif system in ["linux", "darwin"]:
                try:
                    result = subprocess.run(
                        ["hostname", "-I"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        ips = result.stdout.strip().split()
                        for ip in ips:
                            if (
                                ip.startswith("192.168.")
                                or ip.startswith("10.")
                                or ip.startswith("172.")
                            ):
                                print(f"hostname -I módszerrel talált IP: {ip}")
                                return ip
                except:
                    pass

        except Exception as e:
            print(f"Platform specifikus módszer sikertelen: {e}")

        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if not local_ip.startswith("127."):
                print(f"gethostbyname módszerrel talált IP: {local_ip}")
                return local_ip
        except Exception as e:
            print(f"  {e}")

        return "127.0.0.1"

    def _initialize_screens(self) -> Dict[str, Any]:
        return {
            "loading": LoadingScreen(self),
            "login": LoginScreen(self),
            "rooms_screen": RoomsScreen(self),
            "waiting": WaitingScreen(self),
            "game": GameScreen(self),
            "game_over": EndScreen(self),
            "reconnect_screen": ReconnectScreen(self),
        }

    @property
    def game_state(self) -> ClientGameState:
        return self._game_state

    @game_state.setter
    def game_state(self, value: ClientGameState) -> None:
        self._game_state = value

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

    @property
    def screen(self) -> str:
        return self._screen

    @screen.setter
    def screen(self, value: str) -> None:
        self._screen = value

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
    def network(self) -> NetworkManager:
        return self._network

    @property
    def loading(self):
        return self._screens["loading"]

    @property
    def login(self):
        return self._screens["login"]

    @property
    def rooms_screen(self):
        return self._screens["rooms_screen"]

    @property
    def waiting(self):
        return self._screens["waiting"]

    @property
    def game(self):
        return self._screens["game"]

    @property
    def game_over(self):
        return self._screens["game_over"]

    @property
    def reconnect_screen(self):
        return self._screens["reconnect_screen"]

    def _update_window_size(self) -> None:
        self._width, self._height = self._window.get_size()

    def _enforce_minimum_size(self, new_width: int, new_height: int) -> Tuple[int, int]:
        """Enforce minimum window size based on constants"""
        width = max(new_width, SCREEN_WIDTH)
        height = max(new_height, SCREEN_HEIGHT)
        return width, height

    def _handle_window_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            width, height = self._enforce_minimum_size(event.w, event.h)

            if width != event.w or height != event.h:
                self._window = pygame.display.set_mode(
                    (width, height), pygame.RESIZABLE
                )

            self._width = width
            self._height = height

        elif event.type in [pygame.WINDOWMAXIMIZED, pygame.WINDOWRESTORED]:
            self._update_window_size()

            current_width, current_height = self._window.get_size()
            width, height = self._enforce_minimum_size(current_width, current_height)

            if width != current_width or height != current_height:
                self._window = pygame.display.set_mode(
                    (width, height), pygame.RESIZABLE
                )
                self._width = width
                self._height = height

    def run(self) -> None:
        self.draw_screen()
        pygame.display.update()

        local_ip = self.get_local_ip()
        server_url = f"http://{local_ip}:5000"
        print(f"Csatlakozás a szerverhez: {server_url}")

        self._network.connect(server_url)

        running: bool = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type in [
                    pygame.VIDEORESIZE,
                    pygame.WINDOWMINIMIZED,
                    pygame.WINDOWMAXIMIZED,
                    pygame.WINDOWRESTORED,
                ]:
                    self._handle_window_events(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in [1, 3]:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event)
                elif event.type == pygame.MOUSEWHEEL:
                    self.rooms_screen.handle_mouse_wheel(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_release(event.pos)

            self.draw_screen()
            pygame.display.update()
            self._clock.tick(FPS)

        self._network.disconnect()
        pygame.quit()
    def handle_mouse_click(self, pos: Tuple) -> None:
        clicked_something = False
        invalid_click = False 
        
        if hasattr(self, "music_menu"):
            if self.music_menu.visible:
                if self.music_menu.handle_mouse_click(pos, self._music_manager):
                    self._music_manager.button_click_sound()
                    return
            else:
                if self._screen == "login":
                    result = self.login.handle_mouse_click(pos)
                    self.input_active = result
                    clicked_something = result
                elif self._screen == "rooms_screen":
                    result = self.rooms_screen.handle_mouse_click(pos)
                    if isinstance(result, tuple):
                        clicked_something, invalid_click = result
                    else:
                        clicked_something = result
                elif self._screen == "waiting":
                    result = self.waiting.handle_mouse_click(pos)
                    if isinstance(result, tuple):
                        clicked_something, invalid_click = result
                    else:
                        clicked_something = result
                elif self._screen == "game":
                    result = self.game.handle_mouse_click(pos)
                    if isinstance(result, tuple):
                        clicked_something, invalid_click = result
                    else:
                        clicked_something = result

                    if clicked_something and self._is_card_clicked(pos):
                        return
                elif self._screen == "reconnect_screen":
                    result = self.reconnect_screen.handle_mouse_click(pos)
                    if isinstance(result, tuple):
                        clicked_something, invalid_click = result
                    else:
                        clicked_something = result
                elif self._screen == "game_over":
                    result = self.game_over.handle_mouse_click(pos)
                    if isinstance(result, tuple):
                        clicked_something, invalid_click = result
                    else:
                        clicked_something = result

                if invalid_click:
                    self._music_manager.invalid_click_sound()
                elif clicked_something:
                    self._music_manager.button_click_sound()

        volume_rect = None
        if self._screen not in ["loading", "login"]:
            if self.screen in ["rooms_screen", "reconnect_screen", "game_over"]:
                volume_rect = create_volume_button_rect(
                    self._width - 40, self._height - 40
                )
            elif self.screen == "waiting":
                volume_rect = create_volume_button_rect(50, 50)
            elif self.screen == "game":
                volume_rect = create_volume_button_rect(
                    self._width - 65, self._height - 165
                )

            if volume_rect and volume_rect.collidepoint(pos):
                if hasattr(self, "music_menu"):
                    self.music_menu.show(self._width, self._height)
                self._music_manager.button_click_sound()
                return
        
    def _is_card_clicked(self, pos: Tuple) -> bool:
        if hasattr(self.game, 'kartya_poziciok'):
            for rect, lap in self.game.kartya_poziciok:
                if rect.collidepoint(pos):
                    return True
        return False         
        
    def handle_mouse_motion(self, pos: Tuple) -> None:
        if hasattr(self, "music_menu"):
            self.music_menu.handle_mouse_motion(pos)
        if self._screen == "waiting":
            self.waiting.handle_mouse_motion(pos)
        elif self._screen == "rooms_screen":
            self.rooms_screen.handle_mouse_motion(pos)

    def handle_key_press(self, event: pygame.event.Event) -> None:
        if self._screen == "login" and self.input_active:
            self.login.handle_key_press(event)
        elif self._screen == "rooms_screen":
            self.rooms_screen.handle_key_press(event)

    def draw_screen(self) -> None:
        """Módosított draw_screen metódus"""
        if hasattr(self, "music_menu"):
            if self.music_menu.visible:
                self.music_menu.draw(self._window)
            else:
                current_screen = self._screens.get(self._screen)
                if current_screen and hasattr(current_screen, "draw"):
                    current_screen.draw()

    def handle_mouse_release(self, pos: Tuple) -> None:
        if hasattr(self, "music_menu"):
            self.music_menu.handle_mouse_release(pos)
