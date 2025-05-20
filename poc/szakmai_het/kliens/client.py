import os
import sys
import socketio
from typing import Dict, Any, List
sys.path.append(os.path.abspath('..')) 

from models.model import Jatekos, Kartya


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
            
            self.game_client.game_state.jatekosok = [
                Jatekos(jatekos) for jatekos in data["players"]
            ]
            for jatekos in self.game_client.game_state.jatekosok:
                if jatekos.nev == data["username"]:
                    self.game_client.user = jatekos

        @self.sio.on("player_joined")
        def on_player_joined(data: Dict[str, Any]) -> None:
            """
            Handle a player joining the room.

            Args:
                data: A dictionary containing players list and joined_player
            """
           
            self.game_client.game_state.jatekosok = [
                Jatekos(jatekos) for jatekos in data["players"]
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
            self.game_client.game_state.jatekosok = [
                Jatekos(jatekos) for jatekos in data["players"]
            ]
            for jatekosok in self.game_client.game_state.jatekosok:
                if jatekosok.nev == self.game_client.username:
                    self.game_client.user = jatekosok

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
           
            self.game_client.game_state.kerdeses_kartya = None
            self.game_client.kivalasztott_lap = None

            self.game_client.message = f"{data['jatekos']} elé lehelyezésre került egy {data['kartya_tipus']} kártya."

            self.game_client.atadta = False
            self.game_client.lenyiloablak_allapot = False

        @self.sio.on("kezbenlevo_kartyak")
        def kezbenlevo_kartyak(data) -> None:
            
            self.game_client.user.kezbenlevo_kartyak = []
            for k in data.get("kezbenlevo_kartyak", []):
                nev, sorszam = k.rsplit("_", 1)
               
                
                self.game_client.user.kezbenlevo_kartyak.append(
                    Kartya(nev, int(sorszam))
                    )
            print("kezbenlevo_kartyak:")
            for kartya in self.game_client.user.kezbenlevo_kartyak:
                print(f"nev: {kartya.nev}, sorszam: {kartya.sorszam}")
            self.game_client.game_state

        @self.sio.on("jatekos_adatok")
        def jatekos_adatok(data: Dict[str, Any]) -> None:
            """
            Handle player data.

            Args:
                data: A dictionary containing player data
            """

            kezbenlevo_adatok = data.get("kezbenlevo_kartyak", [])
            for jatekos in self.game_client.game_state.jatekosok:
                if jatekos.nev == data.get("kezdo_jatekos", "ismeretlen"):
                    self.game_client.game_state.aktiv_jatekos = jatekos
                if jatekos.nev == self.game_client.username:
                    self.game_client.user.kezbenlevo_kartyak = []
                    for k in kezbenlevo_adatok:
                        nev, sorszam = k.rsplit("_", 1)

                        self.game_client.user.kezbenlevo_kartyak.append(
                            Kartya(nev, int(sorszam))
                        )

                jatekos.elotte_levo_kartyak = data.get("jatekos_adatok", {})[
                    jatekos.nev
                ]["elotte_levo_kartyak"]
                jatekos.lapszam = data.get("jatekos_adatok", {})[jatekos.nev][
                    "jatekos_kartyaszam"
                ]
            self.game_client.atadta = False
            

        @self.sio.on("kartya_kapas")
        def kartya_kapas(data) -> None:
            self.game_client.game_state.aktiv_jatekos.allitas = data.get(
                "jatekos_allitasa", ""
            )

       
            self.game_client.game_state.kerdeses_kartya = Kartya("kerdojel", 0)
            for jatekos in self.game_client.game_state.jatekosok:
                if jatekos.nev == data.get("celzott_jatekos", "ismeretlen"):
                    self.game_client.game_state.celzott_jatekos = jatekos
           
            self.game_client.game_state.kerdeses_kartya.volt_ennel_mar = data[
                "naluk_volt"
            ]
           
            if self.game_client.user.nev == data.get("celzott_jatekos", ""):
                self.game_client.message = (
                    f"Kártyát kaptál: {data.get('lapot_ado', '')}"
                )
            elif self.game_client.user.nev == data.get("lapot_ado", ""):
                self.game_client.message = (
                    f"Kártyát adtál: {data.get('celzott_jatekos', '')}"
                )
            else:
                self.game_client.message = f"{data.get('lapot_ado', '')}-tól kártyát kapott {data.get('celzott_jatekos', '')}"

        @self.sio.on("kartya_tartalma")
        def kartya_tartalma(data) -> None:
            self.game_client.game_state.kerdeses_kartya = Kartya(
                data["lap_tipus"], data["lap_sorszam"]
            )
            print(
                f"kerdeses_kartya: {self.game_client.game_state.kerdeses_kartya.tipus}"
            )
            print(
                f"kerdeses_kartya: {self.game_client.game_state.kerdeses_kartya.sorszam}"
            )
            self.game_client.kivalasztott_lap = Kartya(
                data["lap_tipus"], data["lap_sorszam"]
            )
            self.game_client.kivalasztott_lap.volt_ennel_mar = data["naluk_volt"]

            self.game_client.game_state.kerdeses_kartya.volt_ennel_mar = data[
                "naluk_volt"
            ]

        @self.sio.on("passzolt")
        def passzolt(data) -> None:
            for jatekos in self.game_client.game_state.jatekosok:
                if jatekos.nev == data.get("aktiv_jatekos", "ismeretlen"):
                    self.game_client.game_state.aktiv_jatekos = jatekos

            self.game_client.message = data["message"]
            self.game_client.lenyiloablak_allapot = True

        @self.sio.on("hiba")
        def hiba(data) -> None:
            self.game_client.message = data["message"]
            self.game_client.atadta = False

        @self.sio.on("jatek_vege")
        def jatek_vege(data) -> None:
            if self.game_client.user.nev == data["vesztett_jatekos"]:
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
                "kivalasztott_lap": kivalasztott_lap.nev,
                "lapot_ado_allitasa": allitas,
                "pass": passzolas,
            },
        )

    def passzolas(self, room_id: str) -> None:
        self.sio.emit("pass", {"room_id": room_id})
