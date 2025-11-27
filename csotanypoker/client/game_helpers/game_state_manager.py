from csotanypoker.models.user import this_is_ai_name


class GameStateManager:
    def __init__(self, screen):
        self.screen = screen

    def reset_local_selections(self, preserve_passing: bool = False):
        """Lokális választások visszaállítása

        Args:
            preserve_passing: Ha True, a passing flag értékét megtartja
        """
        self.screen.local_question_card = None
        self.screen.local_targeted_player = None
        self.screen.local_active_animal = None
        self.screen.active_animal = None
        self.screen.answer = False

        if not preserve_passing:
            if (
                hasattr(self.screen.client, "game_state")
                and self.screen.client.game_state
            ):
                self.screen.client.game_state.passing = False

    def update_on_game_change(self, current_game_id):
        """Játék változás kezelése - újracsatlakozáskor is"""
        if current_game_id != self.screen.last_game_id:
            preserve_passing = self.screen.last_game_id is None
            self.reset_local_selections(preserve_passing=preserve_passing)
            self.screen.last_game_id = current_game_id

    def update_on_player_change(self):
        """Játékos váltás kezelése"""
        if not self.screen.client.game_state or not self.screen.client.user:
            return

        active_player = self.screen.client.game_state.active_player_name
        if not active_player:
            return

        is_my_turn = active_player == self.screen.client.user.username

        if not is_my_turn:
            self.reset_local_selections(preserve_passing=False)
            self.screen.client.game_state.card_played = False
        elif (
            self.screen.client.game_state.card_played and not self.screen.client.game_state.targeted_player_name
        ):
            self.screen.client.game_state.card_played = False
            if (
                hasattr(self.screen.client, "opponent_players")
                and self.screen.client.opponent_players
                and len(self.screen.client.opponent_players) == 1
            ):
                self.screen.local_targeted_player = self.screen.client.opponent_players[
                    0
                ].username

    def check_leave_button_visibility(self):
        for user in self.screen.client.users:
            if not user.is_active:
                self.screen.show_leave_button = True
                return
        self.screen.show_leave_button = False

    def set_contextual_message(self):
        if (
            not hasattr(self.screen.client, "message")
            or self.screen.client.message is None
            or getattr(self.screen.client, "message_display_time", 0) <= 0
        ):
            if not self.screen.client.game_state or not self.screen.client.user:
                return

            active_player = self.screen.client.game_state.active_player_name
            targeted_player = self.screen.client.game_state.targeted_player_name
            username = self.screen.client.user.username
            message = ""
            if active_player == username:
                if not self.screen.client.game_state.card_played:
                    if self.screen.client.game_state.passing:
                        message = "Válassz másik játékost és állíts valamit a lapról!"
                    else:
                        message = "Válassz kártyát és játékost, majd állíts valamit!"
            elif targeted_player == username:
                message = "Igaz vagy hamis az állítás?"
            elif targeted_player is None:
                message = f"Várj {this_is_ai_name(active_player)} lépésére."
            else:
                message = f"{this_is_ai_name(targeted_player)} játékos lapot kapott {this_is_ai_name(active_player)}-től."

            self.screen.client.message = message
            self.screen.client.message_display_time = 30
