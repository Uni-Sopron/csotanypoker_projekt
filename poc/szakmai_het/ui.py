from collections import defaultdict
import os
import pygame
from client import NetworkManager
from typing import List, Dict, Any, Tuple, Optional


class GameClient:
    def __init__(self) -> None:
        pygame.init()  # Initialize Pygame
        self.window: pygame.Surface = pygame.display.set_mode(
            (1400, 800)
        )  # width: 800, height: 700
        self.width = 1400
        self.height = 800
        pygame.display.set_caption("Csotány Póker")
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
        self.pipa_rect = None  # Rectangle for the checkmark image
        self.x_rect = None
        self.Passzolas = False
        self.atadta = False
        # Handling players and messages
        self.players: List[str] = []  # List of players in the room
        self.message: str = ""  # Message to be displayed
        self.message_display_time: float = 0  # Message display duration
        self.kivalasztott_jatekos = None
        self.kivalasztott_lap = None
        # Input fields and their active state
        self.input_text: str = ""
        self.input_active: bool = (
            False  # Whether the user has clicked on the input field
        )
        self.volt_ennel_mar = []
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

        self.celzott_jatekos = None  # Target player for the current action
        self.font_kozepes = pygame.font.Font(None, 30)
        self.button_font = pygame.font.Font(None, 40)
        self.Allitas = None
        self.lenyiloablak_allapot = False

        self.lenyiloablak_pozicio = pygame.Rect(
            self.width // 2 - 50, self.height // 2 + 150, 100, 30
        )
        self.elfogado_gomb_pozicio = pygame.Rect(
            self.width // 2 + 60, self.height // 2 + 150, 100, 30
        )

        self.kozepso_lap = None
        self.ellenfel_allitasa = None
        self.sajat_allitas = None
        self.kezben_levo_lapok = None
        self.elotte_levo_kartyak = None

        self.jatekosadatok = None
        self.aktiv_jatekos = None

        self.allatok = [
            "csotany",
            "denever",
            "poloska",
            "patkany",
            "légy",
            "varangy",
            "skorpió",
            "pók",
        ]

    def allat_tipus(self, nev):
        # Ha szükséged van csak a típusra, ezt használhatod
        return nev.split("_")[0]

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

            # if self.message_display_time > 0:
            #     self.message_display_time -= 1 / 30

            # if self.error_display_time > 0:
            #     self.error_display_time -= 1 / 30

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
        elif self.screen == "Jatek_vege":
            self.draw_game_over()

    def draw_game_over(self) -> None:
        """
        Draw the game over screen.
        """
        print("Játék vége")
        self.window.fill(self.WHITE)
        self.draw_text("Játék vége", self.BLACK, 400, 150, True)
        if self.aktiv_jatekos == self.username:
            self.draw_text("Vesztettél!", self.BLACK, 400, 250, True)
        else:
            self.draw_text("Nyertél!", self.BLACK, 400, 250, True)

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

    #
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

        small_font = pygame.font.Font(None, 20)
        info_font = pygame.font.Font(None, 36)
        player_font = pygame.font.Font(None, 24)
        count_font = pygame.font.Font(None, 24)
        message_font = pygame.font.Font(None, 20)
        kep_mappa = os.path.join("kepek")

        logo_images = {}
        for allat in self.allatok:  # használjuk a már ismert állatok listáját
            logo_utvonal = os.path.join(kep_mappa, f"{allat}_logo.png")
            if os.path.exists(logo_utvonal):
                # print(f"Betöltés: {logo_utvonal}")
                logo = pygame.image.load(logo_utvonal)
                logo = pygame.transform.scale(logo, (40, 40))
                logo_images[allat] = logo
            else:
                print(f"Nem található: {logo_utvonal}")

        # player_panels = []
        # print(f"ez van benne {logo_images}")
        while self.screen != "Jatek_vege":
            self.window.fill(self.WHITE)
            self.draw_text(f"Szoba: {self.room_name}", self.BLACK, 10, 10, False)
            self.draw_text(
                f"Felhasználónév: {self.username}", self.BLACK, 10, 40, False
            )

            self.draw_text(
                f"aktiv jatekos: {self.aktiv_jatekos}", self.BLACK, 10, 70, False
            )

            text = message_font.render(self.message, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect = (self.width / 1.2, 30)
            self.window.blit(text, text_rect)

            player_panel_height = 200
            player_panel_width = 120
            player_spacing = 30
            total_players_width = (player_panel_width * (len(self.players) - 1)) + (
                player_spacing * (len(self.players) - 1)
            )
            start_x = (self.width - total_players_width) / 2
            player_panels = []
            for i, (player_name, adat) in enumerate(self.jatekosadatok.items()):
                if player_name != self.username:
                    player_panel_rect = pygame.Rect(
                        start_x + i * (player_panel_width + player_spacing),
                        60,
                        player_panel_width,
                        player_panel_height,
                    )

                    pygame.draw.rect(
                        self.window, self.GRAY, player_panel_rect, border_radius=5
                    )

                    player_name_text = player_font.render(
                        f"nev: {player_name}", True, (0, 0, 0)
                    )
                    self.window.blit(
                        player_name_text,
                        (player_panel_rect.x + 10, player_panel_rect.y + 10),
                    )

                    card_count_text = count_font.render(
                        f"lapszam: {adat['jatekos_kartyaszam']}",
                        True,
                        (0, 0, 0),
                    )
                    self.window.blit(
                        card_count_text,
                        (player_panel_rect.x + 10, player_panel_rect.y + 30),
                    )

                    card_x = player_panel_rect.x + 10
                    card_y = player_panel_rect.y + 60
                    col_width = 60

                    for j, (lap_tipus, count) in enumerate(
                        adat["elotte_levo_kartyak"].items()
                    ):
                        column = j % 2
                        row = j // 2
                        pos_x = player_panel_rect.x + 10 + (column * col_width)
                        pos_y = player_panel_rect.y + 60 + (row * 30)

                        if lap_tipus in logo_images:
                            small_logo = pygame.transform.scale(
                                logo_images[lap_tipus], (25, 25)
                            )
                            self.window.blit(small_logo, (pos_x, pos_y))
                            count_text = small_font.render(str(count), True, (0, 0, 0))
                            self.window.blit(count_text, (pos_x + 30, pos_y + 5))
                        else:
                            card_text = small_font.render(
                                f"{lap_tipus}: {count}", True, (0, 0, 0)
                            )
                            self.window.blit(card_text, (pos_x, pos_y))
                    player_panels.append((player_panel_rect, player_name))

            info_panel_rect = pygame.Rect(self.width - 250, 150, 230, 400)

            info_title = info_font.render("Állatok száma:", True, self.BLACK)
            self.window.blit(
                info_title, (info_panel_rect.x + 10, info_panel_rect.y + 10)
            )

            col_width = 110

            items_per_column = (len(self.elotte_levo_kartyak or {}) + 1) // 2

            for i, lap_tipus in enumerate(self.elotte_levo_kartyak or {}):
                col = i // items_per_column
                row = i % items_per_column

                x_pos = info_panel_rect.x + 15 + (col * col_width)
                y_pos = info_panel_rect.y + 60 + (row * 50)

                if lap_tipus in logo_images:
                    logo = logo_images[lap_tipus]
                    self.window.blit(logo, (x_pos, y_pos))

                    count_text = count_font.render(
                        f"{self.elotte_levo_kartyak[lap_tipus]}", True, self.BLACK
                    )
                    self.window.blit(count_text, (x_pos + 45, y_pos + 10))
                else:
                    lap_info = count_font.render(
                        f"{lap_tipus}: {self.elotte_levo_kartyak[lap_tipus]}",
                        True,
                        self.BLACK,
                    )
                    self.window.blit(lap_info, (x_pos, y_pos + 10))

            kartya_poziciok = []

            y_kep = self.height - 150
            eltolasi_meret = 10  # egymás feletti kártyák eltolása

            lap_csoportok = {}
            for lap in self.kezben_levo_lapok:
                tipus = self.allat_tipus(lap)
                if tipus not in lap_csoportok:
                    lap_csoportok[tipus] = []
                lap_csoportok[tipus].append(lap)

            tipus_szam = len(lap_csoportok)

            x_kep = self.width // 2

            for tipus, lapok in lap_csoportok.items():
                kep_utvonal = os.path.join(kep_mappa, f"{tipus}.png")

                if os.path.exists(kep_utvonal):
                    kep = pygame.image.load(kep_utvonal)
                    eredeti_meret = kep.get_size()
                    meret_arany = min(self.width / 1600, self.height / 1600)
                    kartya_meret = (
                        int(eredeti_meret[0] * meret_arany),
                        int(eredeti_meret[1] * meret_arany),
                    )

                    kep = pygame.transform.scale(kep, kartya_meret)

                    for i, lap in enumerate(lapok):
                        kartya_rect = pygame.Rect(
                            x_kep
                            - (tipus_szam * (int(eredeti_meret[0] * meret_arany)) // 2),
                            y_kep - i * eltolasi_meret,
                            *kartya_meret,
                        )
                        self.window.blit(kep, (kartya_rect.x, kartya_rect.y))
                        kartya_poziciok.append((kartya_rect, lap))

                    x_kep += kartya_meret[0] + 5

            if self.kozepso_lap != None:
                card_width, card_height = 100, 150
                card_x = (self.width - card_width) // 2
                card_y = (self.height - card_height) // 2

                if self.kozepso_lap == "kerdojel":
                    kozepso_lap_path = os.path.join("kepek", "kerdojel.png")
                    if self.celzott_jatekos == self.username:
                        pipa_path = os.path.join("kepek", "pipa.png")
                        if os.path.exists(pipa_path):
                            pipa_img = pygame.image.load(pipa_path)
                            pipa_img = pygame.transform.scale(pipa_img, (40, 40))
                            self.window.blit(
                                pipa_img,
                                (card_x - 50, card_y + (card_height // 2) - 20),
                            )
                            self.pipa_rect = pygame.Rect(
                                (card_x - 50, card_y + (card_height // 2) - 20),
                                (40, 40),
                            )

                        x_path = os.path.join("kepek", "x.png")
                        if os.path.exists(x_path):
                            x_img = pygame.image.load(x_path)
                            x_img = pygame.transform.scale(x_img, (40, 40))
                            self.window.blit(
                                x_img,
                                (
                                    card_x + card_width + 10,
                                    card_y + (card_height // 2) - 20,
                                ),
                            )
                            self.x_rect = pygame.Rect(
                                (
                                    card_x + card_width + 10,
                                    card_y + (card_height // 2) - 20,
                                ),
                                (40, 40),  # vagy bármilyen méret, amit szeretnél
                            )
                        if len(self.volt_ennel_mar) < len(self.players):
                            pass_width, pass_height = 80, 40
                            pass_x = card_x + (card_width // 2) - (pass_width // 2)
                            pass_y = card_y + card_height + 10

                            self.pass_rect = pygame.Rect(
                                (pass_x, pass_y), (pass_width, pass_height)
                            )
                            pygame.draw.rect(
                                self.window, (200, 200, 200), self.pass_rect
                            )  # világos szürke háttér

                            font = pygame.font.SysFont(None, 24)
                            pass_text = font.render(
                                "PASS", True, (0, 0, 0)
                            )  # fekete szöveg
                            text_rect = pass_text.get_rect(center=self.pass_rect.center)
                            self.window.blit(pass_text, text_rect)

                elif self.kozepso_lap:
                    kozepso_lap_path = os.path.join(
                        "kepek", f"{self.allat_tipus(self.kozepso_lap)}.png"
                    )
                    if os.path.exists(kozepso_lap_path):
                        lap_img = pygame.image.load(kozepso_lap_path)
                        lap_img = pygame.transform.scale(
                            lap_img, (card_width, card_height)
                        )
                        self.window.blit(lap_img, (card_x, card_y))
                kozepso_lap_image = pygame.image.load(kozepso_lap_path)

                kozepso_lap_image = pygame.transform.scale(
                    kozepso_lap_image, (card_width, card_height)
                )

                self.window.blit(kozepso_lap_image, (card_x, card_y))

                description_text = small_font.render(
                    self.ellenfel_allitasa, True, (0, 0, 0)
                )  # ellenfél állitása
                self.window.blit(
                    description_text, (card_x + card_width + 50, card_y + 10)
                )

                description_text = small_font.render(
                    self.sajat_allitas, True, (0, 0, 0)
                )  # saját állitás
                self.window.blit(
                    description_text, (card_x - 100, card_y + card_height + 20)
                )
            # print(f"kivalasztott jatekos: {self.kivalasztott_jatekos}")
            # print(f"kivalasztott lap {self.kivalasztott_lap}")
            if self.kivalasztott_jatekos != None and self.kivalasztott_lap != None:
                # Állatok közötti választás
                pygame.draw.rect(
                    self.window, (180, 180, 180), self.lenyiloablak_pozicio
                )
                dropdown_text = small_font.render(self.Allitas, True, (0, 0, 0))
                self.window.blit(
                    dropdown_text,
                    (self.lenyiloablak_pozicio.x + 5, self.lenyiloablak_pozicio.y + 5),
                )

                if self.lenyiloablak_allapot:
                    self.kozepso_lap = self.kivalasztott_lap
                    for i, option in enumerate(self.allatok):
                        option_rect = pygame.Rect(
                            self.lenyiloablak_pozicio.x,
                            self.lenyiloablak_pozicio.y + (i + 1) * 20,
                            100,
                            20,
                        )
                        pygame.draw.rect(self.window, self.GRAY, option_rect)
                        option_text = small_font.render(option, True, (0, 0, 0))
                        self.window.blit(
                            option_text, (option_rect.x + 5, option_rect.y + 5)
                        )

                pygame.draw.rect(
                    self.window,
                    self.GRAY,
                    self.elfogado_gomb_pozicio,
                )
                accept_text = small_font.render("Valaszt", True, self.BLACK)
                self.window.blit(
                    accept_text,
                    (
                        self.elfogado_gomb_pozicio.x + 10,
                        self.elfogado_gomb_pozicio.y + 5,
                    ),
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # self.allapot = 10
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # self.allapot = 10
                        pygame.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    talalt = False
                    # Fordított sorrendben iterálunk, hogy a felül lévő kártyákat detektáljuk előbb
                    for rect, lap in reversed(kartya_poziciok):
                        if self.aktiv_jatekos != self.username:
                            print(
                                f"Nem te vagy az aktív játékos. Aktív: {self.aktiv_jatekos}, Te: {self.username}"
                            )
                        if self.lenyiloablak_allapot:
                            print("A lenyíló ablak nyitva van.")
                        if self.atadta:
                            print("Már átadta a kört.")
                        if self.Passzolas:
                            print("Passzoltál ebben a körben.")
                        if talalt:
                            print("Már kiválasztottál egy kártyát.")

                        if (
                            rect.collidepoint(mx, my)
                            and self.aktiv_jatekos == self.username
                            and not self.lenyiloablak_allapot
                            and not self.atadta
                            and not self.Passzolas
                            and not talalt  # Ha már találtunk egy kártyát, ne válasszunk többet
                        ):
                            self.kozepso_lap = None
                            print(f"Rákattintottál: {lap}")
                            self.kivalasztott_lap = lap
                            talalt = True
                            break  # Kilépünk a ciklusból, miután találtunk egy kártyát

                    mx, my = event.pos
                    for rect, player_name in player_panels:
                        if (
                            rect.collidepoint(mx, my)
                            and self.aktiv_jatekos == self.username
                            and not self.atadta
                        ):
                            if player_name not in self.volt_ennel_mar:
                                self.kozepso_lap = None
                                print(f"Rákattintottál {player_name}-ra")
                                self.kivalasztott_jatekos = player_name
                            else:
                                self.message = "már volt már ennél a játékosnál"

                    if self.lenyiloablak_pozicio.collidepoint(mx, my):
                        self.lenyiloablak_allapot = not self.lenyiloablak_allapot
                    print(self.lenyiloablak_allapot)
                    if self.lenyiloablak_allapot:
                        for i, option in enumerate(self.allatok):
                            option_rect = pygame.Rect(
                                self.lenyiloablak_pozicio.x,
                                self.lenyiloablak_pozicio.y + (i + 1) * 20,
                                100,
                                20,
                            )
                            if option_rect.collidepoint(mx, my):
                                self.Allitas = option
                                self.lenyiloablak_allapot = False

                    if self.elfogado_gomb_pozicio.collidepoint(mx, my) and self.Allitas:
                        print(f"Elfogadott állat: {self.Allitas}")
                        if self.kivalasztott_jatekos and self.kivalasztott_lap:
                            # print(
                            # f"PIPA KATT: {self.kivalasztott_jatekos}, {self.kivalasztott_lap}"
                            # )
                            self.network.oke_click(
                                self.room_id,
                                self.kivalasztott_jatekos,
                                self.kivalasztott_lap,
                                self.Allitas,
                                self.Passzolas,
                            )
                            # Reset after sending
                            self.kivalasztott_jatekos = None
                            self.kivalasztott_lap = None
                            self.Passzolas = False
                            self.atadta = True
                            # self.aktiv_jatekos = None

                        # print("HEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
                    if self.pipa_rect is not None and self.pipa_rect.collidepoint(
                        mx, my
                    ):
                        print("Igazat mondott")
                        self.kozepso_lap = None
                        self.network.tipp(self.room_id, True)
                    if self.x_rect is not None and self.x_rect.collidepoint(mx, my):
                        print("Hazudott")
                        self.kozepso_lap = None

                        self.network.tipp(self.room_id, False)

                    if hasattr(self, "pass_rect") and self.pass_rect.collidepoint(
                        mx, my
                    ):
                        print("PASS gombra kattintva!")
                        self.network.passzolas(self.room_id)
                        self.Passzolas = True
                        # ha van ilyen attribútum, jelenítheted is a képernyőn

            pygame.display.flip()

    def szoveg_felrajzolas(self, text, position, font, color=None):
        if color is None:
            color = self.BLACK
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        self.window.blit(text_surface, text_rect)

    def beviteli_mezo_felrajzolasa(self, rect, text, active=False):
        color = self.BLACK if active else self.GRAY
        pygame.draw.rect(self.window, color, rect, 2)
        input_surface = self.font_kozepes.render(text, True, self.BLACK)
        self.window.blit(input_surface, (rect.x + 10, rect.y + 10))

    def gomb_felrajzolas(self, text, rect, color=None):
        if color is None:
            color = self.BLACK
        pygame.draw.rect(self.window, color, rect)
        button_text = self.button_font.render(text, True, self.WHITE)
        self.window.blit(button_text, (rect.x + 25, rect.y + 10))
