import pygame
from csotanypoker.client.drawing_helpers.constans import (
    DARK_GREEN,
    LEGVILAGOS_ZOLD,
    LIGHT_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    LIGHTER_GREEN,
    LIGHTER_GREEN_TRANSPARENT,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_50,
    MIDDLE_GREEN_TRANSPARENT_90,
    RED,
    WHITE,
    JATEKSZABALY,
    RED_TRANSPARENT,
)

from csotanypoker.client.drawing_helpers.drawing_helpers import (
    _draw_rounded_rect,
    draw_button,
    draw_sound_volume,
    draw_text,
    draw_image,
    draw_logout_button,
    draw_rules_button,
    draw_rules_popup,
    create_volume_button_rect,
    draw_image_button,
    load_image,
)
from csotanypoker.client.drawing_helpers.image_manager import load_background
from csotanypoker.client.drawing_helpers.text_manager import wrap_text
from csotanypoker.models.user import this_is_ai_name
from csotanypoker.models.animal import Animal


class GameDrawer:
    def __init__(self, screen):
        self.screen = screen
        self._logo_images_cache = {}
        self._preload_logos()

    def _preload_logos(self):
        for animal in Animal:
            self._logo_images_cache[animal] = load_image(
                animal.value, image_type="logo", size=(50, 50)
            )

    def draw_all(self):
        load_background(
            self.screen.client.width,
            self.screen.client.height,
            self.screen.client.window,
        )

        self._draw_opponent_players()
        self._draw_card_in_hand()
        self._draw_main_front_card()

        draw_logout_button(
            self.screen.client.window,
            self.screen.logout_button,
            is_hovered="logout" in self.screen.hovered_elements,
            is_pressed="logout" in self.screen.hovered_elements,
        )

        self._draw_center_and_mini_cards()
        self._draw_interactive_elements()
        self._draw_statements()
        self._draw_info_messages()
        self._draw_bottom_buttons()

        if self.screen.show_rules:
            draw_rules_popup(
                self.screen.client.window,
                self.screen.client.width,
                self.screen.client.height,
                JATEKSZABALY[
                    "2"
                    if self.screen.client.selected_room.max_player_count == 2
                    else "3-6"
                ],
                self.screen.client.selected_room.max_player_count,
            )

    def _draw_center_and_mini_cards(self):
        question_card = (
            self.screen.local_question_card
            or self.screen.client.game_state.question_card
        )
        targeted_player = (
            self.screen.local_targeted_player
            or self.screen.client.game_state.targeted_player
        )

        if question_card and (
            targeted_player == self.screen.client.user.username
            or self.screen.client.game_state.active_player
            == self.screen.client.user.username
        ):
            self._draw_center_card_area()

        self._draw_mini_card()

    def _draw_interactive_elements(self):
        """Interaktív elemek rajzolása"""
        if (
            self.screen.client.game_state.active_player
            == self.screen.client.user.username
            and not self.screen.adott
        ):
            self._draw_animal_table()

        if (
            self.screen.client.game_state.targeted_player
            == self.screen.client.user.username
            and self.screen.client.game_state.question_card == "card_back"
        ):
            self._draw_tipp_area()

        if self.screen.show_leave_button:
            self._draw_leave_button()

    def _draw_center_card_area(self):
        """Központi kártya rajzolása animációval"""
        card_to_show = (
            self.screen.local_question_card
            or self.screen.client.game_state.question_card
        )
        if not card_to_show:
            return

        flip_data = self.screen.animation_manager.get_flip_data(
            "center_card", card_to_show
        )
        base_width, base_height = int(65 * 2.5), int(100 * 2.5)

        if not flip_data["is_animating"]:
            card = load_image(
                flip_data["current_card"], "card", size=(base_width, base_height)
            )
            draw_image(
                self.screen.client.window,
                card,
                self.screen.client.width // 2,
                self.screen.client.height // 2,
                centered=True,
            )
            return

        progress = flip_data["progress"]
        scale = 1.0 - (progress * 2.0) if progress < 0.5 else (progress - 0.5) * 2.0
        current_card = (
            flip_data["previous_card"] if progress < 0.5 else flip_data["current_card"]
        )

        scaled_width = max(1, int(base_width * scale))
        card = load_image(current_card, "card", size=(scaled_width, base_height))
        draw_image(
            self.screen.client.window,
            card,
            self.screen.client.width // 2,
            self.screen.client.height // 2,
            centered=True,
        )

    def _draw_tipp_area(self):
        """Tippelő gombok rajzolása"""
        self.screen.cross_rect = draw_image_button(
            self.screen.client.window,
            "x",
            "button",
            self.screen.client.width // 2 - 130,
            self.screen.client.height // 2 + 60,
            (70, 70),
            border_radius=0,
            centered=True,
            is_hovered="cross" in self.screen.hovered_elements,
            is_active="cross" in self.screen.pressed_elements,
        )

        self.screen.checkmark_rect = draw_image_button(
            self.screen.client.window,
            "pipa",
            "button",
            self.screen.client.width // 2 + 130,
            self.screen.client.height // 2 + 60,
            (80, 80),
            border_radius=0,
            centered=True,
            is_hovered="checkmark" in self.screen.hovered_elements,
            is_active="checkmark" in self.screen.pressed_elements,
        )

        if len(self.screen.client.game_state.visited_already) < (
            len(self.screen.client.users) - 1
        ):
            draw_button(
                surface=self.screen.client.window,
                rect=self.screen.pass_button,
                text="Tovább",
                text_color=WHITE,
                background_color=MIDDLE_GREEN,
                border_color=MIDDLE_GREEN,
                font_size=20,
                font_type="bold",
                border_width=5,
                is_hovered="pass" in self.screen.hovered_elements,
                is_pressed="pass" in self.screen.pressed_elements,
                hover_color=LIGHT_GREEN,
                pressed_color=LIGHT_GREEN,
            )

    def _draw_card_in_hand(self):
        """Kézben lévő kártyák rajzolása"""
        self.screen.kartya_poziciok = []

        if (
            not hasattr(self.screen.client, "visible_player")
            or not self.screen.client.visible_player
            or not hasattr(self.screen.client.visible_player, "cards_in_hand")
        ):
            return

        if not self.screen.client.visible_player.cards_in_hand:
            return

        y_kep = self.screen.client.height - 180
        eltolasi_meret = 8

        lap_csoportok = {}
        for lap in self.screen.client.visible_player.cards_in_hand:
            if lap.value not in lap_csoportok:
                lap_csoportok[lap.value] = []
            lap_csoportok[lap.value].append(lap)

        rendezett_allatok = [
            animal.value for animal in Animal if animal.value in lap_csoportok
        ]

        tipus_szam = len(rendezett_allatok)
        x_kep = self.screen.client.width // 2
        base_kartya_meret = (int(650 * 0.16), int(1000 * 0.16))

        for animal_type in rendezett_allatok:
            lapok = lap_csoportok[animal_type]

            for i, lap in enumerate(lapok):
                card_y = y_kep - i * eltolasi_meret
                kartya_rect = pygame.Rect(
                    x_kep - (tipus_szam * base_kartya_meret[0]) // 2,
                    card_y,
                    *base_kartya_meret,
                )

                draw_image_button(
                    self.screen.client.window,
                    animal_type,
                    "card",
                    kartya_rect.x,
                    kartya_rect.y,
                    base_kartya_meret,
                    border_radius=0,
                    centered=False,
                )
                self.screen.kartya_poziciok.append((kartya_rect, lap))

            x_kep += base_kartya_meret[0] + 5

    def _draw_mini_card(self):
        """Mini kártya rajzolása ellenfél mellett"""
        if (
            not (
                self.screen.local_question_card
                or self.screen.client.game_state.question_card
            )
            or not (
                self.screen.local_targeted_player
                or self.screen.client.game_state.targeted_player
            )
            or self.screen.client.game_state.active_player
            == self.screen.client.user.username
        ):
            return

        if (
            not hasattr(self.screen, "opponent_player_rects")
            or not self.screen.opponent_player_rects
        ):
            return

        target_player = (
            self.screen.local_targeted_player
            or self.screen.client.game_state.targeted_player
        )

        targeted_player_rect = None
        for rect, player_name in self.screen.opponent_player_rects:
            if player_name == target_player:
                targeted_player_rect = rect
                break

        if not targeted_player_rect:
            return

        card_to_show = (
            self.screen.local_question_card
            or self.screen.client.game_state.question_card
        )

        flip_data = self.screen.animation_manager.get_flip_data(
            f"mini_{target_player}", card_to_show
        )
        base_width, base_height = int(65 * 1.5), int(100 * 1.5)

        if not flip_data["is_animating"]:
            card_image = load_image(
                flip_data["current_card"], "card", size=(base_width, base_height)
            )
            draw_image(
                self.screen.client.window,
                card_image,
                targeted_player_rect.centerx,
                targeted_player_rect.bottom + 80,
                centered=True,
            )
            return
        progress = flip_data["progress"]
        scale = 1.0 - (progress * 2.0) if progress < 0.5 else (progress - 0.5) * 2.0
        current_card = (
            flip_data["previous_card"] if progress < 0.5 else flip_data["current_card"]
        )

        scaled_width = max(1, int(base_width * scale))
        card_image = load_image(current_card, "card", size=(scaled_width, base_height))
        draw_image(
            self.screen.client.window,
            card_image,
            targeted_player_rect.centerx,
            targeted_player_rect.bottom + 80,
            centered=True,
        )

    def _draw_statements(self):
        """Állítások megjelenítése"""
        if (
            not hasattr(self.screen, "opponent_player_rects")
            or not self.screen.opponent_player_rects
        ):
            return

        if self.screen.client.game_state.active_player:
            self._draw_active_player_statement()

        if self.screen.client.game_state.targeted_player:
            self._draw_targeted_player_answer()

        self._draw_main_player_statement()

    def _draw_active_player_statement(self):
        """Aktív játékos állításának rajzolása"""
        for rect, player_name in self.screen.opponent_player_rects:
            if player_name == self.screen.client.game_state.active_player:
                active_statement = [
                    player.statement
                    for player in self.screen.client.opponent_players
                    if player.username == self.screen.client.game_state.active_player
                ]

                if active_statement and active_statement[0] is not None:
                    statement_text = (
                        f"Ez egy {self._translate_animal(str(active_statement[0]))}"
                    )
                    self._draw_statement_bubble(
                        rect.centerx,
                        rect.bottom + 15,
                        statement_text,
                        WHITE,
                        MIDDLE_GREEN_TRANSPARENT_90,
                    )
                break

    def _draw_targeted_player_answer(self):
        """Célzott játékos válaszának rajzolása"""
        for rect, player_name in self.screen.opponent_player_rects:
            if player_name == self.screen.client.game_state.targeted_player:
                target_answer = [
                    player.is_true
                    for player in self.screen.client.opponent_players
                    if player.username == self.screen.client.game_state.targeted_player
                ]

                if target_answer[0] is not None:
                    statement_y = rect.bottom + 15
                    if player_name == self.screen.client.game_state.active_player:
                        statement_y += 40

                    statement_text = (
                        "Igen, hiszek neked."
                        if target_answer[0]
                        else "Nem hiszek neked."
                    )
                    self._draw_statement_bubble(
                        rect.centerx,
                        statement_y,
                        statement_text,
                        DARK_GREEN,
                        LIGHTER_GREEN_TRANSPARENT,
                    )
                break

    def _draw_main_player_statement(self):
        """Saját játékos állításának rajzolása"""
        if (
            self.screen.client.game_state.active_player
            != self.screen.client.user.username
        ):
            return

        statement = self.screen.client.visible_player.statement
        if statement is None:
            return

        statement_text = f"Ez egy {self._translate_animal(statement)}"
        self._draw_statement_bubble(
            self.screen.client.width // 2,
            self.screen.client.height - 230,
            statement_text,
            WHITE,
            MIDDLE_GREEN_TRANSPARENT_90,
        )

    def _draw_statement_bubble(self, x, y, text, text_color, bg_color):
        """Állítás buborék rajzolása"""
        text_width = len(text) * 8
        statement_bg_rect = pygame.Rect(
            x - text_width // 2 - 10,
            y - 5,
            text_width + 20,
            30,
        )

        _draw_rounded_rect(
            self.screen.client.window,
            bg_color,
            statement_bg_rect,
            border_radius=0.15,
            border_color=DARK_GREEN,
            border_width=1,
        )

        draw_text(
            self.screen.client.window,
            text,
            text_color,
            x,
            y + 10,
            centered=True,
            font="bold",
            font_size=18,
        )

    def _draw_main_front_card(self):
        if (
            not hasattr(self.screen.client, "visible_player")
            or not self.screen.client.visible_player
        ):
            return

        table_x = self.screen.client.width - 240 - 20
        table_y = self.screen.client.height // 2 - 175
        table_width, table_height = 240, 350

        popup_rect = pygame.Rect(table_x, table_y, table_width, table_height)
        _draw_rounded_rect(
            self.screen.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            popup_rect,
            border_radius=0.15,
        )

        draw_text(
            surface=self.screen.client.window,
            text=f"{self.screen.client.visible_player.username}",
            color=WHITE,
            x=table_x + table_width // 2,
            y=table_y + 20,
            centered=True,
            font="bold",
            font_size=20,
        )

        pygame.draw.line(
            surface=self.screen.client.window,
            color=DARK_GREEN,
            start_pos=(table_x, table_y + 45),
            end_pos=(table_x + table_width, table_y + 45),
            width=3,
        )

        draw_text(
            surface=self.screen.client.window,
            text="Lehelyezett lapok",
            color=WHITE,
            x=table_x + table_width // 2,
            y=table_y + 65,
            centered=True,
            font="bold",
            font_size=25,
        )

        if not hasattr(self.screen.client.visible_player, 'cards_in_front'):
            return
        
        cards_in_front = self.screen.client.visible_player.cards_in_front or {}
        if not cards_in_front:
            return
        
        items_per_column = max(1, (len(cards_in_front) + 1) // 2)
        
        for i, card in enumerate(cards_in_front):
            col = i // items_per_column
            row = i % items_per_column
            
            x_pos = table_x + 35 + (col * table_width // 2 - 20)
            y_pos = table_y + 110 + (row * 55)
            
            if card in self._logo_images_cache:
                logo = self._logo_images_cache[card]
                draw_image(self.screen.client.window, logo, x_pos, y_pos, centered=False)
                
                draw_text(
                    self.screen.client.window,
                    f"{cards_in_front[card]}",
                    DARK_GREEN,
                    x_pos + 65,
                    y_pos,
                    False,
                    font_size=40,
                )

    def _draw_info_messages(self):
        if (
            not hasattr(self.screen.client, "game_state")
            or not self.screen.client.game_state
            or not self.screen.client.game_state.active_player
        ):
            return

        _draw_rounded_rect(
            self.screen.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            pygame.Rect(15, 20, 320, 60),
            border_radius=0.35,
        )
        draw_text(
            surface=self.screen.client.window,
            text=f"Aktuális játékos: {this_is_ai_name(self.screen.client.game_state.active_player)}",
            color=DARK_GREEN,
            x=40,
            y=37,
            centered=False,
            font="regular",
            font_size=20,
        )

        if self.screen.client.message and self.screen.client.message_display_time > 0:
            message_lines = wrap_text(self.screen.client.message, 30)

            for i, line in enumerate(message_lines):
                draw_text(
                    self.screen.client.window,
                    line,
                    RED,
                    self.screen.client.width - 150,
                    50 + (i * 30),
                    centered=True,
                    font="thin",
                    font_size=25,
                )

            self.screen.client.message_display_time -= 1

    def _draw_leave_button(self):
        """Szoba elhagyás gomb"""
        draw_button(
            surface=self.screen.client.window,
            rect=self.screen.leave_button,
            text="Szoba elhagyása",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=5,
            is_hovered="leave" in self.screen.hovered_elements,
            is_pressed="leave" in self.screen.pressed_elements,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def _draw_animal_table(self):
        """Állat választó tábla rajzolása"""
        table_x, table_y = 25, self.screen.client.height // 2 - 145
        table_width, table_height = 200, 335

        popup_rect = pygame.Rect(table_x, table_y, table_width, table_height)
        _draw_rounded_rect(
            self.screen.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            popup_rect,
            border_radius=0.15,
        )

        margin = 20
        start_x, start_y = table_x + margin, table_y + margin
        button_spacing_x, button_spacing_y = 90, 67

        if not hasattr(self.screen, "animal_button_rects"):
            self.screen.animal_button_rects = {}

        animals = list(Animal)
        mouse_pos = pygame.mouse.get_pos()

        for i, animal in enumerate(animals):
            row, col = i // 2, i % 2
            button_center_x = start_x + col * button_spacing_x + 35
            button_center_y = start_y + row * button_spacing_y + 25

            temp_rect = pygame.Rect(button_center_x - 30, button_center_y - 25, 60, 50)
            is_hovered = temp_rect.collidepoint(mouse_pos)
            is_active = self.screen.local_active_animal == animal.value

          
            if is_active:
                pygame.draw.circle(
                    self.screen.client.window,
                    LEGVILAGOS_ZOLD,
                    (button_center_x+1, button_center_y+1),
                    35,
                    6,
                )
               
            button_rect = draw_image_button(
                surface=self.screen.client.window,
                image_name=animal.value,
                image_type="logo",
                x=button_center_x,
                y=button_center_y,
                base_size=(58, 58),
                border_radius=1,
                padding=0,
                is_hovered=is_hovered,
                is_active=is_active,
                hover_scale=1.1,
                active_scale=1.1, 
                centered=True,
            )

            self.screen.animal_button_rects[animal.value] = button_rect
        self.screen.oke_button = pygame.Rect(
            table_x + table_width // 2 - 70, table_y + table_height - 50, 140, 45
        )

        draw_button(
            surface=self.screen.client.window,
            rect=self.screen.oke_button,
            text="Rendben",
            text_color=DARK_GREEN,
            background_color=LEGVILAGOS_ZOLD,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=3,
            is_hovered="ok" in self.screen.hovered_elements,
            is_pressed="ok" in self.screen.pressed_elements,
            hover_color=LIGHTER_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def _draw_opponent_players(self):
        if (
            not hasattr(self.screen.client, "opponent_players")
            or not self.screen.client.opponent_players
        ):
            return

        player_panel_height, player_panel_width = 230, 160
        player_spacing = 10

        total_players_width = (
            player_panel_width * len(self.screen.client.opponent_players)
        ) + (player_spacing * (len(self.screen.client.opponent_players) - 1))

        start_x = (self.screen.client.width - total_players_width) // 2
        start_y = 10

        self.screen.opponent_player_rects = []

        for i, player in enumerate(self.screen.client.opponent_players):
            panel_x = start_x + i * (player_panel_width + player_spacing)
            player_panel_rect = pygame.Rect(
                panel_x, start_y, player_panel_width, player_panel_height
            )

            if (
                len(self.screen.client.opponent_players) == 1
                and self.screen.client.user.username
                == self.screen.client.game_state.active_player
            ):
                self.screen.local_targeted_player = player.username

            target_player = (
                self.screen.local_targeted_player
                or self.screen.client.game_state.targeted_player
            )

            if target_player == player.username:
                background_color = LIGHTER_GREEN_TRANSPARENT
                font_color = DARK_GREEN
                animal_font_color = DARK_GREEN
            elif self.screen.client.game_state.active_player == player.username:
                background_color = MIDDLE_GREEN_TRANSPARENT_90
                font_color = WHITE
                animal_font_color = WHITE
            else:
                background_color = LIGHT_GREEN_TRANSPARENT
                font_color = WHITE
                animal_font_color = DARK_GREEN

            _draw_rounded_rect(
                self.screen.client.window,
                background_color,
                player_panel_rect,
                border_color=DARK_GREEN,
                border_width=2,
                border_radius=0.15,
            )

            draw_text(
                self.screen.client.window,
                this_is_ai_name(player.username),
                font_color,
                player_panel_rect.centerx,
                player_panel_rect.y + 15,
                centered=True,
                font="bold",
                font_size=20,
            )

            pygame.draw.line(
                self.screen.client.window,
                DARK_GREEN,
                (player_panel_rect.x, player_panel_rect.y + 35),
                (player_panel_rect.x + player_panel_width, player_panel_rect.y + 35),
                2,
            )

            draw_text(
                self.screen.client.window,
                f"Lapszám: {player.card_count_int}",
                font_color,
                player_panel_rect.x + 10,
                player_panel_rect.y + 40,
                centered=False,
                font="regular",
                font_size=20,
            )

            if player.cards_in_front:
                card_start_y = player_panel_rect.y + 75
                col_width, row_height = 70, 38
                
                for j, (card, count) in enumerate(player.cards_in_front.items()):
                    column, row = j % 2, j // 2
                    pos_x = player_panel_rect.x + 15 + (column * col_width)
                    pos_y = card_start_y + (row * row_height)
                    if card in self._logo_images_cache:
                        logo = self._logo_images_cache[card]
                        draw_image(
                            self.screen.client.window, logo,
                            pos_x, pos_y, size=(37, 37), centered=False
                        )

                        draw_text(
                            self.screen.client.window,
                            str(count),
                            animal_font_color,
                            pos_x + 45,
                            pos_y + 2,
                            centered=False,
                            font="regular",
                            font_size=25,
                        )

            player_is_active = True
            for user in self.screen.client.users:
                if user.username == player.username and not user.is_active:
                    player_is_active = False
                    break

            if not player_is_active:
                _draw_rounded_rect(
                    self.screen.client.window,
                    RED_TRANSPARENT,
                    player_panel_rect,
                    border_color=RED,
                    border_width=3,
                    border_radius=0.15,
                )
            
            self.screen.opponent_player_rects.append((player_panel_rect, player.username))
    
    def _draw_bottom_buttons(self):
        """Alsó gombok rajzolása"""
        draw_rules_button(self.screen.client.window, self.screen.rules_button)

        volume_rect = create_volume_button_rect(
            self.screen.client.width - 65, self.screen.client.height - 165
        )
        draw_sound_volume(
            self.screen.client.window,
            volume_rect.centerx,
            volume_rect.centery,
            "sound",
        )

    def _translate_animal(self, animal_name: str) -> str:
        """Állat nevének fordítása magyarra"""
        translations = {
            "cockroach": "csótány",
            "rat": "patkány",
            "bat": "denevér",
            "toad": "varangy",
            "bedbug": "poloska",
            "spider": "pók",
            "fly": "légy",
            "scorpion": "skorpió",
        }
        return translations.get(animal_name.lower(), animal_name)
