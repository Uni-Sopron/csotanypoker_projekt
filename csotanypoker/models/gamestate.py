from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import List, Optional, Callable, Iterable, Set, Any
import pickle
import os
from csotanypoker.models.animal import Animal
from csotanypoker.models.player import VisiblePlayer

from csotanypoker.server.ai_player import AIPlayer


class AutoSavingSet(set):
    def __init__(
        self, iterable: Optional[Iterable] = None, callback: Optional[Callable] = None
    ):
        super().__init__(iterable or [])
        self.callback = callback

    def _save(self):
        if self.callback:
            self.callback()

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
    visited_already: Optional[Set[str]] = Field(
        set(), description="Azoknak a neve akiknél már volt a kérdéses kártya"
    )
    voters: Optional[Set[str]] = Field(set(), description="Szavazók nevei")


class GameState(AbstractGameState):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    save_path: Optional[str] = Field(None, description="Mentési útvonal")
    active_player: Optional[VisiblePlayer] = Field(None, description="Aktív játékos")
    targeted_player: Optional[VisiblePlayer] = Field(
        None, description="Célzott játékos"
    )
    players: Optional[List[VisiblePlayer]] = Field(
        None, description="Összes játékos a játékban"
    )
    ai_player: Optional[AIPlayer] = Field(None, description="AI játékos objektum")


    def __init__(self, **data):
        save_path = data.get("save_path")
        super().__init__(**data)

        if self.visited_already is None:
            self.visited_already = AutoSavingSet([], self._save)
        else:
            self.visited_already = AutoSavingSet(self.visited_already, self._save)

        if self.voters is None:
            self.voters = AutoSavingSet([], self._save)
        else:
            self.voters = AutoSavingSet(self.voters, self._save)

        if self.players is None:
            self.players = []
        if self.ai_player is None:
            from csotanypoker.server.ai_player import AIPlayer

            self.ai_player = AIPlayer()


        if save_path:
            directory = os.path.dirname(save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

        if name != "save_path" and self.save_path is not None:
            try:
                self._save()
            except Exception as e:
                print(f"Warning: Failed to auto-save GameState: {e}")

    def _save(self):
        """Save the current state to pickle file"""
        if self.save_path is None:
            return

        try:
            directory = os.path.dirname(self.save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(self.save_path, "wb") as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"GameState saved successfully: {self.save_path}")

        except Exception as e:
            print(f"Error saving GameState to {self.save_path}: {e}")

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["GameState"]:
        """Load GameState from pickle file"""
        try:
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return None

            with open(file_path, "rb") as f:
                game_state = pickle.load(f)

            if not isinstance(game_state, cls):
                print(f"Loaded object is not a GameState instance: {type(game_state)}")
                return None

            game_state.save_path = file_path
            if game_state.visited_already is not None:
                game_state.visited_already = AutoSavingSet(
                    game_state.visited_already, game_state._save
                )

            if game_state.voters is not None:
                game_state.voters = AutoSavingSet(game_state.voters, game_state._save)

            print(
                f"GameState loaded successfully: {file_path}, room_id: {game_state.room_id}"
            )
            return game_state

        except Exception as e:
            print(f"Error loading GameState from {file_path}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def manual_save(self):
        """Force a manual save"""
        if self.save_path is None:
            print("Warning: Cannot save - no save_path specified")
            return False

        try:
            self._save()
            return True
        except Exception as e:
            print(f"Manual save failed: {e}")
            return False

    @classmethod
    def create_with_autosave(cls, save_path: str, **kwargs) -> "GameState":
        """Create new GameState with automatic saving enabled"""
        game_state = cls(save_path=save_path, **kwargs)

        game_state.manual_save()
        return game_state


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

    @field_serializer("visited_already")
    def serialize_visited_already(self, value):
        if value is None:
            return None
        return list(value)
