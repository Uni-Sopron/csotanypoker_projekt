import random
from typing import Dict, Optional, Tuple
from csotanypoker.models.animal import Animal


class AIPlayer:
    def __init__(self):
        self.player_risks: Dict[str, int] = {}
        self.guess_patterns: Dict[str, Dict] = {}
        self.trust_statement: Dict[str, Dict] = {}

    def calculate_seen_cards(self, players) -> Dict[Animal, int]:
        # A fügvény megszámolja, hogy az összes játékos elött hány kártya van felfedve
        seen_cards = {}

        for player in players:
            for animal, count in player.cards_in_front.items():
                if animal not in seen_cards:
                    seen_cards[animal] = 0
                seen_cards[animal] += count

        return seen_cards

    def calculate_target_weights(
        self, players, active_player_username: str
    ) -> Dict[str, float]:
        # A fügvény kiszámolja a célpont játékosok súlyait az aktív játékos számára
        weights = {}

        other_players = [p for p in players if p.username != active_player_username]

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

            weights[player.username] = weight

        return weights

    def calculate_card_weights(
        self,
        active_player_cards_in_hand,
        active_player_cards_in_front,
        target_player_cards_in_front,
    ) -> Dict[Animal, float]:
        # A fügvény kiszámolja a kártyák súlyait az aktív játékos kezében
        weights = {}

        for card in active_player_cards_in_hand:
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

    def calculate_statement_strategy(
        self, players, selected_card: Animal, target_player_obj, active_player
    ) -> str:
        # A fügvény kiszámolja a kijelentés stratégiáját az aktív játékos számára
        weights = {}
        truth_weight = 2.0

        seen_cards = self.calculate_seen_cards(players)

        for animal in Animal:
            if animal != selected_card:
                lie_weight = 1.0

                card_in_hand = sum(
                    1 for card in active_player.cards_in_hand if card == animal
                )
                seen_count = seen_cards.get(animal, 0) + card_in_hand
                remaining_cards = 8 - seen_count

                if remaining_cards == 0:
                    lie_weight *= 0
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

        weights[selected_card.value] = truth_weight
        return self._weighted_random_choice(weights)

    def calculate_trust_based_guess(self, active_player_name: str) -> Dict[str, float]:
        # A fügvény kiszámolja  hogy mennyire bízik az aktív játékos a kijelentésekben (igaz vagy hamis)
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

        if "recent_statements" in pattern:
            recent = pattern["recent_statements"][-5:]

            if len(recent) >= 3:
                if all(recent[-3:]):
                    weights["true"] *= 2.5
                    weights["false"] *= 0.3
                elif not any(recent[-3:]):
                    weights["false"] *= 2.5
                    weights["true"] *= 0.3

            if len(recent) >= 4:
                if all(recent[-4:]):
                    weights["true"] *= 3.0
                    weights["false"] *= 0.2
                elif not any(recent[-4:]):
                    weights["false"] *= 3.0
                    weights["true"] *= 0.2

        if pattern["consecutive_truth"] >= 3:
            weights["true"] *= 1.5 + (pattern["consecutive_truth"] * 0.5)
            weights["false"] *= 0.4
        elif pattern["consecutive_false"] >= 3:
            weights["false"] *= 1.5 + (pattern["consecutive_false"] * 0.5)
            weights["true"] *= 0.4

        return weights

    def make_guess_decision(
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

        seen_cards = self.calculate_seen_cards(players)

        seen_count = 0
        for card, count in seen_cards.items():
            if card == statement:
                seen_count += count + card_in_hand

        remaining_cards = 8 - seen_count

        trust_weights = self.calculate_trust_based_guess(active_player.username)
        if remaining_cards == 0:
            weights["false"] *= 13.0
            weights["true"] *= 0
            weights["pass"] *= 0.1
        elif remaining_cards <= 2:
            weights["false"] *= 3.0
            weights["true"] *= 0.5
        elif remaining_cards >= 6:
            weights["true"] *= 1.5

        weights["true"] *= trust_weights["true"]
        weights["false"] *= trust_weights["false"]
        return self._weighted_random_choice(weights)

    def select_card_and_target(
        self,
        players,
        question_card,
        visited_already,
        active_player,
        passing: bool = False,
    ) -> Tuple[Optional[Animal], Optional[str], Optional[str]]:
        # A fügvény kiválasztja az aktív játékos kártyáját és célpontját

        target_weights = self.calculate_target_weights(players, active_player.username)

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
            card_weights = self.calculate_card_weights(
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

        statement = self.calculate_statement_strategy(
            players, selected_card, target_player_obj, active_player
        )

        return selected_card, target_player_name, statement

    def update_guess_patterns(self, guesser_name: str, guess: bool):
        # A függvény frissíti hogy a játékos milyen mintázatot követ a találgatásokban
        # (hányszor tippelt igazat vagy hamisat, összes tipp)

        if guesser_name not in self.guess_patterns:
            self.guess_patterns[guesser_name] = {
                "true_guesses": 0,  # igaz tippek száma
                "false_guesses": 0,  # hamis tippek száma
                "total_guesses": 0,  # összes tipp száma
                "recent_guesses": [],  # utolsó 10 tipp listája
                "consecutive_true": 0,  # jelenlegi egymást követö igaz tippek
                "consecutive_false": 0,  # jelenlegi egymást követö hamis tippek
                "max_consecutive_true": 0,  # leghosszabb igaz tipp sorozat
                "max_consecutive_false": 0,  # leghosszabb hamis tipp sorozat
            }

        pattern = self.guess_patterns[guesser_name]  # a játékos mintázata

        pattern["total_guesses"] += 1  # összes tipp növelése
        if guess:  # ha igaz tippet adott
            pattern["true_guesses"] += 1  # igaz tippek számlálója +1
            pattern["consecutive_true"] += 1  # igaz sorozat folytatódik
            pattern["consecutive_false"] = 0  # hamis sorozat megszakad
            pattern["max_consecutive_true"] = max(  # frissíti a rekordot ha új maximum
                pattern["max_consecutive_true"], pattern["consecutive_true"]
            )
        else:  # ha hamis tippet adott
            pattern["false_guesses"] += 1  # hamis tippek számlálója +1
            pattern["consecutive_false"] += 1  # hamis sorozat folytatódik
            pattern["consecutive_true"] = 0  # igaz sorozat megszakad
            pattern["max_consecutive_false"] = max(  # frissíti a rekordot ha új maximum
                pattern["max_consecutive_false"], pattern["consecutive_false"]
            )

        pattern["recent_guesses"].append(guess)  # hozzáadja a legutóbbi tippekhez
        if len(pattern["recent_guesses"]) > 10:  # ha több mint 10 tipp van
            pattern["recent_guesses"].pop(0)  # törli a legrégebbit

    def decide_guess(self, game_instance) -> str:
        """Visszaadja: 'true', 'false', vagy 'pass'"""
        active_player = game_instance.state.active_player
        statement = active_player.statement

        return self.make_guess_decision(
            active_player,
            game_instance.state.targeted_player,
            game_instance.state.players,
            game_instance.state.visited_already,
            statement,
        )

    def update_truth_statement_memory(self, player_name: str, was_truthful: bool):
        # Frissíti hogy a játékos milyen gyakran mond igazat/hazugságot

        if player_name not in self.trust_statement:
            self.trust_statement[player_name] = {
                "truth_statements": 0,  # igaz állítások száma
                "false_statements": 0,  # hamis állítások száma
                "total_statements": 0,  # összes állítás száma
                "recent_statements": [],  # utolsó 10 állítás listája
                "consecutive_truth": 0,  # jelenlegi egymást követö igaz állítások
                "consecutive_false": 0,  # jelenlegi egymást követö hazugságok
                "max_consecutive_truth": 0,  # leghosszabb igaz állítás sorozat
                "max_consecutive_false": 0,  # leghosszabb hazugság sorozat
            }

        pattern = self.trust_statement[player_name]  # a játékos megbízhatósági profilja

        pattern["total_statements"] += 1  # összes állítás növelése
        if was_truthful:  # ha igazat mondott
            pattern["truth_statements"] += 1  # igaz állítások számlálója +1
            pattern["consecutive_truth"] += 1  # igaz sorozat folytatódik
            pattern["consecutive_false"] = 0  # hazugság sorozat megszakad
            pattern["max_consecutive_truth"] = max(  # frissíti a rekordot ha új maximum
                pattern["max_consecutive_truth"], pattern["consecutive_truth"]
            )
        else:  # ha hazudott
            pattern["false_statements"] += 1  # hazugságok számlálója +1
            pattern["consecutive_false"] += 1  # hazugság sorozat folytatódik
            pattern["consecutive_truth"] = 0  # igaz sorozat megszakad
            pattern["max_consecutive_false"] = max(  # frissíti a rekordot ha új maximum
                pattern["max_consecutive_false"], pattern["consecutive_false"]
            )

        pattern["recent_statements"].append(was_truthful)
        if len(pattern["recent_statements"]) > 10:
            pattern["recent_statements"].pop(0)

    def evaluate_guess(self, game_instance, guess: bool) -> Tuple[bool, any]:
        guesser_name = game_instance.state.targeted_player.username
        active_player_name = game_instance.state.active_player.username

        self.update_guess_patterns(guesser_name, guess)

        result = game_instance.check_truth(guess)

        was_truthful = (guess == True and result == True) or (
            guess == False and result == False
        )
        self.update_truth_statement_memory(active_player_name, was_truthful)

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
            max_same_cards = (
                max(player.cards_in_front.values()) if player.cards_in_front else 0
            )
            self.player_risks[player.username] = max_same_cards

    @staticmethod
    def _weighted_random_choice(choices_weights: Dict[str, float]) -> Optional[str]:
        # Súlyozott véletlenszerű választás a megadott súlyok alapján
        if not choices_weights:
            return None

        choices = list(choices_weights.keys())
        weights = list(choices_weights.values())
        weights = [max(0, w) for w in weights]

        return random.choices(choices, weights=weights)[0]
