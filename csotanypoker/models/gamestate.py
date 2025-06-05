from typing import List, Optional

from csotanypoker.models.card import Card
from csotanypoker.models.player import Player


class GameState:
    def __init__(self):
        self._players = []
        self._deck = []
        self._active_player = None
        self._targeted_player = None
        self._question_card: Optional[Card] = None

    @property
    def players(self) -> List[Player]:
        return self._players

    @players.setter
    def players(self, value: List[Player]) -> None:
        self._players = value

    @property
    def deck(self) -> List[Card]:
        return self._deck

    @deck.setter
    def deck(self, value: List[Card]) -> None:
        self._deck = value

    @property
    def active_player(self) -> Optional[Player]:
        return self._active_player

    @active_player.setter
    def active_player(self, value: Optional[Player]) -> None:
        self._active_player = value

    @property
    def targeted_player(self) -> Optional[Player]:
        return self._targeted_player

    @targeted_player.setter
    def targeted_player(self, value: Optional[Player]) -> None:
        self._targeted_player = value

    @property
    def question_card(self) -> Optional[Card]:
        return self._question_card

    @question_card.setter
    def question_card(self, value: Optional[Card]) -> None:
        self._question_card = value
