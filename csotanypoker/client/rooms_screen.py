import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    DARK_GREEN_TRANSPARENT,
    LIGHT_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    LIGHTER_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
    RED,
    TITLE_FONT_SIZE,
    WHITE,
    DARK_GREEN,
)
from csotanypoker.client.drawing_helpers import (
    draw_text,
    load_background,
    draw_button,
    draw_input_box,
    load_image,
    draw_image,
    _draw_rounded_rect,
    create_logout_button_rect,
    draw_logout_button,
    check_logout_button_interaction,
    handle_logout_button_click,
)


class RoomsScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)
        self.client = client
        self.logout_button = create_logout_button_rect(self.client.height)

        self.selected_room_index = None
        self.scroll_offset = 0
        self.filter_state = 0
        self.original_rooms = []
        self.filtered_rooms = []
        self.search_text = ""

        self.active_input = None

        self.room_name_text = ""
        self.password_text_input = ""
        self.password_protected = False
        self.max_players = 4
        self.max_players_text = ""

        self.join_password_text = ""

        self.hovered_elements = set()
        self.pressed_elements = set()

        self.MAX_VISIBLE_ROOMS = 4
        self.ROOM_ROW_HEIGHT = 55
        self.ROOM_PADDING = 2
        self.SCROLL_BAR_WIDTH = 20
        self.BUTTON_PADDING = 35
        self.PADDING = 10

    @property
    def rooms(self):
        return self.filtered_rooms

    def _deactivate_inputs(self):
        self.active_input = None

    def _is_input_active(self, input_name):
        return self.active_input == input_name

    def _activate_input(self, input_name):
        self.active_input = input_name

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

        if hasattr(self, "create_button") and self.create_button.collidepoint(
            mouse_pos
        ):
            if self._is_create_enabled():
                self.hovered_elements.add("create")
                if mouse_pressed:
                    self.pressed_elements.add("create")

        if hasattr(self, "join_button") and self.join_button.collidepoint(mouse_pos):
            if self._is_join_enabled():
                self.hovered_elements.add("join")
                if mouse_pressed:
                    self.pressed_elements.add("join")

    def update_rooms_from_client(self):
        self.original_rooms = self.client.room_list.copy()
        self.apply_filters()
        self._update_selected_room_index()

    def apply_filters(self):
        filtered_rooms = self.original_rooms.copy()
        filtered_rooms_name = []
        filtered_rooms_id = []
        if self.search_text.strip():
            search_text = self.search_text.lower().strip()

            if "id:" in search_text:
                search_text = search_text[3:].strip()
                filtered_rooms_id = [
                    room
                    for room in filtered_rooms
                    if search_text in room.room_id.lower()
                ]
            else:
                filtered_rooms_name = [
                    room
                    for room in filtered_rooms
                    if (search_text in room.name.lower())
                ]
            filtered_rooms = filtered_rooms_name + filtered_rooms_id

        if self.filter_state == 1:
            filtered_rooms = [
                room for room in filtered_rooms if room.password_protected
            ]
        elif self.filter_state == 2:
            filtered_rooms = [
                room for room in filtered_rooms if not room.password_protected
            ]

        self.filtered_rooms = filtered_rooms
        self.scroll_offset = 0

    def _update_selected_room_index(self):
        if self.selected_room_index is not None and self.selected_room_index < len(
            self.original_rooms
        ):
            selected_room = self.original_rooms[self.selected_room_index]

            for i, room in enumerate(self.filtered_rooms):
                if room.room_id == selected_room.room_id:
                    self.selected_room_index = i
                    return

            self.selected_room_index = None

    def _should_update_rooms(self):
        """Ellenőrzi, hogy frissí­teni kell-e a szobák listáját"""
        if len(self.original_rooms) != len(self.client.room_list):
            return True

        original_json = [
            room.model_dump()
            for room in sorted(self.original_rooms, key=lambda r: r.room_id)
        ]
        current_json = [
            room.model_dump()
            for room in sorted(self.client.room_list, key=lambda r: r.room_id)
        ]

        return original_json != current_json

    def _get_selected_room(self):
        """Visszaadja a kiválasztott szobát, ha van"""
        if self.selected_room_index is not None and self.selected_room_index < len(
            self.rooms
        ):
            return self.rooms[self.selected_room_index]
        return None

    def _is_join_enabled(self, show_error=False):
        """Ellenőrzi, hogy a csatlakozás gomb engedélyezett-e"""
        selected_room = self._get_selected_room()
        if not selected_room:
            if show_error:
                self.client.message = "Nincs kiválasztott szoba"
                self.client.message_display_time = 60
            return False

        if selected_room.password_protected and not self.join_password_text.strip():
            if show_error:
                self.client.message = "Jelszó megadása szükséges"
                self.client.message_display_time = 60
            return False
        return True

    def _is_create_enabled(self, show_error=False):
        """Ellenőrzi, hogy a létrehozás gomb engedélyezett-e"""

        if self.password_protected and not self.password_text_input.strip():
            if show_error:
                self.client.message = "Jelszó megadása szükséges"
                self.client.message_display_time = 60
            return False
        return True

    def handle_mouse_motion(self, pos):
        self._update_button_states()

    def handle_mouse_click(self, pos):
        if handle_logout_button_click(pos, self.logout_button, self.client.network):
            self.room_name_text = ""
            return True

        if hasattr(self, "search_input") and self.search_input.collidepoint(pos):
            self._activate_input("search")
            return

        if hasattr(self, "room_name_input") and self.room_name_input.collidepoint(pos):
            self._activate_input("room_name")
            return

        if (
            hasattr(self, "create_password_input")
            and self.create_password_input.collidepoint(pos)
            and self.password_protected
        ):
            self._activate_input("password")
            return

        if (
            hasattr(self, "join_password_input")
            and self.join_password_input.collidepoint(pos)
            and self._get_selected_room()
            and self._get_selected_room().password_protected
        ):
            self._activate_input("join_password")
            return

        if hasattr(self, "max_count") and self.max_count.collidepoint(pos):
            self._activate_input("max_count")
            self.max_players_text = str(self.max_players)
            return

        if hasattr(self, "search_button") and self.search_button.collidepoint(pos):
            self.apply_filters()
            return

        if hasattr(self, "lock_button") and self.lock_button.collidepoint(pos):
            self.filter_state = (self.filter_state + 1) % 3
            self.apply_filters()
            return

        if hasattr(self, "password_checkbox") and self.password_checkbox.collidepoint(
            pos
        ):
            self.password_protected = not self.password_protected
            return

        if hasattr(self, "max_players_up") and self.max_players_up.collidepoint(pos):
            self._deactivate_inputs()
            if self.max_players < 6:
                self.max_players += 1
            return

        if hasattr(self, "max_players_down") and self.max_players_down.collidepoint(
            pos
        ):
            self._deactivate_inputs()
            if self.max_players > 2:
                self.max_players -= 1
            return

        if hasattr(self, "join_button") and self.join_button.collidepoint(pos):
            if self._is_join_enabled(show_error=True):
                selected_room = self._get_selected_room()
                password = (
                    self.join_password_text if selected_room.password_protected else ""
                )
                self.client.network.join_room(selected_room.room_id, password)
                self.reset_create_room_form()
            return

        if hasattr(self, "create_button") and self.create_button.collidepoint(pos):
            if self._is_create_enabled(show_error=True):
                password = self.password_text_input if self.password_protected else ""

                room_name = (
                    self.room_name_text.strip()
                    or f"{self.client.user.username} szobája"
                )
                self.client.network.create_room(
                    room_name,
                    self.password_protected,
                    self.max_players,
                    password,
                )
                self.reset_create_room_form()
            return

        room_index = self._get_room_index_at_position(pos)
        if room_index is not None:
            self.selected_room_index = (
                room_index if self.selected_room_index != room_index else None
            )
            return

        self._handle_scroll_click(pos)

        self._deactivate_inputs()

    def reset_create_room_form(self):
        self.room_name_text = ""
        self.password_text_input = ""
        self.password_protected = False
        self.max_players = 4
        self.max_players_text = ""

    def _get_room_index_at_position(self, pos):
        if not hasattr(
            self, "rooms_area_rect"
        ) or not self.rooms_area_rect.collidepoint(pos):
            return None

        room_content_rect = pygame.Rect(
            self.rooms_area_rect.x,
            self.rooms_area_rect.y,
            self.rooms_area_rect.width - self.SCROLL_BAR_WIDTH,
            self.rooms_area_rect.height,
        )

        if not room_content_rect.collidepoint(pos):
            return None

        relative_y = pos[1] - (self.rooms_area_rect.y + self.PADDING)
        if relative_y < 0:
            return None

        total_row_height = self.ROOM_ROW_HEIGHT + self.ROOM_PADDING
        room_index = relative_y // total_row_height
        row_internal_y = relative_y % total_row_height

        if row_internal_y >= self.ROOM_ROW_HEIGHT:
            return None

        actual_index = self.scroll_offset + room_index
        visible_rooms = self._get_visible_rooms()

        if 0 <= room_index < len(visible_rooms) and 0 <= actual_index < len(self.rooms):
            return actual_index

        return None

    def _handle_scroll_click(self, pos):
        if not hasattr(self, "rooms_area_rect"):
            return

        if (
            self.rooms_area_rect.collidepoint(pos)
            and len(self.rooms) > self.MAX_VISIBLE_ROOMS
        ):
            relative_y = pos[1] - self.rooms_area_rect.y
            scroll_ratio = relative_y / self.rooms_area_rect.height
            max_scroll = len(self.rooms) - self.MAX_VISIBLE_ROOMS
            self.scroll_offset = max(0, min(max_scroll, int(scroll_ratio * max_scroll)))

    def handle_mouse_wheel(self, event):
        if len(self.filtered_rooms) > self.MAX_VISIBLE_ROOMS:
            max_scroll = len(self.filtered_rooms) - self.MAX_VISIBLE_ROOMS
            scroll_speed = 1

            if event.y > 0:
                self.scroll_offset = max(0, self.scroll_offset - scroll_speed)
            elif event.y < 0:
                self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_speed)

    def handle_key_press(self, event):
        if self._is_input_active("search"):
            self._handle_search_input(event)
        elif self._is_input_active("join_password"):
            self._handle_join_password_input(event)
        elif self._is_input_active("room_name"):
            self._handle_room_name_input(event)
        elif self._is_input_active("password"):
            self._handle_password_input(event)
        elif self._is_input_active("max_count"):
            self._handle_max_count_input(event)
        else:
            self._handle_global_keys(event)

    def _handle_search_input(self, event):
        if event.key == pygame.K_RETURN:
            self.apply_filters()
            self._deactivate_inputs()
        elif event.key == pygame.K_BACKSPACE:
            self.search_text = self.search_text[:-1]
            self.apply_filters()
        else:
            if len(self.search_text) < 20:
                self.search_text += event.unicode
                self.apply_filters()

    def _handle_join_password_input(self, event):
        if event.key in (pygame.K_RETURN, pygame.K_TAB):
            self._deactivate_inputs()
        elif event.key == pygame.K_BACKSPACE:
            self.join_password_text = self.join_password_text[:-1]
        else:
            if len(self.join_password_text) < 15:
                self.join_password_text += event.unicode

    def _handle_room_name_input(self, event):
        if event.key == pygame.K_RETURN:
            self._deactivate_inputs()
        elif event.key == pygame.K_BACKSPACE:
            self.room_name_text = self.room_name_text[:-1]
        elif event.key == pygame.K_TAB:
            if self.password_protected:
                self._activate_input("password")
            else:
                self._deactivate_inputs()
        else:
            if len(self.room_name_text) < 20:
                self.room_name_text += event.unicode

    def _handle_password_input(self, event):
        if event.key == pygame.K_RETURN:
            self._deactivate_inputs()
        elif event.key == pygame.K_BACKSPACE:
            self.password_text_input = self.password_text_input[:-1]
        elif event.key == pygame.K_TAB:
            self._activate_input("room_name")
        else:
            if len(self.password_text_input) < 15:
                self.password_text_input += event.unicode

    def _handle_max_count_input(self, event):
        if event.key == pygame.K_RETURN:
            if self.max_players_text.strip():
                try:
                    new_value = int(self.max_players_text)
                    if 2 <= new_value <= 6:
                        self.max_players = new_value
                    else:
                        self.max_players = 4
                except ValueError:
                    self.max_players = 4
            self._deactivate_inputs()
        elif event.key == pygame.K_BACKSPACE:
            self.max_players_text = self.max_players_text[:-1]
        elif event.key == pygame.K_TAB:
            self._deactivate_inputs()
        else:
            if event.unicode.isdigit() and 2 <= int(event.unicode) <= 6:
                self.max_players_text = event.unicode

    def _handle_global_keys(self, event):
        if event.key >= pygame.K_2 and event.key <= pygame.K_6:
            new_value = int(event.unicode)
            if 2 <= new_value <= 6:
                self.max_players = new_value
        elif event.key == pygame.K_UP:
            if len(self.rooms) > self.MAX_VISIBLE_ROOMS:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif self.max_players < 6:
                self.max_players += 1
        elif event.key == pygame.K_DOWN:
            if len(self.rooms) > self.MAX_VISIBLE_ROOMS:
                max_scroll = len(self.rooms) - self.MAX_VISIBLE_ROOMS
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            elif self.max_players > 2:
                self.max_players -= 1

    def draw(self):
        self._setup_rects()

        if self._should_update_rooms():
            self.update_rooms_from_client()

        self._update_button_states()

        load_background(self.client.width, self.client.height, self.client.window)

        draw_text(
            self.client.window,
            "Szobák",
            DARK_GREEN,
            self.client.width // 2,
            45,
            True,
            "Regular",
            TITLE_FONT_SIZE,
        )
        draw_text(
            self.client.window,
            "Szoba létrehozás",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 1.4,
            True,
            "Regular",
            TITLE_FONT_SIZE,
        )

        self._draw_menu()
        self._draw_rooms_area()
        self._draw_room_creation()
        draw_logout_button(
            self.client.window,
            self.logout_button,
            is_hovered="logout" in self.hovered_elements,
            is_pressed="logout" in self.pressed_elements,
        )

        if self.client.message and self.client.message_display_time > 0:
            draw_text(
                self.client.window,
                self.client.message,
                RED,
                self.client.width - 200,
                50,
                centered=True,
                font="thin",
                font_size=25,
            )
            self.client.message_display_time -= 1

    def _setup_rects(self):
        self.logout_button = create_logout_button_rect(self.client.height)

        self.join_button = pygame.Rect(
            self.client.width - 190 - self.BUTTON_PADDING,
            self.client.height // 1.7,
            190,
            70,
        )

        self.join_password_input = pygame.Rect(
            self.client.width
            - 300
            - self.join_button.width
            - (self.BUTTON_PADDING * 2),
            self.join_button.y + 20,
            300,
            40,
        )

    def _draw_menu(self):
        menu_font_size = 38
        section_width = self.client.width // 5
        menu_y = self.client.height // 6
        input_height = 40

        name_x = section_width // 2 + 30
        draw_text(
            self.client.window,
            "Név",
            DARK_GREEN,
            name_x,
            menu_y,
            True,
            "Regular",
            menu_font_size,
        )

        input_x = name_x + 60
        input_width = self.client.width // 4
        input_y = menu_y - (input_height // 2)
        self.search_input = pygame.Rect(input_x, input_y, input_width, input_height)

        draw_input_box(
            surface=self.client.window,
            rect=self.search_input,
            text=self.search_text,
            text_color=DARK_GREEN,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=None,
            border_radius=0.50,
            font_size=25,
            cursor_color=DARK_GREEN,
            is_active=self._is_input_active("search"),
            placeholder="Keresés...",
            placeholder_color=MIDDLE_GREEN,
        )

        self._draw_search_and_filter_buttons(input_x + input_width + 20, menu_y)

        self.password_x = section_width * 3 + (section_width // 2)
        draw_text(
            self.client.window,
            "Jelszóvédett",
            DARK_GREEN,
            self.password_x,
            menu_y,
            True,
            "Regular",
            menu_font_size,
        )

        self.count_x = section_width * 4 + (section_width // 2)
        draw_text(
            self.client.window,
            "Létszám",
            DARK_GREEN,
            self.count_x,
            menu_y,
            True,
            "Regular",
            menu_font_size,
        )

    def _draw_search_and_filter_buttons(self, icons_x, menu_y):
        search_image = load_image("search_symbol", "button", size=(35, 35))
        self.search_button = pygame.Rect(icons_x - 15, menu_y - 15, 35, 35)
        draw_image(self.client.window, search_image, icons_x, menu_y, centered=True)

        padlock_images = {
            0: load_image("padlock_transparent", "button", size=(35, 35)),
            1: load_image("padlock", "button", size=(35, 35)),
            2: load_image("unlock_padlock", "button", size=(35, 35)),
        }

        current_padlock_image = padlock_images[self.filter_state]
        self.lock_button = pygame.Rect(icons_x + 35 - 17.5, menu_y - 17.5, 35, 35)
        draw_image(
            self.client.window,
            current_padlock_image,
            icons_x + 35,
            menu_y,
            centered=True,
        )

    def _draw_rooms_area(self):
        margin = 20
        area_x = margin
        area_y = self.client.height // 5
        area_width = self.client.width - (2 * margin)
        area_height = self.client.height // 2.5

        self.rooms_area_rect = pygame.Rect(area_x, area_y, area_width, area_height)

        if len(self.rooms) > self.MAX_VISIBLE_ROOMS:
            scroll_x = area_x + area_width - self.SCROLL_BAR_WIDTH
            list_height = self.MAX_VISIBLE_ROOMS * (
                self.ROOM_ROW_HEIGHT + self.ROOM_PADDING
            )
            self.scroll_bar_rect = pygame.Rect(
                scroll_x + 15, area_y + 10, self.SCROLL_BAR_WIDTH, list_height
            )

        visible_rooms = self._get_visible_rooms()
        for i, room in enumerate(visible_rooms):
            self._draw_room_row(room, i)

        if len(self.rooms) > self.MAX_VISIBLE_ROOMS:
            self._draw_scrollbar()

        self._draw_bottom_buttons()

    def _get_visible_rooms(self):
        start_index = self.scroll_offset
        end_index = min(len(self.filtered_rooms), start_index + self.MAX_VISIBLE_ROOMS)
        return self.filtered_rooms[start_index:end_index]

    def _draw_room_row(self, room, row_index):
        if not self.rooms_area_rect:
            return

        row_x = self.rooms_area_rect.x + self.PADDING
        row_y = (
            self.rooms_area_rect.y
            + self.PADDING
            + (row_index * (self.ROOM_ROW_HEIGHT + self.ROOM_PADDING))
        )
        row_width = self.rooms_area_rect.width - (2 * self.PADDING)
        row_height = self.ROOM_ROW_HEIGHT

        row_rect = pygame.Rect(row_x, row_y, row_width, row_height)

        is_selected = (
            self.selected_room_index is not None
            and self.rooms[self.selected_room_index].room_id == room.room_id
        )

        if is_selected:
            bg_color = LIGHTER_GREEN
            border_color = MIDDLE_GREEN
            border_width = 2
        else:
            bg_color = MIDDLE_GREEN_TRANSPARENT_70
            border_color = None
            border_width = 0

        _draw_rounded_rect(
            self.client.window, bg_color, row_rect, border_color, border_width
        )

        name_text = room.name
        same_name_rooms = [r for r in self.rooms if r.name == room.name]
        if len(same_name_rooms) > 1:
            name_text = f"{room.name} ID: {room.room_id}"

        draw_text(
            self.client.window,
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
                self.client.window,
                lock_image,
                self.password_x,
                row_y + row_height // 2,
                centered=True,
            )

        count_text = f"{room.player_count}/{room.max_player_count}"
        draw_text(
            self.client.window,
            count_text,
            DARK_GREEN,
            self.count_x,
            row_y + row_height // 2,
            True,
            "regular",
            30,
        )

    def _draw_bottom_buttons(self):
        selected_room = self._get_selected_room()
        join_enabled = self._is_join_enabled()

        if selected_room and selected_room.password_protected:
            draw_input_box(
                surface=self.client.window,
                rect=self.join_password_input,
                text=self.join_password_text,
                text_color=WHITE,
                background_color=LIGHT_GREEN_TRANSPARENT,
                border_color=MIDDLE_GREEN,
                border_radius=0.50,
                font_size=20,
                cursor_color=WHITE,
                placeholder="Jelszó",
                placeholder_color=WHITE,
                is_active=self._is_input_active("join_password"),
                is_password=True,
            )

        join_bg_color = MIDDLE_GREEN if join_enabled else DARK_GREEN_TRANSPARENT
        join_hover_color = (
            MIDDLE_GREEN_TRANSPARENT_70 if join_enabled else DARK_GREEN_TRANSPARENT
        )
        join_pressed_color = LIGHT_GREEN if join_enabled else DARK_GREEN_TRANSPARENT

        draw_button(
            surface=self.client.window,
            rect=self.join_button,
            text="Csatlakozás:",
            text_color=WHITE,
            background_color=join_bg_color,
            border_color=DARK_GREEN,
            font_size=25,
            font_type="bold",
            border_width=3,
            is_hovered="join" in self.hovered_elements and join_enabled,
            is_pressed="join" in self.pressed_elements and join_enabled,
            hover_color=join_hover_color,
            pressed_color=join_pressed_color,
        )

    def _draw_scrollbar(self):
        """Scrollbar rajzolása"""
        if not hasattr(self, "scroll_bar_rect") or not self.scroll_bar_rect:
            return

        _draw_rounded_rect(
            self.client.window, LIGHT_GREEN_TRANSPARENT, self.scroll_bar_rect
        )

        if len(self.filtered_rooms) > self.MAX_VISIBLE_ROOMS:
            total_rooms = len(self.filtered_rooms)
            visible_ratio = self.MAX_VISIBLE_ROOMS / total_rooms
            scroll_ratio = self.scroll_offset / (total_rooms - self.MAX_VISIBLE_ROOMS)

            thumb_height = max(20, int(self.scroll_bar_rect.height * visible_ratio))
            thumb_y = self.scroll_bar_rect.y + int(
                (self.scroll_bar_rect.height - thumb_height) * scroll_ratio
            )

            thumb_rect = pygame.Rect(
                self.scroll_bar_rect.x + 2,
                thumb_y,
                self.scroll_bar_rect.width - 4,
                thumb_height,
            )
            _draw_rounded_rect(self.client.window, MIDDLE_GREEN, thumb_rect)

    def _draw_room_creation(self):
        creation_title_y = self.client.height // 1.4
        creation_start_y = creation_title_y + 60
        self._draw_room_name_section(creation_start_y)
        self._draw_max_players_section(creation_start_y)
        self._draw_password_section(creation_start_y)
        self._draw_create_button(creation_start_y)

    def _draw_room_name_section(self, y_pos):
        self.room_name_input = pygame.Rect(260, y_pos - 17, 230, 35)

        draw_text(
            self.client.window,
            "Szoba neve:",
            DARK_GREEN,
            100,
            y_pos,
            False,
            "regular",
            30,
            vcenter_rect=self.room_name_input,
        )

        draw_input_box(
            surface=self.client.window,
            rect=self.room_name_input,
            text=self.room_name_text,
            text_color=WHITE,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=None,
            border_radius=0.50,
            font_size=20,
            is_active=self._is_input_active("room_name"),
            cursor_color=WHITE,
            placeholder=f"{self.client.user.username} szobája",
            placeholder_color=MIDDLE_GREEN,
        )

    def _draw_max_players_section(self, y_pos):
        max_players_label_rect = pygame.Rect(
            self.room_name_input.x + self.room_name_input.width + 20,
            y_pos - 17,
            140,
            35,
        )

        self.max_count = pygame.Rect(
            max_players_label_rect.x + max_players_label_rect.width + 15,
            y_pos - 17,
            50,
            35,
        )

        display_text = (
            self.max_players_text
            if self._is_input_active("max_count")
            else str(self.max_players)
        )

        draw_text(
            self.client.window,
            "Max létszám:",
            DARK_GREEN,
            max_players_label_rect.x,
            y_pos,
            False,
            "regular",
            30,
            vcenter_rect=max_players_label_rect,
        )

        draw_input_box(
            surface=self.client.window,
            rect=self.max_count,
            text=display_text,
            text_color=DARK_GREEN,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=MIDDLE_GREEN,
            border_radius=0.25,
            font_size=22,
            is_active=self._is_input_active("max_count"),
            cursor_color=DARK_GREEN,
        )

        arrows_x = self.max_count.x + self.max_count.width + 5
        arrows_y = self.max_count.y

        up_and_down_buttons = load_image("fel_le_nyilak", "button", size=(50, 35))
        draw_image(self.client.window, up_and_down_buttons, arrows_x, arrows_y, False)

        self.max_players_up = pygame.Rect(arrows_x, arrows_y, 50, 17)  # Felső fél
        self.max_players_down = pygame.Rect(arrows_x, arrows_y + 18, 50, 17)  # Alsó fél

    def _draw_password_section(self, y_pos):
        self.create_password_input = pygame.Rect(
            self.client.width // 1.5, y_pos - 17, 200, 35
        )

        checkbox_x = self.create_password_input.x - 45
        checkbox_y = self.create_password_input.y

        padlock_image = load_image(
            "padlock" if self.password_protected else "unlock_padlock",
            "button",
            size=(35, 35),
        )

        self.password_checkbox = pygame.Rect(checkbox_x, checkbox_y, 35, 35)
        draw_image(
            self.client.window,
            padlock_image,
            checkbox_x,
            checkbox_y,
        )

        if self.password_protected:
            draw_input_box(
                surface=self.client.window,
                rect=self.create_password_input,
                text=self.password_text_input,
                text_color=WHITE,
                background_color=LIGHT_GREEN_TRANSPARENT,
                border_color=None,
                border_radius=0.50,
                font_size=20,
                is_active=self._is_input_active("password"),
                is_password=True,
                placeholder="Jelszó",
                placeholder_color=MIDDLE_GREEN,
                cursor_color=WHITE,
            )

    def _draw_create_button(self, y_pos):
        self.create_button = pygame.Rect(
            self.client.width - 190 - self.BUTTON_PADDING,
            y_pos - 35,
            190,
            70,
        )

        create_enabled = self._is_create_enabled()

        if create_enabled:
            bg_color = DARK_GREEN
            hover_color = MIDDLE_GREEN_TRANSPARENT_70
            pressed_color = LIGHT_GREEN
        else:
            bg_color = DARK_GREEN_TRANSPARENT
            hover_color = DARK_GREEN_TRANSPARENT
            pressed_color = DARK_GREEN_TRANSPARENT

        draw_button(
            surface=self.client.window,
            rect=self.create_button,
            text="Létrehozás",
            text_color=WHITE,
            background_color=bg_color,
            border_color=DARK_GREEN,
            font_size=24,
            font_type="bold",
            border_width=2,
            is_hovered="create" in self.hovered_elements and create_enabled,
            is_pressed="create" in self.pressed_elements and create_enabled,
            hover_color=hover_color,
            pressed_color=pressed_color,
        )
