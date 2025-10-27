import pygame
from csotanypoker.client.drawing_helpers.constans import (
    DARK_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    LIGHTER_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    RED,
    TITLE_FONT_SIZE,
)
from csotanypoker.client.drawing_helpers.drawing_helpers import (
    create_standard_input_rect,
    draw_icon_button,
    draw_input_field,
    draw_scrollbar,
    draw_standard_button,
    draw_text,
    draw_logout_button,
    draw_sound_volume,
    draw_image,
    _draw_rounded_rect,
    create_volume_button_rect,
    create_logout_button_rect,
)
from csotanypoker.client.drawing_helpers.image_manager import (
    load_background,
    load_image,
)


class RoomDrawer:
    """Szobák képernyő rajzolásáért felelős osztály"""

    def __init__(self, screen):
        self.screen = screen

    def draw_all(self):
        """Teljes képernyő rajzolása"""
        self._setup_rects()

        if self.screen._should_update_rooms():
            self.screen.update_rooms_from_client()

        self.screen._update_button_states()

        load_background(
            self.screen.client.width,
            self.screen.client.height,
            self.screen.client.window,
        )

        self._draw_user_stats()
        self._draw_titles()
        self._draw_menu()
        self._draw_rooms_area()
        self._draw_room_creation()

        draw_logout_button(
            self.screen.client.window,
            self.screen.logout_button,
            is_hovered="logout" in self.screen.hovered_elements,
            is_pressed="logout" in self.screen.pressed_elements,
        )

        self._draw_message()
        self._draw_volume_button()

    def _setup_rects(self):
        """Rect-ek inicializálása"""
        self.screen.logout_button = create_logout_button_rect(self.screen.client.height)

        self.screen.join_button = pygame.Rect(
            self.screen.client.width - 190 - self.screen.BUTTON_PADDING,
            self.screen.client.height // 1.7,
            190,
            70,
        )

        self.screen.join_password_input = pygame.Rect(
            self.screen.client.width
            - 300
            - self.screen.join_button.width
            - (self.screen.BUTTON_PADDING * 2),
            self.screen.join_button.y + 20,
            300,
            40,
        )

    def _draw_titles(self):
        """Címek rajzolása"""
        draw_text(
            self.screen.client.window,
            "Szobák",
            DARK_GREEN,
            self.screen.client.width // 2,
            45,
            True,
            "Regular",
            TITLE_FONT_SIZE,
        )
        draw_text(
            self.screen.client.window,
            "Szoba létrehozás",
            DARK_GREEN,
            self.screen.client.width // 2,
            self.screen.client.height // 1.4,
            True,
            "Regular",
            TITLE_FONT_SIZE,
        )
    def _draw_menu(self):
            """Felső menü rajzolása"""
            menu_font_size = 38
            section_width = self.screen.client.width // 5
            menu_y = self.screen.client.height // 6
            input_height = 40

            name_x = section_width // 2 + 30
            draw_text(
                self.screen.client.window,
                "Név",
                DARK_GREEN,
                name_x,
                menu_y,
                True,
                "Regular",
                menu_font_size,
            )

            input_x = name_x + 60
            input_width = self.screen.client.width // 4
            self.screen.search_input = create_standard_input_rect(
                input_x, menu_y - input_height // 2, input_width, input_height
            )
            
            self.screen.input_handler.input_rects['search'] = self.screen.search_input

            draw_input_field(
                self.screen.client.window,
                self.screen.search_input,
                self.screen.input_handler.inputs["search"],
                self.screen.input_handler.is_active("search"),
                input_id="search",
                placeholder="Keresés...",
                text_color=DARK_GREEN,
                cursor_color=DARK_GREEN,
                placeholder_color=MIDDLE_GREEN,
                font_size=25,
            )

            self._draw_search_and_filter_buttons(input_x + input_width + 20, menu_y)

            self.screen.password_x = section_width * 3 + (section_width // 2)
            draw_text(
                self.screen.client.window,
                "Jelszóvédett",
                DARK_GREEN,
                self.screen.password_x,
                menu_y,
                True,
                "Regular",
                menu_font_size,
            )

            self.screen.count_x = section_width * 4 + (section_width // 2)
            draw_text(
                self.screen.client.window,
                "Létszám",
                DARK_GREEN,
                self.screen.count_x,
                menu_y,
                True,
                "Regular",
                menu_font_size,
            )

    def _draw_search_and_filter_buttons(self, icons_x, menu_y):
        """Keresés és szűrő gombok"""
        self.screen.search_button = draw_icon_button(
            self.screen.client.window, "search_symbol", icons_x, menu_y
        )

        padlock_images = {0: "padlock_transparent", 1: "padlock", 2: "unlock_padlock"}
        self.screen.lock_button = draw_icon_button(
            self.screen.client.window,
            padlock_images[self.screen.filter_state],
            icons_x + 35,
            menu_y,
        )

    def _draw_rooms_area(self):
        """Szobák lista rajzolása"""
        margin = 20
        area_x, area_y = margin, self.screen.client.height // 5
        area_width = self.screen.client.width - (2 * margin)
        area_height = self.screen.client.height // 2.5

        self.screen.rooms_area_rect = pygame.Rect(
            area_x, area_y, area_width, area_height
        )

        if len(self.screen.rooms) > self.screen.MAX_VISIBLE_ROOMS:
            scroll_x = area_x + area_width - self.screen.SCROLL_BAR_WIDTH
            list_height = self.screen.MAX_VISIBLE_ROOMS * (
                self.screen.ROOM_ROW_HEIGHT + self.screen.ROOM_PADDING
            )
            self.screen.scroll_bar_rect = pygame.Rect(
                scroll_x + 15, area_y + 10, self.screen.SCROLL_BAR_WIDTH, list_height
            )

        visible_rooms = self.screen._get_visible_rooms()
        for i, room in enumerate(visible_rooms):
            self._draw_room_row(room, i)

        if len(self.screen.rooms) > self.screen.MAX_VISIBLE_ROOMS:
            draw_scrollbar(
                self.screen.client.window,
                self.screen.scroll_bar_rect,
                self.screen.scroll_offset,
                len(self.screen.filtered_rooms),
                self.screen.MAX_VISIBLE_ROOMS,
            )

        self._draw_bottom_buttons()

    def _draw_room_row(self, room, row_index):
        """Egy szoba sor rajzolása"""
        if not self.screen.rooms_area_rect:
            return

        row_x = self.screen.rooms_area_rect.x + self.screen.PADDING
        row_y = (
            self.screen.rooms_area_rect.y
            + self.screen.PADDING
            + (row_index * (self.screen.ROOM_ROW_HEIGHT + self.screen.ROOM_PADDING))
        )
        row_width = self.screen.rooms_area_rect.width - (2 * self.screen.PADDING)
        row_height = self.screen.ROOM_ROW_HEIGHT

        row_rect = pygame.Rect(row_x, row_y, row_width, row_height)

        is_selected = (
            self.screen.selected_room_index is not None
            and self.screen.rooms[self.screen.selected_room_index].room_id
            == room.room_id
        )

        bg_color = LIGHTER_GREEN if is_selected else MIDDLE_GREEN_TRANSPARENT_70
        border_color = MIDDLE_GREEN if is_selected else None
        border_width = 2 if is_selected else 0

        _draw_rounded_rect(
            self.screen.client.window, bg_color, row_rect, border_color, border_width
        )

        name_text = f"{room.name} ID: {room.room_id}"
        draw_text(
            self.screen.client.window,
            name_text,
            DARK_GREEN,
            row_x + 70,
            row_y + row_height // 2,
            False,
            "regular",
            25,
            vcenter_rect=row_rect,
        )

        if room.password_protected:
            lock_image = load_image("padlock", "button", size=(40, 40))
            draw_image(
                self.screen.client.window,
                lock_image,
                self.screen.password_x,
                row_y + row_height // 2,
                centered=True,
            )

        count_text = f"{room.player_count}/{room.max_player_count}"
        draw_text(
            self.screen.client.window,
            count_text,
            DARK_GREEN,
            self.screen.count_x,
            row_y + row_height // 2,
            True,
            "regular",
            30,
        )

    def _draw_bottom_buttons(self):
        """Alsó csatlakozás gomb és jelszó mező"""
        selected_room = self.screen._get_selected_room()
        join_enabled = self.screen._is_join_enabled()

        if selected_room and selected_room.password_protected:

            self.screen.input_handler.input_rects['join_password'] = self.screen.join_password_input
            
            draw_input_field(
                self.screen.client.window,
                self.screen.join_password_input,
                self.screen.input_handler.inputs["join_password"],
                self.screen.input_handler.is_active("join_password"),
                input_id="join_password",  
                placeholder="Jelszó",
                is_password=True,
                font_size=20,
            )

        draw_standard_button(
            self.screen.client.window,
            self.screen.join_button,
            "Csatlakozás",
            is_enabled=join_enabled,
            is_hovered="join" in self.screen.hovered_elements,
            is_pressed="join" in self.screen.pressed_elements,
        )


    def _draw_room_creation(self):
        """Szoba létrehozás szekció"""
        creation_start_y = self.screen.client.height // 1.4 + 70
        self._draw_room_name_section(creation_start_y)
        self._draw_max_players_section(creation_start_y)
        self._draw_password_section(creation_start_y)
        self._draw_create_button(creation_start_y)


    def _draw_room_name_section(self, y_pos):
        """Szoba neve input"""
        self.screen.room_name_input = create_standard_input_rect(250, y_pos - 15)
        

        self.screen.input_handler.input_rects['room_name'] = self.screen.room_name_input

        draw_text(
            self.screen.client.window,
            "Szoba neve:",
            DARK_GREEN,
            100,
            y_pos - 10,
            False,
            "regular",
            30,
        )

        draw_input_field(
            self.screen.client.window,
            self.screen.room_name_input,
            self.screen.input_handler.inputs["room_name"],
            self.screen.input_handler.is_active("room_name"),
            input_id="room_name", 
            placeholder=f"{self.screen.client.user.username} szobája",
            placeholder_color=MIDDLE_GREEN,
        )

    def _draw_max_players_section(self, y_pos):
        """Max létszám választó"""
        max_players_label_rect = pygame.Rect(
            self.screen.room_name_input.x + self.screen.room_name_input.width + 20,
            y_pos - 20,
            150,
            55,
        )

        self.screen.max_count = pygame.Rect(
            max_players_label_rect.x + max_players_label_rect.width + 10,
            y_pos - 20,
            70,
            60,
        )
        
        self.screen.input_handler.input_rects['max_players'] = self.screen.max_count

        display_text = (
            self.screen.input_handler.inputs["max_players"]
            if self.screen.input_handler.is_active("max_players")
            else str(self.screen.max_players)
        )

        draw_text(
            self.screen.client.window,
            "Max létszám:",
            DARK_GREEN,
            max_players_label_rect.x,
            y_pos,
            False,
            "regular",
            30,
            vcenter_rect=max_players_label_rect,
        )

        draw_input_field(
            self.screen.client.window,
            self.screen.max_count,
            display_text,
            self.screen.input_handler.is_active("max_players"),
            input_id="max_players",  
            text_color=DARK_GREEN,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=MIDDLE_GREEN,
            cursor_color=DARK_GREEN,
            font_size=30,
        )

        arrows_x = self.screen.max_count.x + self.screen.max_count.width + 5
        arrows_y = self.screen.max_count.y - 3
        up_and_down_buttons = load_image("fel_le_nyilak", "button", size=(80, 64))
        draw_image(
            self.screen.client.window, up_and_down_buttons, arrows_x, arrows_y, False
        )

        self.screen.max_players_up = pygame.Rect(arrows_x, arrows_y, 80, 33)
        self.screen.max_players_down = pygame.Rect(arrows_x, arrows_y + 33, 80, 33)



    def _draw_max_players_section(self, y_pos):
        """Max létszám választó"""
        max_players_label_rect = pygame.Rect(
            self.screen.room_name_input.x + self.screen.room_name_input.width + 20,
            y_pos - 20,
            150,
            55,
        )

        self.screen.max_count = pygame.Rect(
            max_players_label_rect.x + max_players_label_rect.width + 10,
            y_pos - 20,
            70,
            60,
        )

        display_text = (
            self.screen.input_handler.inputs["max_players"]
            if self.screen.input_handler.is_active("max_players")
            else str(self.screen.max_players)
        )

        draw_text(
            self.screen.client.window,
            "Max létszám:",
            DARK_GREEN,
            max_players_label_rect.x,
            y_pos,
            False,
            "regular",
            30,
            vcenter_rect=max_players_label_rect,
        )

        draw_input_field(
            self.screen.client.window,
            self.screen.max_count,
            display_text,
            self.screen.input_handler.is_active("max_players"),
            text_color=DARK_GREEN,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=MIDDLE_GREEN,
            cursor_color=DARK_GREEN,
            font_size=30,
        )

        arrows_x = self.screen.max_count.x + self.screen.max_count.width + 5
        arrows_y = self.screen.max_count.y - 3
        up_and_down_buttons = load_image("fel_le_nyilak", "button", size=(80, 64))
        draw_image(
            self.screen.client.window, up_and_down_buttons, arrows_x, arrows_y, False
        )

        self.screen.max_players_up = pygame.Rect(arrows_x, arrows_y, 80, 33)
        self.screen.max_players_down = pygame.Rect(arrows_x, arrows_y + 33, 80, 33)

    def _draw_password_section(self, y_pos):
        """Jelszó védelem szekció"""
        self.screen.create_password_input = create_standard_input_rect(
            self.screen.client.width // 2 + 200, y_pos - 15, 250, 50
        )
        self.screen.input_handler.input_rects['password'] = self.screen.create_password_input

        checkbox_x = self.screen.create_password_input.x - 60
        checkbox_y = self.screen.create_password_input.y

        padlock_image = load_image(
            "padlock" if self.screen.password_protected else "unlock_padlock",
            "button",
            size=(50, 50),
        )

        self.screen.password_checkbox = pygame.Rect(checkbox_x, checkbox_y, 50, 50)
        draw_image(self.screen.client.window, padlock_image, checkbox_x, checkbox_y)

        if self.screen.password_protected:
            draw_input_field(
                self.screen.client.window,
                self.screen.create_password_input,
                self.screen.input_handler.inputs["password"],
                self.screen.input_handler.is_active("password"),
                input_id="password", 
                placeholder="Jelszó",
                placeholder_color=MIDDLE_GREEN,
                is_password=True,
            )

    def _draw_create_button(self, y_pos):
        """Létrehozás gomb"""
        self.screen.create_button = pygame.Rect(
            self.screen.client.width - 190 - self.screen.BUTTON_PADDING,
            y_pos - 25,
            190,
            70,
        )

        create_enabled = self.screen._is_create_enabled()

        draw_standard_button(
            self.screen.client.window,
            self.screen.create_button,
            "Létrehozás",
            is_enabled=create_enabled,
            is_hovered="create" in self.screen.hovered_elements,
            is_pressed="create" in self.screen.pressed_elements,
            font_size=24,
        )

    def _draw_user_stats(self):
        """Felhasználói statisztikák a bal felső sarokban"""
        if not self.screen.client.user:
            return

        stats_x, stats_y = 20, 10

        draw_text(
            self.screen.client.window,
            f"{self.screen.client.user.username}",
            DARK_GREEN,
            stats_x,
            stats_y,
            False,
            "Regular",
            27,
        )

        if hasattr(self.screen.client, "user_stats") and self.screen.client.user_stats:
            total_games = self.screen.client.user_stats.get("total_games", 0)
            won_games = self.screen.client.user_stats.get("won_games", 0)

            draw_text(
                self.screen.client.window,
                f"Játékok száma: {total_games}",
                DARK_GREEN,
                stats_x,
                stats_y + 35,
                False,
                "Regular",
                20,
            )
            draw_text(
                self.screen.client.window,
                f"Nyert játékok: {won_games}",
                DARK_GREEN,
                stats_x,
                stats_y + 55,
                False,
                "Regular",
                20,
            )
        else:
            draw_text(
                self.screen.client.window,
                "Játékok száma: ...",
                DARK_GREEN,
                stats_x,
                stats_y + 35,
                False,
                "Regular",
                20,
            )
            draw_text(
                self.screen.client.window,
                "Nyert játékok: ...",
                DARK_GREEN,
                stats_x,
                stats_y + 55,
                False,
                "Regular",
                20,
            )

    def _draw_message(self):
        """Hibaüzenet megjelenítése"""
        if self.screen.client.message and self.screen.client.message_display_time > 0:
            draw_text(
                self.screen.client.window,
                self.screen.client.message,
                RED,
                self.screen.client.width - 200,
                50,
                centered=True,
                font="thin",
                font_size=25,
            )
            self.screen.client.message_display_time -= 1

    def _draw_volume_button(self):
        """Hangerő gomb"""
        volume_rect = create_volume_button_rect(
            self.screen.client.width - 40, self.screen.client.height - 40
        )
        draw_sound_volume(
            self.screen.client.window,
            volume_rect.centerx,
            volume_rect.centery,
            "sound",
        )
