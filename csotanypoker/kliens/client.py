import socketio
from typing import Dict, Any, List
from csotanypoker.models.model import Player, Card


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
            self.game_client.screen = "login"
            print("Connected to server")

        @self.sio.event
        def disconnect() -> None:
            """Disconnection event handler."""
            print("Disconnected from server")

        @self.sio.on("login_success")
        def on_login_success(data: Dict[str, Any]) -> None:
            """
            Handle successful login.

            Args:
                data: A dictionary containing username and screen_state
            """
            print(f"Login successful: {data}")
            self.game_client.username = data["username"]

            self.game_client.screen = "waiting"

        @self.sio.on("login_error")
        def on_login_error(data: Dict[str, str]) -> None:
            """
            Handle login error.

            Args:
                data: A dictionary containing error message
            """
            print(f"Login error: {data['message']}")
            self.game_client.login_error = data["message"]
            self.game_client.error_display_time = 3.0  # Display for 3 seconds

        @self.sio.on("joined_room")
        def on_joined_room(data: Dict[str, Any]) -> None:
            """
            Handle joining a room.

            Args:
                data: Room data including room_id, name, players and username
            """
            print(f"Joined room: {data}")
            self.game_client.room_id = data["room_id"]
            self.game_client.room_name = data["name"]

            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]
            for player in self.game_client.game_state.players:
                if player.name == data["username"]:
                    self.game_client.user = player

        @self.sio.on("player_joined")
        def on_player_joined(data: Dict[str, Any]) -> None:
            """
            Handle a player joining the room.

            Args:
                data: A dictionary containing players list and joined_player
            """

            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]
            self.game_client.message = (
                f"{data['joined_player']} csatlakozott a szobához."
            )
            self.game_client.message_display_time = 3.0

        @self.sio.on("start_game")
        def on_start_game(data: Dict[str, List[str]]) -> None:
            """
            Handle game start.

            Args:
                data: A dictionary containing players list
            """
            print("Game started")
            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]
            for players in self.game_client.game_state.players:
                if players.name == self.game_client.username:
                    self.game_client.user = players

            self.game_client.screen = "game"
            self.game_client.message = "A játék elkezdődött!"
            self.game_client.message_display_time = 3.0

        @self.sio.on("error")
        def on_error(data: Dict[str, str]) -> None:
            """
            Handle general errors.

            Args:
                data: A dictionary containing error message
            """
            print(f"Error: {data['message']}")
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 3.0

        @self.sio.on("card_placed")
        def on_card_placed(data: Dict[str, Any]) -> None:
            """
            Handle card placement event.

            Args:
                data: A dictionary containing placement information
            """

            self.game_client.game_state.question_card = None
            self.game_client.selected_card = None

            self.game_client.message = f"{data['player']} elé lehelyezésre került egy {data['card_type']} kártya."

            self.game_client.passed = False
            self.game_client.dropdown_state = False

        @self.sio.on("cards_in_hand")
        def cards_in_hand(data) -> None:
            self.game_client.user.cards_in_hand = []
            for k in data.get("cards_in_hand", []):
                name, index = k.rsplit("_", 1)

                self.game_client.user.cards_in_hand.append(Card(name, int(index)))
            print("cards_in_hand:")
            for card in self.game_client.user.cards_in_hand:
                print(f"nev: {card.name}, sorszam: {card.sorszam}")
            self.game_client.game_state

        @self.sio.on("player_data")
        def player_data(data: Dict[str, Any]) -> None:
            """
            Handle player data.

            Args:
                data: A dictionary containing player data
            """

            kezbenlevo_adatok = data.get("cards_in_hand", [])
            for player in self.game_client.game_state.players:
                if player.name == data.get("starting_player", "ismeretlen"):
                    self.game_client.game_state.active_player = player
                    print(self.game_client.game_state.active_player.name)
                if player.name == self.game_client.username:
                    self.game_client.user.cards_in_hand = []
                    for k in kezbenlevo_adatok:
                        name, sorszam = k.rsplit("_", 1)

                        self.game_client.user.cards_in_hand.append(
                            Card(name, int(sorszam))
                        )

                player.cards_in_front = data.get("player_data", {})[player.name][
                    "cards_in_front"
                ]
                player.card_count = data.get("player_data", {})[player.name][
                    "card_count"
                ]
                print(
                    "kartyak szama: ",
                    data.get("player_data", {})[player.name]["card_count"],
                )
                print(player.card_count)
            self.game_client.passed = False

        @self.sio.on("card_passing")
        def card_passing(data) -> None:
            self.game_client.game_state.active_player.statement = data.get(
                "player_statement", ""
            )

            self.game_client.game_state.question_card = Card("kerdojel", 0)
            for player in self.game_client.game_state.players:
                if player.name == data.get("targeted_player", "ismeretlen"):
                    self.game_client.game_state.targeted_player = player

            self.game_client.game_state.question_card.visited_already = data[
                "visited_by"
            ]

            if self.game_client.user.name == data.get("targeted_player", ""):
                self.game_client.message = (
                    f"Kártyát kaptál: {data.get('card_giver', '')}"
                )
            elif self.game_client.user.name == data.get("card_giver", ""):
                self.game_client.message = (
                    f"Kártyát adtál: {data.get('targeted_player', '')}"
                )
            else:
                self.game_client.message = f"{data.get('card_giver', '')}-tól kártyát kapott {data.get('targeted_player', '')}"

        @self.sio.on("card_content")
        def card_content(data) -> None:
            self.game_client.game_state.question_card = Card(
                data["card_type"], data["card_index"]
            )
            print(f"kerdeses_kartya: {self.game_client.game_state.question_card.type}")
            print(f"kerdeses_kartya: {self.game_client.game_state.question_card.index}")
            self.game_client.selected_card = Card(data["card_type"], data["card_index"])
            self.game_client.selected_card.visited_already = data["visited_by"]

            self.game_client.game_state.question_card.visited_already = data[
                "visited_by"
            ]

        @self.sio.on("passed")
        def passed(data) -> None:
            for player in self.game_client.game_state.players:
                if player.name == data.get("active_player", "ismeretlen"):
                    self.game_client.game_state.active_player = player
                    print(self.game_client.game_state.active_player.name)

            self.game_client.message = data["message"]
            self.game_client.dropdown_state = True

        @self.sio.on("hiba")
        def hiba(data) -> None:
            self.game_client.message = data["message"]
            self.game_client.passed = False

        @self.sio.on("game_over")
        def game_over(data) -> None:
            if self.game_client.user.name == data["losing_player"]:
                self.game_client.message = "Vesztettél!"
            else:
                self.game_client.message = "Gratulálok! Nyertél!"
            self.game_client.screen = "game_over"

    def connect(self, server_url: str = "http://localhost:5000") -> None:
        """
        Connect to the server.

        Args:
            server_url (str, optional): The server URL. Default is "http://localhost:5000".
        """
        try:
            self.sio.connect(server_url)
            print(f"Connected to server at {server_url}")
        except Exception as e:
            print(f"Connection error: {e}")
            self.game_client.message = f"Kapcsolódási hiba: {e}"
            self.game_client.message_display_time = 3.0

    def disconnect(self) -> None:
        """Disconnect from the server."""
        if self.sio.connected:
            self.sio.disconnect()

    def login(self, username: str) -> None:
        """
        Log in to the server with the provided username.

        Args:
            username (str): The username provided by the user.
        """
        self.sio.emit("login", {"username": username})

    def guess(self, room_id: str, guess: str) -> None:
        self.sio.emit("guess", {"room_id": room_id, "guess": guess})

    def oke_click(
        self, room_id: str, selected_player, selected_card, statement, passing
    ) -> None:
        """
        Send an OK click event.

        Args:
            room_id (str): The ID of the current room
        """
        self.sio.emit(
            "oke_click",
            {
                "room_id": room_id,
                "selected_player": selected_player,
                "selected_card": selected_card.name,
                "set_card_giver": statement,
                "pass": passing,
            },
        )

    def passing(self, room_id: str) -> None:
        self.sio.emit("pass", {"room_id": room_id})
