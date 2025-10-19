from csotanypoker.client.drawing_helpers.drawing_helpers import handle_logout_button_click


class GameMouseHandler:

    def __init__(self, screen):
        self.screen = screen
    
    def handle_click(self, pos):
        """Egér kattintás kezelése"""
        if handle_logout_button_click(pos, self.screen.logout_button, self.screen.client.network):
            return (True, False)

        if self._handle_leave_button(pos):
            return (True, False)

        result = self._handle_ok_button(pos)
        if result:
            return result

        if self._handle_pass_button(pos):
            return (True, False)
        
        result = self._handle_tip_buttons(pos)
        if result:
            return result
        
        result = self._handle_opponent_selection(pos)
        if result:
            return result
        
        result = self._handle_animal_selection(pos)
        if result:
            return result

        result = self._handle_card_selection(pos)
        if result:
            return result
        
        return (False, False)
    
    def _handle_leave_button(self, pos):
        """Szoba elhagyás gomb kezelése"""
        if self.screen.leave_button.collidepoint(pos) and self.screen.show_leave_button:
            self.screen.client.network.all_players_leave_room(
                self.screen.client.selected_room.room_id
            )
            self.screen.state_manager.reset_local_selections()
            return True
        return False
    
    def _handle_ok_button(self, pos):
        """OK gomb kezelése"""
        if (not hasattr(self.screen, "oke_button") 
            or self.screen.oke_button is None
            or not self.screen.oke_button.collidepoint(pos)):
            return None
        
        is_valid, error_message = self.screen.validator.validate_ok_click()
        
        if not is_valid:
            if self.screen.validator.can_show_error(error_message):
                return (False, True)
            return None
        
        if not self.screen.adott:
            self.screen.client.game_state.question_card = self.screen.local_question_card
            self.screen.client.game_state.targeted_player = self.screen.local_targeted_player
            
            self.screen.client.network.oke_click(
                statement=self.screen.local_active_animal,
                passing=self.screen.client.passed
            )
            self.screen.client.passed = False
            self.screen.adott = True
            
            self.screen.state_manager.reset_local_selections()
            return (True, False)
        
        return None
    
    def _handle_pass_button(self, pos):
        """Pass gomb kezelése"""
        if not hasattr(self.screen, "pass_button") or not self.screen.pass_button.collidepoint(pos):
            return False
        
        if (self.screen.client.game_state.targeted_player == self.screen.client.user.username
            and len(self.screen.client.game_state.visited_already) < len(self.screen.client.users)):
            self.screen.client.passed = True
            self.screen.client.network.passing()
            return True
        
        return False
    
    def _handle_tip_buttons(self, pos):
        if self.screen.client.game_state.targeted_player != self.screen.client.user.username:
            return None
        
        if self.screen.client.game_state.question_card != "card_back":
            return None

        if (hasattr(self.screen, "cross_rect")
            and self.screen.cross_rect
            and self.screen.cross_rect.collidepoint(pos)):
            self.screen.client.network.guess(False)
            return (True, False)
     
        if (hasattr(self.screen, "checkmark_rect")
            and self.screen.checkmark_rect
            and self.screen.checkmark_rect.collidepoint(pos)):
            self.screen.client.network.guess(True)
            return (True, False)
        
        return None
    
    def _handle_opponent_selection(self, pos):
        if not hasattr(self.screen, "opponent_player_rects"):
            return None
        
        for rect, player_name in self.screen.opponent_player_rects:
            if not rect.collidepoint(pos):
                continue
            
            if self.screen.adott:
                return None
            
            is_valid, error_message = self.screen.validator.validate_player_selection(player_name)
            
            if not is_valid:
                if self.screen.validator.can_show_error(error_message):
                    return (False, True)
                return None

            if self.screen.local_targeted_player == player_name:
                self.screen.local_targeted_player = None
            else:
                self.screen.local_targeted_player = player_name
            
            return (True, False)
        
        return None
    
    def _handle_animal_selection(self, pos):
        if not hasattr(self.screen, "animal_button_rects"):
            return None
        
        if self.screen.client.game_state.active_player != self.screen.client.user.username:
            return None
        
        for animal_name, button_rect in self.screen.animal_button_rects.items():
            if not button_rect.collidepoint(pos):
                continue
            
            is_valid, _ = self.screen.validator.validate_animal_selection()
            if not is_valid:
                return (False, True)

            if self.screen.local_active_animal == animal_name:
                self.screen.local_active_animal = None
                self.screen.active_animal = None
            else:
                self.screen.local_active_animal = animal_name
                self.screen.active_animal = animal_name
            
            return (True, False)
        
        return None
    
    def _handle_card_selection(self, pos):
        """Kártya kiválasztás kezelése"""
        if not hasattr(self.screen, "kartya_poziciok"):
            return None
        
        for rect, lap in reversed(self.screen.kartya_poziciok):
            if not rect.collidepoint(pos):
                continue
            
            is_valid, error_message = self.screen.validator.validate_card_selection()
            
            if not is_valid:
                if self.screen.validator.can_show_error(error_message):
                    return (False, True)
                return None
            
            self.screen.local_question_card = lap if lap is not None else None
            self.screen.selected_card_frame = rect
            self.screen.client._music_manager.weapon_sound(lap.value)
            return (False, False)
        
        return None