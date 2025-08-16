import threading
import socket
import json
import time
import pygame
from collections import defaultdict
import os

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)

#


class Client:
    def __init__(self):  # host="127.0.0.1", port=55555
        # self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client.connect((host, port))
        self.rooms = []
        self.allapot = 5
        pygame.init()
        self.width, self.height = 1400, 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Csotánypóker")
        self.font = pygame.font.Font(None, 50)
        self.font_kozepes = pygame.font.Font(None, 30)
        self.button_font = pygame.font.Font(None, 40)
        self.allat_kivalasztva = None
        self.lenyiloablak_allapot = False
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
        self.lenyiloablak_pozicio = pygame.Rect(
            self.width // 2 - 50, self.height // 2 + 150, 100, 30
        )
        self.elfogado_gomb_pozicio = pygame.Rect(
            self.width // 2 + 60, self.height // 2 + 150, 100, 30
        )

        # threading.Thread(target=self.receive).start()
        # self.kezdo_oldal()
        message = "Feri van soron"
        kezben_levo_lapok = [
            "csotany",
            "csotany",
            "csotany",
            "patkany",
            "denever",
            "poloska",
            "patkany",
            "denever",
            "varangy",
            "varangy",
            "varangy",
            "varangy",
            "skorpio",
            "pok",
            "pok",
            "legy",
        ]
        elotte_levo_kartyak = {
            "csotany": 2,
            "denever": 5,
            "patkany": 1,
        }
        jatekosok = {
            "feri": {
                "elotte_levo_kartyak": {"csotany": 2, "varangy": 1},
                "kezben_levo_kartyak": {4},
            },
            "jozsi": {
                "elotte_levo_kartyak": {"denever": 3, "poloska": 1},
                "kezben_levo_kartyak": {3},
            },
            "laci": {
                "elotte_levo_kartyak": {
                    "denever": 1,
                    "poloska": 4,
                    "patkany": 1,
                    "csotany": 2,
                    "varangy": 1,
                    "legy": 2,
                    "skorpio": 1,
                    "pok": 3,
                },
                "kezben_levo_kartyak": {3},
            },
            "sanyi": {"elotte_levo_kartyak": {}, "kezben_levo_kartyak": {10}},
            "pisti": {"elotte_levo_kartyak": {}, "kezben_levo_kartyak": {0}},
        }

        kozepso_lap = "hatlap"
        # kozepso_lap="csotany"
        # kozepso_lap=None
        allitas = "ez egy Béka"
        allitas2 = "Szerintem ez egy béka"

        self.game_started_screen(
            kezben_levo_lapok,
            elotte_levo_kartyak,
            jatekosok,
            message,
            kozepso_lap,
            allitas,
            allitas2,
        )

    def receive(self):
        while True:
            chunk = self.client.recv(1024).decode("ascii")
            if not chunk:
                break
            data = json.loads(chunk)
            self.uzenetek_kezelese(data)

    def uzenetek_kezelese(self, data):
        uzenet = data.get("type")

        if uzenet == "Szerver_csatlakozas":
            print(f">>>>>>>>>{data.get('message')}<<<<<<<<<<<")
            self.allapot = 0

        elif uzenet == "Varakozas":
            print("Várakozás a játékosokra..")
            self.screen.fill(WHITE)
            self.allapot = 4
            self.varo_oldal()
            time.sleep(1)
        elif uzenet == "szoba nevek":
            self.rooms = data.get("rooms", [])

        elif uzenet == "game_start":
            print(f"{data.get('message')}")
            kezben_levo_lapok = data.get("lapok", [])
            print(kezben_levo_lapok)

            self.screen.fill(WHITE)
            self.allapot = 5
            self.game_started_screen(kezben_levo_lapok)

    def send(self, message):
        data = json.dumps(message).encode("ascii")
        self.client.send(data)

    def name_input_screen(self):
        input_box = pygame.Rect(300, 250, 200, 50)
        button_rect = pygame.Rect(350, 320, 150, 50)
        input_text = ""

        while self.allapot == 0:
            self.screen.fill(WHITE)

            self.szoveg_felrajzolas("Add meg a neved:", (250, 180), self.font, BLACK)
            self.beviteli_mezo_felrajzolasa(input_box, input_text, True)
            self.gomb_felrajzolas("Belépés", button_rect, BLACK)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.nev_elkuldese(input_text)
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        self.nev_elkuldese(input_text)
                        return

    def nev_elkuldese(self, input_text):
        print(f"Játékos neve: {input_text}")
        self.send({"type": "nev", "nev": input_text})
        self.allapot = 1
        self.kezdo_menu()

    def kezdo_oldal(self):
        button_rect = pygame.Rect(self.width // 2 - 50, self.height // 2 - 20, 100, 50)

        while self.allapot == 0:
            self.screen.fill(WHITE)

            self.szoveg_felrajzolas(
                "Csotánypóker",
                (self.width // 2, self.height // 2 - 100),
                self.font,
                BLACK,
            )
            self.gomb_felrajzolas("Start", button_rect, BLACK)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(
                    event.pos
                ):
                    self.screen.fill(WHITE)
                    self.name_input_screen()

    def kezdo_menu(self):
        buttons = [
            ("Szoba készítés", (200, 150)),
            ("Csatlakozás szobához", (200, 250)),
            ("Random szobához csatlakozás", (200, 350)),
        ]
        button_rects = [pygame.Rect(x, y, 450, 50) for _, (x, y) in buttons]

        while self.allapot == 1:
            self.screen.fill(WHITE)
            self.szoveg_felrajzolas(
                "Menü:", (self.screen.get_width() // 2, 50), self.font, BLACK
            )
            for idx, (text, (x, y)) in enumerate(buttons):
                self.gomb_felrajzolas(text, button_rects[idx])
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.allapot = 10
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for idx, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            self.allapot = 2
                            if idx == 0:
                                self.screen.fill(WHITE)
                                self.szobat_letrehozo_oldal()
                            elif idx == 1:
                                self.csatalakozo_oldal()
                            elif idx == 2:
                                self.send(
                                    {
                                        "type": "random_room",
                                        "message": "Csatlakozás véletlenszerű szobához...",
                                    }
                                )

    def szobat_letrehozo_oldal(self):
        szoba_neve_mezo = pygame.Rect(300, 150, 200, 40)
        jelszo_mezo = pygame.Rect(300, 250, 200, 40)
        max_jatekosok_mezo = pygame.Rect(300, 350, 200, 40)

        szoba_neve_szoveg = ""
        jelszo_szoveg = ""
        max_jatekosok_szoveg = ""

        aktiv_bemenet = None

        while self.allapot == 2:
            self.screen.fill(WHITE)
            self.szoveg_felrajzolas(
                "Szoba létrehozása", (self.screen.get_width() // 2, 50), self.font
            )

            self.szoveg_felrajzolas("Szoba neve:", (300, 130), self.font)
            self.beviteli_mezo_felrajzolasa(
                szoba_neve_mezo, szoba_neve_szoveg, aktiv_bemenet == "szoba_neve"
            )

            self.szoveg_felrajzolas("Jelszó:", (300, 230), self.font)
            self.beviteli_mezo_felrajzolasa(
                jelszo_mezo, jelszo_szoveg, aktiv_bemenet == "jelszo"
            )

            self.szoveg_felrajzolas("Max. játékosok (2-6):", (300, 330), self.font)
            self.beviteli_mezo_felrajzolasa(
                max_jatekosok_mezo,
                max_jatekosok_szoveg,
                aktiv_bemenet == "max_jatekosok",
            )

            self.gomb_felrajzolas("Szoba létrehozása", pygame.Rect(350, 400, 300, 50))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                    pygame.quit()
                    return

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if szoba_neve_mezo.collidepoint(event.pos):
                        aktiv_bemenet = "szoba_neve"
                    elif jelszo_mezo.collidepoint(event.pos):
                        aktiv_bemenet = "jelszo"
                    elif max_jatekosok_mezo.collidepoint(event.pos):
                        aktiv_bemenet = "max_jatekosok"
                    elif pygame.Rect(350, 400, 300, 50).collidepoint(event.pos):
                        try:
                            max_jatekosok = int(max_jatekosok_szoveg)
                            if 2 <= max_jatekosok <= 6:
                                self.send(
                                    {
                                        "type": "create_room",
                                        "room_name": szoba_neve_szoveg,
                                        "password": jelszo_szoveg,
                                        "max_players": max_jatekosok,
                                    }
                                )
                        except ValueError:
                            pass
                elif event.type == pygame.KEYDOWN:
                    if aktiv_bemenet == "szoba_neve":
                        if event.key == pygame.K_BACKSPACE:
                            szoba_neve_szoveg = szoba_neve_szoveg[:-1]
                        else:
                            szoba_neve_szoveg += event.unicode
                    elif aktiv_bemenet == "jelszo":
                        if event.key == pygame.K_BACKSPACE:
                            jelszo_szoveg = jelszo_szoveg[:-1]
                        else:
                            jelszo_szoveg += event.unicode
                    elif aktiv_bemenet == "max_jatekosok":
                        if event.key == pygame.K_BACKSPACE:
                            max_jatekosok_szoveg = max_jatekosok_szoveg[:-1]
                        else:
                            if event.unicode.isdigit():
                                max_jatekosok_szoveg += event.unicode

    def jelszo_bekeres(self, uzenet):
        szoveg = ""

        aktiv = True

        while aktiv:
            self.screen.fill(WHITE)

            self.szoveg_felrajzolas(uzenet, (50, 200), self.font, BLACK)

            self.beviteli_mezo_felrajzolasa(pygame.Rect(50, 250, 300, 50), szoveg, True)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return szoveg
                    elif event.key == pygame.K_BACKSPACE:
                        szoveg = szoveg[:-1]
                    else:
                        szoveg += event.unicode

    def varo_oldal(self):
        text = self.font.render("Várakozunk a játékosokra...", True, BLACK)
        text_rect = text.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 100)
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.allapot = 10
                return

        self.screen.fill(WHITE)

        self.screen.blit(text, text_rect)

        pygame.display.flip()

    def jelszo_bekeres(self, prompt):
        input_text = ""

        while self.allapot == 3:
            self.screen.fill(WHITE)
            text_surface = self.font.render(prompt, True, BLACK)
            self.screen.blit(text_surface, (50, 200))

            input_rect = pygame.Rect(50, 250, 300, 50)
            pygame.draw.rect(self.screen, GRAY, input_rect)
            text_surface = self.font.render(input_text, True, BLACK)
            self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return input_text
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

    def csatalakozo_oldal(self):
        self.send({"type": "get_rooms"})

        while self.allapot == 2:
            self.screen.fill(WHITE)
            title = self.font.render("Válassz egy szobát:", True, BLACK)
            self.screen.blit(title, (50, 30))

            room_buttons = []
            for i, room in enumerate(self.rooms):
                room_text = self.font.render(room, True, BLUE)
                rect = room_text.get_rect(topleft=(50, 100 + i * 50))
                room_buttons.append((rect, room))
                self.screen.blit(room_text, rect.topleft)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, room in room_buttons:
                        if rect.collidepoint(mouse_pos):
                            self.allapot = 3
                            password = self.jelszo_bekeres(f"{room} jelszava:")
                            self.send(
                                {
                                    "type": "join_room",
                                    "room_name": room,
                                    "password": password,
                                }
                            )

    def game_started_screen(
        self,
        kezben_levo_lapok,
        elotte_levo_kartyak,
        jatekosok,
        message,
        kozepso_lap,
        allitas,
        allitas2,
    ):
        small_font = pygame.font.Font(None, 20)
        info_font = pygame.font.Font(None, 36)
        player_font = pygame.font.Font(None, 24)
        count_font = pygame.font.Font(None, 24)
        message_font = pygame.font.Font(None, 30)
        kep_mappa = os.path.join("csotanypoker", "client", "kepek")

        kartya_csoportok = defaultdict(list)
        for lap in kezben_levo_lapok:
            kartya_csoportok[lap].append(lap)

        logo_images = {}
        for player_data in jatekosok.values():
            for lap_tipus in player_data["elotte_levo_kartyak"].keys():
                if lap_tipus not in logo_images:
                    logo_utvonal = os.path.join(kep_mappa, f"{lap_tipus}_logo.png")
                    if os.path.exists(logo_utvonal):
                        logo = pygame.image.load(logo_utvonal)
                        logo = pygame.transform.scale(logo, (40, 40))
                        logo_images[lap_tipus] = logo
        player_panels = []
        while self.allapot == 5:
            self.screen.fill((255, 255, 255))

            text = message_font.render(message, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect = (self.width / 1.2, 30)
            self.screen.blit(text, text_rect)

            player_panel_height = 200
            player_panel_width = 120
            player_spacing = 30
            total_players_width = (player_panel_width * len(jatekosok)) + (
                player_spacing * (len(jatekosok) - 1)
            )
            start_x = (self.width - total_players_width) / 2
            player_panels = []
            for i, (player_name, player_data) in enumerate(jatekosok.items()):
                player_panel_rect = pygame.Rect(
                    start_x + i * (player_panel_width + player_spacing),
                    60,
                    player_panel_width,
                    player_panel_height,
                )

                pygame.draw.rect(self.screen, GRAY, player_panel_rect, border_radius=5)

                player_name_text = player_font.render(
                    f"nev: {player_name}", True, (0, 0, 0)
                )
                self.screen.blit(
                    player_name_text,
                    (player_panel_rect.x + 10, player_panel_rect.y + 10),
                )

                card_count_text = count_font.render(
                    f"lapszam: {sum(player_data['kezben_levo_kartyak'])}",
                    True,
                    (0, 0, 0),
                )
                self.screen.blit(
                    card_count_text,
                    (player_panel_rect.x + 10, player_panel_rect.y + 30),
                )

                card_x = player_panel_rect.x + 10
                card_y = player_panel_rect.y + 60
                col_width = 60

                for j, (lap_tipus, count) in enumerate(
                    player_data["elotte_levo_kartyak"].items()
                ):
                    column = j % 2
                    row = j // 2
                    pos_x = player_panel_rect.x + 10 + (column * col_width)
                    pos_y = player_panel_rect.y + 60 + (row * 30)

                    if lap_tipus in logo_images:
                        small_logo = pygame.transform.scale(
                            logo_images[lap_tipus], (25, 25)
                        )
                        self.screen.blit(small_logo, (pos_x, pos_y))
                        count_text = small_font.render(str(count), True, (0, 0, 0))
                        self.screen.blit(count_text, (pos_x + 30, pos_y + 5))
                    else:
                        card_text = small_font.render(
                            f"{lap_tipus}: {count}", True, (0, 0, 0)
                        )
                        self.screen.blit(card_text, (pos_x, pos_y))
                player_panels.append((player_panel_rect, player_name))

            info_panel_rect = pygame.Rect(self.width - 250, 150, 230, 400)

            info_title = info_font.render("Állatok száma:", True, BLACK)
            self.screen.blit(
                info_title, (info_panel_rect.x + 10, info_panel_rect.y + 10)
            )

            col_width = 110

            items_per_column = (len(elotte_levo_kartyak) + 1) // 2

            for i, lap_tipus in enumerate(elotte_levo_kartyak.keys()):
                col = i // items_per_column
                row = i % items_per_column

                x_pos = info_panel_rect.x + 15 + (col * col_width)
                y_pos = info_panel_rect.y + 60 + (row * 50)

                if lap_tipus in logo_images:
                    logo = logo_images[lap_tipus]
                    self.screen.blit(logo, (x_pos, y_pos))

                    count_text = count_font.render(
                        f"{elotte_levo_kartyak[lap_tipus]}", True, BLACK
                    )
                    self.screen.blit(count_text, (x_pos + 45, y_pos + 10))
                else:
                    lap_info = count_font.render(
                        f"{lap_tipus}: {elotte_levo_kartyak[lap_tipus]}", True, BLACK
                    )
                    self.screen.blit(lap_info, (x_pos, y_pos + 10))

            eltolasi_meret = 10
            kartya_poziciok = []

            x_kep, y_kep = self.width / 2, self.height / 1.3
            for lap, lap_lista in kartya_csoportok.items():
                kep_utvonal = os.path.join(kep_mappa, f"{lap}.png")

                if os.path.exists(kep_utvonal):
                    kep = pygame.image.load(kep_utvonal)
                    eredeti_meret = kep.get_size()
                    meret_arany = min(self.width / 1600, self.height / 1600)
                    kartya_meret = (
                        int(eredeti_meret[0] * meret_arany),
                        int(eredeti_meret[1] * meret_arany),
                    )

                    kep = pygame.transform.scale(kep, kartya_meret)
                    for i in range(len(lap_lista)):
                        kartya_rect = pygame.Rect(
                            x_kep - (len(kartya_csoportok) * kartya_meret[0] / 2),
                            y_kep - i * eltolasi_meret,
                            *kartya_meret,
                        )
                        self.screen.blit(kep, (kartya_rect.x, kartya_rect.y))
                        kartya_poziciok.append((kartya_rect, lap))
                    x_kep += kartya_meret[0] + 10

            if kozepso_lap != None:
                card_width, card_height = 100, 150
                card_x = (self.width - card_width) // 2
                card_y = (self.height - card_height) // 2

                if kozepso_lap == "hatlap":
                    kozepso_lap_path = os.path.join(
                        "csotanypoker", "client", "kepek", "hatlap.png"
                    )

                    pipa_path = os.path.join(
                        "csotanypoker", "client", "kepek", "pipa.png"
                    )
                    if os.path.exists(pipa_path):
                        pipa_img = pygame.image.load(pipa_path)
                        pipa_img = pygame.transform.scale(pipa_img, (40, 40))
                        self.screen.blit(
                            pipa_img, (card_x - 50, card_y + (card_height // 2) - 20)
                        )

                    x_path = os.path.join("csotanypoker", "client", "kepek", "x.png")
                    if os.path.exists(x_path):
                        x_img = pygame.image.load(x_path)
                        x_img = pygame.transform.scale(x_img, (40, 40))
                        self.screen.blit(
                            x_img,
                            (
                                card_x + card_width + 10,
                                card_y + (card_height // 2) - 20,
                            ),
                        )

                elif kozepso_lap in kartya_csoportok:
                    kozepso_lap_path = os.path.join(
                        "csotanypoker", "client", "kepek", f"{kozepso_lap}.png"
                    )

                kozepso_lap_image = pygame.image.load(kozepso_lap_path)

                kozepso_lap_image = pygame.transform.scale(
                    kozepso_lap_image, (card_width, card_height)
                )

                self.screen.blit(kozepso_lap_image, (card_x, card_y))

                description_text = small_font.render(
                    allitas, True, (0, 0, 0)
                )  # ellenfél állitása
                self.screen.blit(
                    description_text, (card_x + card_width + 50, card_y + 10)
                )

                description_text = small_font.render(
                    allitas2, True, (0, 0, 0)
                )  # saját állitás
                self.screen.blit(
                    description_text, (card_x - 100, card_y + card_height + 20)
                )

                # Állatok közötti választás
                pygame.draw.rect(
                    self.screen, (180, 180, 180), self.lenyiloablak_pozicio
                )
                dropdown_text = small_font.render(
                    self.allat_kivalasztva, True, (0, 0, 0)
                )
                self.screen.blit(
                    dropdown_text,
                    (self.lenyiloablak_pozicio.x + 5, self.lenyiloablak_pozicio.y + 5),
                )

                if self.lenyiloablak_allapot:
                    for i, option in enumerate(self.allatok):
                        option_rect = pygame.Rect(
                            self.lenyiloablak_pozicio.x,
                            self.lenyiloablak_pozicio.y + (i + 1) * 20,
                            100,
                            20,
                        )
                        pygame.draw.rect(self.screen, GRAY, option_rect)
                        option_text = small_font.render(option, True, (0, 0, 0))
                        self.screen.blit(
                            option_text, (option_rect.x + 5, option_rect.y + 5)
                        )

                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    self.elfogado_gomb_pozicio,
                )
                accept_text = small_font.render("Valasz", True, BLACK)
                self.screen.blit(
                    accept_text,
                    (
                        self.elfogado_gomb_pozicio.x + 10,
                        self.elfogado_gomb_pozicio.y + 5,
                    ),
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.allapot = 10
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.allapot = 10
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for rect, lap in kartya_poziciok:
                        if rect.collidepoint(mx, my):
                            print(f"Rákattintottál: {lap}")
                            break

                    mx, my = event.pos
                    for rect, player_name in player_panels:
                        if rect.collidepoint(mx, my):
                            print(f"Rákattintottál {player_name}-ra")
                            break
                    if self.lenyiloablak_pozicio.collidepoint(mx, my):
                        self.lenyiloablak_allapot = not self.lenyiloablak_allapot

                    if self.lenyiloablak_allapot:
                        for i, option in enumerate(self.allatok):
                            option_rect = pygame.Rect(
                                self.lenyiloablak_pozicio.x,
                                self.lenyiloablak_pozicio.y + (i + 1) * 20,
                                100,
                                20,
                            )
                            if option_rect.collidepoint(mx, my):
                                self.allat_kivalasztva = option
                                self.lenyiloablak_allapot = False

                    if (
                        self.elfogado_gomb_pozicio.collidepoint(mx, my)
                        and self.allat_kivalasztva
                    ):
                        print(f"Elfogadott állat: {self.allat_kivalasztva}")

            pygame.display.flip()

    def szoveg_felrajzolas(self, text, position, font, color=BLACK):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, text_rect)

    def beviteli_mezo_felrajzolasa(self, rect, text, active=False):
        color = BLACK if active else GRAY
        pygame.draw.rect(self.screen, color, rect, 2)
        input_surface = self.font_kozepes.render(text, True, BLACK)
        self.screen.blit(input_surface, (rect.x + 10, rect.y + 10))

    def gomb_felrajzolas(self, text, rect, color=BLACK):
        pygame.draw.rect(self.screen, color, rect)
        button_text = self.button_font.render(text, True, WHITE)
        self.screen.blit(button_text, (rect.x + 25, rect.y + 10))


def main():
    client = Client()


if __name__ == "__main__":
    main()
