from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Set

from csotanypoker.models.animal import Animal


class AbstractGameState(BaseModel):
    game_id: str = Field("", description="Játék egyedi azonosítója")
    room_id: str = Field("", description="Szoba azonosítója")
    question_card: Optional[Animal] = Field(None, description="Kérdéses kártya")
    visited_already: Set[str] = Field(
        set(), description="Azoknak a neve akiknél már volt a kérdéses kártya"
    )
    voters: Set[str] = Field(set(), description="Szavazók nevei")
    passing: bool = Field(
        False, description="Jelzi, hogy a játékos passzol-e ebben a körben"
    )
    card_played: bool = Field(
        False, description="Jelzi, hogy a játékos kijátszotta-e a kártyáját"
    )


class ClientGameState(AbstractGameState):
    active_player_name: str = Field("", description="Aktív játékos neve")
    targeted_player_name: Optional[str] = Field(
        None, description="Célzott játékos neve"
    )

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
