from colors_and_sizes import (
    BLACK,
    GRAY,
    WHITE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    RED,
    ANIMALS,
    FONT_SMALL,
    FONT_MEDIUM,
)

import pygame
from base_screen import BaseScreen
from drawing_helpers import draw_text, load_image, draw_image


class GameScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)

        self.client.kivalasztott_lap = None
        self.kivalasztott_jatekos = None
        self.kivalasztott_jatekos_keret = None
        self.kivalasztott_kartya_keret = None

        self.keret_szin = RED
        self.Allitas = None
        self.lenyiloablak_pozicio = pygame.Rect(
            SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 150, 100, 30
        )
        self.elfogado_gomb_pozicio = pygame.Rect(
            SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2 + 150, 100, 30
        )

        self.pipa_rect = None
        self.x_rect = None
        self.Passzolas = False
        self.client.atadta = False

    def draw(self) -> None:
        """
        Draw the game screen.
        """
        self.client.window.fill(WHITE)

        small_font = pygame.font.Font(None, FONT_SMALL)
        medium_font = pygame.font.Font(None, FONT_MEDIUM)

        logo_images = {}
        for allat in ANIMALS:
            logo_images[allat] = load_image(allat, size=(40, 40), logo=True)

        while self.client.screen != "Jatek_vege":
            self.client.window.fill(WHITE)
            draw_text(
                self.client.window,
                f"Szoba: {self.client.room_name}",
                BLACK,
                10,
                10,
                False,
            )
            draw_text(
                self.client.window,
                f"Felhasználónév: {self.client.user.nev}",
                BLACK,
                10,
                40,
                False,
            )

            draw_text(
                self.client.window,
                f"aktiv jatekos: {self.client.game_state.aktiv_jatekos.nev}",
                BLACK,
                10,
                70,
                False,
            )
            draw_text(
                self.client.window,
                self.client.message,
                BLACK,
                SCREEN_WIDTH / 1.2,
                30,
                False,
                small_font,
            )

            player_panel_height = 200
            player_panel_width = 120
            player_spacing = 30
            total_players_width = (
                player_panel_width * (len(self.client.game_state.jatekosok) - 1)
            ) + (player_spacing * (len(self.client.game_state.jatekosok) - 1))
            start_x = (SCREEN_WIDTH - total_players_width) / 2
            player_panels = []
            for i, jatekos in enumerate(
                j
                for j in self.client.game_state.jatekosok
                if j.nev != self.client.user.nev
            ):
                player_panel_rect = pygame.Rect(
                    start_x + i * (player_panel_width + player_spacing),
                    60,
                    player_panel_width,
                    player_panel_height,
                )

                pygame.draw.rect(
                    self.client.window, GRAY, player_panel_rect, border_radius=5
                )
                draw_text(
                    self.client.window,
                    jatekos.nev,
                    BLACK,
                    player_panel_rect.x + 10,
                    player_panel_rect.y + 10,
                    False,
                    medium_font,
                )

                draw_text(
                    self.client.window,
                    f"lapszam: {jatekos.lapszam}",
                    BLACK,
                    player_panel_rect.x + 10,
                    player_panel_rect.y + 30,
                    False,
                    medium_font,
                )

                card_x = player_panel_rect.x + 10
                card_y = player_panel_rect.y + 60
                col_width = 60

                for j, (lap_tipus, count) in enumerate(
                    jatekos.elotte_levo_kartyak.items()
                ):
                    column = j % 2
                    row = j // 2
                    pos_x = player_panel_rect.x + 10 + (column * col_width)
                    pos_y = player_panel_rect.y + 60 + (row * 30)

                    if lap_tipus in logo_images:
                        draw_image(
                            self.client.window,
                            logo_images[lap_tipus],
                            pos_x,
                            pos_y,
                            size=(25, 25),
                            centered=False,
                        )

                        draw_text(
                            self.client.window,
                            str(count),
                            BLACK,
                            pos_x + 30,
                            pos_y + 5,
                            False,
                            medium_font,
                        )

                    else:
                        draw_text(
                            self.client.window,
                            f"{lap_tipus}: {count}",
                            BLACK,
                            pos_x,
                            pos_y,
                            False,
                            medium_font,
                        )

                player_panels.append((player_panel_rect, jatekos.nev))
            if self.kivalasztott_jatekos_keret:
                pygame.draw.rect(
                    self.client.window,
                    self.keret_szin,
                    self.kivalasztott_jatekos_keret,
                    3,
                )

            info_panel_rect = pygame.Rect(SCREEN_WIDTH - 250, 150, 230, 400)

            draw_text(
                self.client.window,
                "Állatok száma:",
                BLACK,
                info_panel_rect.x + 10,
                info_panel_rect.y + 10,
                False,
            )
            col_width = 110

            items_per_column = (
                len(self.client.user.elotte_levo_kartyak or {}) + 1
            ) // 2

            for i, lap_tipus in enumerate(self.client.user.elotte_levo_kartyak or {}):
                col = i // items_per_column
                row = i % items_per_column

                x_pos = info_panel_rect.x + 15 + (col * col_width)
                y_pos = info_panel_rect.y + 60 + (row * 50)

                if lap_tipus in logo_images:
                    logo = logo_images[lap_tipus]

                    draw_image(self.client.window, logo, x_pos, y_pos, centered=False)

                    draw_text(
                        self.client.window,
                        f"{self.client.user.elotte_levo_kartyak[lap_tipus]}",
                        BLACK,
                        x_pos + 45,
                        y_pos + 10,
                        False,
                        medium_font,
                    )
                else:
                    draw_text(
                        self.client.window,
                        f"{lap_tipus}: {self.client.user.elotte_levo_kartyak[lap_tipus]}",
                        BLACK,
                        x_pos,
                        y_pos + 10,
                        False,
                        medium_font,
                    )

            kartya_poziciok = []

            y_kep = SCREEN_HEIGHT - 150
            eltolasi_meret = 10  # egymás feletti kártyák eltolása

            lap_csoportok = {}
            for lap in self.client.user.kezbenlevo_kartyak:
              
                if lap.tipus not in lap_csoportok:
                    lap_csoportok[lap.tipus] = []
                lap_csoportok[lap.tipus].append(lap)

            tipus_szam = len(lap_csoportok)

            x_kep = SCREEN_WIDTH // 2

            for tipus, lapok in lap_csoportok.items():
                meret_arany = min(SCREEN_WIDTH / 1600, SCREEN_HEIGHT / 1600)
                kep = load_image(tipus, scale_ratio=meret_arany)
                kartya_meret = kep.get_size()

                for i, lap in enumerate(lapok):
                    kartya_rect = pygame.Rect(
                        x_kep - (tipus_szam * kartya_meret[0]) // 2,
                        y_kep - i * eltolasi_meret,
                        *kartya_meret,
                    )

                    draw_image(
                        self.client.window,
                        kep,
                        kartya_rect.x,
                        kartya_rect.y,
                        size=kartya_meret,
                        centered=False,
                    )
                    kartya_poziciok.append((kartya_rect, lap))

                x_kep += kartya_meret[0] + 5
            if self.kivalasztott_kartya_keret:
                pygame.draw.rect(
                    self.client.window,
                    self.keret_szin,
                    self.kivalasztott_kartya_keret,
                    3,
                )
            if self.client.game_state.kerdeses_kartya != None:
                card_width, card_height = 100, 150
                card_x = (SCREEN_WIDTH - card_width) // 2
                card_y = (SCREEN_HEIGHT - card_height) // 2
                if self.client.game_state.kerdeses_kartya.tipus == "kerdojel":
                    kozepso_lap_image = load_image(
                        self.client.game_state.kerdeses_kartya.tipus,
                        size=(card_width, card_height),
                    )
                    draw_image(
                        self.client.window,
                        kozepso_lap_image,
                        card_x,
                        card_y,
                        size=(card_width, card_height),
                        centered=False,
                    )

                    if (
                        self.client.game_state.celzott_jatekos.nev
                        == self.client.user.nev
                    ):
                        pipa_img = load_image("pipa", size=(40, 40))
                        self.pipa_rect = pygame.Rect(
                            (card_x - 50, card_y + (card_height // 2) - 20),
                            (40, 40),
                        )
                        draw_image(
                            self.client.window,
                            pipa_img,
                            self.pipa_rect.x,
                            self.pipa_rect.y,
                            size=(40, 40),
                            centered=False,
                        )

                        x_img = load_image("x", size=(40, 40))
                        self.x_rect = pygame.Rect(
                            (
                                card_x + card_width + 10,
                                card_y + (card_height // 2) - 20,
                            ),
                            (40, 40),
                        )
                        draw_image(
                            self.client.window,
                            x_img,
                            self.x_rect.x,
                            self.x_rect.y,
                            size=(40, 40),
                            centered=False,
                        )

                        if len(
                            self.client.game_state.kerdeses_kartya.volt_ennel_mar
                        ) < len(self.client.game_state.jatekosok):
                            pass_width, pass_height = 80, 40
                            pass_x = card_x + (card_width // 2) - (pass_width // 2)
                            pass_y = card_y + card_height + 10

                            self.pass_rect = pygame.Rect(
                                (pass_x, pass_y), (pass_width, pass_height)
                            )
                            pygame.draw.rect(self.client.window, GRAY, self.pass_rect)

                            draw_text(
                                self.client.window,
                                "Tovább",
                                BLACK,
                                pass_x + (pass_width / 2),
                                pass_y + (pass_height / 2),
                                True,
                                medium_font,
                            )

                elif self.client.game_state.kerdeses_kartya:
                    lap_img = load_image(
                        self.client.game_state.kerdeses_kartya.tipus,
                        size=(card_width, card_height),
                    )
                    draw_image(
                        self.client.window,
                        lap_img,
                        card_x,
                        card_y,
                        size=(card_width, card_height),
                        centered=False,
                    )

                draw_text(
                    self.client.window,
                    self.client.game_state.aktiv_jatekos.allitas,
                    BLACK,
                    card_x + card_width + 50,
                    card_y + 10,
                    False,
                    small_font,
                )

            if (
                self.kivalasztott_jatekos != None
                and self.client.kivalasztott_lap != None
            ):
               
                pygame.draw.rect(
                    self.client.window, (180, 180, 180), self.lenyiloablak_pozicio
                )
                draw_text(
                    self.client.window,
                    self.Allitas,
                    BLACK,
                    self.lenyiloablak_pozicio.x + 5,
                    self.lenyiloablak_pozicio.y + 5,
                    False,
                    small_font,
                )

                if self.client.lenyiloablak_allapot:
                    self.client.game_state.kerdeses_kartya = (
                        self.client.kivalasztott_lap
                    )

                    for i, option in enumerate(ANIMALS):
                        option_rect = pygame.Rect(
                            self.lenyiloablak_pozicio.x,
                            self.lenyiloablak_pozicio.y + (i + 1) * 20,
                            100,
                            20,
                        )
                        pygame.draw.rect(self.client.window, GRAY, option_rect)
                        draw_text(
                            self.client.window,
                            option,
                            BLACK,
                            option_rect.x + 5,
                            option_rect.y + 5,
                            False,
                            small_font,
                        )

                pygame.draw.rect(
                    self.client.window,
                    GRAY,
                    self.elfogado_gomb_pozicio,
                )
                draw_text(
                    self.client.window,
                    "Valaszt",
                    BLACK,
                    self.elfogado_gomb_pozicio.x + 10,
                    self.elfogado_gomb_pozicio.y + 5,
                    False,
                    small_font,
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    talalt = False

                    for rect, lap in reversed(kartya_poziciok):
                        if (
                            self.client.game_state.aktiv_jatekos.nev
                            != self.client.user.nev
                        ):
                            print(
                                f"Nem te vagy az aktív játékos. Aktív: {self.client.game_state.aktiv_jatekos.nev}, Te: {self.client.user.nev}"
                            )
                        if self.client.lenyiloablak_allapot:
                            print("A lenyíló ablak nyitva van.")
                        if self.client.atadta:
                            print("Már átadta a kört.")
                        if self.Passzolas:
                            print("Passzoltál ebben a körben.")
                        if talalt:
                            print("Már kiválasztottál egy kártyát.")

                        if (
                            rect.collidepoint(mx, my)
                            and self.client.game_state.aktiv_jatekos.nev
                            == self.client.user.nev
                            and not self.client.lenyiloablak_allapot
                            and not self.client.atadta
                            and not self.Passzolas
                            and not talalt
                        ):
                            self.client.game_state.kerdeses_kartya = None
                            print(f"Rákattintottál: {lap}")
                            if lap != None:
                                self.client.kivalasztott_lap = lap
                            self.kivalasztott_kartya_keret = rect
                            talalt = True
                            break

                    mx, my = event.pos
                    for rect, player_name in player_panels:
                        if (
                            rect.collidepoint(mx, my)
                            and self.client.game_state.aktiv_jatekos.nev
                            == self.client.user.nev
                            and not self.client.atadta
                        ):
                            if (
                                self.client.game_state.kerdeses_kartya == None
                                or player_name
                                not in self.client.game_state.kerdeses_kartya.volt_ennel_mar
                            ):
                                self.client.game_state.kerdeses_kartya = None
                                print(f"Rákattintottál {player_name}-ra")
                                self.kivalasztott_jatekos = player_name
                                self.kivalasztott_jatekos_keret = rect
                            else:
                                self.client.message = "már volt már ennél a játékosnál"

                    if self.lenyiloablak_pozicio.collidepoint(mx, my):
                        self.client.lenyiloablak_allapot = (
                            not self.client.lenyiloablak_allapot
                        )
                    if self.client.lenyiloablak_allapot:
                        for i, option in enumerate(ANIMALS):
                            option_rect = pygame.Rect(
                                self.lenyiloablak_pozicio.x,
                                self.lenyiloablak_pozicio.y + (i + 1) * 20,
                                100,
                                20,
                            )
                            if option_rect.collidepoint(mx, my):
                                self.Allitas = option
                                self.client.lenyiloablak_allapot = False

                    if self.elfogado_gomb_pozicio.collidepoint(mx, my) and self.Allitas:
                        print(f"Elfogadott állat: {self.Allitas}")
                        if self.kivalasztott_jatekos and self.client.kivalasztott_lap:
                            self.client.network.oke_click(
                                self.client.room_id,
                                self.kivalasztott_jatekos,
                                self.client.kivalasztott_lap,
                                self.Allitas,
                                self.Passzolas,
                            )

                            self.kivalasztott_jatekos = None
                            self.client.kivalasztott_lap = None
                            self.Passzolas = False
                            self.client.atadta = True
                            self.kivalasztott_jatekos_keret = None
                            self.kivalasztott_kartya_keret = None
                    if self.pipa_rect is not None and self.pipa_rect.collidepoint(
                        mx, my
                    ):
                        print("Igazat mondott")
                        self.client.game_state.kerdeses_kartya = None
                        self.client.network.tipp(self.client.room_id, True)
                    if self.x_rect is not None and self.x_rect.collidepoint(mx, my):
                        print("Hazudott")
                        self.client.game_state.kerdeses_kartya = None

                        self.client.network.tipp(self.client.room_id, False)

                    if hasattr(self, "pass_rect") and self.pass_rect.collidepoint(
                        mx, my
                    ):
                        print("PASS gombra kattintva!")
                        self.client.network.passzolas(self.client.room_id)
                        self.Passzolas = True

            pygame.display.flip()

  

    def handle_key_press(self, event):
        pass

    def handle_mouse_click(self, pos):
        pass
