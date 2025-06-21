from typing import List, Optional, Callable, Iterable

from csotanypoker.models.card import Card
from csotanypoker.models.player import Player
from csotanypoker.models.room import Room
import pickle


class AutoSavingList(list):
    def __init__(
        self, iterable: Optional[Iterable] = None, callback: Optional[Callable] = None
    ):
        super().__init__(iterable or [])
        self._callback = callback

    def _trigger(self):
        if self._callback:
            self._callback()

    def append(self, item):
        super().append(item)
        self._trigger()

    def remove(self, item):
        super().remove(item)
        self._trigger()


class GameState:
    def __init__(self, id=None, save_path=None):
        self.id: Optional[str] = id
        self._save_path: Optional[str] = save_path

        self._players: AutoSavingList[Player] = AutoSavingList(callback=self._save)
        self._deck: AutoSavingList[Card] = AutoSavingList(callback=self._save)
        self._active_player: Optional[Player] = None
        self._targeted_player: Optional[Player] = None
        self._question_card: Optional[Card] = None

        self._game_status: str = "run"  # "run" vagy "end"
        self._voters: set[str] = set()
        self._loser_username: str = ""
        self._save()

    def _save(self):
        if self._save_path is not None:
            with open(self._save_path, "wb") as f:
                pickle.dump(self, f)

    # TODO: Vissza kell olvasni az adatokat
    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        self._players = AutoSavingList(value, callback=self._save)
        self._save()

    @property
    def deck(self):
        return self._deck

    @deck.setter
    def deck(self, value):
        self._deck = AutoSavingList(value, callback=self._save)
        self._save()

    @property
    def active_player(self):
        return self._active_player

    @active_player.setter
    def active_player(self, value):
        self._active_player = value
        self._save()

    @property
    def targeted_player(self):
        return self._targeted_player

    @targeted_player.setter
    def targeted_player(self, value):
        self._targeted_player = value
        self._save()

    @property
    def question_card(self):
        return self._question_card

    @question_card.setter
    def question_card(self, value):
        self._question_card = value
        self._save()

    @property
    def game_status(self) -> str:
        return self._game_status

    @game_status.setter
    def game_status(self, value: str) -> None:
        self._game_status = value
        self._save()

    @property
    def voters(self) -> List[str]:
        return self._voters

    @voters.setter
    def voters(self, value: List[str]) -> None:
        self._voters = value
        self._save()

    @property
    def loser_username(self) -> str:
        return self._loser_username

    @loser_username.setter
    def loser_username(self, value: str) -> None:
        self._loser_username = value
        self._save()
