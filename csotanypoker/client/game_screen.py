import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    ANIMALS,
    BLACK,
    FONT_MEDIUM,
    FONT_SMALL,
    GRAY,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from csotanypoker.client.drawing_helpers import draw_image, draw_text, load_image


class GameScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)

        self.client.selected_card = None
        self.selected_player = None
        self.selected_player_frame = None
        self.selected_card_frame = None

        self.frame_color = RED
        self.statement = None
        self.dropdown_position = pygame.Rect(
            SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 150, 100, 30
        )
        self.accept_button_position = pygame.Rect(
            SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2 + 150, 100, 30
        )

        self.checkmark_rect = None
        self.cross_rect = None
        self.passing = False
        self.client.passed = False
        self.logout_button = pygame.Rect(100, 600, 140, 50)
        self.leave_button = pygame.Rect(100, 500, 140, 50)

    def draw(self) -> None:
        """
        Draw the game screen.
        """
        self.client.window.fill(WHITE)

        small_font = pygame.font.Font(None, FONT_SMALL)
        medium_font = pygame.font.Font(None, FONT_MEDIUM)

        logo_images = {}
        for allat in ANIMALS:
            logo_images[allat] = load_image(allat, type="logo", size=(40, 40))

        while self.client.screen == "game":
            self.client.window.fill(WHITE)
            font_medium = pygame.font.Font(None, FONT_MEDIUM)
            pygame.draw.rect(self.client.window, GRAY, self.logout_button)
            draw_text(
                self.client.window,
                "Kijelentkezés",
                BLACK,
                self.logout_button.centerx,
                self.logout_button.centery,
                centered=True,
                font=font_medium,
            )
            print(
                f"A játék során aktiv játékosok: {self.client.active_player_list_name}"
            )

            if len(self.client.active_player_list_name) < len(
                self.client.game_state.players
            ):
                pygame.draw.rect(self.client.window, GRAY, self.leave_button)
                draw_text(
                    self.client.window,
                    "Szoba elhagyása",
                    BLACK,
                    self.leave_button.centerx,
                    self.leave_button.centery,
                    centered=True,
                    font=font_medium,
                )

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
                f"Felhasználónév: {self.client.user.name}",
                BLACK,
                10,
                40,
                False,
            )

            draw_text(
                self.client.window,
                f"aktiv player: {self.client.game_state.active_player.name}",
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
                player_panel_width * (len(self.client.game_state.players) - 1)
            ) + (player_spacing * (len(self.client.game_state.players) - 1))
            start_x = (SCREEN_WIDTH - total_players_width) / 2
            player_panels = []
            for i, player in enumerate(
                j
                for j in self.client.game_state.players
                if j.name != self.client.user.name
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
                    player.name,
                    BLACK,
                    player_panel_rect.x + 10,
                    player_panel_rect.y + 10,
                    False,
                    medium_font,
                )
                draw_text(
                    self.client.window,
                    f"lapszam: {player.card_count}",
                    BLACK,
                    player_panel_rect.x + 10,
                    player_panel_rect.y + 30,
                    False,
                    medium_font,
                )

                card_x = player_panel_rect.x + 10
                card_y = player_panel_rect.y + 60
                col_width = 60

                for j, (card_type, count) in enumerate(player.cards_in_front.items()):
                    column = j % 2
                    row = j // 2
                    pos_x = player_panel_rect.x + 10 + (column * col_width)
                    pos_y = player_panel_rect.y + 60 + (row * 30)

                    if card_type in logo_images:
                        draw_image(
                            self.client.window,
                            logo_images[card_type],
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
                            f"{card_type}: {count}",
                            BLACK,
                            pos_x,
                            pos_y,
                            False,
                            medium_font,
                        )

                player_panels.append((player_panel_rect, player.name))
            if self.selected_player_frame:
                pygame.draw.rect(
                    self.client.window,
                    self.frame_color,
                    self.selected_player_frame,
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

            items_per_column = (len(self.client.user.cards_in_front or {}) + 1) // 2

            for i, card_type in enumerate(self.client.user.cards_in_front or {}):
                col = i // items_per_column
                row = i % items_per_column

                x_pos = info_panel_rect.x + 15 + (col * col_width)
                y_pos = info_panel_rect.y + 60 + (row * 50)

                if card_type in logo_images:
                    logo = logo_images[card_type]

                    draw_image(self.client.window, logo, x_pos, y_pos, centered=False)

                    draw_text(
                        self.client.window,
                        f"{self.client.user.cards_in_front[card_type]}",
                        BLACK,
                        x_pos + 45,
                        y_pos + 10,
                        False,
                        medium_font,
                    )
                else:
                    draw_text(
                        self.client.window,
                        f"{card_type}: {self.client.user.cards_in_front[card_type]}",
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
            for lap in self.client.user.cards_in_hand:
                if lap.type not in lap_csoportok:
                    lap_csoportok[lap.type] = []
                lap_csoportok[lap.type].append(lap)

            tipus_szam = len(lap_csoportok)

            x_kep = SCREEN_WIDTH // 2

            for animal_type, lapok in lap_csoportok.items():
                meret_arany = min(SCREEN_WIDTH / 1600, SCREEN_HEIGHT / 1600)
                kep = load_image(animal_type, "card", scale_ratio=meret_arany)
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
            if self.selected_card_frame:
                pygame.draw.rect(
                    self.client.window,
                    self.frame_color,
                    self.selected_card_frame,
                    3,
                )
            if self.client.game_state.question_card != None:
                card_width, card_height = 100, 150
                card_x = (SCREEN_WIDTH - card_width) // 2
                card_y = (SCREEN_HEIGHT - card_height) // 2
                if self.client.game_state.question_card.type == "hatlap":
                    kozepso_lap_image = load_image(
                        self.client.game_state.question_card.type,
                        type="card",
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
                        self.client.game_state.targeted_player.name
                        == self.client.user.name
                    ):
                        pipa_img = load_image("pipa", type="button", size=(40, 40))
                        self.checkmark_rect = pygame.Rect(
                            (card_x - 50, card_y + (card_height // 2) - 20),
                            (40, 40),
                        )
                        draw_image(
                            self.client.window,
                            pipa_img,
                            self.checkmark_rect.x,
                            self.checkmark_rect.y,
                            size=(40, 40),
                            centered=False,
                        )

                        x_img = load_image("x", type="button", size=(40, 40))
                        self.cross_rect = pygame.Rect(
                            (
                                card_x + card_width + 10,
                                card_y + (card_height // 2) - 20,
                            ),
                            (40, 40),
                        )
                        draw_image(
                            self.client.window,
                            x_img,
                            self.cross_rect.x,
                            self.cross_rect.y,
                            size=(40, 40),
                            centered=False,
                        )

                        if len(
                            self.client.game_state.question_card.visited_already
                        ) < len(self.client.game_state.players):
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

                elif self.client.game_state.question_card:
                    lap_img = load_image(
                        self.client.game_state.question_card.type,
                        "card",
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
                    self.client.game_state.active_player.statement,
                    BLACK,
                    card_x + card_width + 50,
                    card_y + 10,
                    False,
                    small_font,
                )

            if self.selected_player != None and self.client.selected_card != None:
                pygame.draw.rect(
                    self.client.window, (180, 180, 180), self.dropdown_position
                )
                draw_text(
                    self.client.window,
                    self.statement,
                    BLACK,
                    self.dropdown_position.x + 5,
                    self.dropdown_position.y + 5,
                    False,
                    small_font,
                )

                if self.client.dropdown_state:
                    self.client.game_state.question_card = self.client.selected_card

                    for i, option in enumerate(ANIMALS):
                        option_rect = pygame.Rect(
                            self.dropdown_position.x,
                            self.dropdown_position.y + (i + 1) * 20,
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
                    self.accept_button_position,
                )
                draw_text(
                    self.client.window,
                    "Valaszt",
                    BLACK,
                    self.accept_button_position.x + 10,
                    self.accept_button_position.y + 5,
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
                    if self.logout_button.collidepoint(mx, my):
                        # print("Kijelentkezés gombra kattintva!")
                        self.client.network.logout()
                        return
                    if self.leave_button.collidepoint(mx, my):
                        print("Szoba elhagyása gombra kattintva!")
                        self.client.network.leave_room()
                    for rect, lap in reversed(kartya_poziciok):
                        # if (
                        #     self.client.game_state.active_player.name
                        #     != self.client.user.name
                        # ):
                        #     # print(
                        #     #     f"Nem te vagy az aktív játékos. Aktív: {self.client.game_state.active_player.name}, Te: {self.client.user.name}"
                        #     # )
                        # if self.client.dropdown_state:
                        #     print("A lenyíló ablak nyitva van.")
                        # if self.client.passed:
                        #     print("Már átadta a kört.")
                        # if self.passing:
                        #     print("Passzoltál ebben a körben.")
                        # if talalt:
                        #     print("Már kiválasztottál egy kártyát.")

                        if (
                            rect.collidepoint(mx, my)
                            and self.client.game_state.active_player.name
                            == self.client.user.name
                            and not self.client.dropdown_state
                            and not self.client.passed
                            and not self.passing
                            and not talalt
                        ):
                            self.client.game_state.question_card = None
                            # print(f"Rákattintottál: {lap}")
                            if lap != None:
                                self.client.selected_card = lap
                            self.selected_card_frame = rect
                            talalt = True
                            break

                    mx, my = event.pos

                    inactive_players = [
                        p
                        for p in self.client.game_state.players
                        if player.name not in self.client.active_player_list_name
                    ]

                    for rect, player_name in player_panels:
                        if (
                            rect.collidepoint(mx, my)
                            and self.client.game_state.active_player.name
                            == self.client.user.name
                            and not self.client.passed
                        ):
                            if inactive_players:
                                inactive_names = ", ".join(
                                    [p.name for p in inactive_players]
                                )
                                self.client.message = f"{inactive_names} inaktív"
                                break

                            player_obj = next(
                                (
                                    p
                                    for p in self.client.game_state.players
                                    if p.name == player_name
                                ),
                                None,
                            )

                            if player_obj is None:
                                self.client.message = "Hiba: játékos nem található."
                                break

                            if (
                                self.client.game_state.question_card == None
                                or player_name
                                not in self.client.game_state.question_card.visited_already
                            ):
                                self.client.game_state.question_card = None

                                self.selected_player = player_name
                                self.selected_player_frame = rect
                            else:
                                self.client.message = "Már volt már ennél a játékosnál"

                    if self.dropdown_position.collidepoint(mx, my):
                        self.client.dropdown_state = not self.client.dropdown_state
                    if self.client.dropdown_state:
                        for i, option in enumerate(ANIMALS):
                            option_rect = pygame.Rect(
                                self.dropdown_position.x,
                                self.dropdown_position.y + (i + 1) * 20,
                                100,
                                20,
                            )
                            if option_rect.collidepoint(mx, my):
                                self.statement = option
                                self.client.dropdown_state = False

                    if (
                        self.accept_button_position.collidepoint(mx, my)
                        and self.statement
                    ):
                        # print(f"Elfogadott állat: {self.statement}")
                        if self.selected_player and self.client.selected_card:
                            self.client.network.oke_click(
                                self.client.room_id,
                                self.selected_player,
                                self.client.selected_card,
                                self.statement,
                                self.passing,
                            )

                            self.selected_player = None
                            self.client.selected_card = None
                            self.passing = False
                            self.client.passed = True
                            self.selected_player_frame = None
                            self.selected_card_frame = None
                    if (
                        self.checkmark_rect is not None
                        and self.checkmark_rect.collidepoint(mx, my)
                    ):
                        # print("Igazat mondott")
                        self.client.game_state.question_card = None
                        self.client.network.guess(self.client.room_id, True)
                    if self.cross_rect is not None and self.cross_rect.collidepoint(
                        mx, my
                    ):
                        # print("Hazudott")
                        self.client.game_state.question_card = None

                        self.client.network.guess(self.client.room_id, False)

                    if hasattr(self, "pass_rect") and self.pass_rect.collidepoint(
                        mx, my
                    ):
                        # print("PASS gombra kattintva!")
                        self.client.network.passing(self.client.room_id)
                        self.passing = True
            pygame.display.flip()

    def handle_key_press(self, event):
        pass

    def handle_mouse_click(self, pos):
        pass
