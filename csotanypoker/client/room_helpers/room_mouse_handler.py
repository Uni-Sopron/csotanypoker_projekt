"""Egér interakció kezelés szobák képernyőhöz"""
import pygame

from csotanypoker.client.drawing_helpers.drawing_helpers import handle_logout_button_click


class RoomMouseHandler:
    """Egér kattintások és mozgás kezelése"""
    
    def __init__(self, screen):
        self.screen = screen
        self.dragging_scrollbar = False
        self._scroll_drag_offset = 0

    def handle_motion(self, pos):
        """Egér mozgás kezelése"""
        self.screen._update_button_states()
        
        if self.dragging_scrollbar and hasattr(self.screen, 'scroll_bar_rect') and self.screen.scroll_bar_rect:
            self._handle_scrollbar_drag(pos)

    def _handle_scrollbar_drag(self, pos):
        """Scrollbar húzás kezelése"""
        total_rooms = len(self.screen.filtered_rooms)
        if total_rooms <= self.screen.MAX_VISIBLE_ROOMS:
            return
            
        visible_ratio = self.screen.MAX_VISIBLE_ROOMS / total_rooms
        thumb_height = max(20, int(self.screen.scroll_bar_rect.height * visible_ratio))
        
        new_thumb_y = pos[1] - self._scroll_drag_offset
        new_thumb_y = max(
            self.screen.scroll_bar_rect.y,
            min(new_thumb_y, self.screen.scroll_bar_rect.y + self.screen.scroll_bar_rect.height - thumb_height)
        )
        
        scroll_ratio = (new_thumb_y - self.screen.scroll_bar_rect.y) / (self.screen.scroll_bar_rect.height - thumb_height)
        max_scroll = total_rooms - self.screen.MAX_VISIBLE_ROOMS
        self.screen.scroll_offset = int(scroll_ratio * max_scroll)
        self.screen.scroll_offset = max(0, min(max_scroll, self.screen.scroll_offset))

    def handle_click(self, pos):
        """Egér kattintás kezelése"""
  
        if handle_logout_button_click(pos, self.screen.logout_button, self.screen.client.network):
            self.screen.reset_create_room_form()
            return True

        if self._handle_scrollbar_click(pos):
            return True

        if self._handle_input_clicks(pos):
            return True

        if self._handle_button_clicks(pos):
            return True

        room_index = self._get_room_index_at_position(pos)
        if room_index is not None:
            self.screen.selected_room_index = room_index if self.screen.selected_room_index != room_index else None
            return True

        self.screen.input_handler.deactivate()
        return False

    def _handle_scrollbar_click(self, pos):
        """Scrollbar kattintás kezelése"""
        if not hasattr(self.screen, 'scroll_bar_rect') or not self.screen.scroll_bar_rect:
            return False
            
        if len(self.screen.rooms) <= self.screen.MAX_VISIBLE_ROOMS:
            return False
            
        if not self.screen.scroll_bar_rect.collidepoint(pos):
            return False

        total_rooms = len(self.screen.filtered_rooms)
        visible_ratio = self.screen.MAX_VISIBLE_ROOMS / total_rooms
        scroll_ratio = self.screen.scroll_offset / (total_rooms - self.screen.MAX_VISIBLE_ROOMS) if total_rooms > self.screen.MAX_VISIBLE_ROOMS else 0
        
        thumb_height = max(20, int(self.screen.scroll_bar_rect.height * visible_ratio))
        thumb_y = self.screen.scroll_bar_rect.y + int((self.screen.scroll_bar_rect.height - thumb_height) * scroll_ratio)
        
        thumb_rect = pygame.Rect(
            self.screen.scroll_bar_rect.x + 2,
            thumb_y,
            self.screen.scroll_bar_rect.width - 4,
            thumb_height,
        )
        
        if thumb_rect.collidepoint(pos):
            self.dragging_scrollbar = True
            self._scroll_drag_offset = pos[1] - thumb_y
            return True
        
        relative_y = pos[1] - self.screen.scroll_bar_rect.y
        click_ratio = relative_y / self.screen.scroll_bar_rect.height
        max_scroll = total_rooms - self.screen.MAX_VISIBLE_ROOMS
        new_offset = int(click_ratio * max_scroll)
        self.screen.scroll_offset = max(0, min(max_scroll, new_offset))
        return True

    def _handle_input_clicks(self, pos):
        """Input mezők kattintásának kezelése"""
        input_rects = {
            'search': getattr(self.screen, 'search_input', None),
            'room_name': getattr(self.screen, 'room_name_input', None),
            'password': getattr(self.screen, 'create_password_input', None) if self.screen.password_protected else None,
            'join_password': getattr(self.screen, 'join_password_input', None) if self.screen._get_selected_room() and self.screen._get_selected_room().password_protected else None,
            'max_players': getattr(self.screen, 'max_count', None),
        }

        for input_name, rect in input_rects.items():
            if rect and rect.collidepoint(pos):
                self.screen.input_handler.activate(input_name)
                if input_name == 'max_players':
                    self.screen.input_handler.inputs['max_players'] = str(self.screen.max_players)
                return True
        
        return False

    def _handle_button_clicks(self, pos):
        """Gombok kattintásának kezelése"""
        if hasattr(self.screen, "search_button") and self.screen.search_button.collidepoint(pos):
            self.screen.apply_filters()
            return True

        if hasattr(self.screen, "lock_button") and self.screen.lock_button.collidepoint(pos):
            self.screen.filter_state = (self.screen.filter_state + 1) % 3
            self.screen.apply_filters()
            return True

        if hasattr(self.screen, "password_checkbox") and self.screen.password_checkbox.collidepoint(pos):
            self.screen.password_protected = not self.screen.password_protected
            return True

        if hasattr(self.screen, "max_players_up") and self.screen.max_players_up.collidepoint(pos):
            self.screen.input_handler.deactivate()
            if self.screen.max_players < 6:
                self.screen.max_players += 1
            return True

        if hasattr(self.screen, "max_players_down") and self.screen.max_players_down.collidepoint(pos):
            self.screen.input_handler.deactivate()
            if self.screen.max_players > 2:
                self.screen.max_players -= 1
            return True

        if hasattr(self.screen, "join_button") and self.screen.join_button.collidepoint(pos):
            if self.screen._is_join_enabled(show_error=True):
                selected_room = self.screen._get_selected_room()
                password = self.screen.input_handler.inputs['join_password'] if selected_room.password_protected else ""
                self.screen.client.network.join_room(selected_room.room_id, password)
                self.screen.reset_create_room_form()
            return True

        if hasattr(self.screen, "create_button") and self.screen.create_button.collidepoint(pos):
            if self.screen._is_create_enabled(show_error=True):
                password = self.screen.input_handler.inputs['password'] if self.screen.password_protected else ""
                room_name = self.screen.input_handler.inputs['room_name'].strip() or f"{self.screen.client.user.username} szobája"
                self.screen.client.network.create_room(room_name, self.screen.password_protected, self.screen.max_players, password)
                self.screen.reset_create_room_form()
            return True

        return False

    def _get_room_index_at_position(self, pos):
        """Szoba index meghatározása pozíció alapján"""
        if not hasattr(self.screen, "rooms_area_rect") or not self.screen.rooms_area_rect.collidepoint(pos):
            return None

        room_content_rect = pygame.Rect(
            self.screen.rooms_area_rect.x,
            self.screen.rooms_area_rect.y,
            self.screen.rooms_area_rect.width - self.screen.SCROLL_BAR_WIDTH,
            self.screen.rooms_area_rect.height,
        )

        if not room_content_rect.collidepoint(pos):
            return None

        relative_y = pos[1] - (self.screen.rooms_area_rect.y + self.screen.PADDING)
        if relative_y < 0:
            return None

        total_row_height = self.screen.ROOM_ROW_HEIGHT + self.screen.ROOM_PADDING
        room_index = relative_y // total_row_height
        row_internal_y = relative_y % total_row_height

        if row_internal_y >= self.screen.ROOM_ROW_HEIGHT:
            return None

        actual_index = self.screen.scroll_offset + room_index
        visible_rooms = self.screen._get_visible_rooms()

        if 0 <= room_index < len(visible_rooms) and 0 <= actual_index < len(self.screen.rooms):
            return actual_index

        return None

    def handle_release(self, pos):
        """Egérgomb felengedésének kezelése"""
        self.dragging_scrollbar = False

    def handle_wheel(self, event):
        """Egérgörgetés kezelése"""
        if len(self.screen.filtered_rooms) > self.screen.MAX_VISIBLE_ROOMS:
            max_scroll = len(self.screen.filtered_rooms) - self.screen.MAX_VISIBLE_ROOMS
            scroll_speed = 1

            if event.y > 0:
                self.screen.scroll_offset = max(0, self.screen.scroll_offset - scroll_speed)
            elif event.y < 0:
                self.screen.scroll_offset = min(max_scroll, self.screen.scroll_offset + scroll_speed)


def get_room_mouse_handler(screen):
    """Factory függvény a RoomMouseHandler létrehozásához"""
    return RoomMouseHandler(screen)