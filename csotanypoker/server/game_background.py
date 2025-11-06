import os
from random import choice, shuffle
from csotanypoker.models.animal import Animal
from csotanypoker.server.gamestate import GameState


class GameLogic:
    def __init__(self, id, players, room_id=None, from_db=False):
        data_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '.')
        save_dir = os.path.join(data_dir, "games_saves")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"game_{id}.pkl")

        if not from_db:
            self.state = GameState(
                game_id=id,
                room_id=room_id,
                save_path=save_path,
            )

            self.state.players = players

            self.state.active_player = self.choose_starting_player()
            self.deck = []
            self.generate_deck()
            self.shuffle_deck()
            self.deal_cards()
        else:
            self.state = GameState.load_from_file(save_path)
            if self.state is None:
                raise ValueError(f"Failed to load GameState from {save_path}")

        self.state.manual_save()

    def generate_deck(self):
        deck_cards = []
        for type in Animal:
            for i in range(1, 9):
                deck_cards.append(Animal(type))
        self.deck = deck_cards

        self.deck = [animal for animal in Animal for _ in range(8)]

    def shuffle_deck(self):
        deck_list = list(self.deck)
        shuffle(deck_list)
        if len(self.state.players) == 2:
            deck_list = deck_list[:-10]
        self.deck = deck_list

    def deal_cards(self):
        player_count = len(self.state.players)
        deck_size = len(self.deck)
        portions = deck_size // player_count
        for i in range(player_count):
            self.state.players[i].cards_in_hand = self.deck[
                i * portions : (i + 1) * portions
            ]
        

    def choose_starting_player(self):
        return choice(self.state.players)

    def has_cards_in_hand(self):
        return len(self.state.active_player.cards_in_hand) == 0

    def has_4_cards_in_front(self):
        if len(self.state.players) == 2:
            lose_count = 5
        else:
            lose_count = 4
        for player in self.state.players:
            for card_type, count in player.cards_in_front.items():
                if count >= lose_count:
                    self.state.active_player = player
                    return True
        return False

    def select_target_player(self, name):
        for player in self.state.players:
            if player.username == name:
                self.state.targeted_player = player
                break

    def select_card(self, selected_card=None, passing=None):
        for card in self.state.active_player.cards_in_hand:
            if card == selected_card:
                self.state.question_card = card
                if not passing:
                    self.state.active_player.cards_in_hand.remove(card)

                if self.state.active_player.username not in self.state.visited_already:
                    self.state.visited_already.add(self.state.active_player.username)
                return

    def make_statement(self, statement=""):
        self.state.active_player.statement = statement

    def check_truth(self, answer):
        self.state.targeted_player.is_true = answer
        if self.state.targeted_player.is_true is True:
            if self.state.active_player.statement == self.state.question_card.value:
                return True
            else:
                return False
        elif self.state.targeted_player.is_true is False:
            if self.state.active_player.statement != self.state.question_card.value:
                return True
            else:
                return False

    def place_card(self, player):
       
        card_type = self.state.question_card
        if card_type not in player.cards_in_front:
            player.cards_in_front[card_type] = 1
        else:
            player.cards_in_front[card_type] += 1
        return player
