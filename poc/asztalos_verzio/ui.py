import pygame
from client import NetworkManager
from typing import List, Dict, Any, Tuple, Optional


class GameClient:
    def __init__(self) -> None:
        pygame.init()  # Initialize Pygame
        self.window: pygame.Surface = pygame.display.set_mode(
            (800, 700)
        )  # width: 800, height: 700
        pygame.display.set_caption("Proba Jatek")
        self.clock: pygame.time.Clock = (
            pygame.time.Clock()
        )  # Timer to regulate the refresh rate (fps)
        self.font: pygame.font.Font = pygame.font.Font(None, 20)

        # Define colors
        self.WHITE: tuple[int, int, int] = (255, 255, 255)
        self.BLACK: tuple[int, int, int] = (0, 0, 0)
        self.GRAY: tuple[int, int, int] = (200, 200, 200)
        self.GREEN: tuple[int, int, int] = (0, 200, 0)
        self.RED: tuple[int, int, int] = (200, 0, 0)

        # Game state and screens
        self.screen: str = "login"  # Current screen ("login", "lobby", "waiting", "game", "rejoin_prompt")
        self.rooms: List[Dict[str, Any]] = []

        # Handling players and messages
        self.players: List[str] = []  # List of players in the room
        self.message: str = ""  # Message to be displayed
        self.message_display_time: float = 0  # Message display duration

        # Input fields and their active state
        self.input_text: str = ""
        self.input_active: bool = (
            False  # Whether the user has clicked on the input field
        )
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

    def run(self) -> None:
        """
        Handles events, updates game state, and screen rendering.
        """
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

            if self.message_display_time > 0:
                self.message_display_time -= 1 / 30

            if self.error_display_time > 0:
                self.error_display_time -= 1 / 30

            # Update screen
            pygame.display.update()
            self.clock.tick(30)  # 30 frames per second

        self.network.disconnect()
        pygame.quit()

    def handle_mouse_click(self, pos: Tuple) -> None:
        """
        Handles mouse clicks on different screens.

        Args:
            pos (Tuple): Mouse click position with (x, y) coordinates
        """
        if self.screen == "login":
            self.input_active = self.input_box.collidepoint(
                pos
            )  # Checks if the click occurred inside the input box

        elif self.screen == "lobby":
            self.room_active = self.room_box.collidepoint(pos)
            y: int = 150
            for i, room in enumerate(self.rooms):
                room_rect = pygame.Rect(50, y, 700, 40)
                if room_rect.collidepoint(pos):
                    self.selected_room = i
                    self.network.join_room(room["id"])  # Join the room
                y += 50

            if self.refresh_button.collidepoint(pos):
                self.network.get_rooms()

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
            if event.key == pygame.K_RETURN:  # Enter key pressed
                if self.input_text:
                    self.network.login(
                        self.input_text
                    )  # Login with the provided username
            elif event.key == pygame.K_BACKSPACE:  # Delete
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode

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
            self.draw_login()
        elif self.screen == "lobby":
            self.draw_lobby()
        elif self.screen == "waiting":
            self.draw_waiting()
        elif self.screen == "game":
            self.draw_game()
        elif self.screen == "rejoin_prompt":
            self.draw_rejoin_prompt()

    def draw_text(
        self,
        text: str,
        color: Tuple,
        x: int,
        y: int,
        center: bool = False,
    ) -> pygame.Rect:
        """
        Draw text on the screen.

        Args:
            text (str): The text to be displayed
            color (Tuple): The color of the text
            x (int): X coordinate
            y (int): Y coordinate
            center (bool, optional): If True, the text is centered around (x, y). Default: False

        Returns:
            pygame.Rect: The area occupied by the text
        """
        text_obj = self.font.render(text, 1, color)
        text_rect = text_obj.get_rect()

        if center:
            text_rect.center = (x, y)  # Set text center position
        else:
            text_rect.topleft = (x, y)  # Set text top-left position

        self.window.blit(text_obj, text_rect)
        return text_rect

    def draw_login(self) -> None:
        """
        Bejelentkező képernyő rajzolása.
        """
        self.window.fill(self.WHITE)  # Clear the screen with white
        self.draw_text("Add meg a felhasználóneved", self.BLACK, 400, 150, True)
        pygame.draw.rect(self.window, self.GRAY, self.input_box, 2)

        # Draw the input text
        self.window.blit(
            self.font.render(self.input_text, True, self.BLACK),
            (self.input_box.x + 5, self.input_box.y + 5),
        )

        # Display error message if any
        if self.login_error and self.error_display_time > 0:
            self.draw_text(self.login_error, self.RED, 400, 320, True)

    def draw_lobby(self) -> None:
        """
        Draw the lobby screen with the list of available rooms.
        """
        self.window.fill(self.WHITE)
        self.draw_text("Lobby", self.BLACK, 400, 50, True)
        self.draw_text("Szobák:", self.BLACK, 50, 100)
        self.draw_text(f"Felhasználónév:: {self.username}", self.BLACK, 600, 50, True)

        # Draw the list of rooms
        y = 150
        for i, room in enumerate(self.rooms):
            print(room)
            print(room["name"])
            room_rect = pygame.Rect(50, y, 700, 40)
            pygame.draw.rect(self.window, self.GRAY, room_rect)
            self.draw_text(
                f"{room['name']} ({room['players']}/{room['max_players']} players)",
                self.BLACK,
                60,
                y + 10,
            )
            y += 50

        # Create new room section
        self.draw_text("Új szoba készités:", self.BLACK, 50, 420)
        pygame.draw.rect(self.window, self.GRAY, self.room_box, 2)

        # Draw input text
        self.window.blit(
            self.font.render(self.room_input, True, self.BLACK),
            (self.room_box.x + 5, self.room_box.y + 5),
        )

        # Refresh button
        pygame.draw.rect(self.window, self.GRAY, self.refresh_button)  
        self.draw_text(
            "Frissítés",
            self.BLACK,
            self.refresh_button.centerx,
            self.refresh_button.centery,
            True,
        )

    def draw_waiting(self) -> None:
        """
        Draw the waiting screen.
        """
        self.window.fill(self.WHITE)
        self.draw_text(f"Szoba: {self.room_name}", self.BLACK, 400, 50, True)
        self.draw_text(f"Felhasználónév: {self.username}", self.BLACK, 600, 50, True)
        status = "Várakozás a játékosokra."

        # Check if there are enough players to start the game
        if self.selected_room is not None:
            max_players = self.rooms[self.selected_room]["max_players"]
            if len(self.players) == max_players:
                status = "Játék indul!"

        self.draw_text(status, self.BLACK, 400, 100, True)

        # Display the list of players
        self.draw_text("Játékosok:", self.BLACK, 50, 150)
        y = 200
        for player in self.players:
            self.draw_text(player, self.BLACK, 60, y)
            y += 40

        # Leave button
        pygame.draw.rect(self.window, self.GRAY, self.leave_button)
        self.draw_text(
            "Szoba elhagyása",
            self.BLACK,
            self.leave_button.centerx,
            self.leave_button.centery,
            True,
        )

    def draw_game(self) -> None:
        """
        Draw the game screen.
        """
        self.window.fill(self.WHITE)
        self.draw_text(f"Szoba: {self.room_name}", self.BLACK, 400, 50, True)
        self.draw_text(f"Felhasználónév: {self.username}", self.BLACK, 600, 50, True)

        # Create and draw player buttons
        player_buttons = self.get_player_buttons()
        for player, rect in player_buttons:
            pygame.draw.rect(self.window, self.GRAY, rect)
            self.draw_text(player, self.BLACK, rect.centerx, rect.centery, True)

        # Display message if there is one
        if self.message_display_time > 0:
            self.draw_text(self.message, self.BLACK, 400, 250, True)

        # Exit button
        pygame.draw.rect(self.window, self.GRAY, self.leave_button)
        self.draw_text(
            "Játék elhagyása",
            self.BLACK,
            self.leave_button.centerx,
            self.leave_button.centery,
            True,
        )

    def draw_rejoin_prompt(self) -> None:
        """
        Ask the user if they want to rejoin an active game.
        """
        self.window.fill(self.WHITE)
        self.draw_text("Vissza csatalkozás a Játékba", self.BLACK, 400, 150, True)
        self.draw_text(
            f"Ebben a szobában még folyik a játék: {self.rejoin_room_name}",
            self.BLACK,
            400,
            200,
            True,
        )
        self.draw_text("Szeretnél vissza csatlakozni", self.BLACK, 400, 250, True)

        pygame.draw.rect(self.window, self.GREEN, self.yes_button)
        self.draw_text(
            "Igen",
            self.BLACK,
            self.yes_button.centerx,
            self.yes_button.centery,
            True,
        )

        pygame.draw.rect(self.window, self.RED, self.no_button)
        self.draw_text(
            "Nem",
            self.BLACK,
            self.no_button.centerx,
            self.no_button.centery,
            True,
        )

    def get_player_buttons(self) -> List[Tuple]:
        """
        Create player buttons on the game screen.

        Returns:
            List[Tuple]: List containing player names and their respective buttons.
        """
        player_buttons: list = []
        x: int = 50

        # Create buttons for players
        for player in self.players:
            if player != self.username:
                player_rect = pygame.Rect(x, 150, 200, 40)
                player_buttons.append((player, player_rect))
                x += 250

        return player_buttons

    def on_login_success(self, username: str) -> None:
        """
        Handle successful login event.
        Args:
            username (str): The user's name.
        """
        self.username = username

        self.screen = "lobby"

    def on_login_error(self, message: str) -> None:
        """
        Handle login error.

        Args:
            message (str): The error message.
        """
        self.login_error = message
        self.error_display_time = 5  # Set display time for error message (5 seconds)

    def on_room_list(self, rooms: List[Dict[str, Any]]) -> None:
        """
        Update the list of available rooms.

        Args:
            rooms (List[Dict[str,Any]]): The list of available rooms.
        """
        self.rooms = rooms

    def on_joined_room(
        self,
        room_id: str,
        name: str,
        players: List[str],
        username: Optional[str] = None,
    ) -> None:
        """
        Handle the event of joining a room.

        Args:
            room_id (str): The room's ID.
            name (str): The room's name.
            players (List[str]): List of players in the room.
            username (Optional[str], optional): Username.
        """
        self.room_id = room_id
        self.room_name = name
        self.players = players

        if username:
            self.username = username
        self.screen = "waiting"

    def on_player_joined(self, players: List[str]) -> None:
        """
        Handle a new player joining.

        Args:
            players (List[str]): The list of players.
        """
        self.players = players

    def on_player_left(self, players: List[str]) -> None:
        """
        Handle a player leaving.
        Args:
            players (List[str]): The list of players.
        """
        self.players = players

    def show_notification(self, message: str) -> None:
        """
        Display a notification on the screen.
        Args:
            message (str): The message to be displayed.
        """
        self.message = message
        self.message_display_time = 5  # Set display time for the message (5 seconds)

    def on_start_game(self, players: List[str]) -> None:
        """
        Handle the start of the game.
        Args:
            players (List[str]): List of players in the game.
        """
        self.players = players
        self.screen = "game"

    def show_rejoin_prompt(self, room_id: str, room_name: str) -> None:
        """
        Ask the user if they want to rejoin a previous game.

        Args:
            room_id (str): The ID of the active room.
            room_name (str): The name of the room.
        """
        self.rejoin_room_id = room_id
        self.rejoin_room_name = room_name
        self.screen = "rejoin_prompt"


if __name__ == "__main__":
    client = GameClient()
    client.run()
