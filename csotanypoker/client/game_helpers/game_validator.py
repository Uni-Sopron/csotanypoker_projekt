class GameValidator:
    def __init__(self, screen):
        self.screen = screen

    def validate_ok_click(self):
        if (
            self.screen.client.game_state.active_player
            != self.screen.client.user.username
        ):
            return False, None

        if self.screen.show_leave_button:
            return False, "Várd meg míg minden játékos visszatér!"

        if not self.screen.client.game_state.passing:
            if not self.screen.local_question_card:
                return False, "Nincs kártya kiválasztva!"

        if not self.screen.local_targeted_player:
            return False, "Válassz egy játékost!"

        if not self.screen.local_active_animal:
            return False, "Válassz egy állatot!"

        return True, None

    def validate_player_selection(self, player_name):
        if (
            self.screen.client.game_state.active_player
            != self.screen.client.user.username
        ):
            return False, "Nem te vagy soron"

        if self.screen.show_leave_button:
            for user in self.screen.client.users:
                if user.username == player_name and not user.is_active:
                    return (
                        False,
                        f"{player_name} játékos nem aktív. Várd meg amíg visszatér!",
                    )
            inactive_players = [
                user for user in self.screen.client.users if not user.is_active
            ]
            if inactive_players:
                return False, "Várd meg míg minden játékos visszatér!"

        if player_name in self.screen.client.game_state.visited_already:
            return False, "Nála már volt ez a lap. Válassz másik játékost."

        return True, None

    def validate_card_selection(self):
        """Kártya kiválasztás validálása"""
        if self.screen.adott:
            return False, "Már adtál lapot ebben a körben."

        if (
            self.screen.client.game_state.active_player
            != self.screen.client.user.username
        ):
            return False, "Nem te vagy soron"

        if self.screen.client.game_state.passing:
            return False, "Passoltál ebben a körben, nem választhatsz új kártyát."

        return True, None

    def validate_animal_selection(self):
        """Állat kiválasztás validálása"""
        if self.screen.adott:
            return False, "Már adtál lapot ebben a körben."

        return True, None

    def can_show_error(self, error_message):
        if error_message:
            self.screen.client.message = error_message
            self.screen.client.message_display_time = 30
            return True
        return False
