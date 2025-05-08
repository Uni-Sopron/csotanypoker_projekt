import socketio
from typing import Dict, Any, List


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
            self.game_client.players = data["players"]

        @self.sio.on("player_joined")
        def on_player_joined(data: Dict[str, Any]) -> None:
            """
            Handle a player joining the room.

            Args:
                data: A dictionary containing players list and joined_player
            """
            print(f"Player joined: {data['joined_player']}")
            self.game_client.players = data["players"]
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
            self.game_client.players = data["players"]

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

        @self.sio.on("kartya_lehelyezve")
        def on_kartya_lehelyezve(data: Dict[str, Any]) -> None:
            """
            Handle card placement event.

            Args:
                data: A dictionary containing placement information
            """
            print(f"Kártya lehelyezve: {data}")
            self.game_client.kozepso_lap = None
            self.game_client.volt_ennel_mar = []
            self.game_client.kivalasztott_lap = None

            self.game_client.message = f"{data['jatekos']} elé lehelyezésre került egy {data['kartya_tipus']} kártya."

            self.game_client.atadta = False
            self.game_client.lenyiloablak_allapot = False

        @self.sio.on("kezbenlevo_kartyak")
        def kezbenlevo_kartyak(data) -> None:
            print(f"Kezben lévő kártyák: {data}")
            self.game_client.kezben_levo_lapok = data["kezbenlevo_kartyak"]

        @self.sio.on("jatekos_adatok")
        def jatekos_adatok(data: Dict[str, Any]) -> None:
            """
            Handle player data.

            Args:
                data: A dictionary containing player data
            """

            self.game_client.aktiv_jatekos = data.get("kezdo_jatekos", "ismeretlen")
            self.game_client.atadta = False

            self.game_client.jatekosadatok = {
                nev: jatekos
                for nev, jatekos in data.get("jatekos_adatok", {}).items()
                if nev != self.game_client.username
            }
            for nev, jatekos in data.get("jatekos_adatok", {}).items():
                if nev == self.game_client.username:
                    self.game_client.elotte_levo_kartyak = {}
                    self.game_client.elotte_levo_kartyak = jatekos.get(
                        "elotte_levo_kartyak", []
                    )

                    print(f"Előtte lévő lapok: {self.game_client.elotte_levo_kartyak}")

            self.game_client.kezben_levo_lapok = data.get("kezbenlevo_kartyak", [])
            print(data.get("kezbenlevo_kartyak", []))

        @self.sio.on("kartya_kapas")
        def kartya_kapas(data) -> None:
            print(f"adatok kiirasa: {data}")
            self.game_client.ellenfel_allitasa = (
                f"Ez az állat egy: {data.get('jatekos_allitasa', '')}"
            )
            self.game_client.kozepso_lap = "kerdojel"

            self.game_client.celzott_jatekos = data.get("celzott_jatekos", "")
            self.game_client.volt_ennel_mar = data["naluk_volt"]
            if self.game_client.username == data.get("celzott_jatekos", ""):
                self.game_client.message = (
                    f"Kártyát kaptál: {data.get('lapot_ado', '')}"
                )
            elif self.game_client.username == data.get("lapot_ado", ""):
                self.game_client.message = (
                    f"Kártyát adtál: {data.get('celzott_jatekos', '')}"
                )
            else:
                self.game_client.message = f"{data.get('lapot_ado', '')}-tól kártyát kapott {data.get('celzott_jatekos', '')}"

        @self.sio.on("kartya_tartalma")
        def kartya_tartalma(data) -> None:
            print(f"adatok kiirasa: {data['lap']}")
            self.game_client.kozepso_lap = data["lap"]
            self.game_client.kivalasztott_lap = data["lap"]
            self.game_client.volt_ennel_mar = data["naluk_volt"]

        @self.sio.on("kivalasztott_kartya_tartalma")
        def kivalasztott_kartya_tartalma(data) -> None:
            self.game_client.kozepso_lap = data["lap"]
            self.game_client.kivalasztott_lap = data["lap"]
            self.game_client.volt_ennel_mar = data["naluk_volt"]

        @self.sio.on("passzolt")
        def passzolt(data) -> None:
            self.game_client.aktiv_jatekos = data["aktiv_jatekos"]

            self.game_client.message = data["message"]
            self.game_client.lenyiloablak_allapot = True

        @self.sio.on("hiba")
        def hiba(data) -> None:
            self.game_client.message = data["message"]
            self.game_client.atadta = False

        @self.sio.on("jatek_vege")
        def jatek_vege(data) -> None:
            if self.game_client.username == data["vesztett_jatekos"]:
                self.game_client.message = "Vesztettél!"
            else:
                self.game_client.message = "Gratulálok! Nyertél!"
            self.game_client.screen = "Jatek_vege"

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

    def tipp(self, room_id: str, tipp: str) -> None:
        self.sio.emit("tipp", {"room_id": room_id, "tipp": tipp})

    def oke_click(
        self, room_id: str, kivalasztott_jatekos, kivalasztott_lap, allitas, passzolas
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
                "kivalasztott_jatekos": kivalasztott_jatekos,
                "kivalasztott_lap": kivalasztott_lap,
                "lapot_ado_allitasa": allitas,
                "pass": passzolas,
            },
        )

    def passzolas(self, room_id: str) -> None:
        self.sio.emit("pass", {"room_id": room_id})
