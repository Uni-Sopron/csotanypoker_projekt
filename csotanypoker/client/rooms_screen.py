import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (
    BLACK,
    BLUE,
    DARK_GREEN_TRANSPARENT,
    GRAY,
    GREEN,
    LIGHT_GREEN,
    LIGHT_GREEN_TRANSPARENT,
    LIGHTER_GREEN,
    MIDDLE_GREEN,
    MIDDLE_GREEN_TRANSPARENT_70,
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
)


class RoomsScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)
        self.client = client
        self.logout_button_hovered = False
        self.logout_button_pressed = False
        self.search_text = ""
        self.password_text = ""
        self.create_button_hovered = False
        self.create_button_pressed = False

        self.rooms = self.client.room_list

        self.selected_room = None
        self.selected_room_index = None
        self.filter_state = 0
        self.scroll_offset = 0
        self.max_visible_rooms = 4

        self.search_active = False
        self.room_name_active = False
        self.password_active = False
        self.join_password_active = False

        self.password_text_input = ""
        self.join_password_text = ""
        self.password_protected = False
        self.max_players = 4

        self.max_count = pygame.Rect(700, 600, 35, 35)
        self.max_players_up = pygame.Rect(1055, 600, 20, 17)
        self.max_players_down = pygame.Rect(1055, 617, 20, 17)

        self.scroll_bar_width = 20
        self.scroll_bar_rect = None

        self.rooms_area_rect = None
        self.room_row_height = 55
        self.room_padding = 2

        self.join_button_hovered = False
        self.join_button_pressed = False
        self.room_name_text = ""

    def draw(self):
        # print(self.room_name_text)
        self.join_button = pygame.Rect(
            self.client.width - 200, self.client.height // 1.7, 190, 70
        )

        self.join_password_input = pygame.Rect(
            self.client.width - 330 - self.join_button.width,
            self.join_button.y + 20,
            300,
            40,
        )

        self.join_password_input.x = self.client.width - 330 - self.join_button.width
        self.join_password_input.y = self.join_button.y + 20

        self.logout_button = pygame.Rect(20, self.client.height - 105, 220, 85)

        load_background(self.client.width, self.client.height, self.client.window)

        draw_text(
            self.client.window,
            "Szobák",
            DARK_GREEN,
            self.client.width // 2,
            45,
            True,
            "Regular",
            60,
        )
        draw_text(
            self.client.window,
            "Szoba létrehozás",
            DARK_GREEN,
            self.client.width // 2,
            self.client.height // 1.4,
            True,
            "Regular",
            60,
        )
        self.menu()
        self.rooms_area()
        self.draw_room_creation()
        draw_button(
            surface=self.client.window,
            rect=self.logout_button,
            text="Kijelentkezés",
            text_color=WHITE,
            background_color=DARK_GREEN,
            border_color=DARK_GREEN,
            font_size=30,
            font_type="bold",
            border_width=5,
            is_hovered=self.logout_button_hovered,
            is_pressed=self.logout_button_pressed,
            hover_color=MIDDLE_GREEN,
            pressed_color=LIGHT_GREEN,
        )

    def menu(self):
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
            is_active=self.search_active,
            placeholder="Keresés...",
            placeholder_color=MIDDLE_GREEN,
        )

        icons_x = input_x + input_width + 20
        search_image = load_image("search_symbol", "button", size=(35, 35))

        search_button_x = icons_x - 15
        search_button_y = menu_y - 15
        self.search_button = pygame.Rect(search_button_x, search_button_y, 35, 35)

        draw_image(
            surface=self.client.window,
            image=search_image,
            x=icons_x,
            y=menu_y,
            centered=True,
        )

        padlock_transparent = load_image("padlock_transparent", "button", size=(35, 35))
        padlock_locked = load_image("padlock", "button", size=(35, 35))
        padlock_unlocked = load_image("unlock_padlock", "button", size=(35, 35))

        if self.filter_state == 0:
            current_padlock_image = padlock_transparent
        elif self.filter_state == 1:
            current_padlock_image = padlock_locked
        else:
            current_padlock_image = padlock_unlocked

        lock_button_x = icons_x + 35 - 17.5
        lock_button_y = menu_y - 17.5
        self.lock_button = pygame.Rect(lock_button_x, lock_button_y, 35, 35)

        draw_image(
            surface=self.client.window,
            image=current_padlock_image,
            x=icons_x + 35,
            y=menu_y,
            centered=True,
        )

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

    def rooms_area(self):
        margin = 20
        area_x = margin
        area_y = self.client.height // 5
        area_width = self.client.width - (2 * margin)
        area_height = self.client.height // 2.5

        self.rooms_area_rect = pygame.Rect(area_x, area_y, area_width, area_height)

        if len(self.rooms) > self.max_visible_rooms:
            list_margin = 10
            list_y = area_y + list_margin
            list_height = self.max_visible_rooms * (
                self.room_row_height + self.room_padding
            )

            scroll_x = area_x + area_width - self.scroll_bar_width
            self.scroll_bar_rect = pygame.Rect(
                scroll_x + 15, list_y, self.scroll_bar_width, list_height
            )

        visible_rooms = self.get_visible_rooms()
        for i, room in enumerate(visible_rooms):
            self.room_row(room, i)

        if len(self.rooms) > self.max_visible_rooms:
            self.draw_scrollbar()

        self.draw_bottom_buttons()

    def get_visible_rooms(self):
        start_index = self.scroll_offset
        end_index = min(len(self.rooms), start_index + self.max_visible_rooms)
        return self.rooms[start_index:end_index]

    def room_row(self, room, row_index):
        if not self.rooms_area_rect:
            return

        row_margin = 10
        row_x = self.rooms_area_rect.x + row_margin
        row_y = (
            self.rooms_area_rect.y
            + row_margin
            + (row_index * (self.room_row_height + self.room_padding))
        )
        row_width = self.rooms_area_rect.width - (2 * row_margin)
        row_height = self.room_row_height

        row_rect = pygame.Rect(row_x, row_y, row_width, row_height)

        if (
            self.selected_room_index is not None
            and self.rooms[self.selected_room_index].room_id == room.room_id
        ):
            print("Selected room:", room.name)
            bg_color = LIGHTER_GREEN
            border_color = MIDDLE_GREEN
            border_width = 2
        else:
            bg_color = MIDDLE_GREEN_TRANSPARENT_70
            border_color = None
            border_width = 0

        _draw_rounded_rect(
            surface=self.client.window,
            color=bg_color,
            rect=row_rect,
            border_color=border_color,
            border_width=border_width,
        )

        name_text = room.name

        same_name_rooms = [r for r in self.rooms if r.name == room.name]
        if len(same_name_rooms) > 1:
            name_text = f"{room.name} ID: {room.room_id}"

        draw_text(
            surface=self.client.window,
            text=name_text,
            color=DARK_GREEN,
            x=row_x + 70,
            y=row_y + row_height // 2,
            centered=False,
            font="regular",
            font_size=25,
            vcenter_rect=row_rect,
        )

        if room.password_protected:
            lock_x = self.password_x
            lock_image = load_image("padlock", "button", size=(40, 40))

            draw_image(
                surface=self.client.window,
                image=lock_image,
                x=lock_x,
                y=row_y + row_height // 2,
                centered=True,
            )

        count_text = f"{room.player_count}/{room.max_player_count}"

        draw_text(
            surface=self.client.window,
            text=count_text,
            color=DARK_GREEN,
            x=self.count_x,
            y=row_y + row_height // 2,
            centered=True,
            font="regular",
            font_size=30,
        )

    def draw_bottom_buttons(self):
        if (
            self.selected_room_index is not None
            and self.selected_room_index < len(self.rooms)
            and self.rooms[self.selected_room_index].password_protected
        ):
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
                is_active=self.join_password_active,
                is_password=True,
            )

        draw_button(
            surface=self.client.window,
            rect=self.join_button,
            text="Csatlakozás:",
            text_color=WHITE,
            background_color=MIDDLE_GREEN
            if self.selected_room_index is not None
            else MIDDLE_GREEN_TRANSPARENT_70,
            border_color=DARK_GREEN,
            font_size=25,
            font_type="bold",
            border_width=3,
            is_hovered=self.join_button_hovered,
            is_pressed=self.join_button_pressed,
            hover_color=DARK_GREEN_TRANSPARENT,
            pressed_color=LIGHT_GREEN,
        )

    def draw_scrollbar(self):
        _draw_rounded_rect(
            self.client.window, LIGHT_GREEN_TRANSPARENT, self.scroll_bar_rect
        )

        if len(self.rooms) > self.max_visible_rooms:
            total_rooms = len(self.rooms)
            visible_ratio = self.max_visible_rooms / total_rooms
            scroll_ratio = self.scroll_offset / (total_rooms - self.max_visible_rooms)

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

    def get_room_index_at_position(self, pos):
        if not self.rooms_area_rect.collidepoint(pos):
            return None

        room_content_rect = pygame.Rect(
            self.rooms_area_rect.x,
            self.rooms_area_rect.y,
            self.rooms_area_rect.width - self.scroll_bar_width,
            self.rooms_area_rect.height,
        )

        if not room_content_rect.collidepoint(pos):
            return None

        relative_y = pos[1] - self.rooms_area_rect.y
        room_index = relative_y // self.room_row_height
        actual_index = self.scroll_offset + room_index

        if 0 <= actual_index < len(self.rooms):
            return actual_index
        return None

    def filter_rooms(self):
        self.search()

    def search(self):
        print(f"Keresés: '{self.search_text}'")

        self.rooms = self.client.room_list.copy()
        if self.search_text.strip():
            keresett_szoveg = self.search_text.lower().strip()
            filtered_rooms = []
            for room in self.rooms:
                room_name = room.name.lower()
                room_id = room.room_id.lower()

                if keresett_szoveg in room_name or keresett_szoveg in room_id:
                    filtered_rooms.append(room)
            self.rooms = filtered_rooms

        if self.filter_state == 1:
            self.rooms = [room for room in self.rooms if room.password_protected]
        elif self.filter_state == 2:
            self.rooms = [room for room in self.rooms if not room.password_protected]

        self.scroll_offset = 0

    def handle_mouse_click(self, pos):
        if self.search_input.collidepoint(pos):
            self.search_active = True
            print("Keresés aktiválva")
            self.room_name_active = False
            self.password_active = False
            self.join_password_active = False
            return

        if self.search_button.collidepoint(pos):
            print(f"Keresőgomb megnyomva! Keresés: '{self.search_text}'")
            self.search()
            return

        if self.lock_button.collidepoint(pos):
            self.filter_state = (self.filter_state + 1) % 3
            # filter_names = ["Minden szoba", "Csak jelszóvédett", "Csak nyilvános"]
            # print(f"Szűrő állapot: {filter_names[self.filter_state]}")
            self.filter_rooms()
            return

        room_index = self.get_room_index_at_position(pos)
        if room_index is not None:
            if self.selected_room_index == room_index:
                self.selected_room_index = None
                print("Szoba kijelölés törölve")
            else:
                self.selected_room_index = room_index
                print(f"Kiválasztott szoba: {self.rooms[room_index].name}")

            return

        if (
            self.rooms_area_rect.collidepoint(pos)
            and len(self.rooms) > self.max_visible_rooms
        ):
            relative_y = pos[1] - self.rooms_area_rect.y
            scroll_ratio = relative_y / self.rooms_area_rect.height
            max_scroll = len(self.rooms) - self.max_visible_rooms
            self.scroll_offset = max(0, min(max_scroll, int(scroll_ratio * max_scroll)))
            return

        if (
            self.selected_room_index is not None
            and self.selected_room_index < len(self.rooms)
            and self.rooms[self.selected_room_index].password_protected
            and self.join_password_input.collidepoint(pos)
        ):
            self.join_password_active = True
            self.search_active = False
            self.room_name_active = False
            self.password_active = False
            return

        if self.join_button.collidepoint(pos) and self.selected_room_index is not None:
            selected_room = self.rooms[self.selected_room_index]

            password = (
                self.join_password_text if selected_room.password_protected else ""
            )
            self.client.network.join_room(selected_room.room_id, password)
        if (
            self.scroll_bar_rect
            and self.scroll_bar_rect.collidepoint(pos)
            and len(self.rooms) > self.max_visible_rooms
        ):
            relative_y = pos[1] - self.scroll_bar_rect.y
            scroll_ratio = relative_y / self.scroll_bar_rect.height
            max_scroll = len(self.rooms) - self.max_visible_rooms
            self.scroll_offset = max(0, min(max_scroll, int(scroll_ratio * max_scroll)))
            return

        if self.room_name_input.collidepoint(pos):
            self.room_name_active = True
            self.password_active = False
            self.search_active = False
            self.join_password_active = False
            return

        if self.create_password_input.collidepoint(pos) and self.password_protected:
            print("Jelszó mező aktiválva")
            self.password_active = True
            self.room_name_active = False
            self.search_active = False
            self.join_password_active = False
            return

        if self.password_checkbox.collidepoint(pos):
            print("Jelszó védett: ", not self.password_protected)
            self.password_protected = not self.password_protected
            return

        if self.max_players_up.collidepoint(pos):
            if self.max_players < 6:
                self.max_players += 1
            return

        if self.max_players_down.collidepoint(pos):
            if self.max_players > 2:
                self.max_players -= 1
            return

        if self.create_button.collidepoint(pos) and self.room_name_text.strip():
            if self.password_protected and self.password_text_input:
                password = self.password_text_input if self.password_protected else ""
                self.client.network.create_room(
                    self.room_name_text,
                    self.password_protected,
                    self.max_players,
                    password,
                )
                return
            elif not self.password_protected:
                password = self.password_text_input if self.password_protected else ""
                self.client.network.create_room(
                    self.room_name_text,
                    self.password_protected,
                    self.max_players,
                    password,
                )
                return

        if self.logout_button.collidepoint(pos):
            self.client.network.logout()

            return

        self.room_name_active = False
        self.password_active = False
        self.search_active = False
        self.join_password_active = False

    def handle_mouse_wheel(self, event):
        if len(self.rooms) > self.max_visible_rooms:
            max_scroll = len(self.rooms) - self.max_visible_rooms
            scroll_speed = 1

            if event.y > 0:
                self.scroll_offset = max(0, self.scroll_offset - scroll_speed)
            elif event.y < 0:
                self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_speed)

    def handle_key_press(self, event):
        if self.search_active:
            if event.key == pygame.K_RETURN:
                self.search()
                self.search_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
            else:
                if len(self.search_text) < 20:
                    self.search_text += event.unicode

        elif self.join_password_active:
            if event.key == pygame.K_RETURN:
                self.join_password_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.join_password_text = self.join_password_text[:-1]
            elif event.key == pygame.K_TAB:
                self.join_password_active = False
            else:
                if len(self.join_password_text) < 15:
                    self.join_password_text += event.unicode

        elif self.room_name_active:
            if event.key == pygame.K_RETURN:
                self.room_name_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.room_name_text = self.room_name_text[:-1]
            elif event.key == pygame.K_TAB:
                self.room_name_active = False
                if self.password_protected:
                    self.password_active = True
            else:
                if len(self.room_name_text) < 20:
                    self.room_name_text += event.unicode

        elif self.password_active and self.password_protected:
            if event.key == pygame.K_RETURN:
                self.password_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.password_text_input = self.password_text_input[:-1]
            elif event.key == pygame.K_TAB:
                self.password_active = False
                self.room_name_active = True
            else:
                if len(self.password_text_input) < 15:
                    self.password_text_input += event.unicode

        elif not any(
            [
                self.search_active,
                self.join_password_active,
                self.room_name_active,
                self.password_active,
            ]
        ):
            if event.key >= pygame.K_2 and event.key <= pygame.K_6:
                new_value = int(event.unicode)
                if 2 <= new_value <= 6:
                    self.max_players = new_value
            elif event.key == pygame.K_UP:
                if len(self.rooms) > self.max_visible_rooms:
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif self.max_players < 6:
                    self.max_players += 1
            elif event.key == pygame.K_DOWN:
                if len(self.rooms) > self.max_visible_rooms:
                    max_scroll = len(self.rooms) - self.max_visible_rooms
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                elif self.max_players > 2:
                    self.max_players -= 1

    def update_rooms_list(self, rooms_data):
        self.rooms = rooms_data

        if self.selected_room_index is not None and self.selected_room_index >= len(
            self.rooms
        ):
            self.selected_room_index = None

        if len(self.rooms) > self.max_visible_rooms:
            max_scroll = len(self.rooms) - self.max_visible_rooms
            self.scroll_offset = min(self.scroll_offset, max_scroll)
        else:
            self.scroll_offset = 0

    def draw_room_creation(self):
        creation_title_y = self.client.height // 1.4

        creation_start_y = creation_title_y + 60

        draw_text(
            self.client.window,
            "Szoba neve:",
            DARK_GREEN,
            100,
            creation_start_y,
            centered=False,
            font="regular",
            font_size=30,
        )
        self.room_name_input = pygame.Rect(150 + 100 + 10, creation_start_y, 230, 35)

        self.room_name_input.y = creation_start_y

        if not self.room_name_active and self.room_name_text == "":
            self.room_name_text = f"{self.client.username} szobája"
        draw_input_box(
            surface=self.client.window,
            rect=self.room_name_input,
            text=self.room_name_text,
            text_color=WHITE,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=None,
            border_radius=0.50,
            font_size=20,
            is_active=self.room_name_active,
        )

        checkbox_y = creation_start_y

        self.max_players_rect = pygame.Rect(
            self.room_name_input.x + self.room_name_input.width + 10,
            checkbox_y,
            150,
            35,
        )
        self.max_count.y = checkbox_y
        self.max_count.x = self.max_players_rect.x + self.max_players_rect.width + 10

        draw_input_box(
            surface=self.client.window,
            rect=self.max_count,
            text=str(self.max_players),
            text_color=DARK_GREEN,
            background_color=LIGHT_GREEN_TRANSPARENT,
            border_color=MIDDLE_GREEN,
            border_radius=0.25,
            font_size=20,
            is_active=False,
            cursor_visible=False,
            cursor_color=DARK_GREEN,
        )

        self.max_players_up.y = checkbox_y - 5
        self.max_players_down.y = checkbox_y + 25

        draw_text(
            self.client.window,
            "Max létszám:",
            DARK_GREEN,
            self.max_players_rect.x,
            self.max_players_rect.y,
            centered=False,
            font="regular",
            font_size=30,
            vcenter_rect=self.max_players_rect,
        )
        up_and_down_buttons = padlock_image = load_image(
            "fel_le_nyilak", "button", size=(60, 50)
        )

        draw_image(
            surface=self.client.window,
            image=up_and_down_buttons,
            x=self.max_players_rect.x + self.max_players_rect.width + 50,
            y=self.max_players_rect.y - 8,
            centered=False,
        )

        self.create_password_input = pygame.Rect(
            self.client.width // 1.5, checkbox_y, 200, 35
        )

        if self.password_protected:
            padlock_image = load_image("padlock", "button", size=(35, 35))
        else:
            padlock_image = load_image("unlock_padlock", "button", size=(35, 35))

        self.password_checkbox = pygame.Rect(
            self.create_password_input.x - 40,
            self.create_password_input.y + 15,
            35,
            35,
        )
        draw_image(
            surface=self.client.window,
            image=padlock_image,
            x=self.password_checkbox.x,
            y=self.password_checkbox.y,
            centered=True,
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
                is_active=self.password_active,
                is_password=True,
                placeholder="Jelszó",
                placeholder_color=MIDDLE_GREEN,
            )
        self.create_button = pygame.Rect(
            self.client.width - 210,
            checkbox_y - 15,
            170,
            60,
        )
        create_enabled = bool(self.room_name_text.strip())
        button_color = DARK_GREEN if create_enabled else DARK_GREEN_TRANSPARENT

        draw_button(
            surface=self.client.window,
            rect=self.create_button,
            text="Létrehozás",
            text_color=WHITE,
            background_color=button_color,
            border_color=DARK_GREEN,
            font_size=24,
            font_type="bold",
            border_width=2,
            is_hovered=self.create_button_hovered and create_enabled,
            is_pressed=self.create_button_pressed and create_enabled,
            hover_color=MIDDLE_GREEN_TRANSPARENT_70,
            pressed_color=LIGHT_GREEN,
        )
