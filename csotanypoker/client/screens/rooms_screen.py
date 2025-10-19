"""Szobák képernyő - egyszerűsített verzió"""
import pygame

from csotanypoker.client.drawing_helpers.drawing_helpers import check_logout_button_interaction
from csotanypoker.client.screens.base_screen import BaseScreen
from csotanypoker.client.room_helpers.room_input_handler import RoomInputHandler
from csotanypoker.client.room_helpers.room_mouse_handler import RoomMouseHandler
from csotanypoker.client.room_helpers.room_drawer import RoomDrawer


class RoomsScreen(BaseScreen):
    """Szobák listája és szoba létrehozás képernyő"""
    
    def __init__(self, client):
        super().__init__(client)
        self.client = client
        
        # Handler objektumok
        self.input_handler = RoomInputHandler(self)
        self.mouse_handler = RoomMouseHandler(self)
        self.drawer = RoomDrawer(self)
        
        # Állapot változók
        self.selected_room_index = None
        self.scroll_offset = 0
        self.filter_state = 0
        self.original_rooms = []
        self.filtered_rooms = []
        self.password_protected = False
        self.max_players = 4
        
        self.hovered_elements = set()
        self.pressed_elements = set()
        
        # Konstansok
        self.MAX_VISIBLE_ROOMS = 4
        self.ROOM_ROW_HEIGHT = 55
        self.ROOM_PADDING = 2
        self.SCROLL_BAR_WIDTH = 20
        self.BUTTON_PADDING = 35
        self.PADDING = 10
        self.logout_button = pygame.Rect(20, self.client.height - 105, 220, 85)

    @property
    def rooms(self):
        return self.filtered_rooms

    
    def apply_filters(self):
        filtered_rooms = self.original_rooms.copy()
        search_text = self.input_handler.inputs['search'].lower().strip()
        
        if search_text:
            filtered_rooms = [
                room for room in filtered_rooms
                if search_text in room.name.lower() or search_text in room.room_id.lower()
            ]

        if self.filter_state == 1:
            filtered_rooms = [room for room in filtered_rooms if room.password_protected]
        elif self.filter_state == 2:
            filtered_rooms = [room for room in filtered_rooms if not room.password_protected]

        self.filtered_rooms = filtered_rooms
        self.scroll_offset = 0
        
    def _get_selected_room(self):
        """Visszaadja a kiválasztott szobát, ha van"""
        if self.selected_room_index is not None and self.selected_room_index < len(self.rooms):
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

        if selected_room.password_protected and not self.input_handler.inputs['join_password'].strip():
            if show_error:
                self.client.message = "Jelszó megadása szükséges"
                self.client.message_display_time = 60
            return False
        return True

    def _is_create_enabled(self, show_error=False):
        """Ellenőrzi, hogy a létrehozás gomb engedélyezett-e"""
        if self.password_protected and not self.input_handler.inputs['password'].strip():
            if show_error:
                self.client.message = "Jelszó megadása szükséges"
                self.client.message_display_time = 60
            return False
        return True
    
    def handle_mouse_motion(self, pos):
        """Egér mozgás kezelése"""
        self.mouse_handler.handle_motion(pos)

    def handle_mouse_click(self, pos):
        """Egér kattintás kezelése"""
        return self.mouse_handler.handle_click(pos)

    def handle_mouse_release(self, pos):
        """Egérgomb felengedésének kezelése"""
        self.mouse_handler.handle_release(pos)

    def handle_mouse_wheel(self, event):
        """Egérgörgetés kezelése"""
        self.mouse_handler.handle_wheel(event)

    def handle_key_press(self, event):
        """Billentyű lenyomás kezelése"""
        self.input_handler.handle_key_press(event)

    
    def reset_create_room_form(self):
        """Szoba létrehozás form visszaállítása alapállapotba"""
        self.input_handler.reset()
        self.password_protected = False
        self.max_players = 4
        self.selected_room_index = None

    def _get_visible_rooms(self):
        """Aktuálisan látható szobák listája"""
        start_index = self.scroll_offset
        end_index = min(len(self.filtered_rooms), start_index + self.MAX_VISIBLE_ROOMS)
        return self.filtered_rooms[start_index:end_index]

    def _update_button_states(self):
        """Gombok hover/pressed állapotának frissítése"""
    
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

        if hasattr(self, "create_button") and self.create_button.collidepoint(mouse_pos):
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
        """Szobák lista frissítése a client-től"""
        self.original_rooms = self.client.room_list.copy()
        self.apply_filters()
        self._update_selected_room_index()

    def _update_selected_room_index(self):
        """Kiválasztott szoba index frissítése szűrés után"""
        if self.selected_room_index is not None and self.selected_room_index < len(self.original_rooms):
            selected_room = self.original_rooms[self.selected_room_index]

            for i, room in enumerate(self.filtered_rooms):
                if room.room_id == selected_room.room_id:
                    self.selected_room_index = i
                    return

            self.selected_room_index = None

    def _should_update_rooms(self):
        """Ellenőrzi, hogy frissíteni kell-e a szobák listáját"""
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

    
    def draw(self):
        """Teljes képernyő kirajzolása"""
        self.drawer.draw_all()