import time
from typing import Any, Dict, List
import socketio
from csotanypoker.models.animal import Animal
from csotanypoker.models.player import OpponentPlayer, VisiblePlayer
from csotanypoker.models.room import Room
from csotanypoker.models.user import Client_User


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
            print("My socket id:", self.sio.sid)

        @self.sio.event
        def disconnect() -> None:
            """Disconnection event handler."""
            print("Disconnected from server")

        @self.sio.on("reconnect_offer")
        def on_reconnect_offer(data: Dict[str, Any]) -> None:
            print("BELEPETT AZ UJRA_csatlakozasba")
            self.game_client.user.username = data["username"]
            self.game_client.room_list.clear()
            for room_id, room_info in data["rooms"].items():
                room = Room(
                    room_id=room_id,
                    name=room_info["name"],
                    max_player_count=room_info["player_count"],
                )
                room.player_count = room_info["actual_player_count"]
                room.password_protected = room_info["password_protected"]

                self.game_client.room_list.append(room)

            self.game_client.previous_room_id = data["previous_room_id"]
            self.game_client.room_id = data["previous_room_id"]
            self.game_client.screen = "reconnect_screen"
            self.game_client.game_start = data.get("game_start")
            if data.get("game_start"):
                self.game_client.message = "A játék elkezdődött"
            else:
                self.game_client.message = "A játék még nem indult el"

        @self.sio.on("login_success")
        def on_login_success(data: Dict[str, Any]) -> None:
            """
            Handle successful login.

            Args:
                data: A dictionary containing username and screen_state
            """

            self.game_client.user = Client_User(
                username=data["user"]["username"], is_active=data["user"]["is_active"]
            )
            self.game_client.room_list.clear()

            for room_id, room_info in data["rooms"].items():
                room = Room(
                    room_id=room_id,
                    name=room_info["name"],
                    max_player_count=room_info["max_player_count"],
                    player_count=room_info["player_count"],
                    password_protected=room_info["password_protected"],
                )
                self.game_client.room_list.append(room)

            self.game_client.screen = "rooms_screen"

        @self.sio.on("login_error")
        def on_login_error(data: Dict[str, str]) -> None:
            """
            Handle login error.

            Args:
                data: A dictionary containing error message
            """

            self.game_client.login_error = data["message"]
            self.game_client.error_display_time = 30.0

        @self.sio.on("register_error")
        def on_register_error(data: Dict[str, str]) -> None:
            self.game_client.login_error = data["message"]
            self.game_client.error_display_time = 30.0

        @self.sio.on("joined_room")
        def on_joined_room(data: Dict[str, Any]) -> None:
            print(f"Joined room: {data}")
            self.game_client.room_id = data["room_id"]
            self.game_client.room_name = data["name"]

            self.game_client.users = [
                Client_User(username=player["username"], is_active=player["is_active"])
                for player in data["players"]
            ]

            self.game_client.selected_room = Room(
                room_id=data["room_id"],
                name=data["name"],
                player_count=len(self.game_client.users),
                max_player_count=data["max_player_count"],
            )

            self.game_client.screen = "waiting"

            @self.sio.on("start_game")
            def on_start_game(data: Dict[str, List[str]]) -> None:
                print("=== GAME STARTING ===")

                player_list = data.get("players", [])

                self.game_client.visible_player = None
                self.game_client.opponent_players = []

                for player_username in player_list:
                    if self.game_client.user.username == player_username:
                        print(f"Setting up my player: {player_username}")
                        self.game_client.visible_player = VisiblePlayer(
                            username=player_username,
                        )
                    else:
                        print(f"Adding opponent: {player_username}")
                        self.game_client.opponent_players.append(
                            OpponentPlayer(
                                username=player_username,
                            )
                        )
                self.game_client.players = [
                    self.game_client.visible_player
                ] + self.game_client.opponent_players

        @self.sio.on("game_over")
        def game_over(data) -> None:
            self.game_client.losing_player_name = None

            if self.game_client.user.username == data["losing_player"]:
                self.game_client.game_over_message = "Vesztettél!"

            else:
                self.game_client.game_over_message = "Gratulálok! Nyertél!"
                self.game_client.losing_player_name = data["losing_player"]

            self.game_client.game_over.start_time = time.time()
            self.game_client.screen = "game_over"

        @self.sio.on("Game_state")
        def on_game_state(data: Dict[str, Any]) -> None:
            game_state = data.get("game_state", {})

            visible_player_data = data.get("visible_player_data", {})

            opponent_players_data = data.get("opponent_players_data", [])
            print(f"\n=== OPPONENT PLAYERS DATA ===")
            for i, opponent in enumerate(opponent_players_data):
                print(f"Opponent {i + 1}:")
                print(f"  Username: {opponent.get('username')}")
                print(f"  Cards in front: {opponent.get('cards_in_front', {})}")
                print(f"  Card count: {opponent.get('card_count_int', 0)}")
                print(f"  Statement: {opponent.get('statement', '')}")
                print(f"  Is true: {opponent.get('is_true', '')}")

            self.game_client.game_state.game_id = game_state.get("game_id")
            self.game_client.game_state.room_id = game_state.get("room_id")
            self.game_client.game_state.active_player = game_state.get("active_player")
            self.game_client.game_state.targeted_player = game_state.get(
                "targeted_player"
            )
            self.game_client.game_state.question_card = game_state.get("question_card")
            self.game_client.game_state.visited_already = game_state.get(
                "visited_already", []
            )
            self.game_client.game_state.voters = game_state.get("voters", [])

            cards_in_hand = []
            for card_name in visible_player_data.get("cards_in_hand", []):
                try:
                    cards_in_hand.append(Animal(card_name))
                except KeyError:
                    print(f"Warning: Unknown animal card: {card_name}")

            cards_in_front = {}
            for animal_name, count in visible_player_data.get(
                "cards_in_front", {}
            ).items():
                try:
                    cards_in_front[Animal(animal_name)] = count
                except KeyError:
                    print(f"Warning: Unknown animal in front: {animal_name}")

            self.game_client.visible_player = VisiblePlayer(
                username=visible_player_data.get("username", ""),
                cards_in_hand=cards_in_hand,
                cards_in_front=cards_in_front,
                statement=visible_player_data.get("statement", ""),
                is_true=visible_player_data.get("is_true"),
            )

            self.game_client.opponent_players = []
            for opponent_data in opponent_players_data:
                print(f"Processing opponent: {opponent_data.get('username')}")
                opponent_cards_in_front = {}
                for animal_name, count in opponent_data.get(
                    "cards_in_front", {}
                ).items():
                    try:
                        opponent_cards_in_front[Animal(animal_name)] = count
                    except KeyError:
                        print(f"Warning: Unknown opponent animal: {animal_name}")

                opponent = OpponentPlayer(
                    username=opponent_data.get("username", ""),
                    cards_in_front=opponent_cards_in_front,
                    statement=opponent_data.get("statement", ""),
                    is_true=opponent_data.get("is_true"),
                    card_count_int=opponent_data.get("card_count_int", 0),
                )
                print(
                    f"Opponent player: {opponent.username}, Cards in front: {opponent.cards_in_front}, Card count: {opponent.card_count_int}"
                )
                self.game_client.opponent_players.append(opponent)

            self.game_client.screen = "game"

        @self.sio.on("rooms_updated")
        def on_rooms_updated(data: Dict[str, Any]) -> None:
            new_rooms_data = data["rooms"]

            current_room_ids = set(room.room_id for room in self.game_client.room_list)
            new_room_ids = set(new_rooms_data.keys())

            rooms_changed = current_room_ids != new_room_ids

            if not rooms_changed:
                for room in self.game_client.room_list:
                    if room.room_id in new_rooms_data:
                        new_room_info = new_rooms_data[room.room_id]
                        if (
                            room.player_count != new_room_info["player_count"]
                            or room.name != new_room_info["name"]
                            or room.max_player_count
                            != new_room_info["max_player_count"]
                            or room.password_protected
                            != new_room_info["password_protected"]
                        ):
                            rooms_changed = True
                            break

            if rooms_changed:
                self.game_client.room_list.clear()
                for room_id, room_info in new_rooms_data.items():
                    room = Room(
                        room_id=room_id,
                        name=room_info["name"],
                        max_player_count=room_info["max_player_count"],
                        password_protected=room_info["password_protected"],
                        player_count=room_info["player_count"],
                    )
                    print(f"Room updated: {room.name},{room.player_count}")
                    self.game_client.room_list.append(room)
            else:
                print("Rooms data unchanged, skipping update")

        @self.sio.on("room_players_updated")
        def on_room_players_updated(data: Dict[str, Any]) -> None:
            if (
                self.game_client.selected_room
                and self.game_client.selected_room.room_id == data["room"]["room_id"]
            ):
                self.game_client.users = [
                    Client_User(
                        username=player["username"], is_active=player["is_active"]
                    )
                    for player in data["players"]
                ]
                self.game_client.selected_room.player_count = len(
                    self.game_client.users
                )

        @self.sio.on("join_room_error")
        def on_join_room_error(data: Dict[str, str]) -> None:
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 30.0

        @self.sio.on("left_room")
        def on_left_room(data: Dict[str, str]) -> None:
            print("Left room event received")
            self.game_client.message = data["message"]
            self.game_client.message_display_time = 30.0

            self.game_client.selected_room = None
            self.game_client.room_id = None
            self.game_client.room_name = None
            self.game_client.users = []

            self.game_client.screen = "rooms_screen"

        @self.sio.on("player_left_room")
        def on_player_left_room(data: Dict[str, Any]) -> None:
            self.game_client.users = [
                Client_User(username=player["username"], is_active=player["is_active"])
                for player in data["players"]
            ]

            self.game_client.message = data["message"]
            self.game_client.message_display_time = 50
            if self.game_client.selected_room is not None:
                self.game_client.selected_room.player_count = len(
                    self.game_client.users
                )

        @self.sio.on("rejoin_waiting_success")
        def on_rejoin_waiting_success(data: Dict[str, Any]) -> None:
            self.game_client.users = [
                Client_User(username=player["username"], is_active=player["is_active"])
                for player in data["players"]
            ]
            self.game_client.selected_room = Room(
                room_id=data["room_id"],
                name=data["room_name"],
                max_player_count=data["max_player_count"],
            )
            self.game_client.room_name = data["room_name"]

            self.game_client.selected_room.room_id = data["room_id"]

            self.game_client.screen = "waiting"
            self.game_client.message = "Visszaléptél a váróterembe"
            self.game_client.message_display_time = 30.0

        @self.sio.on("rematch_vote_received")
        def on_vote_rematch(data: Dict[str, Any]) -> None:
            print("BELEPETT a rematch_vote_received eseménybe")
            self.game_client.game_state.voters = set(data["voters"])
            print(f"Voters updated: {self.game_client.game_state.voters}")

        @self.sio.on("player_rejoined")
        def on_player_rejoined(data: Dict[str, Any]) -> None:
            username = data["rejoined_player"]

            for user in self.game_client.users:
                if user.username == username:
                    user.is_active = True
            self.game_client.selected_room.player_count = len(self.game_client.users)

            self.game_client.message = f"{username} újra csatlakozott a játékhoz."
            self.game_client.message_display_time = 30.0

    def logout(self) -> None:
        self.sio.emit("logout", {"username": self.game_client.user.username})

        self.game_client.screen = "login"
        self.game_client.room_list.clear()
        self.game_client.selected_room = None
        self.game_client.room_id = None
        self.game_client.room_name = None

    def disconnect(self) -> None:
        self.sio.disconnect()

    def vote_rematch(self, room_id: str, username: str) -> None:
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
                "username": self.game_client.user.username,
                "room_id": self.game_client.room_id,
            },
        )

    def leave_room(self) -> None:
        self.sio.emit("leave_room", {"username": self.game_client.user.username})

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
            self.game_client.message_display_time = 30.0

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

    def guess(self, guess: str) -> None:
        self.sio.emit("guess", {"guess": guess})

    def oke_click(self, statement, passing) -> None:
        try:
            original_question_card = self.game_client.game_state.question_card

            if isinstance(original_question_card, str):
                pass
            elif original_question_card is None:
                pass
            elif hasattr(original_question_card, "value"):
                self.game_client.game_state.question_card = original_question_card.value

            game_state = self.game_client.game_state.model_dump()

            self.game_client.game_state.question_card = original_question_card

        except Exception as e:
            game_state = {
                "game_id": getattr(self.game_client.game_state, "game_id", ""),
                "room_id": getattr(self.game_client.game_state, "room_id", ""),
                "active_player": getattr(
                    self.game_client.game_state, "active_player", ""
                ),
                "targeted_player": getattr(
                    self.game_client.game_state, "targeted_player", None
                ),
                "question_card": None
                if original_question_card is None
                else (
                    original_question_card.value
                    if hasattr(original_question_card, "value")
                    else str(original_question_card)
                ),
                "visited_already": getattr(
                    self.game_client.game_state, "visited_already", []
                ),
                "voters": getattr(self.game_client.game_state, "voters", []),
            }

        self.sio.emit(
            "oke_click",
            {
                "game_state": game_state,
                "statement": statement,
                "pass": passing,
            },
        )

    def passing(self) -> None:
        self.sio.emit("pass")

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
