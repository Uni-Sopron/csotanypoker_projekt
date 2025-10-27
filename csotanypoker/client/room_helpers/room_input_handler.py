import pygame
from csotanypoker.client.drawing_helpers.drawing_helpers import get_input_state
from csotanypoker.client.drawing_helpers.text_manager import (
    handle_continuous_arrow_keys,
    handle_continuous_backspace,
    handle_input_text_event,
    handle_mouse_click_in_input,
)


class RoomInputHandler:
    
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
        self.input_rects = {}

    def is_active(self, input_name):
        return self.active_input == input_name

    def activate(self, input_name):
        self.active_input = input_name
        state = get_input_state(input_name)
        state.cursor_pos = len(self.inputs[input_name])

    def deactivate(self):
        self.active_input = None

    def handle_mouse_click_in_field(self, pos, input_name, rect, is_password=False):
        cursor_pos = handle_mouse_click_in_input(
            pos,
            rect,
            self.inputs[input_name],
            27 if input_name != 'max_players' else 30,
            15,
            is_password,
        )
        if cursor_pos is not None:
            state = get_input_state(input_name)
            state.cursor_pos = cursor_pos
            return True
        return False

    def handle_key_press(self, event):
        if self.active_input:
            self._handle_input_key(event)
        else:
            self._handle_global_keys(event)

    def handle_key_release(self, event):
   
        if not self.active_input:
            return
            
        state = get_input_state(self.active_input)
        
        if event.key == pygame.K_BACKSPACE:
            state.backspace_held = False
        elif event.key == pygame.K_LEFT:
            state.left_held = False
        elif event.key == pygame.K_RIGHT:
            state.right_held = False

    def update_continuous_input(self):
        if not self.active_input:
            return

  
        state = get_input_state(self.active_input)
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        new_text, new_cursor, changed = handle_continuous_backspace(
            state, self.inputs[self.active_input], current_time
        )
        if changed:
            self.inputs[self.active_input] = new_text
            if self.active_input == 'search':
                self.screen.apply_filters()

        text_len = len(self.inputs[self.active_input])
        new_cursor, changed = handle_continuous_arrow_keys(state, keys, current_time, text_len)
        if changed:
            state.cursor_pos = new_cursor

    def _handle_input_key(self, event):
        """Aktív input mező billentyűzet kezelése"""
        input_name = self.active_input
        
        if event.key == pygame.K_RETURN:
            self._handle_enter_key(input_name)
            return
        elif event.key == pygame.K_TAB:
            self._handle_tab_navigation(input_name)
            return
        elif event.key == pygame.K_ESCAPE:
            self.deactivate()
            return
        if input_name == 'max_players':
            self._handle_max_players_input(event)
            return

        state = get_input_state(input_name)
        rect = self.input_rects.get(input_name)
        
        if not rect:
            self._handle_input_key_fallback(event, input_name)
            return

        is_password = input_name in ['password', 'join_password']
        font_size = 27 if input_name != 'max_players' else 30
        
        new_text, new_cursor, handled = handle_input_text_event(
            event,
            self.inputs[input_name],
            state.cursor_pos,
            self.max_lengths[input_name],
            rect,
            font_size,
            15,
            is_password,
        )
        
        if handled:
            self.inputs[input_name] = new_text
            state.cursor_pos = new_cursor
            
            if event.key == pygame.K_BACKSPACE:
                state.backspace_held = True
                state.last_backspace_time = pygame.time.get_ticks()
            elif event.key == pygame.K_LEFT:
                state.left_held = True
                state.last_arrow_time = pygame.time.get_ticks()
            elif event.key == pygame.K_RIGHT:
                state.right_held = True
                state.last_arrow_time = pygame.time.get_ticks()
            
            if input_name == 'search':
                self.screen.apply_filters()

    def _handle_max_players_input(self, event):
        """Max players speciális input kezelés"""
        if event.unicode.isdigit() and 2 <= int(event.unicode) <= 6:
            self.inputs['max_players'] = event.unicode
            state = get_input_state('max_players')
            state.cursor_pos = 1
        elif event.key == pygame.K_BACKSPACE:
            self.inputs['max_players'] = ''
            state = get_input_state('max_players')
            state.cursor_pos = 0

    def _handle_input_key_fallback(self, event, input_name):
        """Fallback input kezelés ha nincs rect"""
        if event.key == pygame.K_BACKSPACE:
            if self.inputs[input_name]:
                self.inputs[input_name] = self.inputs[input_name][:-1]
                if input_name == 'search':
                    self.screen.apply_filters()
        elif len(event.unicode) == 1 and event.unicode.isprintable():
            if len(self.inputs[input_name]) < self.max_lengths[input_name]:
                self.inputs[input_name] += event.unicode
                if input_name == 'search':
                    self.screen.apply_filters()

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