import socketio

class NetworkManager:
    def __init__(self, game_client) -> None:
        """
        Args:
            game_client(GameClient): The game client object used to communicate network events.
        """
        self.sio: socketio.Client = socketio.Client()
        self.game_client = game_client

        @self.sio.event
        def connect() -> None:
            """Connection event handler."""
            print("Connected to server")

        @self.sio.event
        def login_success(data: dict) -> None:
            """
            Successful login event handler.

            Args:
                data (dict): A dictionary containing the username.
            """

            if data["screen_state"] is None:
                self.game_client.on_login_success(data["username"])
            else:
                self.game_client.screen = data["screen_state"]
                self.game_client.username = data["username"]
            self.get_rooms()

        @self.sio.event
        def login_error(data: dict) -> None:
            """
            Triggered when the username is already taken.
            Args:
                data (dict): A dictionary containing the server error message.
            """
            self.game_client.on_login_error(data["message"])

        @self.sio.event
        def rejoin_prompt(data: dict) -> None:
            """
            Reconnection request event handler.

            Args:
                data (dict): A dictionary containing the room ID and name.
            """
            self.game_client.show_rejoin_prompt(data["room_id"], data["room_name"])

        @self.sio.event
        def room_list(data: dict) -> None:
            """
            Room list event handler.

            Args:
                data (dict): A dictionary containing the list of available rooms.
            """
            self.game_client.on_room_list(data["rooms"])

        @self.sio.event
        def room_created(data: dict) -> None:
            """
            Room created event handler.

            Args:
                data (dict): A dictionary containing the details of the newly created room.
            """
            self.get_rooms()

        @self.sio.event
        def joined_room(data: dict) -> None:
            """
            Room join event handler.

            Args:
                data (dict): A dictionary containing room details.
            """
            self.game_client.on_joined_room(
                data["room_id"], data["name"], data["players"], data.get("username")
            )

        @self.sio.event
        def player_joined(data: dict) -> None:
            """
            Event handler for when a player joins a room.

            Args:
                data (dict): A dictionary containing the player list and the name of the joining player.
            """
            self.game_client.on_player_joined(data["players"])
            joined_player = data.get("joined_player", "A player")
            self.game_client.show_notification(
                f"{joined_player} csatlakozott a szobához."
            )  # Notification for the joining player

        @self.sio.event
        def player_left(data: dict) -> None:
            """
            Event handler for when a player leaves the room.

            Args:
                data (dict): A dictionary containing the player list and the name of the leaving player.
            """
            self.game_client.on_player_left(data["players"])
            left_player = data.get("left_player", "A player")
            self.game_client.show_notification(
                f"{left_player} left the room."
            )  # Notification for the leaving player

        @self.sio.event
        def user_notification(data: dict) -> None:
            """
            Notification event handler (e.g., join, leave, player click).

            Args:
                data (dict): A dictionary containing the notification message.
            """
            message = data.get("message", "")
            self.game_client.show_notification(message)

        @self.sio.event
        def start_game(data: dict) -> None:
            """
            Game start event handler.

            Args:
                data (dict): A dictionary containing the list of players.
            """
            self.game_client.on_start_game(data["players"])

    def connect(self, server_url: str = "http://localhost:5000") -> None:
        """
        Connect to the server.

        Args:
            server_url (str, optional): The server URL. Default is "http://localhost:5000".
        """
        self.sio.connect(server_url)

    def disconnect(self) -> None:
        """Disconnect from the server."""
        self.sio.disconnect()

    def login(self, username: str) -> None:
        """
        Log in to the server with the provided username.

        Args:
            username (str): The username provided by the user.
        """
        self.sio.emit("login", {"username": username})

    def get_rooms(self) -> None:
        """Request a list of rooms from the server."""
        self.sio.emit("get_rooms")

    def create_room(self, room_name: str) -> None:
        """
        Create a new room.

        Args:
            room_name (str): The name of the new room.
        """
        self.sio.emit("create_room", {"name": room_name})

    def join_room(self, room_id: str) -> None:
        """
        Join a room.

        Args:
            room_id (str): The ID of the room to join.
        """
        self.sio.emit("join_room", {"room_id": room_id, "rejoin": False})

    def leave_room(self, room_id: str) -> None:
        """
        Leave a room.

        Args:
            room_id (str): The ID of the room to leave.
        """
        self.sio.emit("leave_room", {"room_id": room_id})

    def player_click(self, room_id: str, player: str) -> None:
        """
        Send a player click event.

        Args:
            room_id (str): The ID of the room where the click occurred.
            player (str): The name of the clicked player.
        """
        self.sio.emit("player_click", {"room_id": room_id, "clicked_player": player})

    def send_rejoin_decision(self, room_id: str, decision: bool) -> None:
        """
        Send the player's reconnection decision.

        Args:
            room_id (str): The ID of the room where reconnection was requested.
            decision (bool): True if the player wants to rejoin, False otherwise.
        """
        self.sio.emit("rejoin_decision", {"room_id": room_id, "decision": decision})
