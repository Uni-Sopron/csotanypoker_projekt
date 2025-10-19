"""Input kezelés szobák képernyőhöz"""
import pygame


class RoomInputHandler:
    """Input mezők és billentyűzet kezelése"""
    
    def __init__(self, screen):
        self.screen = screen
        self.active_input = None
        self.inputs = {
            'search': '',
            'room_name': '',
            'password': '',
            'join_password': '',
            'max_players': '',
        }
        self.max_lengths = {
            'search': 20,
            'room_name': 20,
            'password': 15,
            'join_password': 15,
            'max_players': 1,
        }

    def is_active(self, input_name):
        return self.active_input == input_name

    def activate(self, input_name):
        self.active_input = input_name

    def deactivate(self):
        self.active_input = None

    def handle_key_press(self, event):
        """Billentyű lenyomás kezelése"""
        if self.active_input:
            self._handle_input_key(event)
        else:
            self._handle_global_keys(event)

    def _handle_input_key(self, event):
        """Aktív input mező billentyűzet kezelése"""
        input_name = self.active_input
        
        if event.key == pygame.K_RETURN:
            self._handle_enter_key(input_name)
        elif event.key == pygame.K_TAB:
            self._handle_tab_navigation(input_name)
        elif event.key == pygame.K_BACKSPACE:
            self.inputs[input_name] = self.inputs[input_name][:-1]
            if input_name == 'search':
                self.screen.apply_filters()
        else:
            self._handle_character_input(event, input_name)

    def _handle_enter_key(self, input_name):
        """Enter billentyű kezelése"""
        if input_name == 'search':
            self.screen.apply_filters()
        elif input_name == 'max_players' and self.inputs['max_players'].strip():
            try:
                new_value = int(self.inputs['max_players'])
                self.screen.max_players = new_value if 2 <= new_value <= 6 else 4
            except ValueError:
                self.screen.max_players = 4
        self.deactivate()

    def _handle_tab_navigation(self, current_input):
        """Tab navigáció input mezők között"""
        if current_input == 'room_name':
            if self.screen.password_protected:
                self.activate('password')
            else:
                self.deactivate()
        elif current_input == 'password':
            self.activate('room_name')
        else:
            self.deactivate()

    def _handle_character_input(self, event, input_name):
        """Karakter bevitel kezelése"""
        max_len = self.max_lengths.get(input_name, 20)
        
        if input_name == 'max_players':
            if event.unicode.isdigit() and 2 <= int(event.unicode) <= 6:
                self.inputs[input_name] = event.unicode
        elif len(self.inputs[input_name]) < max_len:
            self.inputs[input_name] += event.unicode
            if input_name == 'search':
                self.screen.apply_filters()

    def _handle_global_keys(self, event):
        """Globális billentyűk kezelése (nem input módban)"""
        if event.key >= pygame.K_2 and event.key <= pygame.K_6:
            new_value = int(event.unicode)
            if 2 <= new_value <= 6:
                self.screen.max_players = new_value
        elif event.key == pygame.K_UP:
            self._handle_up_key()
        elif event.key == pygame.K_DOWN:
            self._handle_down_key()

    def _handle_up_key(self):
        """Fel nyíl kezelése"""
        if len(self.screen.rooms) > self.screen.MAX_VISIBLE_ROOMS:
            self.screen.scroll_offset = max(0, self.screen.scroll_offset - 1)
        elif self.screen.max_players < 6:
            self.screen.max_players += 1

    def _handle_down_key(self):
        """Le nyíl kezelése"""
        if len(self.screen.rooms) > self.screen.MAX_VISIBLE_ROOMS:
            max_scroll = len(self.screen.rooms) - self.screen.MAX_VISIBLE_ROOMS
            self.screen.scroll_offset = min(max_scroll, self.screen.scroll_offset + 1)
        elif self.screen.max_players > 2:
            self.screen.max_players -= 1

    def reset(self):
        """Input értékek alaphelyzetbe állítása"""
        self.inputs = {key: '' for key in self.inputs}
        self.deactivate()