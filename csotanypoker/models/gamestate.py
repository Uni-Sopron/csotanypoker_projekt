from pydantic import BaseModel, Field, ConfigDict
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
    question_card: Optional[dict] = Field(None, description="Kérdéses kártya")
    visited_already: Optional[List[str]] = Field(
        None, description="Azoknak a neve akiknél már volt a kérdéses kártya"
    )
    voters: Optional[Set[str]] = Field(None, description="Szavazók nevei")


class GameState(AbstractGameState):
    save_path: Optional[str] = Field(
        None, alias="_save_path", description="Mentési útvonal"
    )
    active_player: Union[VisiblePlayer, OpponentPlayer] = Field(
        ..., description="Aktív játékos"
    )
    targeted_player: OpponentPlayer = Field(..., description="Célzott játékos")
    players: Optional[Set[Union[VisiblePlayer, OpponentPlayer]]] = Field(
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
    """Kliens oldali játékállapot"""

    active_player: Optional[str] = Field(None, description="Aktív játékos neve")
    targeted_player: Optional[str] = Field(None, description="Célzott játékos neve")
    question_card: Optional[Animal] = Field(
        None, description="Kérdés kártya állat enum"
    )


# class GameState(BaseModel):
#     model_config = ConfigDict(arbitrary_types_allowed=True, validate_by_name=True)

#     id: Optional[str] = None
#     save_path: Optional[str] = Field(None, alias="_save_path")

#     active_player: Optional[dict] = None
#     targeted_player: Optional[dict] = None
#     question_card: Optional[dict] = None
#     game_status: Literal["run", "end"] = "run"
#     loser_username: str = ""

#     def __init__(self, players=None, deck=None, voters=None, **data):
#         super().__init__(**data)
#         # ki kell kerülni a __setattr__ hívását, mert az AutoSavingSet osztályban is van __setattr__ és az végtelen ciklust okozna
#         object.__setattr__(self, "_save_enabled", True)
#         object.__setattr__(
#             self, "players", AutoSavingSet(players or set(), callback=self._save)
#         )
#         object.__setattr__(
#             self, "deck", AutoSavingSet(deck or set(), callback=self._save)
#         )
#         object.__setattr__(
#             self, "voters", AutoSavingSet(voters or set(), callback=self._save)
#         )

#         self._save()

#     def __setattr__(self, name, value):
#         if name in ["players", "deck", "voters"]:
#             object.__setattr__(self, name, value)
#         else:
#             super().__setattr__(name, value)
#             if hasattr(self, "_save_enabled") and not name.startswith("_"):
#                 self._save()

#     def _save(self):
#         if not getattr(self, "_save_enabled", False) or self.save_path is None:
#             return
#         try:
#             directory = os.path.dirname(self.save_path)
#             if directory and not os.path.exists(directory):
#                 os.makedirs(directory)
#             with open(self.save_path, "wb") as f:
#                 pickle.dump(self, f)
#         except Exception as e:
#             print(f"Hiba a mentés során: {e}")

#     @classmethod
#     def load_from_file():
#         pass
