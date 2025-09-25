import time
from typing import Any, Dict, List
import socketio
from csotanypoker.client.drawing_helpers import this_is_ai_name
from csotanypoker.models.animal import Animal
from csotanypoker.models.player import OpponentPlayer, VisiblePlayer
from csotanypoker.models.room import Room
from csotanypoker.models.user import Client_User
import threading


class NetworkManager:
    def __init__(self, game_client) -> None:
        """
        Args:
            game_client(GameClient): The game client object used to communicate network events.
        """
        self.sio: socketio.Client = socketio.Client()
        self.game_client = game_client
        self._update_in_progress = False
        self._data_lock = threading.RLock()

        @self.sio.event
        def connect() -> None:
            """Connection event handler."""
            with self._data_lock:
                self.game_client.screen = "login"

        @self.sio.event
        def disconnect() -> None:
            """Disconnection event handler."""
            print("Disconnected from server")

        @self.sio.on("ai_player_add_error")
        def on_ai_player_add_error(data: Dict[str, Any]) -> None:
            with self._data_lock:
                self.game_client.message = data.get("message", "AI hozzáadási hiba")
                self.game_client.message_display_time = 30.0

        @self.sio.on("reconnect_offer")
        def on_reconnect_offer(data: Dict[str, Any]) -> None:
            with self._data_lock:
                self.game_client.message = None
                try:
                    if self.game_client.user is None:
                        self.game_client.user = Client_User(
                            username=data.get("username", ""),
                            is_active=True,
                        )
                    else:
                        self.game_client.user.username = data.get("username", "")
                        self.game_client.user.is_active = True

                    if (
                        not hasattr(self.game_client, "room_list")
                        or self.game_client.room_list is None
                    ):
                        self.game_client.room_list = []
                    else:
                        self.game_client.room_list.clear()

                    rooms_data = data.get("rooms", {})
                    previos_room_data = data["previous_room"]
                    self.game_client.previous_room = Room(
                        room_id=previos_room_data["room_id"],
                        name=previos_room_data["name"],
                        max_player_count=previos_room_data["player_count"],
                    )
                    self.game_client.previous_room.player_count = previos_room_data[
                        "actual_player_count"
                    ]
                    self.game_client.previous_room.password_protected = (
                        previos_room_data["password_protected"]
                    )

                    for room_id, room_info in rooms_data.items():
                        try:
                            name = room_info.get("name", "Unknown Room")
                            player_count = room_info.get("player_count", 4)
                            actual_player_count = room_info.get(
                                "actual_player_count", 0
                            )
                            password_protected = room_info.get(
                                "password_protected", False
                            )

                            if not isinstance(name, str):
                                name = str(name)
                            if not isinstance(player_count, int) or player_count <= 0:
                                player_count = 4
                            if (
                                not isinstance(actual_player_count, int)
                                or actual_player_count < 0
                            ):
                                actual_player_count = 0

                            room = Room(
                                room_id=room_id,
                                name=name,
                                max_player_count=player_count,
                            )
                            room.player_count = actual_player_count
                            room.password_protected = bool(password_protected)

                            self.game_client.room_list.append(room)

                        except Exception as e:
                            print(f"Error creating room in reconnect_offer: {e}")
                            continue

                    self.game_client.previous_room_id = data.get("previous_room_id")
                    self.game_client.room_id = data.get("previous_room_id")
                    self.game_client.screen = "reconnect_screen"
                    self.game_client.game_start = data.get("game_start", False)

                    self.get_user_stats(self.game_client.user.username)
                    if data.get("game_start"):
                        self.game_client.message = "A játék elkezdődött"
                    else:
                        self.game_client.message = "A játék még nem indult el"

                except Exception as e:
                    print(f"Critical error in reconnect_offer handler: {e}")
                    self.game_client.message = None
                    self.game_client.screen = "login"
                    if not hasattr(self.game_client, "room_list"):
                        self.game_client.room_list = []

        @self.sio.on("login_success")
        def on_login_success(data: Dict[str, Any]) -> None:
            """Handle successful login."""
            with self._data_lock:
                try:
                    self.game_client.user = None
                    user_data = data.get("user", {})
                    print(f"Login success, user data: {user_data}")
                    self.game_client.user = Client_User(
                        username=user_data.get("username", ""),
                        is_active=user_data.get("is_active", True),
                    )

                    self.get_user_stats(self.game_client.user.username)

                    time.sleep(0.5)
                    if (
                        not hasattr(self.game_client, "room_list")
                        or self.game_client.room_list is None
                    ):
                        self.game_client.room_list = []
                    else:
                        self.game_client.room_list.clear()

                    rooms_data = data.get("rooms", {})
                    for room_id, room_info in rooms_data.items():
                        try:
                            room = Room(
                                room_id=room_id,
                                name=room_info.get("name", "Unknown Room"),
                                max_player_count=room_info.get("max_player_count", 4),
                                player_count=room_info.get("player_count", 0),
                                password_protected=room_info.get(
                                    "password_protected", False
                                ),
                            )
                            self.game_client.room_list.append(room)
                        except Exception as e:
                            print(f"Error creating room in login_success: {e}")
                            continue

                    self.game_client.screen = "rooms_screen"

                except Exception as e:
                    print(f"Error in login_success: {e}")

        @self.sio.on("login_error")
        def on_login_error(data: Dict[str, str]) -> None:
            """Handle login error."""
            with self._data_lock:
                self.game_client.message = data.get("message", "Ismeretlen hiba")
                self.game_client.message_display_time = 30.0

        @self.sio.on("register_error")
        def on_register_error(data: Dict[str, str]) -> None:
            with self._data_lock:
                self.game_client.message = data.get("message", "Regisztrációs hiba")
                self.game_client.message_display_time = 30.0

        @self.sio.on("joined_room")
        def on_joined_room(data: Dict[str, Any]) -> None:
            print(f"Joined room: {data}")
            with self._data_lock:
                try:
                    self.game_client.room_id = data.get("room_id")
                    self.game_client.room_name = data.get("name")

                    players_data = data.get("players", [])
                    self.game_client.users = []
                    for player_data in players_data:
                        if isinstance(player_data, dict):
                            user = Client_User(
                                username=player_data.get("username", ""),
                                is_active=player_data.get("is_active", False),
                            )
                            self.game_client.users.append(user)

                    self.game_client.selected_room = Room(
                        room_id=data.get("room_id", ""),
                        name=data.get("name", ""),
                        player_count=len(self.game_client.users),
                        max_player_count=data.get("max_player_count", 4),
                    )

                    self.game_client.screen = "waiting"
                except Exception as e:
                    print(f"Error in joined_room: {e}")

        @self.sio.on("start_game")
        def on_start_game(data: Dict[str, List[str]]) -> None:
            print("=== GAME STARTING ===")
            with self._data_lock:
                try:
                    player_list = data.get("players", [])

                    self.game_client.visible_player = None
                    self.game_client.opponent_players = []

                    if not self.game_client.user or not self.game_client.user.username:
                        print("Error: No valid user found during game start")
                        return

                    for player_username in player_list:
                        if not isinstance(player_username, str):
                            print(
                                f"Warning: Invalid player username: {player_username}"
                            )
                            continue

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

                    if self.game_client.visible_player:
                        self.game_client.players = [
                            self.game_client.visible_player
                        ] + self.game_client.opponent_players
                    else:
                        print("Warning: visible_player is None after game start")
                        self.game_client.players = self.game_client.opponent_players

                except Exception as e:
                    print(f"Error in start_game: {e}")

        @self.sio.on("game_over")
        def game_over(data) -> None:
            with self._data_lock:
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
            """Thread-safe game state update with comprehensive error handling."""
            with self._data_lock:
                if self._update_in_progress:
                    print("Update already in progress, skipping...")
                    return

                self._update_in_progress = True
                try:
                    game_state = data.get("game_state", {})
                    visible_player_data = data.get("visible_player_data", {})
                    opponent_players_data = data.get("opponent_players_data", [])

                    if (
                        hasattr(self.game_client, "game_state")
                        and self.game_client.game_state
                    ):
                        self.game_client.game_state.game_id = game_state.get("game_id")
                        self.game_client.game_state.room_id = game_state.get("room_id")
                        self.game_client.game_state.active_player = game_state.get(
                            "active_player"
                        )
                        self.game_client.game_state.targeted_player = game_state.get(
                            "targeted_player"
                        )
                        self.game_client.game_state.question_card = game_state.get(
                            "question_card"
                        )
                        print(
                            "a szerver visited_already:",
                            game_state.get("visited_already"),
                        )

                        visited_already_data = game_state.get("visited_already", [])
                        if isinstance(visited_already_data, list):
                            self.game_client.game_state.visited_already = set(
                                visited_already_data
                            )
                        else:
                            self.game_client.game_state.visited_already = set()

                        voters_data = game_state.get("voters", [])
                        if isinstance(voters_data, list):
                            self.game_client.game_state.voters = set(voters_data)
                        else:
                            self.game_client.game_state.voters = set()

                    if visible_player_data:
                        cards_in_hand = []
                        cards_in_hand_data = visible_player_data.get(
                            "cards_in_hand", []
                        )
                        print(f"cards_in_hand_data: {cards_in_hand_data}")
                        if isinstance(cards_in_hand_data, list):
                            for card_name in cards_in_hand_data:
                                if card_name and isinstance(card_name, str):
                                    try:
                                        cards_in_hand.append(Animal(card_name))
                                    except (KeyError, ValueError) as e:
                                        print(
                                            f"Warning: Unknown animal card: {card_name} - {e}"
                                        )

                        cards_in_front = {}
                        cards_in_front_data = visible_player_data.get(
                            "cards_in_front", {}
                        )

                        if isinstance(cards_in_front_data, dict):
                            for animal_name, count in cards_in_front_data.items():
                                if animal_name and isinstance(animal_name, str):
                                    try:
                                        cards_in_front[Animal(animal_name)] = (
                                            int(count) if count is not None else 0
                                        )
                                    except (KeyError, ValueError) as e:
                                        print(
                                            f"Warning: Unknown animal in front: {animal_name} - {e}"
                                        )

                        username = visible_player_data.get("username", "")
                        if username:
                            self.game_client.visible_player = VisiblePlayer(
                                username=username,
                                cards_in_hand=cards_in_hand,
                                cards_in_front=cards_in_front,
                                statement=visible_player_data.get("statement", ""),
                                is_true=visible_player_data.get("is_true"),
                            )
                        else:
                            print("Warning: No username in visible_player_data")

                    new_opponent_players = []
                    if isinstance(opponent_players_data, list):
                        for opponent_data in opponent_players_data:
                            if not isinstance(opponent_data, dict):
                                continue

                            try:
                                username = opponent_data.get("username", "")
                                if not username:
                                    print("Warning: Opponent without username")
                                    continue

                                print(f"Processing opponent: {username}")

                                opponent_cards_in_front = {}
                                cards_in_front_data = opponent_data.get(
                                    "cards_in_front", {}
                                )

                                if isinstance(cards_in_front_data, dict):
                                    for (
                                        animal_name,
                                        count,
                                    ) in cards_in_front_data.items():
                                        if animal_name and isinstance(animal_name, str):
                                            try:
                                                opponent_cards_in_front[
                                                    Animal(animal_name)
                                                ] = (
                                                    int(count)
                                                    if count is not None
                                                    else 0
                                                )
                                            except (KeyError, ValueError) as e:
                                                print(
                                                    f"Warning: Unknown opponent animal: {animal_name} - {e}"
                                                )

                                opponent = OpponentPlayer(
                                    username=username,
                                    cards_in_front=opponent_cards_in_front,
                                    statement=opponent_data.get("statement", ""),
                                    is_true=opponent_data.get("is_true"),
                                    card_count_int=int(
                                        opponent_data.get("card_count_int", 0)
                                    ),
                                )

                                print(
                                    f"Opponent player: {opponent.username}, Cards in front: {len(opponent.cards_in_front)}, Card count: {opponent.card_count_int}"
                                )
                                new_opponent_players.append(opponent)

                            except Exception as e:
                                print(
                                    f"Error processing opponent {opponent_data.get('username', 'unknown')}: {e}"
                                )
                                continue

                    self.game_client.opponent_players = new_opponent_players

                    if (
                        self.game_client.visible_player
                        and hasattr(self.game_client, "game_state")
                        and self.game_client.game_state
                    ):
                        self.game_client.screen = "game"
                        # if self.game_client._screens["game"]:
                        #     self.game_client._screens["game"]._reset_local_selections()
                    else:
                        print(
                            "Warning: Not switching to game screen due to missing data"
                        )

                except Exception as e:
                    print(f"Critical error in Game_state handler: {e}")
                    import traceback

                    traceback.print_exc()
                finally:
                    self._update_in_progress = False

        @self.sio.on("rooms_updated")
        def on_rooms_updated(data: Dict[str, Any]) -> None:
            self.get_user_stats(self.game_client.user.username)
            with self._data_lock:
                try:
                    new_rooms_data = data.get("rooms", {})

                    current_rooms = []
                    current_room_ids = set()

                    try:
                        if (
                            hasattr(self.game_client, "room_list")
                            and self.game_client.room_list
                        ):
                            current_rooms = [
                                room
                                for room in self.game_client.room_list
                                if room is not None
                            ]
                            current_room_ids = {
                                getattr(room, "room_id", None)
                                for room in current_rooms
                                if hasattr(room, "room_id")
                            }
                            current_room_ids.discard(None)
                    except Exception as e:
                        print(f"Error processing current rooms: {e}")
                        current_room_ids = set()

                    new_room_ids = set(new_rooms_data.keys())

                    rooms_changed = current_room_ids != new_room_ids

                    if not rooms_changed and current_rooms:
                        for room in current_rooms:
                            try:
                                room_id = getattr(room, "room_id", None)
                                if room_id and room_id in new_rooms_data:
                                    new_room_info = new_rooms_data[room_id]
                                    if (
                                        getattr(room, "player_count", 0)
                                        != new_room_info.get("player_count", 0)
                                        or getattr(room, "name", "")
                                        != new_room_info.get("name", "")
                                        or getattr(room, "max_player_count", 0)
                                        != new_room_info.get("max_player_count", 0)
                                        or getattr(room, "password_protected", False)
                                        != new_room_info.get(
                                            "password_protected", False
                                        )
                                    ):
                                        rooms_changed = True
                                        break
                            except Exception as e:
                                print(f"Error checking room changes: {e}")
                                rooms_changed = True
                                break

                    if rooms_changed:
                        new_room_list = []

                        for room_id, room_info in new_rooms_data.items():
                            try:
                                name = room_info.get("name", "Unknown Room")
                                max_player_count = room_info.get("max_player_count", 4)
                                player_count = room_info.get("player_count", 0)
                                password_protected = room_info.get(
                                    "password_protected", False
                                )

                                if not isinstance(name, str):
                                    name = str(name)
                                if (
                                    not isinstance(max_player_count, int)
                                    or max_player_count <= 0
                                ):
                                    max_player_count = 4
                                if (
                                    not isinstance(player_count, int)
                                    or player_count < 0
                                ):
                                    player_count = 0
                                if not isinstance(password_protected, bool):
                                    password_protected = bool(password_protected)

                                room = Room(
                                    room_id=room_id,
                                    name=name,
                                    max_player_count=max_player_count,
                                    password_protected=password_protected,
                                    player_count=player_count,
                                )
                                new_room_list.append(room)
                                print(f"Room created: {room.name}, {room.player_count}")

                            except Exception as e:
                                print(f"Error creating room object for {room_id}: {e}")
                                continue

                        self.game_client.room_list = new_room_list
                        print(f"Room list updated with {len(new_room_list)} rooms")
                    else:
                        print("Rooms data unchanged, skipping update")

                except Exception as e:
                    print(f"Critical error in rooms_updated handler: {e}")

                    if (
                        not hasattr(self.game_client, "room_list")
                        or self.game_client.room_list is None
                    ):
                        self.game_client.room_list = []

        @self.sio.on("room_players_updated")
        def on_room_players_updated(data: Dict[str, Any]) -> None:
            with self._data_lock:
                try:
                    room_data = data.get("room", {})
                    players_data = data.get("players", [])

                    if (
                        self.game_client.selected_room
                        and self.game_client.selected_room.room_id
                        == room_data.get("room_id")
                    ):
                        self.game_client.users = []
                        for player_data in players_data:
                            if isinstance(player_data, dict):
                                user = Client_User(
                                    username=player_data.get("username", ""),
                                    is_active=player_data.get("is_active", False),
                                )
                                self.game_client.users.append(user)

                        self.game_client.selected_room.player_count = len(
                            self.game_client.users
                        )
                except Exception as e:
                    print(f"Error in room_players_updated: {e}")

        @self.sio.on("join_room_error")
        def on_join_room_error(data: Dict[str, str]) -> None:
            with self._data_lock:
                self.game_client.message = data.get(
                    "message", "Szobához csatlakozás sikertelen"
                )
                self.game_client.message_display_time = 30.0

        @self.sio.on("left_room")
        def on_left_room(data: Dict[str, str]) -> None:
            with self._data_lock:
                print("Left room event received")

                if self.game_client.screen == "reconnect_screen":
                    self.game_client.message = (
                        "A szoba közben megszünt. Szoba elhagyása"
                    )

                else:
                    self.game_client.message = data.get("message", "Szoba elhagyva")

                self.game_client.message_display_time = 30.0

                self.game_client.selected_room = None
                self.game_client.room_id = None
                self.game_client.room_name = None
                self.game_client.users = []
                if self.game_client._screens["game"]:
                    self.game_client._screens["game"]._reset_local_selections()
                self.game_client.screen = "rooms_screen"

        @self.sio.on("player_left_room")
        def on_player_left_room(data: Dict[str, Any]) -> None:
            with self._data_lock:
                try:
                    players_data = data.get("players", [])
                    self.game_client.users = []

                    for player_data in players_data:
                        if isinstance(player_data, dict):
                            user = Client_User(
                                username=player_data.get("username", ""),
                                is_active=player_data.get("is_active", False),
                            )
                            self.game_client.users.append(user)

                    self.game_client.message = data.get(
                        "message", "Játékos elhagyta a szobát"
                    )
                    self.game_client.message_display_time = 50

                    if self.game_client.selected_room is not None:
                        self.game_client.selected_room.player_count = len(
                            self.game_client.users
                        )
                except Exception as e:
                    print(f"Error in player_left_room: {e}")

        @self.sio.on("rejoin_waiting_success")
        def on_rejoin_waiting_success(data: Dict[str, Any]) -> None:
            with self._data_lock:
                print("Sikeresen visszaléptél a váróterembe")

                try:
                    players_data = data.get("players", [])
                    self.game_client.users = []

                    for player_data in players_data:
                        if isinstance(player_data, dict):
                            user = Client_User(
                                username=player_data.get("username", ""),
                                is_active=player_data.get("is_active", False),
                            )
                            self.game_client.users.append(user)

                    self.game_client.selected_room = Room(
                        room_id=data.get("room_id", ""),
                        name=data.get("room_name", ""),
                        max_player_count=data.get("max_player_count", 4),
                    )
                    self.game_client.room_name = data.get("room_name", "")
                    self.game_client.selected_room.room_id = data.get("room_id", "")

                    self.game_client.screen = "waiting"
                    self.game_client.message = "Visszaléptél a váróterembe"
                    self.game_client.message_display_time = 30.0
                except Exception as e:
                    print(f"Error in rejoin_waiting_success: {e}")

        @self.sio.on("rematch_vote_received")
        def on_vote_rematch(data: Dict[str, Any]) -> None:
            with self._data_lock:
                print("BELEPETT a rematch_vote_received eseménybe")

                try:
                    if self.game_client.game_state:
                        voters_data = data.get("voters", [])
                        if isinstance(voters_data, list):
                            self.game_client.game_state.voters = set(voters_data)
                        print(f"Voters updated: {self.game_client.game_state.voters}")
                except Exception as e:
                    print(f"Error in rematch_vote_received: {e}")

        @self.sio.on("player_rejoined")
        def on_player_rejoined(data: Dict[str, Any]) -> None:
            with self._data_lock:
                try:
                    username = data.get("rejoined_player", "")
                    if not username:
                        return

                    if hasattr(self.game_client, "users") and self.game_client.users:
                        for user in self.game_client.users:
                            if hasattr(user, "username") and user.username == username:
                                user.is_active = True
                                break

                    if self.game_client.selected_room is not None:
                        self.game_client.selected_room.player_count = len(
                            self.game_client.users
                        )

                    self.game_client.message = (
                        f"{this_is_ai_name(username)} vissza csatlakozott."
                    )
                    self.game_client.message_display_time = 30.0
                except Exception as e:
                    print(f"Error in player_rejoined: {e}")

        @self.sio.on("ai_player_add_success")
        def on_ai_player_added(data: Dict[str, Any]) -> None:
            with self._data_lock:
                self.game_client.message = "AI játékos sikeresen hozzáadva"
            self.game_client.message_display_time = 30.0

        @self.sio.on("user_stats")
        def on_user_stats(data: Dict[str, Any]) -> None:
            """Handle user statistics received from server"""
            with self._data_lock:
                try:
                    username = data.get("username")
                    total_games = data.get("total_games", 0)
                    won_games = data.get("won_games", 0)

                    if not hasattr(self.game_client, "all_player_stats"):
                        self.game_client.all_player_stats = {}

                    self.game_client.all_player_stats[username] = {
                        "total_games": total_games,
                        "won_games": won_games,
                    }

                    if username == self.game_client.user.username:
                        self.game_client.user_stats = {
                            "total_games": total_games,
                            "won_games": won_games,
                        }

                except Exception as e:
                    print(f"Error in user_stats handler: {e}")

    def get_user_stats(self, username: str) -> None:
        """Felhasználó statisztikáinak lekérése"""
        self.sio.emit("get_user_stats", {"username": username})

    def logout(self) -> None:
        with self._data_lock:
            if self.game_client.user and hasattr(self.game_client.user, "username"):
                self.sio.emit("logout", {"username": self.game_client.user.username})
            self.game_client.message = None
            self.game_client.screen = "login"
            if hasattr(self.game_client, "room_list"):
                self.game_client.room_list.clear()
            self.game_client.selected_room = None
            self.game_client.room_id = None
            self.game_client.room_name = None

    def add_ai_player(self) -> None:
        with self._data_lock:
            if self.game_client.selected_room.room_id:
                self.sio.emit(
                    "add_ai_player", {"room_id": self.game_client.selected_room.room_id}
                )

    def disconnect(self) -> None:
        self.sio.disconnect()

    def vote_rematch(self, room_id: str, username: str) -> None:
        self.sio.emit("vote_rematch", {"room_id": room_id, "username": username})

    def all_players_leave_room(self, room_id, reconnecting=False) -> None:
        self.sio.emit(
            "all_players_leave_room", {"room_id": room_id, "reconnecting": reconnecting}
        )

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

    def leave_room(self, reconnecting=False) -> None:
        self.sio.emit(
            "leave_room",
            {"username": self.game_client.user.username, "reconnecting": reconnecting},
        )

    def connect(self, server_url: str = "http://localhost:5000") -> None:
        """
        Connect to the server.

        Args:
            server_url (str, optional): The server URL. Default is "http://localhost:5000".
        """

        while self.game_client.screen == "loading":
            try:
                print(f"Connecting to server at {server_url}...")
                self.sio.connect(server_url)
                print("Connected to server")
                break
            except Exception as e:
                print(f"Error connecting to server: {e}")
                time.sleep(0.5)

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
                "visited_already": list(
                    getattr(self.game_client.game_state, "visited_already", [])
                ),
                "voters": list(getattr(self.game_client.game_state, "voters", [])),
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
