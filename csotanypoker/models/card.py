from typing import  List

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
