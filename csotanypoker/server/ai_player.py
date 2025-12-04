import random
from typing import Dict, Optional, Tuple
from csotanypoker.models.animal import Animal


class AIPlayer:
    def __init__(self):
        self.guess_patterns: Dict[str, Dict] = {}
        self.trust_statement: Dict[str, Dict] = {}

    def _calculate_seen_cards(self, players) -> Dict[Animal, int]:
        # A fügvény megszámolja, hogy az összes játékos elött hány kártya van felfedve
        seen_cards = {}

        for player in players:
            for animal, count in player.cards_in_front.items():
                if animal not in seen_cards:
                    seen_cards[animal] = 0
                seen_cards[animal] += count

        return seen_cards

    def _calculate_target_weights(
        self,
        players,
        active_player: str,
        passing_card: Optional[Animal] = None,
    ) -> Dict[str, float]:
        """
        Kiszámolja a célpont játékosok súlyait.

        Ha passing_card meg van adva (passzolás esetén), akkor figyelembe veszi,
        hogy az adott kártyából mennyi van már az egyes játékosoknál.
        """
        weights = {}

        other_players = [p for p in players if p.username != active_player.username]

        for player in other_players:
            weight = 1.0

            card_count = player.card_count()
            if card_count <= 2:
                weight *= 3.0
            elif card_count <= 4:
                weight *= 2.0
            elif card_count <= 6:
                weight *= 1.5

            max_same_cards = (
                max(player.cards_in_front.values()) if player.cards_in_front else 0
            )
            if max_same_cards >= 3:
                weight *= 5.0
            elif max_same_cards >= 2:
                weight *= 2.5
            elif max_same_cards >= 1:
                weight *= 1.8

            card_types = set()
            for card in active_player.cards_in_hand:
                card_types.add(card)

            if passing_card is not None:
                cards_of_this_type = player.cards_in_front.get(passing_card, 0)
                if cards_of_this_type >= 3:
                    weight *= 9.0
                elif cards_of_this_type >= 2:
                    weight *= 5.0
                elif cards_of_this_type >= 1:
                    weight *= 3.0
            else:
                for card in card_types:
                    if card in player.cards_in_front:
                        weight *= 1.5

            weights[player.username] = weight

        return weights

    def _calculate_card_weights(
        self,
        active_player_cards_in_hand,
        active_player_cards_in_front,
        target_player_cards_in_front,
    ) -> Dict[Animal, float]:
        weights = {}
        card_types = set()
        for card in active_player_cards_in_hand:
            card_types.add(card)

        for card in card_types:
            weight = 1.0

            cards_in_front = target_player_cards_in_front.get(card, 0)
            if cards_in_front >= 3:
                weight *= 9.0
            elif cards_in_front >= 2:
                weight *= 5.0
            elif cards_in_front >= 1:
                weight *= 3.0

            our_cards_in_front = active_player_cards_in_front.get(card, 0)
            if our_cards_in_front >= 3:
                weight *= 0.50
            elif our_cards_in_front >= 2:
                weight *= 0.70

            weights[card] = weight

        return weights

    def _calculate_statement_strategy(
        self, players, selected_card: Animal, target_player_obj, active_player
    ) -> str:
        weights = {}
        truth_weight = 2.0

        seen_cards = self._calculate_seen_cards(players + [active_player])

        for animal in Animal:
            if animal != selected_card:
                lie_weight = 1.0

                seen_count = seen_cards.get(animal, 0)
                remaining_cards = 8 - seen_count

                if remaining_cards == 0:
                    lie_weight = 0
                elif remaining_cards <= 2:
                    lie_weight *= 0.3
                elif remaining_cards >= 6:
                    lie_weight *= 1.5

                weights[str(animal)] = lie_weight

        if target_player_obj.username in self.guess_patterns:
            pattern = self.guess_patterns[target_player_obj.username]

            if pattern["total_guesses"] >= 3:
                true_ratio = pattern["true_guesses"] / pattern["total_guesses"]

                if true_ratio >= 0.7:
                    for animal_value in weights:
                        weights[animal_value] *= 4.0
                    truth_weight *= 0.3
                elif true_ratio <= 0.3:
                    for animal_value in weights:
                        weights[animal_value] *= 0.3
                    truth_weight *= 3.0
            if pattern["consecutive_true"] >= 3:
                for animal_value in weights:
                    weights[animal_value] *= 2.0
                truth_weight *= 0.5
            elif pattern["consecutive_false"] >= 3:
                for animal_value in weights:
                    weights[animal_value] *= 0.5
                truth_weight *= 2.0

        weights[selected_card.value] = truth_weight
        return self._weighted_random_choice(weights)

    def _calculate_trust_based_guess(self, active_player_name: str) -> Dict[str, float]:
        if active_player_name not in self.trust_statement:
            return {"true": 1.0, "false": 1.0}

        pattern = self.trust_statement[active_player_name]

        if pattern["total_statements"] < 2:
            return {"true": 1.0, "false": 1.0}

        truth_ratio = pattern["truth_statements"] / pattern["total_statements"]
        weights = {"true": 1.0, "false": 1.0}

        if truth_ratio >= 0.85:
            weights["true"] *= 4.0
            weights["false"] *= 0.2
        elif truth_ratio >= 0.75:
            weights["true"] *= 3.0
            weights["false"] *= 0.3
        elif truth_ratio >= 0.65:
            weights["true"] *= 2.0
            weights["false"] *= 0.5
        elif truth_ratio <= 0.15:
            weights["false"] *= 4.0
            weights["true"] *= 0.2
        elif truth_ratio <= 0.25:
            weights["false"] *= 3.0
            weights["true"] *= 0.3
        elif truth_ratio <= 0.35:
            weights["false"] *= 2.0
            weights["true"] *= 0.5

        if pattern["consecutive_truth"] >= 3:
            weights["true"] *= 1.5 + (pattern["consecutive_truth"] * 0.5)
            weights["false"] *= 0.4
        elif pattern["consecutive_false"] >= 3:
            weights["false"] *= 1.5 + (pattern["consecutive_false"] * 0.5)
            weights["true"] *= 0.4

        return weights

    def _make_guess_decision(
        self,
        active_player,
        targeted_player,
        players,
        visited_already: int,
        statement: str,
    ) -> Optional[str]:
        # A fügvény kiszámolja az aktív játékos döntését a kijelentés alapján (igaz, hamis vagy passzol)
        card_in_hand = sum(
            1 for card in targeted_player.cards_in_hand if card == statement
        )

        weights = {"true": 1.0, "false": 2.5, "pass": 1.5}
        if len(players) == 2 or len(visited_already) >= len(players) - 1:
            weights["pass"] = 0

        seen_cards = self._calculate_seen_cards(players)
        seen_count = 0
        for card, count in seen_cards.items():
            if card == statement:
                seen_count += count + card_in_hand

        remaining_cards = 8 - seen_count

        if remaining_cards == 0:
            weights["false"] *= 13.0
            weights["true"] = 0
            weights["pass"] = 0
        elif remaining_cards <= 2:
            weights["false"] *= 3.0
            weights["true"] *= 0.5
            weights["pass"] *= 1.2
        elif remaining_cards >= 6:
            weights["true"] *= 1.5
        trust_weights = self._calculate_trust_based_guess(active_player.username)
        weights["true"] *= trust_weights["true"]
        weights["false"] *= trust_weights["false"]

        if abs(weights["true"] - weights["false"]) < 1.0:
            weights["pass"] *= 1.5

        return self._weighted_random_choice(weights)

    def select_card_and_target(
        self,
        players,
        question_card,
        visited_already,
        active_player,
        passing: bool = False,
    ) -> Tuple[Optional[Animal], Optional[str], Optional[str]]:
        if passing and question_card:
            target_weights = self._calculate_target_weights(
                players, active_player, passing_card=question_card
            )
        else:
            target_weights = self._calculate_target_weights(
                players, active_player, passing_card=None
            )

        available_targets = {
            name: weight
            for name, weight in target_weights.items()
            if name not in visited_already
        }

        if not available_targets:
            return None, None, None

        target_player_name = self._weighted_random_choice(available_targets)
        target_player_obj = [p for p in players if p.username == target_player_name][0]

        if not passing:
            card_weights = self._calculate_card_weights(
                active_player.cards_in_hand,
                active_player.cards_in_front,
                target_player_obj.cards_in_front,
            )
            if max(card_weights.values()) < 0.1:
                return None, None, None

            selected_card = self._weighted_random_choice(card_weights)
        else:
            selected_card = question_card
            if not selected_card:
                return None, None, None

        if not target_player_obj:
            return None, None, None

        statement = self._calculate_statement_strategy(
            players, selected_card, target_player_obj, active_player
        )

        return selected_card, target_player_name, statement

    def _update_guess_patterns(self, guesser_name: str, guess: bool):
        # A függvény frissíti hogy a játékos milyen mintázatot követ a találgatásokban
        # (hányszor tippelt igazat vagy hamisat, összes tipp)

        if guesser_name not in self.guess_patterns:
            self.guess_patterns[guesser_name] = {
                "true_guesses": 0,  # igaz tippek száma
                "total_guesses": 0,  # összes tipp száma
                "consecutive_true": 0,  # jelenlegi egymást követö igaz tippek
                "consecutive_false": 0,  # jelenlegi egymást követö hamis tippek
            }

        pattern = self.guess_patterns[guesser_name]  # a játékos mintázata

        pattern["total_guesses"] += 1  # összes tipp növelése
        if guess:  # ha igaz tippet adott
            pattern["true_guesses"] += 1  # igaz tippek számlálója +1
            pattern["consecutive_true"] += 1  # igaz sorozat folytatódik
            pattern["consecutive_false"] = 0  # hamis sorozat megszakad

        else:  # ha hamis tippet adott
            pattern["consecutive_false"] += 1  # hamis sorozat folytatódik
            pattern["consecutive_true"] = 0  # igaz sorozat megszakad

    def decide_guess(self, game_instance) -> str:
        """Visszaadja: 'true', 'false', vagy 'pass'"""
        active_player = game_instance.state.active_player
        statement = active_player.statement

        return self._make_guess_decision(
            active_player,
            game_instance.state.targeted_player,
            game_instance.state.players,
            game_instance.state.visited_already,
            statement,
        )

    def _update_truth_statement_memory(self, player_name: str, was_truthful: bool):
        # Frissíti hogy a játékos milyen gyakran mond igazat/hazugságot

        if player_name not in self.trust_statement:
            self.trust_statement[player_name] = {
                "truth_statements": 0,  # igaz állítások száma
                "false_statements": 0,  # hamis állítások száma
                "total_statements": 0,  # összes állítás száma
                "consecutive_truth": 0,  # jelenlegi egymást követö igaz állítások
                "consecutive_false": 0,  # jelenlegi egymást követö hazugságok
            }

        pattern = self.trust_statement[player_name]  # a játékos megbízhatósági profilja

        pattern["total_statements"] += 1  # összes állítás növelése
        if was_truthful:  # ha igazat mondott
            pattern["truth_statements"] += 1  # igaz állítások számlálója +1
            pattern["consecutive_truth"] += 1  # igaz sorozat folytatódik
            pattern["consecutive_false"] = 0  # hazugság sorozat megszakad

        else:  # ha hazudott
            pattern["false_statements"] += 1  # hazugságok számlálója +1
            pattern["consecutive_false"] += 1  # hazugság sorozat folytatódik
            pattern["consecutive_truth"] = 0  # igaz sorozat megszakad

    def evaluate_guess(self, game_instance, guess: bool) -> Tuple[bool, any]:
        guesser_name = game_instance.state.targeted_player.username
        active_player_name = game_instance.state.active_player.username

        self._update_guess_patterns(guesser_name, guess)

        result = game_instance.check_truth(guess)

        was_truthful = (guess == True and result == True) or (
            guess == False and result == False
        )
        self._update_truth_statement_memory(active_player_name, was_truthful)

        if result:
            nextplayer = game_instance.place_card(game_instance.state.active_player)
        else:
            nextplayer = game_instance.place_card(game_instance.state.targeted_player)

        return was_truthful, nextplayer

    def reset_round(self, players):
        # A fügvény visszaállítja a kör eleji állapotot
        for player in players:
            player.statement = None
            player.is_true = None

    @staticmethod
    def _weighted_random_choice(choices_weights: Dict[str, float]) -> Optional[str]:
        # Súlyozott véletlenszerű választás a megadott súlyok alapján
        if not choices_weights:
            return None

        choices = list(choices_weights.keys())
        weights = list(choices_weights.values())
        weights = [max(0, w) for w in weights]

        return random.choices(choices, weights=weights)[0]
