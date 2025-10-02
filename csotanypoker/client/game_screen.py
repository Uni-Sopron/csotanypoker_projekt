import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    LIGHT_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    MIDDLE_GREEN_TRANSPARENT_50,
    LIGHTER_GREEN_TRANSPARENT,
    MIDDLE_GREEN_TRANSPARENT_90,
    RED,
    RED_TRANSPARENT,
    WHITE,
    DARK_GREEN,
    JATEKSZABALY,
)
from csotanypoker.models.animal import Animal
from csotanypoker.client.drawing_helpers import (
    _draw_rounded_rect,
    draw_button,
    draw_image,
    draw_image_button,
    draw_text,
    load_background,
    load_image,
    create_logout_button_rect,
    create_rules_button_rect,
    draw_logout_button,
    draw_rules_button,
    draw_rules_popup,
    check_logout_button_interaction,
    check_rules_button_interaction,
    handle_logout_button_click,
    this_is_ai_name,
    wrap_text,
    preload_all_images,
    create_volume_button_rect,
    draw_sound_volume,
)


class GameScreen(BaseScreen):
    def __init__(self, client) -> None:
        super().__init__(client)

        self.selected_card_frame = None
        self.show_rules = False
        self.frame_color = RED
        self.statement = None
        self.show_leave_button = False
        self.adott = False
        self.show_center_card = False
        self.show_tipp_area = False

        self.checkmark_rect = None
        self.cross_rect = None
        self.client.passed = False

        self.local_question_card = None
        self.local_targeted_player = None
        self.local_active_animal = None

        self.logout_button = create_logout_button_rect(self.client.height)
        self.rules_button = create_rules_button_rect(
            self.client.width, self.client.height
        )
        self.leave_button = pygame.Rect(
            self.logout_button.x, self.logout_button.y - 90, 200, 75
        )
        self.last_game_id = None
        self.hovered_elements = set()
        self.pressed_elements = set()

        self.active_animal = None

        self._logo_images_cache = None
        self._images_preloaded = False

    def _ensure_images_preloaded(self):
        if not self._images_preloaded:
            preload_all_images()
            self._logo_images_cache = {}
            for allat in Animal:
                self._logo_images_cache[allat] = load_image(
                    allat.value, image_type="logo", size=(50, 50)
                )

            self._images_preloaded = True

    def _update_button_states(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered_elements.clear()
        if not mouse_pressed:
            self.pressed_elements.clear()

        is_logout_hovered, is_logout_pressed = check_logout_button_interaction(
            mouse_pos, mouse_pressed, self.logout_button
        )
        if is_logout_hovered:
            self.hovered_elements.add("logout")
        if is_logout_pressed:
            self.pressed_elements.add("logout")

        self.show_rules = check_rules_button_interaction(mouse_pos, self.rules_button)

        if self.leave_button.collidepoint(mouse_pos):
            self.hovered_elements.add("leave")
            if mouse_pressed:
                self.pressed_elements.add("leave")

        if hasattr(self, "oke_button") and self.oke_button.collidepoint(mouse_pos):
            self.hovered_elements.add("ok")
            if mouse_pressed:
                self.pressed_elements.add("ok")

        if hasattr(self, "pass_button") and self.pass_button.collidepoint(mouse_pos):
            self.hovered_elements.add("pass")
            if mouse_pressed:
                self.pressed_elements.add("pass")

        if (
            hasattr(self, "cross_rect")
            and self.cross_rect
            and self.cross_rect.collidepoint(mouse_pos)
        ):
            self.hovered_elements.add("cross")
            if mouse_pressed:
                self.pressed_elements.add("cross")

        if (
            hasattr(self, "checkmark_rect")
            and self.checkmark_rect
            and self.checkmark_rect.collidepoint(mouse_pos)
        ):
            self.hovered_elements.add("checkmark")
            if mouse_pressed:
                self.pressed_elements.add("checkmark")

    def draw_center_card_area(self):
        card_to_show = self.local_question_card or self.client.game_state.question_card

        if card_to_show:
            card = load_image(card_to_show, "card", size=(65 * 2.5, 100 * 2.5))
            draw_image(
                self.client.window,
                card,
                self.client.width // 2,
                self.client.height // 2,
                centered=True,
            )

    def draw_tipp_area(self):
        self.cross_rect = draw_image_button(
            self.client.window,
            "x",
            "button",
            self.client.width // 2 - 130,
            self.client.height // 2 + 60,
            (70, 70),
            border_radius=0,
            centered=True,
            is_hovered="cross" in self.hovered_elements,
            is_active="cross" in self.pressed_elements,
        )

        self.checkmark_rect = draw_image_button(
            self.client.window,
            "pipa",
            "button",
            self.client.width // 2 + 130,
            self.client.height // 2 + 60,
            (80, 80),
            border_radius=0,
            centered=True,
            is_hovered="checkmark" in self.hovered_elements,
            is_active="checkmark" in self.pressed_elements,
        )

        print("eddig meglátogatottak száma: ", self.client.game_state.visited_already)
        print("playerek száma: ", len(self.client.users))
        if len(self.client.game_state.visited_already) < (len(self.client.users) - 1):
            draw_button(
                surface=self.client.window,
                rect=self.pass_button,
                text="Tovább",
                text_color=WHITE,
                background_color=MIDDLE_GREEN,
                border_color=MIDDLE_GREEN,
                font_size=20,
                font_type="bold",
                border_width=5,
                is_hovered="pass" in self.hovered_elements,
                is_pressed="pass" in self.pressed_elements,
                hover_color=LIGHT_GREEN,
                pressed_color=LIGHT_GREEN,
            )

    def draw_card_in_hand(self):
        self.kartya_poziciok = []

        y_kep = self.client.height - 180
        eltolasi_meret = 8

        lap_csoportok = {}
        for lap in self.client.visible_player.cards_in_hand:
            if lap.value not in lap_csoportok:
                lap_csoportok[lap.value] = []
            lap_csoportok[lap.value].append(lap)

        rendezett_allatok = [
            animal.value for animal in Animal if animal.value in lap_csoportok
        ]

        tipus_szam = len(rendezett_allatok)
        x_kep = self.client.width // 2

        for animal_type in rendezett_allatok:
            lapok = lap_csoportok[animal_type]

            base_kartya_meret = (int(650 * 0.16), int(1000 * 0.16))

            for i, lap in enumerate(lapok):
                kartya_meret = base_kartya_meret
                card_y = y_kep - i * eltolasi_meret

                kartya_rect = pygame.Rect(
                    x_kep - (tipus_szam * base_kartya_meret[0]) // 2,
                    card_y,
                    *kartya_meret,
                )

                draw_image_button(
                    self.client.window,
                    animal_type,
                    "card",
                    kartya_rect.x,
                    kartya_rect.y,
                    kartya_meret,
                    border_radius=0,
                    centered=False,
                )
                self.kartya_poziciok.append((kartya_rect, lap))

            x_kep += base_kartya_meret[0] + 5

    def draw_mini_card(self):
        if (
            not (self.local_question_card or self.client.game_state.question_card)
            or not (
                self.local_targeted_player or self.client.game_state.targeted_player
            )
            or self.client.game_state.active_player == self.client.user.username
        ):
            return

        if not hasattr(self, "opponent_player_rects") or not self.opponent_player_rects:
            return

        target_player = (
            self.local_targeted_player or self.client.game_state.targeted_player
        )

        targeted_player_rect = None
        for rect, player_name in self.opponent_player_rects:
            if player_name == target_player:
                targeted_player_rect = rect
                break

        if not targeted_player_rect:
            return

        card_to_show = self.local_question_card or self.client.game_state.question_card

        mini_card_size = (65 * 1.5, 100 * 1.5)
        card_image = load_image(card_to_show, "card", size=mini_card_size)

        card_x = targeted_player_rect.centerx
        card_y = targeted_player_rect.bottom + 80

        draw_image(
            self.client.window,
            card_image,
            card_x,
            card_y,
            centered=True,
        )

    def draw_statements(self):
        if not hasattr(self, "opponent_player_rects") or not self.opponent_player_rects:
            return

        if self.client.game_state.active_player:
            for rect, player_name in self.opponent_player_rects:
                if player_name == self.client.game_state.active_player:
                    active_statement = [
                        player.statement
                        for player in self.client.opponent_players
                        if player.username == self.client.game_state.active_player
                    ]

                    if active_statement != [] and active_statement[0] is not None:
                        statement_x = rect.centerx
                        statement_y = rect.bottom + 15

                        statement_text = f"Ez egy {self.translate_animal_to_hungarian(str(active_statement[0]))}"
                        text_width = len(statement_text) * 8
                        statement_bg_rect = pygame.Rect(
                            statement_x - text_width // 2 - 10,
                            statement_y - 5,
                            text_width + 20,
                            30,
                        )

                        _draw_rounded_rect(
                            self.client.window,
                            MIDDLE_GREEN_TRANSPARENT_90,
                            statement_bg_rect,
                            border_radius=0.15,
                            border_color=DARK_GREEN,
                            border_width=1,
                        )

                        draw_text(
                            self.client.window,
                            statement_text,
                            WHITE,
                            statement_x,
                            statement_y + 10,
                            centered=True,
                            font="bold",
                            font_size=18,
                        )
                    break

        if self.client.game_state.targeted_player:
            for rect, player_name in self.opponent_player_rects:
                if player_name == self.client.game_state.targeted_player:
                    target_answer = [
                        player.is_true
                        for player in self.client.opponent_players
                        if player.username == self.client.game_state.targeted_player
                    ]

                    if target_answer[0] != None:
                        statement_x = rect.centerx
                        statement_y = rect.bottom + 15

                        if player_name == self.client.game_state.active_player:
                            statement_y += 40

                        if target_answer[0] == True:
                            statement_text = f"Igen, hiszek neked."
                        else:
                            statement_text = f"Nem hiszek neked."
                        text_width = len(statement_text) * 8
                        statement_bg_rect = pygame.Rect(
                            statement_x - text_width // 2 - 10,
                            statement_y - 5,
                            text_width + 20,
                            30,
                        )

                        _draw_rounded_rect(
                            self.client.window,
                            LIGHTER_GREEN_TRANSPARENT,
                            statement_bg_rect,
                            border_radius=0.15,
                            border_color=DARK_GREEN,
                            border_width=1,
                        )

                        draw_text(
                            self.client.window,
                            statement_text,
                            DARK_GREEN,
                            statement_x,
                            statement_y + 10,
                            centered=True,
                            font="bold",
                            font_size=18,
                        )
                    break

        main_player_statement = None
        statement_color = WHITE
        bg_color = MIDDLE_GREEN_TRANSPARENT_90

        if self.client.game_state.active_player == self.client.user.username:
            main_player_statement = self.client.visible_player.statement

            if main_player_statement != None:
                main_player_statement = f"Ez egy: {self.translate_animal_to_hungarian(main_player_statement)}"

        if main_player_statement:
            statement_x = self.client.width // 2
            statement_y = self.client.height - 200

            text_width = len(main_player_statement) * 8
            statement_bg_rect = pygame.Rect(
                statement_x - text_width // 2 - 10, statement_y - 5, text_width + 20, 30
            )

            _draw_rounded_rect(
                self.client.window,
                bg_color,
                statement_bg_rect,
                border_radius=0.15,
                border_color=DARK_GREEN,
                border_width=1,
            )

            draw_text(
                self.client.window,
                main_player_statement,
                statement_color,
                statement_x,
                statement_y + 10,
                centered=True,
                font="bold",
                font_size=18,
            )

    def draw_main_front_card(self):
        table_x = self.client.width - 240 - 20
        table_y = self.client.height // 2 - 175
        table_width = 240
        table_height = 350

        popup_rect = pygame.Rect(table_x, table_y, table_width, table_height)
        _draw_rounded_rect(
            self.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            popup_rect,
            border_radius=0.15,
        )

        draw_text(
            surface=self.client.window,
            text=f"{self.client.visible_player.username}",
            color=WHITE,
            x=table_x + table_width // 2,
            y=table_y + 20,
            centered=True,
            font="bold",
            font_size=20,
        )

        pygame.draw.line(
            surface=self.client.window,
            color=DARK_GREEN,
            start_pos=(table_x, table_y + 20 + 25),
            end_pos=(table_x + table_width, table_y + 20 + 25),
            width=3,
        )

        draw_text(
            surface=self.client.window,
            text="Lehelyezett lapok",
            color=WHITE,
            x=table_x + table_width // 2,
            y=table_y + 20 + 25 + 20,
            centered=True,
            font="bold",
            font_size=25,
        )

        cards_in_front = self.client.visible_player.cards_in_front or {}
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
                draw_image(self.client.window, logo, x_pos, y_pos, centered=False)

                draw_text(
                    self.client.window,
                    f"{cards_in_front[card]}",
                    DARK_GREEN,
                    x_pos + 65,
                    y_pos,
                    False,
                    font_size=40,
                )

    def draw_info_messages(self):
        _draw_rounded_rect(
            self.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            pygame.Rect(20, 20, 330, 60),
            border_radius=0.35,
        )
        draw_text(
            surface=self.client.window,
            text=f"Aktuális játékos: {this_is_ai_name(self.client.game_state.active_player)}",
            color=DARK_GREEN,
            x=50,
            y=10 + 27,
            centered=False,
            font="regular",
            font_size=20,
        )

        self._set_contextual_message()

        if self.client.message and self.client.message_display_time > 0:
            message_lines = wrap_text(self.client.message, 30)

            for i, line in enumerate(message_lines):
                draw_text(
                    self.client.window,
                    line,
                    RED,
                    self.client.width - 150,
                    50 + (i * 30),
                    centered=True,
                    font="thin",
                    font_size=25,
                )

            self.client.message_display_time -= 1

    def _set_contextual_message(self):
        if (
            not hasattr(self.client, "message")
            or self.client.message is None
            or getattr(self.client, "message_display_time", 0) <= 0
        ):
            if self.client.game_state and self.client.user:
                if self.client.game_state.active_player == self.client.user.username:
                    if self.client.passed:
                        self.client.message = (
                            "Válassz másik játékost és állíts valamit a lapról"
                        )
                        self.client.message_display_time = 1
                    else:
                        self.client.message = (
                            "Válassz kártyát és játékost, majd állíts valamit"
                        )
                        self.client.message_display_time = 1

                elif (
                    self.client.game_state.targeted_player == self.client.user.username
                ):
                    self.client.message = "Igaz vagy hamis az állítás?"
                    self.client.message_display_time = 1
                elif (
                    self.client.game_state.active_player != self.client.user.username
                    and self.client.game_state.targeted_player is None
                ):
                    self.client.message = f"Várj az {this_is_ai_name(self.client.game_state.active_player)} lépésére"
                    self.client.message_display_time = 1
                else:
                    self.client.message = f"{this_is_ai_name(self.client.game_state.targeted_player)} játékos lapot kapott {this_is_ai_name(self.client.game_state.active_player)}-től"
                    self.client.message_display_time = 1

    def draw_leave_button(self):
        draw_button(
            surface=self.client.window,
            rect=self.leave_button,
            text="Szoba elhagyása",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=26,
            font_type="bold",
            border_width=5,
            is_hovered="leave" in self.hovered_elements,
            is_pressed="leave" in self.pressed_elements,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def _reset_local_selections(self):
        print("_reset_local_selections")
        self.local_question_card = None
        self.local_targeted_player = None
        self.local_active_animal = None
        self.active_animal = None

    def draw_animal_table(self):
        table_x = 25
        table_y = self.client.height // 2 - 135
        table_width = 200
        table_height = 320

        popup_rect = pygame.Rect(table_x, table_y, table_width, table_height)
        _draw_rounded_rect(
            self.client.window,
            MIDDLE_GREEN_TRANSPARENT_50,
            popup_rect,
            border_radius=0.15,
        )

        margin = 15
        start_x = table_x + margin
        start_y = table_y + margin
        button_spacing_x = 90
        button_spacing_y = 65

        if not hasattr(self, "animal_button_rects"):
            self.animal_button_rects = {}

        animals = list(Animal)
        mouse_pos = pygame.mouse.get_pos()

        for i, animal in enumerate(animals):
            row = i // 2
            col = i % 2

            button_center_x = start_x + col * button_spacing_x + 35
            button_center_y = start_y + row * button_spacing_y + 25

            temp_rect = pygame.Rect(button_center_x - 30, button_center_y - 25, 60, 50)
            is_hovered = temp_rect.collidepoint(mouse_pos)

            is_active = self.local_active_animal == animal.value

            button_rect = draw_image_button(
                surface=self.client.window,
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
                active_scale=1.2,
                centered=True,
            )

            self.animal_button_rects[animal.value] = button_rect

        self.oke_button = pygame.Rect(
            table_x + table_width // 2 - 50, table_y + table_height - 40, 100, 35
        )

        draw_button(
            surface=self.client.window,
            rect=self.oke_button,
            text="Rendben",
            text_color=WHITE,
            background_color=MIDDLE_GREEN,
            border_color=MIDDLE_GREEN,
            font_size=20,
            font_type="bold",
            border_width=5,
            is_hovered="ok" in self.hovered_elements,
            is_pressed="ok" in self.pressed_elements,
            hover_color=LIGHT_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def draw(self) -> None:
        self._ensure_images_preloaded()
        self.show_leave_button_setting()
        self.logout_button = create_logout_button_rect(self.client.height)
        self.rules_button = create_rules_button_rect(
            self.client.width, self.client.height
        )

        current_game_id = getattr(self.client.game_state, "game_id", None)
        if current_game_id != self.last_game_id:
            self._reset_local_selections()
            self.last_game_id = current_game_id

        if self.client.game_state.active_player != self.client.user.username:
            self._reset_local_selections()

        if self.adott and not (
            self.local_targeted_player or self.client.game_state.targeted_player
        ):
            self.adott = False
            self._reset_local_selections()

        self.leave_button = pygame.Rect(
            self.logout_button.x, self.logout_button.y - 90, 200, 75
        )
        self.pass_button = pygame.Rect(
            self.client.width // 2 - 50, self.client.height // 2 + 130, 100, 35
        )

        self._update_button_states()

        load_background(self.client.width, self.client.height, self.client.window)

        self.draw_opponent_players()
        self.draw_card_in_hand()
        self.draw_main_front_card()

        draw_logout_button(
            self.client.window,
            self.logout_button,
            is_hovered="logout" in self.hovered_elements,
            is_pressed="logout" in self.pressed_elements,
        )

        question_card = self.local_question_card or self.client.game_state.question_card
        targeted_player = (
            self.local_targeted_player or self.client.game_state.targeted_player
        )

        if question_card and (
            targeted_player == self.client.user.username
            or self.client.game_state.active_player == self.client.user.username
        ):
            self.draw_center_card_area()

        if (
            self.client.game_state.active_player == self.client.user.username
            and self.adott == False
        ):
            self.draw_animal_table()

        if targeted_player == self.client.user.username and self.adott == False:
            self.draw_tipp_area()

        if self.show_leave_button:
            self.draw_leave_button()
        self.draw_mini_card()

        self.draw_statements()

        self.draw_info_messages()
        draw_rules_button(self.client.window, self.rules_button)

        if self.show_rules:
            draw_rules_popup(
                self.client.window,
                self.client.width,
                self.client.height,
                JATEKSZABALY[
                    "2" if self.client.selected_room.max_player_count == 2 else "3-6"
                ],
                self.client.selected_room.max_player_count,
            )
        volume_rect = create_volume_button_rect(
            self.client.width - 65, self.client.height - 165
        )
        draw_sound_volume(
            self.client.window,
            volume_rect.centerx,
            volume_rect.centery,
            "sound",
        )
        pygame.display.flip()

    def draw_opponent_players(self) -> None:
        if not self.client.opponent_players:
            return

        player_panel_height = 230
        player_panel_width = 160
        player_spacing = 10

        total_players_width = (
            player_panel_width * len(self.client.opponent_players)
        ) + (player_spacing * (len(self.client.opponent_players) - 1))

        start_x = (self.client.width - total_players_width) // 2
        start_y = 10

        self.opponent_player_rects = []

        for i, player in enumerate(self.client.opponent_players):
            panel_x = start_x + i * (player_panel_width + player_spacing)
            player_panel_rect = pygame.Rect(
                panel_x, start_y, player_panel_width, player_panel_height
            )

            target_player = (
                self.local_targeted_player or self.client.game_state.targeted_player
            )

            if target_player == player.username:
                background_color = LIGHTER_GREEN_TRANSPARENT
                font_color = DARK_GREEN
            elif self.client.game_state.active_player == player.username:
                background_color = MIDDLE_GREEN_TRANSPARENT_70
                font_color = WHITE
            else:
                background_color = LIGHT_GREEN_TRANSPARENT
                font_color = WHITE

            _draw_rounded_rect(
                self.client.window,
                background_color,
                player_panel_rect,
                border_color=DARK_GREEN,
                border_width=2,
                border_radius=0.15,
            )

            draw_text(
                self.client.window,
                this_is_ai_name(player.username),
                font_color,
                player_panel_rect.centerx,
                player_panel_rect.y + 15,
                centered=True,
                font="bold",
                font_size=20,
            )

            pygame.draw.line(
                self.client.window,
                DARK_GREEN,
                (player_panel_rect.x, player_panel_rect.y + 35),
                (player_panel_rect.x + player_panel_width, player_panel_rect.y + 35),
                2,
            )

            draw_text(
                self.client.window,
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
                col_width = 70
                row_height = 38

                for j, (card, count) in enumerate(player.cards_in_front.items()):
                    column = j % 2
                    row = j // 2

                    pos_x = player_panel_rect.x + 15 + (column * col_width)
                    pos_y = card_start_y + (row * row_height)

                    if card in self._logo_images_cache:
                        logo = self._logo_images_cache[card]
                        draw_image(
                            self.client.window,
                            logo,
                            pos_x,
                            pos_y,
                            size=(37, 37),
                            centered=False,
                        )

                        draw_text(
                            self.client.window,
                            str(count),
                            DARK_GREEN,
                            pos_x + 45,
                            pos_y + 2,
                            centered=False,
                            font="regular",
                            font_size=25,
                        )

            player_is_active = True
            for user in self.client.users:
                if user.username == player.username and user.is_active is False:
                    player_is_active = False
                    break

            if not player_is_active:
                _draw_rounded_rect(
                    self.client.window,
                    RED_TRANSPARENT,
                    player_panel_rect,
                    border_color=RED,
                    border_width=3,
                    border_radius=0.15,
                )

            self.opponent_player_rects.append((player_panel_rect, player.username))

    def handle_key_press(self, event):
        pass

    def show_leave_button_setting(self):
        for user in self.client.users:
            if user.is_active is False:
                self.show_leave_button = True
                return
        self.show_leave_button = False

    def handle_mouse_click(self, pos):
        if handle_logout_button_click(pos, self.logout_button, self.client.network):
            return (True, False)  

        if self.leave_button.collidepoint(pos) and self.show_leave_button:
            self.client.network.all_players_leave_room(
                self.client.selected_room.room_id
            )
            self._reset_local_selections()
            return (True, False)

        if hasattr(self, "oke_button") and self.oke_button.collidepoint(pos):
            if self.client.game_state.active_player == self.client.user.username:
                if self.show_leave_button is True:
                    self.client.message = "Várd meg míg minden játékos visszatér!"
                    self.client.message_display_time = 20
                    return (False, True) 

                if not self.client.passed:
                    if not self.local_question_card:
                        self.client.message = "Nincs kártya kiválasztva!"
                        self.client.message_display_time = 30
                        return (False, True)  

                if not self.local_targeted_player:
                    self.client.message = "Válassz egy játékost!"
                    self.client.message_display_time = 20
                    return (False, True)  

                if not self.local_active_animal:
                    self.client.message = "Válassz egy állatot!"
                    self.client.message_display_time = 20
                    return (False, True) 

                if self.adott == False:
                    self.client.game_state.question_card = self.local_question_card
                    self.client.game_state.targeted_player = self.local_targeted_player

                    self.client.network.oke_click(
                        statement=self.local_active_animal, passing=self.client.passed
                    )
                    self.client.passed = False
                    self.adott = True

                    self._reset_local_selections()
                    return (True, False)  

        if hasattr(self, "pass_button") and self.pass_button.collidepoint(pos):
            if (
                self.client.game_state.targeted_player == self.client.user.username
                and len(self.client.game_state.visited_already) < len(self.client.users)
            ):
                self.client.passed = True
                self.client.network.passing()
                return (True, False)

        if (
            hasattr(self, "cross_rect")
            and self.cross_rect
            and self.cross_rect.collidepoint(pos)
            and self.adott is False
        ):
            if self.client.game_state.targeted_player == self.client.user.username:
                print("Cross button clicked - False answer")
                self.adott = True
                self.client.network.guess(False)
                return (True, False)

        if (
            hasattr(self, "checkmark_rect")
            and self.checkmark_rect
            and self.checkmark_rect.collidepoint(pos)
            and self.adott is False
        ):
            if self.client.game_state.targeted_player == self.client.user.username:
                print("Checkmark button clicked - True answer")
                self.adott = True
                self.client.network.guess(True)
                return (True, False)


        if hasattr(self, "opponent_player_rects"):
            for rect, player_name in self.opponent_player_rects:
                if rect.collidepoint(pos) and self.adott == False:
                    if (
                        self.client.game_state.active_player
                        == self.client.user.username
                    ):
                        if self.show_leave_button is True:
                            clicked_user = None
                            for user in self.client.users:
                                if user.username == player_name:
                                    clicked_user = user
                                    break

                            if clicked_user and not clicked_user.is_active:
                                self.client.message = f"{player_name} játékos nem aktív. Várd meg amíg visszatér!"
                                self.client.message_display_time = 30
                                return (False, True)  
                            else:
                                inactive_players = [
                                    user
                                    for user in self.client.users
                                    if not user.is_active
                                ]

                                if inactive_players:
                                    self.client.message = (
                                        "Várd meg míg minden játékos visszatér!"
                                    )
                                    self.client.message_display_time = 30
                                    return (
                                        False,
                                        True,
                                    ) 

                        if player_name in self.client.game_state.visited_already:
                            self.client.message = (
                                "Nála már volt ez a lap. Válassz másik játékost."
                            )
                            self.client.message_display_time = 30
                            return (False, True) 
                        if self.local_targeted_player == player_name:
                            self.local_targeted_player = None
                        else:
                            self.local_targeted_player = player_name

                        return (True, False)  
                    else:
                        self.client.message = "Nem te vagy soron"
                        self.client.message_display_time = 30
                        return (False, True)  

        if hasattr(self, "animal_button_rects"):
            if self.client.game_state.active_player == self.client.user.username:
                for animal_name, button_rect in self.animal_button_rects.items():
                    if button_rect.collidepoint(pos):
                        if self.adott == False:
                            if self.local_active_animal == animal_name:
                                self.local_active_animal = None
                                self.active_animal = None
                            else:
                                self.local_active_animal = animal_name
                                self.active_animal = animal_name

                            return (True, False)  
                        else:
                            return (False, True)  


        for rect, lap in reversed(self.kartya_poziciok):
            if rect.collidepoint(pos):
                if self.client.passed:
                    print("Passzoltál ebben a körben.")
                    return (False, True) 

                if self.adott:
                    print("Már adtál lapot ebben a körben.")
                    return (False, True)  

                if self.client.game_state.active_player == self.client.user.username:
                    self.local_question_card = lap if lap is not None else None
                    self.selected_card_frame = rect
                    self.client._music_manager.weapon_sound(lap.value)
                    return (False, False) 
                else:
                    self.client.message = "Nem te vagy soron"
                    self.client.message_display_time = 30
                    return (False, True)  

        return (False, False)  

    def translate_animal_to_hungarian(self, animal_name: str) -> str:
        animal_translations = {
            "cockroach": "csótány",
            "rat": "patkány",
            "bat": "denevér",
            "toad": "varangy",
            "bedbug": "poloska",
            "spider": "pók",
            "fly": "légy",
            "scorpion": "skorpió",
        }

        return animal_translations.get(animal_name.lower(), animal_name)

    def handle_mouse_motion(self, pos):
        """Handle mouse motion for button hover states"""
        pass
