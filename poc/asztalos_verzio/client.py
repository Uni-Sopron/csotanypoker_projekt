import socketio


class NetworkManager:
    def __init__(self, game_client):
        self.sio = socketio.Client()
        self.game_client = game_client

        @self.sio.event
        def connect():
            print("Connected to server")

        @self.sio.event
        def login_success(
            data,
        ):  # If the server responds that the login is successful.
            self.game_client.on_login_success(data["username"])
            self.get_rooms()

        @self.sio.event
        def room_list(data):
            self.game_client.on_room_list(data["rooms"])

        @self.sio.event
        def room_created(data):
            self.get_rooms()

        @self.sio.event
        def joined_room(data):
            self.game_client.on_joined_room(
                data["room_id"], data["name"], data["players"]
            )

        @self.sio.event
        def player_joined(data):
            self.game_client.on_player_joined(data["players"])

        @self.sio.event
        def player_left(data):
            self.game_client.on_player_left(data["players"])

        @self.sio.event
        def user_notification(data):
            message = data.get("message", "")
            self.game_client.show_notification(message)

        @self.sio.event
        def start_game(data):
            self.game_client.on_start_game(data["players"])

    def connect(self, server_url="http://localhost:5000"):
        self.sio.connect(server_url)

    def disconnect(self):
        self.sio.disconnect()

    def login(self, username):  # Sends the username to the server.
        self.sio.emit("login", {"username": username})

    def get_rooms(self):
        self.sio.emit("get_rooms")

    def create_room(self, room_name):
        self.sio.emit("create_room", {"name": room_name})

    def join_room(self, room_id):
        self.sio.emit("join_room", {"room_id": room_id})

    def leave_room(self, room_id):
        self.sio.emit("leave_room", {"room_id": room_id})

    def player_click(self, room_id, player):
        self.sio.emit("player_click", {"room_id": room_id, "clicked_player": player})
