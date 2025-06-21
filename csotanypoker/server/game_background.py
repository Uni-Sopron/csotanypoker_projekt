from random import choice, shuffle
import uuid

from csotanypoker.models.card import Card
from csotanypoker.models.gamestate import GameState


TYPES = [
    "csotany",
    "denever",
    "poloska",
    "patkany",
    "légy",
    "varangy",
    "skorpió",
    "pók",
]


class GameLogic:
    def __init__(self, id, players, from_db=False):
        self.state = GameState(id, f"{id}.pkl")
        self.state.players = players
        self.state.active_player = self.choose_starting_player()
        self.generate_deck()
        self.shuffle_deck()
        self.deal_cards()

    def generate_deck(self):
        deck_cards = []
        for type in TYPES:
            for i in range(1, 9):
                deck_cards.append(Card(type, i))
        self.state.deck = deck_cards

    def shuffle_deck(self):
        deck_list = list(self.state.deck)
        shuffle(deck_list)
        if len(self.state.players) == 2:
            deck_list = deck_list[:-10]
        self.state.deck = deck_list

    def deal_cards(self):
        player_count = len(self.state.players)
        deck_size = len(self.state.deck)
        portions = deck_size // player_count
        for i in range(player_count):
            self.state.players[i].cards_in_hand = self.state.deck[
                i * portions : (i + 1) * portions
            ]
        for player in self.state.players:
            player.card_count = len(player.cards_in_hand)

    def choose_starting_player(self):
        return choice(self.state.players)

    def has_cards_in_hand(self):
        return len(self.state.active_player.cards_in_hand) == 0

    def has_4_cards_in_front(self):
        if len(self.state.players) == 2:
            lose_count = 5
        else:
            lose_count = 4
        for card_type, count in self.state.active_player.cards_in_front.items():
            if count >= lose_count:
                return True
        return False

    def select_target_player(self, name):
        for player in self.state.players:
            if player.name == name:
                self.state.targeted_player = player
                break

    def select_card(self, selected_card_id=None):
        for card in self.state.active_player.cards_in_hand:
            if card.name == selected_card_id:
                self.state.question_card = card
                self.state.active_player.cards_in_hand.remove(card)

                self.state.active_player.card_count = len(
                    self.state.active_player.cards_in_hand
                )

                if (
                    self.state.active_player.name
                    not in self.state.question_card.visited_already
                ):
                    self.state.question_card.visited_already.append(
                        self.state.active_player.name
                    )
                return

    def make_statement(self, statement=None):
        self.state.active_player.statement = statement

    def check_truth(self, answer):
        self.state.targeted_player.is_true = answer
        if self.state.targeted_player.is_true is True:
            if self.state.active_player.statement == self.state.question_card.type:
                print("correct answer")
                return True
            else:
                print("wrong answer")
                return False
        elif self.state.targeted_player.is_true is False:
            if self.state.active_player.statement != self.state.question_card.type:
                print("correct answer")
                return True
            else:
                print("wrong answer")
                return False

    def place_card(self, player):
        # A játékos elhelyezi a kérdéskártyát maga előtt
        card_type = self.state.question_card.type
        if card_type not in player.cards_in_front:
            player.cards_in_front[card_type] = 1
        else:
            player.cards_in_front[card_type] += 1

        # Visszaállítjuk az aktív játékost az új játékosra
        self.state.active_player = player
