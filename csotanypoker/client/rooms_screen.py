import pygame

from csotanypoker.client.base_screen import BaseScreen
from csotanypoker.client.constans import (BLACK, BLUE, FONT_MEDIUM, FONT_SMALL,
                                          GRAY, GREEN, WHITE)
from csotanypoker.client.drawing_helpers import draw_text


class RoomsScreen(BaseScreen):
    def __init__(self, client):
        super().__init__(client)

        self.room_list_rect = pygame.Rect(100, 160, 1200, 200)
        self.room_item_height = 50
        self.room_padding = 0

        self.scroll_offset = 0
        self.max_visible_rooms = self.room_list_rect.height // (
            self.room_item_height + self.room_padding
        )
        self.scroll_bar_width = 20
        self.scroll_bar_rect = pygame.Rect(
            self.room_list_rect.right - self.scroll_bar_width,
            self.room_list_rect.top,
            self.scroll_bar_width,
            self.room_list_rect.height,
        )

        self.search_input = pygame.Rect(280, 125, 240, 30)
        self.search_button = pygame.Rect(525, 125, 80, 30)
        self.search_text = ""
        self.search_active = False

        self.filter_checkbox = pygame.Rect(630, 130, 20, 20)
        self.filter_state = 0  # 0=None, 1=Check, 2=X

        self.join_password_input = pygame.Rect(370, 395, 150, 40)
        self.join_password_text = ""
        self.join_password_active = False

        self.room_name_input = pygame.Rect(220, 600, 240, 35)

        self.max_players_rect = pygame.Rect(970, 600, 80, 35)
        self.password_checkbox = pygame.Rect(700, 600, 35, 35)

        self.max_players_up = pygame.Rect(1055, 600, 20, 17)
        self.max_players_down = pygame.Rect(1055, 617, 20, 17)

        self.join_button = pygame.Rect(1130, 395, 150, 40)
        self.create_button = pygame.Rect(1130, 600, 150, 40)

        self.room_name_active = False
        self.password_active = False
        self.password_protected = False
        self.max_players = 4
        self.room_name_text = self.client.username
        self.password_text = ""
        self.password_text_input = ""
        self.create_password_input = pygame.Rect(700, 650, 150, 40)
        self.selected_room_index = None

        self.rooms = self.client.room_list

    def search(self):
        print(self.search_text)
        self.rooms = self.client.room_list
        if self.search_text == "":
            self.rooms = self.client.room_list
        else:
            keresett_szoveg = self.search_text.lower()
            rooms = []
            for room in self.rooms:
                room_name = room.name.lower()
                if keresett_szoveg in room_name:
                    rooms.append(room)
            self.rooms = rooms

    def draw(self):
        self.client.window.fill(WHITE)

        font_large = pygame.font.Font(None, 48)
        draw_text(
            self.client.window,
            "Szobák:",
            BLACK,
            self.client.width // 2,
            80,
            True,
            font_large,
        )

        self.draw_search_section()
        self.draw_room_list_header()
        self.draw_room_list()
        self.draw_room_creation()

    def draw_search_section(self):
        font_small = pygame.font.Font(None, FONT_SMALL)

        draw_text(self.client.window, "Név", BLACK, 180, 140, True, font_small)

        color = BLUE if self.search_active else GRAY
        pygame.draw.rect(self.client.window, WHITE, self.search_input)
        pygame.draw.rect(self.client.window, color, self.search_input, 2)

        if self.search_text:
            draw_text(
                self.client.window,
                self.search_text,
                BLACK,
                self.search_input.x + 5,
                self.search_input.y + 15,
                False,
                font_small,
            )

        pygame.draw.rect(self.client.window, GRAY, self.search_button)
        pygame.draw.rect(self.client.window, BLACK, self.search_button, 2)
        draw_text(
            self.client.window,
            "keresés",
            BLACK,
            self.search_button.centerx,
            self.search_button.centery,
            True,
            font_small,
        )

        pygame.draw.rect(self.client.window, WHITE, self.filter_checkbox)
        pygame.draw.rect(self.client.window, BLACK, self.filter_checkbox, 2)

        if self.filter_state == 1:
            draw_text(
                self.client.window,
                "O",
                BLACK,
                self.filter_checkbox.centerx,
                self.filter_checkbox.centery,
                True,
                font_small,
            )
        elif self.filter_state == 2:
            draw_text(
                self.client.window,
                "X",
                BLACK,
                self.filter_checkbox.centerx,
                self.filter_checkbox.centery,
                True,
                font_small,
            )

    def draw_room_list_header(self):
        header_y = 120
        font_medium = pygame.font.Font(None, FONT_MEDIUM)

        draw_text(
            self.client.window, "Jelszó", BLACK, 720, header_y + 15, True, font_medium
        )
        draw_text(
            self.client.window, "Létszám", BLACK, 1200, header_y + 15, True, font_medium
        )

    def draw_room_list(self):
        font_small = pygame.font.Font(None, FONT_SMALL)

        room_content_rect = pygame.Rect(
            self.room_list_rect.x,
            self.room_list_rect.y,
            self.room_list_rect.width - self.scroll_bar_width,
            self.room_list_rect.height,
        )
        pygame.draw.rect(self.client.window, WHITE, room_content_rect)
        pygame.draw.rect(self.client.window, BLACK, room_content_rect, 2)

        clip_surface = pygame.Surface(
            (room_content_rect.width, room_content_rect.height)
        )
        clip_surface.fill(WHITE)

        room_name_counts = {}
        for room in self.rooms:
            room_name_counts[room.name] = room_name_counts.get(room.name, 0) + 1

        start_index = max(0, self.scroll_offset)
        end_index = min(len(self.rooms), start_index + self.max_visible_rooms)

        for i in range(start_index, end_index):
            room = self.rooms[i]
            visible_index = i - start_index
            y_pos = visible_index * (self.room_item_height + self.room_padding)
            room_rect = pygame.Rect(
                0, y_pos, room_content_rect.width, self.room_item_height
            )

            if i == self.selected_room_index:
                pygame.draw.rect(clip_surface, (200, 255, 200), room_rect)
                pygame.draw.rect(clip_surface, GREEN, room_rect, 3)
            else:
                pygame.draw.rect(clip_surface, BLACK, room_rect, 1)

            display_name = room.name
            if room_name_counts[room.name] > 1:
                display_name = f"{room.name} (ID: {room.room_id})"

            draw_text(
                clip_surface,
                display_name,
                BLACK,
                room_rect.x + 20,
                0,
                False,
                font_small,
                vcenter_rect=room_rect,
            )

            if room.password_protected:
                draw_text(
                    clip_surface,
                    "X",
                    BLACK,
                    620,
                    y_pos + self.room_item_height // 2,
                    True,
                    font_small,
                )

            player_text = f"{room.player_count}/{room.max_player_count}"
            draw_text(
                clip_surface,
                player_text,
                BLACK,
                1100,
                y_pos + self.room_item_height // 2,
                True,
                font_small,
            )

        self.client.window.blit(
            clip_surface, (room_content_rect.x, room_content_rect.y)
        )

        if len(self.rooms) > self.max_visible_rooms:
            self.draw_scrollbar()

        if (
            self.selected_room_index is not None
            and self.selected_room_index < len(self.rooms)
            and self.rooms[self.selected_room_index].password_protected
        ):
            draw_text(self.client.window, "Jelszó megadása:", BLACK, 250, 415, False)
            color = BLUE if self.join_password_active else GRAY
            pygame.draw.rect(self.client.window, WHITE, self.join_password_input)
            pygame.draw.rect(self.client.window, color, self.join_password_input, 2)

            if self.join_password_text:
                draw_text(
                    self.client.window,
                    self.join_password_text,
                    BLACK,
                    self.join_password_input.x + 5,
                    self.join_password_input.y + 20,
                    False,
                )

        pygame.draw.rect(
            self.client.window,
            GREEN if self.selected_room_index is not None else GRAY,
            self.join_button,
        )
        pygame.draw.rect(self.client.window, BLACK, self.join_button, 2)
        draw_text(
            self.client.window,
            "Csatlakozás:",
            BLACK,
            self.join_button.centerx,
            self.join_button.centery,
            True,
        )

    def draw_scrollbar(self):
        pygame.draw.rect(self.client.window, GRAY, self.scroll_bar_rect)
        pygame.draw.rect(self.client.window, BLACK, self.scroll_bar_rect, 1)

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

            pygame.draw.rect(self.client.window, WHITE, thumb_rect)
            pygame.draw.rect(self.client.window, BLACK, thumb_rect, 1)

    def get_room_index_at_position(self, pos):
        if not self.room_list_rect.collidepoint(pos):
            return None

        room_content_rect = pygame.Rect(
            self.room_list_rect.x,
            self.room_list_rect.y,
            self.room_list_rect.width - self.scroll_bar_width,
            self.room_list_rect.height,
        )

        if not room_content_rect.collidepoint(pos):
            return None

        relative_y = pos[1] - self.room_list_rect.y
        room_index = relative_y // (self.room_item_height + self.room_padding)
        actual_index = self.scroll_offset + room_index

        if 0 <= actual_index < len(self.rooms):
            return actual_index
        return None

    def fileter_rooms(self):
        self.rooms = self.client.room_list
        if self.filter_state == 0:
            self.rooms = self.client.room_list
        elif self.filter_state == 1:
            self.rooms = [room for room in self.rooms if room.password_protected]
        elif self.filter_state == 2:
            self.rooms = [room for room in self.rooms if not room.password_protected]

    def handle_mouse_click(self, pos):
        if self.search_input.collidepoint(pos):
            self.search_active = True
            print("Keresés aktiválva")
            self.room_name_active = False
            self.password_active = False
            self.join_password_active = False
            return

        if self.search_button.collidepoint(pos):
            print(f"Keresés: '{self.search_text}'")
            self.search()
            return

        if self.filter_checkbox.collidepoint(pos):
            self.filter_state = (self.filter_state + 1) % 3
            filter_names = ["Semmi", "Pipa", "X"]
            print(f"Szűrő állapot: {filter_names[self.filter_state]}")
            self.fileter_rooms()
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
            self.scroll_bar_rect.collidepoint(pos)
            and len(self.rooms) > self.max_visible_rooms
        ):
            relative_y = pos[1] - self.scroll_bar_rect.y
            scroll_ratio = relative_y / self.scroll_bar_rect.height
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

            if selected_room.password_protected:
                print(
                    f"Csatlakozás szobához: {selected_room.name}, Jelszó: '{password}'"
                )
            else:
                print(f"Csatlakozás szobához: {selected_room.name}")
            return

        if self.room_name_input.collidepoint(pos):
            self.room_name_active = True
            self.password_active = False
            self.search_active = False
            self.join_password_active = False
            return

        if self.create_password_input.collidepoint(pos) and self.password_protected:
            self.password_active = True
            self.room_name_active = False
            self.search_active = False
            self.join_password_active = False
            return

        if self.password_checkbox.collidepoint(pos):
            print(self.password_protected)
            self.password_protected = not self.password_protected
            print(self.password_protected)
            return

        if self.max_players_up.collidepoint(pos):
            if self.max_players < 6:
                self.max_players += 1
                print(f"Max játékosok: {self.max_players}")
            return

        if self.max_players_down.collidepoint(pos):
            if self.max_players > 2:
                self.max_players -= 1
                print(f"Max játékosok: {self.max_players}")
            return

        if self.create_button.collidepoint(pos) and self.room_name_text.strip() :
            if self.password_protected and  self.password_text_input:

                password = self.password_text_input if self.password_protected else ""
                self.client.network.create_room(
                    self.room_name_text, self.password_protected, self.max_players, password
                )
                return
            elif not self.password_protected:
                password = self.password_text_input if self.password_protected else ""
                self.client.network.create_room(
                    self.room_name_text, self.password_protected, self.max_players, password
                )
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
        font_large = pygame.font.Font(None, 48)
        draw_text(
            self.client.window,
            "Szoba készítés:",
            BLACK,
            self.client.width // 2,
            550,
            True,
            font_large,
        )

        font_small = pygame.font.Font(None, FONT_SMALL)

        draw_text(
            self.client.window,
            "Név:",
            BLACK,
            150,
            0,
            centered=False,
            font=font_small,
            vcenter_rect=self.room_name_input,
        )

        color = BLUE if self.room_name_active else GRAY

        pygame.draw.rect(self.client.window, WHITE, self.room_name_input)
        pygame.draw.rect(self.client.window, color, self.room_name_input, 2)

        if self.room_name_text:
            draw_text(
                self.client.window,
                self.room_name_text,
                BLACK,
                self.room_name_input.x + 5,
                0,
                centered=False,
                font=font_small,
                vcenter_rect=self.room_name_input,
            )
        elif not self.room_name_active and self.room_name_text == "":
            self.room_name_text = self.client.username

        draw_text(
            self.client.window,
            "Jelszóval védett:",
            BLACK,
            550,
            0,
            centered=False,
            font=font_small,
            vcenter_rect=self.password_checkbox,
        )
        pygame.draw.rect(self.client.window, WHITE, self.password_checkbox)
        pygame.draw.rect(self.client.window, BLACK, self.password_checkbox, 2)

        checkbox_char = "O" if self.password_protected else "X"
        draw_text(
            self.client.window,
            checkbox_char,
            BLACK,
            self.password_checkbox.centerx,
            self.password_checkbox.centery,
            centered=True,
            font=font_small,
        )

        draw_text(
            self.client.window,
            "Max létszám:",
            BLACK,
            850,
            0,
            centered=False,
            font=font_small,
            vcenter_rect=self.max_players_rect,
        )
        pygame.draw.rect(self.client.window, WHITE, self.max_players_rect)
        pygame.draw.rect(self.client.window, BLACK, self.max_players_rect, 2)

        draw_text(
            self.client.window,
            str(self.max_players),
            BLACK,
            self.max_players_rect.centerx,
            self.max_players_rect.centery,
            centered=True,
            font=font_small,
        )

        pygame.draw.rect(self.client.window, GRAY, self.max_players_up)
        pygame.draw.rect(self.client.window, BLACK, self.max_players_up, 1)
        draw_text(
            self.client.window,
            "^",
            BLACK,
            self.max_players_up.centerx,
            self.max_players_up.centery,
            centered=True,
            font=font_small,
        )

        pygame.draw.rect(self.client.window, GRAY, self.max_players_down)
        pygame.draw.rect(self.client.window, BLACK, self.max_players_down, 1)
        draw_text(
            self.client.window,
            "v",
            BLACK,
            self.max_players_down.centerx,
            self.max_players_down.centery,
            centered=True,
            font=font_small,
        )

        create_enabled = bool(self.room_name_text.strip())
        button_color = GREEN if create_enabled else GRAY
        pygame.draw.rect(self.client.window, button_color, self.create_button)
        pygame.draw.rect(self.client.window, BLACK, self.create_button, 2)
        draw_text(
            self.client.window,
            "Létrehozás:",
            BLACK,
            self.create_button.centerx,
            self.create_button.centery,
            centered=True,
            font=font_small,
        )

        if self.password_protected:
            draw_text(
                self.client.window,
                "Jelszó:",
                BLACK,
                550,
                0,
                centered=False,
                font=font_small,
                vcenter_rect=self.create_password_input,
            )

            password_color = BLUE if self.password_active else GRAY
            pygame.draw.rect(self.client.window, WHITE, self.create_password_input)
            pygame.draw.rect(
                self.client.window, password_color, self.create_password_input, 2
            )

            if self.password_text_input:
                draw_text(
                    self.client.window,
                    self.password_text_input,
                    BLACK,
                    self.create_password_input.x + 5,
                    0,
                    centered=False,
                    font=font_small,
                    vcenter_rect=self.create_password_input,
                )
