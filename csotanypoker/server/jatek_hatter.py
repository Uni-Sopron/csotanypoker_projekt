from random import choice, shuffle

from sqlalchemy.orm import Session

from csotanypoker.models.model import Card, GameState
from csotanypoker.server.adatbazis import DBCard, DBPlayer, get_db_session

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
    def __init__(self, players, from_db=False):
        self.state = GameState()

        self.state.players = players
        self.state.active_player = self.choose_starting_player()
        self.generate_deck()
        self.shuffle_deck()
        self.deal_cards()

    def generate_deck(self):
        for type in TYPES:
            for i in range(1, 9):
                self.state.deck.append(Card(type, i))

    def shuffle_deck(self):
        shuffle(self.state.deck)
        if len(self.state.players) == 2:
            self.state.deck = self.state.deck[:-10]

    def deal_cards(self):
        player_count = len(self.state.players)
        deck_size = len(self.state.deck)
        portions = deck_size // player_count
        for i in range(player_count):
            self.state.players[i].cards_in_hand = self.state.deck[
                i * portions : (i + 1) * portions
            ]

    def choose_starting_player(self):
        return choice(self.state.players)

    def has_cards_in_hand(self):
        return self.state.active_player.cards_in_hand == []

    def has_4_cards_in_front(self):
        for kartya, db in self.state.active_player.cards_in_front.items():
            if db == 4:
                return True
        return False

    def select_target_player(self, name):
        for i in self.state.players:
            if name == i.name:
                self.state.targeted_player = i
                break

    def select_card(self, selected_card_id=None):
        db: Session = get_db_session()
        player_db = (
            db.query(DBPlayer)
            .filter(DBPlayer.name == self.state.active_player.name)
            .first()
        )

        for card in self.state.active_player.cards_in_hand:
            if card.name == selected_card_id:
                self.state.question_card = card
                selected_card = (
                    db.query(DBCard)
                    .filter(DBCard.name == self.state.question_card.name)
                    .first()
                )
                self.state.active_player.cards_in_hand.remove(card)  # Remove the card
                if (
                    self.state.active_player.name
                    not in self.state.question_card.visited_already
                ):
                    self.state.question_card.visited_already.append(
                        self.state.active_player.name
                    )
                    selected_card.previous_holders.append(player_db)
                    db.commit()
                return

    def make_statement(self, statement=None):
        db: Session = get_db_session()
        player = (
            db.query(DBPlayer)
            .filter(DBPlayer.name == self.state.active_player.name)
            .first()
        )
        player.statement = statement
        db.commit()
        self.state.active_player.statement = statement  # The current player's statement

    def check_truth(self, answer):
        self.state.targeted_player.is_true = answer  # The current player's answer
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
        db: Session = get_db_session()
        selected_card = (
            db.query(DBCard)
            .filter(DBCard.name == self.state.question_card.name)
            .first()
        )
        player_db = db.query(DBPlayer).filter(DBPlayer.name == player.name).first()
        player_db.front_cards.append(selected_card)

        db.commit()

        if self.state.question_card.type not in player.cards_in_front:
            player.cards_in_front[self.state.question_card.type] = 1

        else:
            player.cards_in_front[self.state.question_card.type] += 1

        self.state.active_player = player
