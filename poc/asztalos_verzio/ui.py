import pygame
from client import NetworkManager
from typing import List, Dict, Any


class GameClient:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        self.window = pygame.display.set_mode((800, 700))
        pygame.display.set_caption("Proba Jatek")  # ablak címe
        self.clock = pygame.time.Clock()  # How often the screen should refresh (if not set, it depends on the speed of the machine).
        self.font = pygame.font.Font(None, 20)

        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)

        self.screen = "login"  #  login, lobby, waiting, game
        self.username = ""
        self.rooms: List[Dict[str, Any]] = []  # <- PÉLDÁNYSZINTŰ attribútum

        self.players = []
        self.message = ""
        self.message_display_time = 0
        self.input_text = ""
        self.input_active = False  # The user clicks into the input field.
        self.room_input = ""
        self.room_active = False
        self.selected_room = None  # The room index selected by the user.

        self.input_box = pygame.Rect(
            250, 250, 300, 40
        )  # Starting coordinates (x, y) and size (width, height).
        self.room_box = pygame.Rect(250, 450, 300, 40)
        self.refresh_button = pygame.Rect(500, 500, 200, 50)
        self.leave_button = pygame.Rect(300, 500, 200, 50)

        self.network = NetworkManager(self)

    def run(self):  # This manages the game runtime and user interactions.
        self.network.connect()

        running = True
        while running:
            for event in pygame.event.get():  # Handling user interactions.
                if event.type == pygame.QUIT:  # If the user closes the window.
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:  # Clicking the button.
                    self.handle_mouse_click(
                        event.pos
                    )  # event.pos: the mouse position (x, y) when the click occurred
                elif event.type == pygame.KEYDOWN:  # Key press.
                    self.handle_key_press(event)

            # Draw current screen
            self.draw_screen()

            if self.message_display_time > 0:
                self.message_display_time -= 1 / 60

            pygame.display.update()
            self.clock.tick(30)  # 30 Frames / second

        self.network.disconnect()
        pygame.quit()

    def handle_mouse_click(
        self, pos
    ):  # It handles the clicks depending on which screen we are on.
        if self.screen == "login":
            # Login screen interactions
            self.input_active = self.input_box.collidepoint(
                pos
            )  # It checks if the pos(x, y) is within the input field.

        elif self.screen == "lobby":
            # Lobby screen interactions
            self.room_active = self.room_box.collidepoint(pos)

            # It checks which room the user clicked on.
            y = 150
            print(self.rooms)
            for i, room in enumerate(self.rooms):
                room_rect = pygame.Rect(50, y, 700, 40)
                if room_rect.collidepoint(pos):
                    self.selected_room = i
                    self.network.join_room(room["id"])
                y += 50

            if self.refresh_button.collidepoint(
                pos
            ):  # Clicking the refresh button retrieves the rooms again.
                self.network.get_rooms()

        elif self.screen in ["waiting", "game"]:
            # Leave button
            if self.leave_button.collidepoint(pos) and self.room_id:
                self.network.leave_room(self.room_id)
                self.room_id = None
                self.room_name = ""
                self.screen = "lobby"
                self.network.get_rooms()

        # Player clicks in game
        if self.screen == "game":
            player_btns = self.get_player_buttons()
            for player, rect in player_btns:
                if rect.collidepoint(pos) and self.room_id:
                    self.network.player_click(self.room_id, player)

    def handle_key_press(
        self, event
    ):  # Handling key presses depending on the game state.
        if self.screen == "login" and self.input_active:
            if (
                event.key == pygame.K_RETURN
            ):  # Pressing Enter sends the username to the server.
                if self.input_text:
                    self.network.login(self.input_text)
            elif event.key == pygame.K_BACKSPACE:  # delete
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode  # character added to the input_text

        elif self.screen == "lobby" and self.room_active:
            if event.key == pygame.K_RETURN:
                if self.room_input:
                    self.network.create_room(self.room_input)
                    self.room_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.room_input = self.room_input[:-1]
            else:
                self.room_input += event.unicode

    def draw_screen(self):  # It draws the screen according to the game state.
        if self.screen == "login":
            self.draw_login()
        elif self.screen == "lobby":
            self.draw_lobby()
        elif self.screen == "waiting":
            self.draw_waiting()
        elif self.screen == "game":
            self.draw_game()

    def draw_text(self, text, color, x, y, center=False):
        text_obj = self.font.render(text, 1, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.window.blit(text_obj, text_rect)
        return text_rect

    def draw_login(self):  # It draws the login screen.
        self.window.fill(self.WHITE)
        self.draw_text("Enter Username", self.BLACK, 400, 150, True)
        pygame.draw.rect(self.window, self.GRAY, self.input_box, 2)
        self.window.blit(
            self.font.render(self.input_text, True, self.BLACK),
            (self.input_box.x + 5, self.input_box.y + 5),
        )

    def draw_lobby(self):  # It draws the lobby screen.
        self.window.fill(self.WHITE)
        self.draw_text("Lobby", self.BLACK, 400, 50, True)
        self.draw_text("Rooms:", self.BLACK, 50, 100)
        self.draw_text(f"Name:{self.username}", self.BLACK, 600, 50, True)
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

        # Create room
        self.draw_text("Create New Room:", self.BLACK, 50, 420)
        pygame.draw.rect(self.window, self.GRAY, self.room_box, 2)
        self.window.blit(
            self.font.render(self.room_input, True, self.BLACK),
            (self.room_box.x + 5, self.room_box.y + 5),
        )

        pygame.draw.rect(self.window, self.GRAY, self.refresh_button)
        self.draw_text(
            "Refresh",
            self.BLACK,
            self.refresh_button.centerx,
            self.refresh_button.centery,
            True,
        )

    def draw_waiting(self):  # It draws the waiting room screen.
        """Draw waiting room screen"""
        self.window.fill(self.WHITE)
        self.draw_text(f"Room: {self.room_name}", self.BLACK, 400, 50, True)
        self.draw_text(f"Name:{self.username}", self.BLACK, 600, 50, True)
        status = "Waiting for players."

        if self.selected_room is not None:
            max_players = self.rooms[self.selected_room]["max_players"]
            if len(self.players) == max_players:  # Ha a szoba tele van, a játék indul
                status = "Game is starting!"
        self.draw_text(status, self.BLACK, 400, 100, True)

        self.draw_text(
            "Players:", self.BLACK, 50, 150
        )  # Displaying the players in the room.
        y = 200
        for player in self.players:
            self.draw_text(player, self.BLACK, 60, y)
            y += 40

        # Leave button
        pygame.draw.rect(self.window, self.GRAY, self.leave_button)
        self.draw_text(
            "Leave Room",
            self.BLACK,
            self.leave_button.centerx,
            self.leave_button.centery,
            True,
        )

    def draw_game(self):  # It draws the game screen.
        self.window.fill(self.WHITE)
        self.draw_text(f"Room: {self.room_name}", self.BLACK, 400, 50, True)
        self.draw_text(f"Name:{self.username}", self.BLACK, 600, 50, True)

        player_buttons = (
            self.get_player_buttons()
        )  # Creating buttons for the players in the room
        for player, rect in player_buttons:
            pygame.draw.rect(self.window, self.GRAY, rect)
            self.draw_text(player, self.BLACK, rect.centerx, rect.centery, True)

        if self.message_display_time > 0:
            self.draw_text(self.message, self.BLACK, 400, 250, True)

        # Leave button
        pygame.draw.rect(self.window, self.GRAY, self.leave_button)
        self.draw_text(
            "Leave Game",
            self.BLACK,
            self.leave_button.centerx,
            self.leave_button.centery,
            True,
        )

    def get_player_buttons(self):  # Creating player buttons.
        player_buttons = []
        x = 50
        for player in self.players:
            if player != self.username:
                player_rect = pygame.Rect(x, 150, 200, 40)
                player_buttons.append((player, player_rect))
                x += 250
        return player_buttons

    def on_login_success(self, username):
        self.username = username
        self.screen = "lobby"

    def on_room_list(self, rooms):  # Updating the list of rooms."
        self.rooms = rooms

    def on_joined_room(self, room_id, name, players):  # Entering a room.
        self.room_id = room_id
        self.room_name = name
        self.players = players
        self.screen = "waiting"

    def on_player_joined(self, players):  # Updating the players in the room.
        self.players = players

    def on_player_left(self, players):  # Updating the players in the room.
        self.players = players

    def show_notification(self, message):  # Displaying a notification.
        self.message = message
        self.message_display_time = 5

    def on_start_game(self, players):  # Starting the game.
        self.players = players
        self.screen = "game"


if __name__ == "__main__":
    client = GameClient()
    client.run()
