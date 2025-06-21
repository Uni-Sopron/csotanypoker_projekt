from typing import Any, Dict, List, Optional

from csotanypoker.models.card import Card


class Player:
    def __init__(self, nev):
        self._name:str = nev
        self._cards_in_hand:List[Card] = []
        self._cards_in_front:Dict[str, int]  = {}
        self._card_count:int= 0
        self._statement: Optional[str] = None  # allitás amit a kártyárol tett (allat tipusa)
        self._is_true :Optional[bool]= None  # a játkos szerint igazat vagy hamis az az állitás amit mondtak neki (true/false)

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
