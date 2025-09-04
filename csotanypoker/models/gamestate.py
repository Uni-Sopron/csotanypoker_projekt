from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import List, Optional, Literal, Callable, Iterable, Set, Union
import pickle
import os
from csotanypoker.models.animal import Animal
from csotanypoker.models.player import OpponentPlayer, VisiblePlayer


class AutoSavingSet(set):
    def __init__(
        self, iterable: Optional[Iterable] = None, callback: Optional[Callable] = None
    ):
        super().__init__(iterable)
        self._callback = callback

        def _save(self):
            if self._callback:
                self._callback()

        def add(self, item):
            super().add(item)
            self._save()

        def remove(self, item):
            super().remove(item)
            self._save()

        def discard(self, item):
            super().discard(item)
            self._save()

        def pop(self):
            result = super().pop()
            self._save()
            return result

        def clear(self):
            super().clear()
            self._save()

        def update(self, *others):
            super().update(*others)
            self._save()


class AbstractGameState(BaseModel):
    game_id: Optional[str] = Field(None, description="Játék egyedi azonosítója")
    room_id: Optional[str] = Field(None, description="Szoba azonosítója")
    question_card: Optional[Animal] = Field(None, description="Kérdéses kártya")
    visited_already: Optional[List[str]] = Field(
        [], description="Azoknak a neve akiknél már volt a kérdéses kártya"
    )
    voters: Optional[Set[str]] = Field(set(), description="Szavazók nevei")


class GameState(AbstractGameState):
    save_path: Optional[str] = Field(
        None, alias="_save_path", description="Mentési útvonal"
    )
    active_player: Optional[VisiblePlayer] = Field(None, description="Aktív játékos")
    targeted_player: Optional[VisiblePlayer] = Field(
        None, description="Célzott játékos"
    )
    players: Optional[Set[VisiblePlayer]] = Field(
        None, description="Összes játékos a játékban"
    )

    def _save(self):
        if not getattr(self, "_save_enabled", False) or self.save_path is None:
            return
        try:
            directory = os.path.dirname(self.save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(self.save_path, "wb") as f:
                pickle.dump(self, f)
        except Exception as e:
            print(f"Hiba a mentés során: {e}")

    @classmethod
    def load_from_file():
        pass


class ClientGameState(AbstractGameState):
    active_player: Optional[str] = Field(None, description="Aktív játékos neve")
    targeted_player: Optional[str] = Field(None, description="Célzott játékos neve")

    @field_serializer("question_card")
    def serialize_question_card(self, value):
        if value is None:
            return None
        return value.value 

    @field_serializer("voters")
    def serialize_voters(self, value):
        if value is None:
            return None
        return list(value)  
