from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_serializer

from csotanypoker.models.animal import Animal


class AbstractPlayer(BaseModel):
    username: str = Field(..., description="Játékos felhasználónév")
    cards_in_front: Dict[Animal, int] = Field(default_factory=dict)
    statement: Optional[str] = None
    is_true: Optional[bool] = None

    @field_serializer("cards_in_front")
    def serialize_cards_in_front(self, value):
        return {animal.value: count for animal, count in value.items()}

    def card_count(self) -> int:
        raise NotImplementedError


class VisiblePlayer(AbstractPlayer):
    cards_in_hand: List[Animal] = Field(
        default_factory=list, description="Kézbeli kártyák"
    )

    @field_serializer("cards_in_hand")
    def serialize_cards_in_hand(self, value):
        return [animal.value for animal in value]

    def card_count(self) -> int:
        return len(self.cards_in_hand)


class OpponentPlayer(AbstractPlayer):
    card_count_int: int = Field(default=0, description="Kártyák száma")

    def card_count(self) -> int:
        return self.card_count_int
