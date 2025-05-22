from typing import Any, Dict, List, Optional


class Card:
    def __init__(self, type, index):
        self._name = f"{type}_{index}"
        self._type = type
        self._index = index
        self._visited_already = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        self._type = value
        self._name = f"{self._type}_{self._index}"

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int) -> None:
        self._index = value
        self._name = f"{self._type}_{self._index}"

    @property
    def visited_already(self) -> List:
        return self._visited_already

    @visited_already.setter
    def visited_already(self, value: List) -> None:
        self._visited_already = value

    @property
    def type(self) -> str:
        return self._name.split("_")[0]

    @type.setter
    def type(self, value: str) -> None:
        self._type = value
        self._name = f"{value}_{self._index}"


class Player:
    def __init__(self, nev):
        self._name = nev
        self._cards_in_hand = []
        self._cards_in_front = {}
        self._card_count = 0
        self._statement = None
        self._is_true = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def cards_in_hand(self) -> List:
        return self._cards_in_hand

    @cards_in_hand.setter
    def cards_in_hand(self, value: List) -> None:
        self._cards_in_hand = value

    @property
    def cards_in_front(self) -> Dict:
        return self._cards_in_front

    @cards_in_front.setter
    def cards_in_front(self, value: Dict) -> None:
        self._cards_in_front = value

    @property
    def card_count(self) -> int:
        return self._card_count

    @card_count.setter
    def card_count(self, value: int) -> None:
        self._card_count = value

    @property
    def statement(self) -> Any:
        return self._statement

    @statement.setter
    def statement(self, value: Any) -> None:
        self._statement = value

    @property
    def is_true(self) -> bool:
        return self._is_true

    @is_true.setter
    def is_true(self, value: bool) -> None:
        self._is_true = value


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
