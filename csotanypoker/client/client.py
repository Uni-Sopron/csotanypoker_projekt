import time
from typing import Any, Dict, List


import socketio

from csotanypoker.models.card import Card
from csotanypoker.models.player import Player
from csotanypoker.models.room import Room


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
            # print("Connected to server")

        @self.sio.event
        def disconnect() -> None:
            """Disconnection event handler."""
            # print("Disconnected from server")

        @self.sio.on("reconnect_offer")
        def on_reconnect_offer(data: Dict[str, Any]) -> None:
            self.game_client.username = data["username"]
            self.game_client.room_list.clear()
            for room_id, room_info in data["rooms"].items():
                
                room = Room(
                    room_id,
                    room_info["name"],
                    max_player_count=room_info["player_count"],
                )
                room.player_count = room_info["actual_player_count"]
                room.password_protected = room_info["password_protected"]
                room.game_ids = room_info["game_ids"]
                self.game_client.room_list.append(room)

            self.game_client.previous_room_id = data["previous_room_id"]
            self.game_client.room_id = data["previous_room_id"]
            self.game_client.screen = "reconnect_screen"
            for room in self.game_client.room_list:
                if room.game_ids != []:
                    self.game_client.message = "A játék elindult"
                else:
                    self.game_client.message = "A játék még nem indult el"

        @self.sio.on("login_success")
        def on_login_success(data: Dict[str, Any]) -> None:
            """
            Handle successful login.

            Args:
                data: A dictionary containing username and screen_state
            """
            self.game_client.username = data["username"]
            self.game_client.room_list.clear()

            for room_id, room_info in data["rooms"].items():
                room = Room(
                    room_id,
                    room_info["name"],
                    max_player_count=room_info["player_count"],
                )
                room.player_count = room_info["actual_player_count"]
                room.password_protected = room_info["password_protected"]
                self.game_client.room_list.append(room)

            self.game_client.screen = "rooms_screen"

        @self.sio.on("login_error")
        def on_login_error(data: Dict[str, str]) -> None:
            """
            Handle login error.

            Args:
                data: A dictionary containing error message
            """
            # print(f"Login error: {data['message']}")
            self.game_client.login_error = data["message"]
            self.game_client.error_display_time = 3.0

        @self.sio.on("joined_room")
        def on_joined_room(data: Dict[str, Any]) -> None:
            """
            Handle joining a room.

            Args:
                data: Room data including room_id, name, players and username
            """
            # print(f"Joined room: {data}")
            self.game_client.room_id = data["room_id"]
            self.game_client.room_name = data["name"]

            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]

            self.game_client.selected_room = Room(
                data["room_id"],
                data["name"],
                max_player_count=data["max_player_count"],
            )
            self.game_client.selected_room.password = data.get("password", None)
            self.game_client.selected_room.users = self.game_client.game_state.players
            for player in self.game_client.game_state.players:
                if player.name == data["username"]:
                    self.game_client.user = player
            self.game_client.screen = "waiting"

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
            # print("Game started")

            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]
            self.game_client.game_state.voters = []
            for players in self.game_client.game_state.players:
                if players.name == self.game_client.username:
                    self.game_client.user = players
            
            self.game_client.selected_room.game_ids = data.get("game_ids")
            print(f"Game IDs: {self.game_client.selected_room.game_ids}")
            self.game_client.screen = "game"
            self.game_client.message = "A játék elkezdődött!"
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

            self.game_client.game_state

        @self.sio.on("player_data")
        def player_data(data: Dict[str, Any]) -> None:
            kezbenlevo_adatok = data.get("cards_in_hand", [])
            # print("jatekos_nev:", data["name"])
            # print("kezbenlevo_adatok:", kezbenlevo_adatok)
            # print("aktív játékos:", data.get("starting_player", "ismeretlen"))
            # print("játékos_adatok:", data["player_data"])

            for player in self.game_client.game_state.players:
                if player.name == data.get("starting_player", "ismeretlen"):
                    self.game_client.game_state.active_player = player
                    # print(f"Aktív játékos: {player.name}")

                if player.name == self.game_client.username:
                    self.game_client.user = player
                    self.game_client.user.cards_in_hand = []
                    for k in kezbenlevo_adatok:
                        *name_parts, sorszam = k.split("_")
                        name = "_".join(name_parts)
                        self.game_client.user.cards_in_hand.append(
                            Card(name, int(sorszam))
                        )

                player_info = data["player_data"][player.name]
                if player_info:
                    # print(f"Játékos: {player.name}")
                    # print(f"elotte lévő kártyák: {player_info['cards_in_front']}")
                    player.cards_in_front = player_info["cards_in_front"]
                    player.card_count = player_info["card_count"]
                    player.is_active = player_info["is_active"]
                    # print(f"{player.name} - kártyák száma: {player.card_count}")

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
                    # print(self.game_client.game_state.active_player.name)

            self.game_client.message = data["message"]
            self.game_client.dropdown_state = True

        @self.sio.on("game_over")
        def game_over(data) -> None:
            if self.game_client.user.name == data["losing_player"]:
                self.game_client.message = "Vesztettél!"
            else:
                self.game_client.message = "Gratulálok! Nyertél!"
            self.game_client.game_over.start_time = time.time()
            self.game_client.screen = "game_over"

        @self.sio.on("rooms_updated")
        def on_rooms_updated(data: Dict[str, Any]) -> None:
            self.game_client.room_list.clear()

            for room_id, room_info in data["rooms"].items():
                room = Room(
                    room_id,
                    room_info["name"],
                    max_player_count=room_info["player_count"],
                )
                room.player_count = room_info["actual_player_count"]
                room.password_protected = room_info["password_protected"]
                self.game_client.room_list.append(room)

        @self.sio.on("room_players_updated")
        def on_room_players_updated(data: Dict[str, Any]) -> None:
            aktiv_users = data.get("activ_users", [])
            if (
                self.game_client.selected_room
                and self.game_client.selected_room.room_id == data["room_id"]
            ):
                self.game_client.game_state.players = [
                    Player(player) for player in data["players"]
                ]
                self.game_client.selected_room.users = (
                    self.game_client.game_state.players
                )

                for player in self.game_client.game_state.players:
                    player.is_active = player.name in aktiv_users

                    if player.name == self.game_client.username:
                        self.game_client.user = player

        @self.sio.on("join_room_error")
        def on_join_room_error(data: Dict[str, str]) -> None:
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 3.0

        @self.sio.on("left_room")
        def on_left_room(data: Dict[str, str]) -> None:
            print("Left room event received")
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 3.0
            self.game_client.screen = "rooms_screen"
            self.game_client.selected_room = None
            self.game_client.room_id = None
            self.game_client.room_name = None

        @self.sio.on("player_left_room")
        def on_player_left_room(data: Dict[str, Any]) -> None:
            aktiv_users = data.get("activ_users", [])
            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]

            for player in self.game_client.game_state.players:
                player.is_active = player.name in aktiv_users

            if self.game_client.selected_room:
                self.game_client.selected_room.users = (
                    self.game_client.game_state.players
                )
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 3.0

        @self.sio.on("rejoin_waiting_success")
        def on_rejoin_waiting_success(data: Dict[str, Any]) -> None:
            aktiv_users = data["activ_users"]
            print(f"AKTIV USERS: {aktiv_users}")
            self.game_client.game_state.players = [
                Player(player) for player in data["players"]
            ]
            self.game_client.selected_room = Room(
                data["room_id"],
                data["room_name"],
                max_player_count=data["max_player_count"],
            )
            self.game_client.room_name = data["room_name"]
            self.game_client.selected_room.password = data["password"]
            if data["password"] != None:
                self.game_client.selected_room.password_protected = True
            else:
                self.game_client.selected_room.password_protected = False

            if self.game_client.selected_room:
                self.game_client.selected_room.users = (
                    self.game_client.game_state.players
                )
                # self.game_client.selected_room.game_started = False
            self.game_client.selected_room.room_id = data["room_id"]
            for player in self.game_client.game_state.players:
                if player.name == self.game_client.username:
                    self.game_client.user = player
                    break
            for player in self.game_client.game_state.players:
                player.is_active = player.name in aktiv_users
            self.game_client.screen = "waiting"
            self.game_client.message = "Visszaléptél a váróterembe"
            self.game_client.message_display_time = 3.0

        @self.sio.on("rejoin_game_success")
        def on_rejoin_game_success(data: Dict[str, Any]) -> None:
            print("Rejoin game success")
            game_state = data.get("game_state", {})
            self.game_client.username = data["username"]
            self.game_client.previous_room_id = data["previous_room_id"]
            room_id = game_state["room_id"]
            # print(f"Rejoining room: {room_id}")
            active_player = game_state["active_player"]
            # print(f"Active player: {active_player}")
            players = game_state["players"]
            # print(f"Players: {players}")
            active_users = game_state["activ_users"]
            # print(f"Active users: {active_users}")
            max_player_count = game_state["max_player_count"]
            # print(f"Max player count: {max_player_count}")

            self.game_client.current_room_id = room_id
            self.game_client.active_player = active_player
            self.game_client.players = players
            self.game_client.player_data = player_data
            self.game_client.active_users = active_users
            self.game_client.max_player_count = max_player_count

            # print(f"Reconnecting to game in room: {room_id}")
            # print(f"Active player: {active_player}")
            # print(f"Players: {players}")
            # print(f"My username: {self.game_client.username}")
            for players in self.game_client.game_state.players:
                if players.name == self.game_client.username:
                    self.game_client.user = players

            for room in self.game_client.room_list:
                if room.room_id == room_id:
                    self.game_client.room_id = room_id
                    self.game_client.selected_room = Room(
                        data["previous_room_id"],
                        data["room_name"],
                        max_player_count=max_player_count,
                    )

            self.game_client.screen = "game"

        @self.sio.on("rejoin_error")
        def on_rejoin_error(data: Dict[str, str]) -> None:
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 3.0

        @self.sio.on("rematch_vote_received")
        def on_vote_rematch(data: Dict[str, Any]) -> None:
            # print("BELEPETT a rematch_vote_received eseménybe")
            self.game_client.game_state.voters= data["voters"]

        @self.sio.on("player_rejoined")
        def on_player_rejoined(data: Dict[str, Any]) -> None:
            username = data["rejoined_player"]
            for player in self.game_client.game_state.players:
                if player.name == username:
                    player.is_active = True
                    self.game_client.message = (
                        f"{username} újra csatlakozott a játékhoz."
                    )
                    self.game_client.message_display_time = 3.0
                    break

    def logout(self) -> None:
        self.sio.emit("logout", {"username": self.game_client.username})
        # print("Logout request sent")
        self.game_client.screen = "login"
        self.game_client.room_list.clear()
        self.game_client.selected_room = None
        self.game_client.room_id = None
        self.game_client.room_name = None

    def rejoin_game(self) -> None:
        """
        Send a request to rejoin the game after disconnection.
        """
        self.sio.emit(
            "rejoin_game",
            {
                "username": self.game_client.username,
                "room_id": self.game_client.previous_room_id,
            },
        )
        print("Rejoin game request sent")

    def disconnect(self) -> None:
        self.sio.disconnect()
        # print("Disconnected from server")

    def vote_rematch(self, room_id: str, username: str) -> None:
        # print(f"Visszavágó szavazás: {room_id}, {username}")
        self.sio.emit("vote_rematch", {"room_id": room_id, "username": username})

    def all_players_leave_room(self, room_id) -> None:
        self.sio.emit("all_players_leave_room", {"room_id": room_id})

    def rejoin_waiting_room(self) -> None:
        """
        Send a request to rejoin the waiting room after game ends.
        """

        self.sio.emit(
            "rejoin_waiting_room",
            {
                "username": self.game_client.username,
                "room_id": self.game_client.room_id,
            },
        )

    def leave_room(self) -> None:
        self.sio.emit("leave_room", {"username": self.game_client.username})

    def connect(self, server_url: str = "http://localhost:5000") -> None:
        """
        Connect to the server.

        Args:
            server_url (str, optional): The server URL. Default is "http://localhost:5000".
        """
        try:
            self.sio.connect(server_url)
            # print(f"Connected to server at {server_url}")
        except Exception as e:
            # print(f"Connection error: {e}")
            self.game_client.message = f"Kapcsolódási hiba: {e}"
            self.game_client.message_display_time = 3.0

    def login(self, username: str, password: str) -> None:
        self.sio.emit("login", {"username": username, "password": password})

    def register(self, username: str, password: str) -> None:
        self.sio.emit("register", {"username": username, "password": password})

    def join_room(
        self, room_id: str, password: str = "", skipp_password: bool = False
    ) -> None:
        self.sio.emit(
            "join_room",
            {
                "room_id": room_id,
                "password": password,
                "skipp_password": skipp_password,
            },
        )

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

    def create_room(
        self,
        room_name: str,
        password_protected,
        max_player_count: int = 4,
        pasword: str = "",
    ) -> None:
        self.sio.emit(
            "create_room",
            {
                "room_name": room_name,
                "password_protected": password_protected,
                "max_player_count": max_player_count,
                "password": pasword,
            },
        )
